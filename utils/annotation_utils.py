from __future__ import annotations

import json
from pathlib import Path
from typing import Any


AnnotationRecord = dict[str, Any]
AnnotationsById = dict[str, AnnotationRecord]

REQUIRED_RECORD_FIELDS = {
    "clip_id",
    "frame_width",
    "frame_height",
    "fps",
    "first_prediction_frame",
    "last_prediction_frame",
    "contact_frame",
    "action_label",
    "per_frame_annotations",
}


def build_sample_id(clip_id: str, contact_frame: int) -> str:
    return f"{clip_id}_{contact_frame}"


def load_annotations(path: str | Path) -> AnnotationsById:
    annotations_path = Path(path)
    with annotations_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(
            f"{annotations_path} must be a JSON object keyed by sample_id, got {type(data).__name__}."
        )

    annotations: AnnotationsById = {}
    for sample_id, record in data.items():
        if not isinstance(sample_id, str):
            raise ValueError("Annotation keys must be strings.")
        if not isinstance(record, dict):
            raise ValueError(f"Record {sample_id!r} must be a JSON object.")

        missing = sorted(REQUIRED_RECORD_FIELDS - record.keys())
        if missing:
            raise ValueError(f"Record {sample_id!r} is missing required fields: {', '.join(missing)}.")

        per_frame_annotations = record["per_frame_annotations"]
        if not isinstance(per_frame_annotations, dict):
            raise ValueError(f"Record {sample_id!r} has a non-dict per_frame_annotations field.")

        expected_sample_id = build_sample_id(str(record["clip_id"]), int(record["contact_frame"]))
        if sample_id != expected_sample_id:
            raise ValueError(
                f"Record {sample_id!r} does not match the expected sample_id {expected_sample_id!r}."
            )

        annotations[sample_id] = record

    return annotations


def parse_sample_ids_csv(value: str) -> list[str]:
    sample_ids = [sample_id.strip() for sample_id in value.split(",") if sample_id.strip()]
    if not sample_ids:
        raise ValueError("No sample IDs were provided.")
    return sample_ids


def read_sample_ids_file(path: str | Path) -> list[str]:
    sample_ids: list[str] = []
    for raw_line in Path(path).read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        sample_ids.append(line)
    if not sample_ids:
        raise ValueError(f"No sample IDs found in {path}.")
    return sample_ids


def dedupe_preserve_order(values: list[str]) -> list[str]:
    return list(dict.fromkeys(values))
