"""Export the existing t-SNE selection as WebP spacetime samples.

Run from the repository root with /usr/bin/python3 scripts/prepare_explorer.py.
Requires OpenCV with WebP support. Decode original Ego4D clips, since legacy
trimmed MP4 offsets are not recorded. Never infer contacts or temporal offsets.
"""

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import math
from pathlib import Path

import cv2


def validate(annotation):
    observation = annotation['last_prediction_frame']
    contact = annotation['contact_frame']
    if not 0 <= observation < contact or annotation['fps'] <= 0:
        raise ValueError('Invalid temporal interval or frame rate')
    for frame in (observation, contact):
        anchors = annotation['per_frame_annotations'].get(str(frame), {})
        for key in ('contact_thumb', 'contact_index'):
            point = anchors.get(key)
            if not point or any(
                not isinstance(point.get(axis), (int, float))
                or not math.isfinite(point[axis])
                or not 0 <= point[axis] < annotation[dimension]
                for axis, dimension in (('x', 'frame_width'), ('y', 'frame_height'))
            ):
                raise ValueError(f'Missing or invalid {key} at frame {frame}')


def export_sample(row, annotation, videos, output, quality):
    event = row['id']
    observation = annotation['last_prediction_frame']
    contact = annotation['contact_frame']
    count = min(24, contact - observation + 1)
    indices = sorted({round(observation + (contact - observation) * i / (count - 1))
                      for i in range(count)})
    directory = output / event
    directory.mkdir(parents=True, exist_ok=True)
    capture = cv2.VideoCapture(str(videos / f"{annotation['clip_id']}.mp4"))
    try:
        if not capture.isOpened():
            raise RuntimeError(f'{event}: cannot open source clip')
        width, height = annotation['frame_width'], annotation['frame_height']
        if (int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))) != (width, height):
            raise RuntimeError(f'{event}: source dimensions do not match annotations')
        if not capture.set(cv2.CAP_PROP_POS_FRAMES, observation):
            raise RuntimeError(f'{event}: cannot seek to observation')
        if round(capture.get(cv2.CAP_PROP_POS_FRAMES)) != observation:
            raise RuntimeError(f'{event}: unexpected source frame position')
        frames = []
        for index in range(observation, contact + 1):
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError(f'{event}: cannot decode frame {index}')
            if index not in indices:
                continue
            resized = cv2.resize(frame, (480, round(480 * height / width)),
                                 interpolation=cv2.INTER_AREA)
            filename = f'{len(frames):03d}.webp'
            if not cv2.imwrite(str(directory / filename), resized,
                               [cv2.IMWRITE_WEBP_QUALITY, quality]):
                raise RuntimeError(f'{event}: cannot write {filename}')
            frames.append({'index': index, 'src': f'/data/explorer/{event}/{filename}'})
    finally:
        capture.release()

    semantic = annotation['semantic_annotation']
    action = semantic.get('interaction_description') or annotation['action_label']
    manifest = {
        'event': event, 'action': action, 'width': width, 'height': height,
        'fps': annotation['fps'], 'first': observation,
        'observation': observation, 'contact': contact,
        'anchors': {str(frame): annotation['per_frame_annotations'][str(frame)]
                    for frame in (observation, contact)},
        'frames': frames,
    }
    (directory / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return {
        'id': event, 'object': semantic['object'], 'verb': semantic['action'],
        'action': action, 'manifestUrl': f'/data/explorer/{event}/manifest.json',
        'frames': [
            {'src': frames[0]['src'], 'label': 'Before contact',
             'description': f"{semantic['object']} before contact"},
            {'src': frames[-1]['src'], 'label': 'At contact',
             'description': f"{semantic['object']} at first contact"},
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection', type=Path, default=Path('static/data/tsne.json'))
    parser.add_argument('--annotations', type=Path,
                        default=Path('data/EgoContact/annotations/24_04_2026.json'))
    parser.add_argument('--videos', type=Path, default=Path('data/Ego4D'))
    parser.add_argument('--quality', type=int, choices=range(1, 101), default=80)
    parser.add_argument('--workers', type=int, default=4)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error('--workers must be positive')
    cv2.setNumThreads(1)
    annotations = json.loads(args.annotations.read_text())
    selection = json.loads(args.selection.read_text())
    eligible, skipped = [], []
    for row in selection:
        try:
            validate(annotations[row['id']])
        except (KeyError, ValueError) as error:
            skipped.append({'id': row['id'], 'object': row['label'], 'reason': str(error)})
        else:
            eligible.append(row)
    output = Path('static/data/explorer')
    output.mkdir(parents=True, exist_ok=True)
    # Preserve selection order regardless of worker completion order.
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        results = pool.map(lambda row: export_sample(
            row, annotations[row['id']], args.videos, output, args.quality), eligible)
        samples = []
        for sample in results:
            samples.append(sample)
            if len(samples) % 25 == 0:
                print(f'Exported {len(samples)}/{len(eligible)}', flush=True)
    Path('src/lib/data/explorer-samples.json').write_text(json.dumps(samples, indent=2) + '\n')
    report = {'selection': str(args.selection), 'requested': len(selection),
              'exported': len(samples), 'quality': args.quality, 'width': 480,
              'skipped': skipped}
    (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
