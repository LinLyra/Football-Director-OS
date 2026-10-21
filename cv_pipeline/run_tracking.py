"""Run real YOLO + ByteTrack inference and export auditable track data.

This intentionally detects and tracks only classes supported by the selected
model. It does not invent ball possession, passes, shots, or team identity.
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import time
from collections import defaultdict
from pathlib import Path

import cv2
import torch
from ultralytics import YOLO


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", default=Path("cv_outputs"), type=Path)
    parser.add_argument("--model", default="yolo11n.pt")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--confidence", default=0.25, type=float)
    parser.add_argument("--max-seconds", default=30.0, type=float)
    parser.add_argument("--imgsz", default=640, type=int)
    return parser.parse_args()


def choose_device(requested: str) -> str:
    if requested != "auto":
        return requested
    if torch.backends.mps.is_available():
        return "mps"
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"Input does not exist: {args.input}")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_video = args.output_dir / "tracked-raw.mp4"
    web_video = args.output_dir / "tracked.mp4"
    tracks_path = args.output_dir / "tracks.jsonl"
    manifest_path = args.output_dir / "manifest.json"

    capture = cv2.VideoCapture(str(args.input))
    fps = capture.get(cv2.CAP_PROP_FPS) or 25.0
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frame_limit = int(min(capture.get(cv2.CAP_PROP_FRAME_COUNT), fps * args.max_seconds))
    writer = cv2.VideoWriter(
        str(raw_video), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height)
    )

    device = choose_device(args.device)
    model = YOLO(args.model)
    started = time.time()
    frame_index = 0
    detection_count = 0
    unique_tracks: set[int] = set()
    per_second: dict[int, list[int]] = defaultdict(list)

    with tracks_path.open("w", encoding="utf-8") as track_file:
        while frame_index < frame_limit:
            ok, frame = capture.read()
            if not ok:
                break

            result = model.track(
                frame,
                persist=True,
                tracker="bytetrack.yaml",
                classes=[0],
                conf=args.confidence,
                imgsz=args.imgsz,
                device=device,
                verbose=False,
            )[0]
            boxes = result.boxes
            frame_tracks = []
            if boxes is not None and boxes.xyxy is not None:
                coords = boxes.xyxy.cpu().tolist()
                confidences = boxes.conf.cpu().tolist()
                track_ids = boxes.id.int().cpu().tolist() if boxes.id is not None else [-1] * len(coords)
                for track_id, confidence, (x1, y1, x2, y2) in zip(track_ids, confidences, coords):
                    if track_id >= 0:
                        unique_tracks.add(track_id)
                    detection_count += 1
                    item = {
                        "track_id": track_id,
                        "class": "person",
                        "confidence": round(float(confidence), 4),
                        "bbox_xyxy": [round(v, 2) for v in (x1, y1, x2, y2)],
                        "footpoint_normalized": [
                            round(((x1 + x2) / 2) / width, 5),
                            round(y2 / height, 5),
                        ],
                    }
                    frame_tracks.append(item)
                    color = (78, 255, 214) if track_id % 2 == 0 else (255, 210, 105)
                    cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 1)
                    cv2.putText(
                        frame,
                        f"P{track_id} {confidence:.2f}",
                        (int(x1), max(12, int(y1) - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.32,
                        color,
                        1,
                        cv2.LINE_AA,
                    )

            timestamp = frame_index / fps
            per_second[int(timestamp)].append(len(frame_tracks))
            track_file.write(json.dumps({
                "frame": frame_index,
                "timestamp_seconds": round(timestamp, 3),
                "tracks": frame_tracks,
            }) + "\n")
            cv2.putText(frame, "REAL YOLO + BYTETRACK OUTPUT", (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (214, 255, 75), 1, cv2.LINE_AA)
            cv2.putText(frame, f"frame {frame_index:05d} | tracks {len(frame_tracks):02d}", (12, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (240, 245, 241), 1, cv2.LINE_AA)
            writer.write(frame)
            frame_index += 1

    capture.release()
    writer.release()
    subprocess.run([
        "ffmpeg", "-y", "-i", str(raw_video), "-c:v", "libx264", "-preset", "fast",
        "-crf", "24", "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart", str(web_video)
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    elapsed = time.time() - started
    manifest = {
        "pipeline": "YOLO object detection + ByteTrack multi-object tracking",
        "input": args.input.name,
        "model": args.model,
        "device": device,
        "source_fps": fps,
        "frames_processed": frame_index,
        "processing_seconds": round(elapsed, 2),
        "effective_fps": round(frame_index / elapsed, 2) if elapsed else None,
        "detections": detection_count,
        "unique_track_ids": len(unique_tracks),
        "limitations": [
            "COCO person detections only",
            "No ball detector",
            "No automatic team identity",
            "No semantic pass, shot, or possession inference",
        ],
        "per_second_visible_tracks": {
            str(second): round(sum(values) / len(values), 2)
            for second, values in per_second.items()
        },
        "runtime": {"python": platform.python_version(), "torch": torch.__version__},
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
