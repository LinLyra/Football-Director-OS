"""Derive conservative event candidates from YOLO/ByteTrack JSONL output."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracks", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def add_event(events: list[dict], event_type: str, frame: int, fps: float, score: float, evidence: dict) -> None:
    events.append({
        "id": f"{event_type.lower()}-{frame:06d}",
        "type": event_type,
        "frame": frame,
        "timestamp_seconds": round(frame / fps, 2),
        "confidence": round(max(0.51, min(0.90, score)), 2),
        "status": "candidate",
        "evidence": evidence,
    })


def main() -> None:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    fps = float(manifest["source_fps"])
    width = float(manifest.get("source_width", 1920))
    height = float(manifest.get("source_height", 1080))
    rows = [json.loads(line) for line in args.tracks.read_text(encoding="utf-8").splitlines() if line]
    balls: dict[int, dict] = {}
    people: dict[int, list[dict]] = {}
    for row in rows:
        frame = int(row["frame"])
        frame_balls = [item for item in row["tracks"] if item["class"] == "sports ball"]
        if frame_balls:
            balls[frame] = max(frame_balls, key=lambda item: item["confidence"])
        people[frame] = [item for item in row["tracks"] if item["class"] == "person"]

    events: list[dict] = []
    contact_frames: list[tuple[int, int, float]] = []
    for frame, ball in balls.items():
        bx1, by1, bx2, by2 = ball["bbox_xyxy"]
        bx, by = (bx1 + bx2) / 2 / width, (by1 + by2) / 2 / height
        candidates = []
        for person in people.get(frame, []):
            px, py = person["footpoint_normalized"]
            distance = math.hypot(px - bx, py - by)
            candidates.append((distance, person["track_id"]))
        if candidates:
            distance, track_id = min(candidates)
            if distance <= 0.11:
                contact_frames.append((frame, track_id, distance))

    last_event = -10_000
    for frame, track_id, distance in contact_frames:
        supporting = [item for item in contact_frames if frame <= item[0] <= frame + 8 and item[1] == track_id]
        if len(supporting) >= 4 and frame - last_event >= round(fps * 2.2):
            add_event(events, "BALL_CONTACT_CANDIDATE", frame, fps, 0.64 + len(supporting) * 0.02, {
                "ball_detection_track_id": balls[frame]["track_id"],
                "nearest_player_track_id": track_id,
                "normalized_distance": round(distance, 4),
                "supporting_frames": [item[0] for item in supporting],
            })
            last_event = frame

    gap = round(fps * 0.5)
    movements = []
    for frame, ball in balls.items():
        later = frame + gap
        if later not in balls:
            continue
        x1, y1 = balls[frame]["footpoint_normalized"]
        x2, y2 = balls[later]["footpoint_normalized"]
        movements.append((math.hypot(x2 - x1, y2 - y1), frame, later))
    if movements:
        threshold = max(0.10, float(np.percentile([item[0] for item in movements], 88)))
        last_event = -10_000
        for displacement, frame, later in movements:
            if displacement >= threshold and frame - last_event >= round(fps * 2.2):
                add_event(events, "RAPID_BALL_MOVEMENT_CANDIDATE", later, fps, 0.63 + displacement * 0.8, {
                    "start_frame": frame,
                    "end_frame": later,
                    "normalized_displacement": round(displacement, 4),
                    "threshold": round(threshold, 4),
                    "start_ball_track_id": balls[frame]["track_id"],
                    "end_ball_track_id": balls[later]["track_id"],
                })
                last_event = frame

    events.sort(key=lambda item: item["frame"])
    counts = Counter(item["type"] for item in events)
    payload = {
        "schema_version": "1.0",
        "source": "Pexels 15448993",
        "method": "YOLO person/sports-ball detections + ByteTrack + deterministic geometry",
        "disclaimer": "Generic-detector outputs are candidates, not football action ground truth.",
        "frames_processed": len(rows),
        "ball_visible_frames": len(balls),
        "ball_frame_coverage": round(len(balls) / max(1, len(rows)), 4),
        "event_counts_by_type": dict(sorted(counts.items())),
        "events": events,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({key: payload[key] for key in ("frames_processed", "ball_visible_frames", "ball_frame_coverage", "event_counts_by_type")}, indent=2))


if __name__ == "__main__":
    main()
