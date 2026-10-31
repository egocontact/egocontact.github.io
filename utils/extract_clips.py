#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import cv2
from tqdm.auto import tqdm

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None

try:
    from annotation_utils import dedupe_preserve_order, load_annotations, parse_sample_ids_csv, read_sample_ids_file
except ImportError:
    from utils.annotation_utils import (
        dedupe_preserve_order,
        load_annotations,
        parse_sample_ids_csv,
        read_sample_ids_file,
    )


def non_negative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        raise argparse.ArgumentTypeError("Value must be non-negative.")
    return parsed


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("Value must be positive.")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract per-sample interaction clips from Ego4D source videos."
    )
    parser.add_argument("--annotations-json", required=True, help="Path to keyed annotations JSON.")
    parser.add_argument("--clip-dir", required=True, help="Directory containing raw Ego4D clips.")
    parser.add_argument("--output-dir", required=True, help="Directory to write extracted sample clips to.")
    parser.add_argument(
        "--frames-post-contact",
        type=non_negative_int,
        default=0,
        help="Extra frames to include after the contact frame.",
    )
    parser.add_argument(
        "--workers",
        type=positive_int,
        default=1,
        help="Number of clips to extract concurrently.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip samples whose output clip already exists and is non-empty.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--sample-ids-file",
        help="Text file containing one sample_id per line.",
    )
    group.add_argument(
        "--sample-ids",
        help="Comma-separated list of sample_ids.",
    )
    group.add_argument(
        "--tsne-json",
        help="Path to tsne_points.json; extracts clips for all IDs in it.",
    )
    parser.add_argument(
        "--output-json",
        help="If given (with --tsne-json), write tsne JSON enriched with video paths here.",
    )
    return parser.parse_args()


def load_requested_sample_ids(args: argparse.Namespace) -> list[str]:
    if args.sample_ids_file:
        return dedupe_preserve_order(read_sample_ids_file(args.sample_ids_file))
    if args.tsne_json:
        with open(args.tsne_json) as f:
            entries = json.load(f)
        return dedupe_preserve_order([e["id"] for e in entries])
    return dedupe_preserve_order(parse_sample_ids_csv(args.sample_ids))


def get_ffmpeg_exe() -> str:
    if imageio_ffmpeg is None:
        raise RuntimeError(
            "Missing dependency `imageio-ffmpeg`. Install it with "
            "`python -m pip install imageio-ffmpeg`."
        )

    try:
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:
        raise RuntimeError("Unable to locate the ffmpeg binary from `imageio-ffmpeg`.") from exc


def extract_clip(
    sample_id: str,
    record: dict,
    clip_dir: Path,
    output_dir: Path,
    frames_post_contact: int,
    ffmpeg_exe: str,
    skip_existing: bool,
) -> tuple[bool, str]:
    clip_path = clip_dir / f"{record['clip_id']}.mp4"
    if not clip_path.exists():
        return False, f"{sample_id}: source clip not found at {clip_path}"

    fps = float(record["fps"])
    start_frame = int(record["first_prediction_frame"])
    end_frame = int(record["contact_frame"]) + frames_post_contact
    n_frames = end_frame - start_frame + 1
    if n_frames <= 0:
        return False, f"{sample_id}: invalid frame range {start_frame}..{end_frame}"

    output_path = output_dir / f"{sample_id}.mp4"
    if skip_existing and output_path.exists():
        if output_path.stat().st_size > 0:
            return True, f"{sample_id}: skipped existing clip at {output_path}"
        output_path.unlink(missing_ok=True)

    capture: cv2.VideoCapture | None = None
    process: subprocess.Popen[bytes] | None = None

    try:
        capture = cv2.VideoCapture(str(clip_path))
        if not capture.isOpened():
            return False, f"{sample_id}: failed to open source clip {clip_path}"

        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width <= 0 or height <= 0:
            return False, f"{sample_id}: could not read frame size from {clip_path}"

        total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        if total_frames and start_frame >= total_frames:
            return False, (
                f"{sample_id}: start frame {start_frame} exceeds clip length "
                f"({total_frames} frames)"
            )

        capture.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        cmd = [
            ffmpeg_exe,
            "-y",
            "-loglevel",
            "error",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "bgr24",
            "-s:v",
            f"{width}x{height}",
            "-r",
            f"{fps:.6f}",
            "-i",
            "-",
            "-an",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ]
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )

        frames_written = 0
        for _ in range(n_frames):
            ok, frame = capture.read()
            if not ok:
                break
            if process.stdin is None:
                raise RuntimeError("ffmpeg stdin is unavailable.")
            process.stdin.write(frame.tobytes())
            frames_written += 1

        if process.stdin is not None:
            process.stdin.close()
        stderr = process.stderr.read().decode("utf-8", errors="replace") if process.stderr else ""
        returncode = process.wait()

        if frames_written == 0:
            output_path.unlink(missing_ok=True)
            return False, f"{sample_id}: no frames extracted from {clip_path}"

        if returncode != 0:
            output_path.unlink(missing_ok=True)
            detail = stderr.strip().splitlines()[-1] if stderr.strip() else "unknown ffmpeg error"
            return False, f"{sample_id}: ffmpeg error: {detail}"

        return True, (
            f"{sample_id}: wrote {frames_written} frames "
            f"({start_frame}..{start_frame + frames_written - 1}) to {output_path}"
        )
    except Exception as exc:
        if output_path.exists():
            output_path.unlink(missing_ok=True)
        return False, f"{sample_id}: {exc}"
    finally:
        if capture is not None:
            capture.release()
        if process is not None:
            if process.stdin is not None and not process.stdin.closed:
                process.stdin.close()
            if process.poll() is None:
                process.kill()
                process.wait()


def log_progress_message(completed: int, total: int, ok: bool, message: str, use_tqdm: bool) -> None:
    formatted = f"[{completed}/{total}] {message}"
    stream = sys.stdout if ok else sys.stderr
    if use_tqdm:
        tqdm.write(formatted, file=stream)
    else:
        print(formatted, file=stream)


def main() -> int:
    args = parse_args()

    try:
        annotations = load_annotations(args.annotations_json)
        requested_sample_ids = load_requested_sample_ids(args)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    missing_sample_ids = [sample_id for sample_id in requested_sample_ids if sample_id not in annotations]
    if missing_sample_ids:
        print("Error: the following sample IDs were not found in the annotations JSON:", file=sys.stderr)
        for sample_id in missing_sample_ids:
            print(f"  - {sample_id}", file=sys.stderr)
        return 1

    clip_dir = Path(args.clip_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        ffmpeg_exe = get_ffmpeg_exe()
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    failures: list[str] = []
    total = len(requested_sample_ids)
    completed = 0
    use_tqdm = sys.stderr.isatty()
    with tqdm(
        total=total,
        desc="Extracting clips",
        unit="clip",
        dynamic_ncols=True,
        disable=not use_tqdm,
    ) as progress_bar:
        if args.workers == 1:
            for sample_id in requested_sample_ids:
                ok, message = extract_clip(
                    sample_id=sample_id,
                    record=annotations[sample_id],
                    clip_dir=clip_dir,
                    output_dir=output_dir,
                    frames_post_contact=args.frames_post_contact,
                    ffmpeg_exe=ffmpeg_exe,
                    skip_existing=args.skip_existing,
                )
                completed += 1
                progress_bar.update(1)
                log_progress_message(completed, total, ok, message, use_tqdm)
                if not ok:
                    failures.append(message)
        else:
            with ThreadPoolExecutor(max_workers=args.workers) as executor:
                future_to_sample_id = {
                    executor.submit(
                        extract_clip,
                        sample_id=sample_id,
                        record=annotations[sample_id],
                        clip_dir=clip_dir,
                        output_dir=output_dir,
                        frames_post_contact=args.frames_post_contact,
                        ffmpeg_exe=ffmpeg_exe,
                        skip_existing=args.skip_existing,
                    ): sample_id
                    for sample_id in requested_sample_ids
                }
                for future in as_completed(future_to_sample_id):
                    sample_id = future_to_sample_id[future]
                    try:
                        ok, message = future.result()
                    except Exception as exc:
                        ok, message = False, f"{sample_id}: {exc}"
                    completed += 1
                    progress_bar.update(1)
                    log_progress_message(completed, total, ok, message, use_tqdm)
                    if not ok:
                        failures.append(message)

    if failures:
        print(f"Extraction finished with {len(failures)} failure(s).", file=sys.stderr)

    print(f"Extraction finished: {len(requested_sample_ids) - len(failures)} succeeded, {len(failures)} failed.")

    # Enrich tsne JSON with video paths if requested
    if args.tsne_json and args.output_json:
        failed_ids = {msg.split(":")[0] for msg in failures}
        with open(args.tsne_json) as f:
            tsne_entries = json.load(f)
        enriched = []
        for entry in tsne_entries:
            sid = entry["id"]
            if sid not in failed_ids and (output_dir / f"{sid}.mp4").exists():
                enriched.append({**entry, "video": str(output_dir / f"{sid}.mp4")})
            else:
                enriched.append(entry)
        output_json_path = Path(args.output_json)
        output_json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_json_path, "w") as f:
            json.dump(enriched, f, indent=2)
        print(f"Wrote enriched JSON to {output_json_path}.")

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
