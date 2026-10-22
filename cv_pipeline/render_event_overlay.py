"""Render a real SoccerNet sequence with auditable tracks and event overlays."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import deque
from pathlib import Path

import cv2

from derive_events import Box, load_sequence


TEAM_COLORS = {
    "team_a": (75, 255, 214),
    "team_b": (255, 190, 92),
    "other_role": (230, 230, 230),
}
EVENT_COLORS = {
    "SHOT_CANDIDATE": (75, 255, 214),
    "PRESSURE_CANDIDATE": (62, 215, 255),
    "POSSESSION_CHANGE_CANDIDATE": (255, 190, 92),
    "RAPID_PROGRESSION_CANDIDATE": (220, 255, 100),
    "FINAL_THIRD_ENTRY_CANDIDATE": (210, 180, 255),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequence-dir", required=True, type=Path)
    parser.add_argument("--events", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--width", default=1280, type=int)
    return parser.parse_args()


def draw_label(frame, text: str, origin: tuple[int, int], color: tuple[int, int, int]) -> None:
    x, y = origin
    (text_width, text_height), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.34, 1)
    cv2.rectangle(frame, (x, y - text_height - 7), (x + text_width + 7, y), color, -1)
    cv2.putText(frame, text, (x + 3, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.34, (5, 14, 9), 1, cv2.LINE_AA)


def event_title(event_type: str) -> str:
    return event_type.replace("_CANDIDATE", "").replace("_", " ")


def main() -> None:
    args = parse_args()
    frames, meta = load_sequence(args.sequence_dir)
    payload = json.loads(args.events.read_text(encoding="utf-8"))
    ball_id = int(payload["ball_track"]["track_id"])
    teams = {int(key): value for key, value in payload["team_clustering"]["assignments"].items()}
    events_by_frame = {int(item["frame"]): item for item in payload["events"]}

    scale = args.width / meta["width"]
    output_height = round(meta["height"] * scale)
    raw_output = args.output.with_name(f"{args.output.stem}-raw.mp4")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(raw_output), cv2.VideoWriter_fourcc(*"mp4v"), meta["fps"],
        (args.width, output_height),
    )
    ball_trail: deque[tuple[int, int]] = deque(maxlen=18)
    active_event = None
    active_until = 0

    for frame_number in range(1, meta["length"] + 1):
        source = cv2.imread(str(args.sequence_dir / "img1" / f"{frame_number:06d}{meta['extension']}"))
        if source is None:
            continue
        frame = cv2.resize(source, (args.width, output_height), interpolation=cv2.INTER_AREA)
        boxes = frames.get(frame_number, [])
        ball_box = next((item for item in boxes if item.track_id == ball_id), None)
        if ball_box:
            bx, by = ball_box.center
            ball_trail.append((round(bx * scale), round(by * scale)))
        for first, second in zip(ball_trail, list(ball_trail)[1:]):
            cv2.line(frame, first, second, (255, 255, 255), 2, cv2.LINE_AA)

        for box in boxes:
            x1, y1 = round(box.x * scale), round(box.y * scale)
            x2, y2 = round((box.x + box.w) * scale), round((box.y + box.h) * scale)
            if box.track_id == ball_id:
                cx, cy = round((x1 + x2) / 2), round((y1 + y2) / 2)
                cv2.circle(frame, (cx, cy), max(7, round(box.w * scale)), (255, 255, 255), 2, cv2.LINE_AA)
                draw_label(frame, f"BALL {box.track_id}", (cx + 8, max(20, cy - 5)), (255, 255, 255))
                continue
            role = teams.get(box.track_id, "other_role")
            color = TEAM_COLORS.get(role, TEAM_COLORS["other_role"])
            cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
            draw_label(frame, f"{role.upper()}  P{box.track_id}", (x1, max(20, y1)), color)

        if frame_number in events_by_frame:
            active_event = events_by_frame[frame_number]
            active_until = frame_number + round(meta["fps"] * 1.8)
        if active_event and frame_number <= active_until:
            color = EVENT_COLORS.get(active_event["type"], (75, 255, 214))
            cv2.rectangle(frame, (24, output_height - 105), (args.width - 24, output_height - 24), (5, 17, 11), -1)
            cv2.rectangle(frame, (24, output_height - 105), (30, output_height - 24), color, -1)
            cv2.putText(frame, event_title(active_event["type"]), (48, output_height - 68), cv2.FONT_HERSHEY_SIMPLEX, 0.68, color, 2, cv2.LINE_AA)
            detail = f"CANDIDATE  |  confidence {active_event['confidence']:.2f}  |  evidence frame {active_event['frame']}"
            cv2.putText(frame, detail, (48, output_height - 43), cv2.FONT_HERSHEY_SIMPLEX, 0.39, (220, 230, 223), 1, cv2.LINE_AA)

        cv2.rectangle(frame, (0, 0), (args.width, 45), (4, 14, 9), -1)
        cv2.putText(frame, "DIRECTOR/OS  REAL VISION LAB", (18, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.51, (75, 255, 214), 1, cv2.LINE_AA)
        timestamp = (frame_number - 1) / meta["fps"]
        cv2.putText(frame, f"{meta['name']}  |  {timestamp:05.2f}s  |  frame {frame_number:04d}", (args.width - 335, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (220, 230, 223), 1, cv2.LINE_AA)
        writer.write(frame)

    writer.release()
    subprocess.run([
        "ffmpeg", "-y", "-i", str(raw_output), "-c:v", "libx264", "-preset", "fast",
        "-crf", "23", "-pix_fmt", "yuv420p", "-an", "-movflags", "+faststart",
        str(args.output),
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    raw_output.unlink(missing_ok=True)
    print(json.dumps({
        "sequence": meta["name"], "output": str(args.output), "frames": meta["length"],
        "events_rendered": len(payload["events"]), "resolution": [args.width, output_height],
    }, indent=2))


if __name__ == "__main__":
    main()
