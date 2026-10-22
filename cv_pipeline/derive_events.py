"""Derive auditable football event candidates from SoccerNet tracking labels.

This adapter is intentionally conservative. It uses the annotated object tracks,
samples real pixels to cluster shirt colours, and emits *candidate* events with
frame-level evidence. It does not claim tactical ground truth or trained action
recognition.
"""

from __future__ import annotations

import argparse
import configparser
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class Box:
    frame: int
    track_id: int
    x: float
    y: float
    w: float
    h: float

    @property
    def center(self) -> tuple[float, float]:
        return self.x + self.w / 2, self.y + self.h / 2

    @property
    def foot(self) -> tuple[float, float]:
        return self.x + self.w / 2, self.y + self.h


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sequence-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--sample-stride", type=int, default=25)
    return parser.parse_args()


def load_sequence(sequence_dir: Path) -> tuple[dict[int, list[Box]], dict]:
    config = configparser.ConfigParser()
    config.read(sequence_dir / "seqinfo.ini")
    section = config["Sequence"]
    meta = {
        "name": section.get("name", sequence_dir.name),
        "fps": section.getfloat("frameRate", 25),
        "width": section.getint("imWidth"),
        "height": section.getint("imHeight"),
        "length": section.getint("seqLength"),
        "extension": section.get("imExt", ".jpg"),
    }
    frames: dict[int, list[Box]] = defaultdict(list)
    with (sequence_dir / "gt" / "gt.txt").open(encoding="utf-8") as source:
        for line in source:
            values = line.strip().split(",")
            if len(values) < 6:
                continue
            frame, track_id = int(values[0]), int(values[1])
            x, y, w, h = map(float, values[2:6])
            frames[frame].append(Box(frame, track_id, x, y, w, h))
    return frames, meta


def identify_ball(frames: dict[int, list[Box]], sequence_length: int) -> tuple[int, dict]:
    areas: dict[int, list[float]] = defaultdict(list)
    for boxes in frames.values():
        for box in boxes:
            areas[box.track_id].append(box.w * box.h)
    eligible = {
        track_id: samples
        for track_id, samples in areas.items()
        if len(samples) >= sequence_length * 0.35
    }
    if not eligible:
        raise ValueError("No sufficiently persistent track can represent the ball")
    track_id = min(eligible, key=lambda item: np.median(eligible[item]))
    return track_id, {
        "method": "smallest persistent median bounding-box area",
        "median_area_pixels": round(float(np.median(eligible[track_id])), 2),
        "visible_frames": len(eligible[track_id]),
        "confidence": 0.78,
        "status": "candidate",
    }


def image_path(sequence_dir: Path, frame: int, extension: str) -> Path:
    return sequence_dir / "img1" / f"{frame:06d}{extension}"


def shirt_descriptor(image: np.ndarray, box: Box) -> np.ndarray | None:
    height, width = image.shape[:2]
    x1 = max(0, int(box.x + box.w * 0.22))
    x2 = min(width, int(box.x + box.w * 0.78))
    y1 = max(0, int(box.y + box.h * 0.12))
    y2 = min(height, int(box.y + box.h * 0.52))
    if x2 - x1 < 2 or y2 - y1 < 2:
        return None
    crop = image[y1:y2, x1:x2]
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]
    # Remove pitch-green, shadows, and near-white glare before measuring kit colour.
    green = (hsv[:, :, 0] >= 32) & (hsv[:, :, 0] <= 92) & (saturation >= 45)
    valid = (~green) & (value >= 35) & (value <= 245)
    pixels = crop[valid]
    if len(pixels) < 6:
        return None
    selected_hsv = hsv[valid]
    # A hue distribution survives motion blur better than one median colour. Low
    # saturation and dark-kit fractions distinguish white and charcoal kits.
    colourful = selected_hsv[:, 1] >= 45
    histogram, _ = np.histogram(
        selected_hsv[colourful, 0] if np.any(colourful) else selected_hsv[:, 0],
        bins=12,
        range=(0, 180),
    )
    histogram = histogram.astype(float) / max(1, histogram.sum())
    extras = np.array([
        np.mean(selected_hsv[:, 1]) / 255,
        np.mean(selected_hsv[:, 2]) / 255,
        np.mean(selected_hsv[:, 1] < 45),
        np.mean(selected_hsv[:, 2] < 85),
    ])
    return np.concatenate([histogram, extras])


def kmeans_kit_roles(features: dict[int, np.ndarray]) -> tuple[dict[int, str], dict]:
    ids = sorted(features)
    matrix = np.stack([features[item] for item in ids])
    cluster_count = min(4, len(matrix))
    # Deterministic farthest-point initialization avoids random demo results.
    centres = [matrix[np.argmax(np.linalg.norm(matrix - np.mean(matrix, axis=0), axis=1))]]
    while len(centres) < cluster_count:
        nearest = np.min(
            np.linalg.norm(matrix[:, None, :] - np.stack(centres)[None, :, :], axis=2),
            axis=1,
        )
        centres.append(matrix[np.argmax(nearest)])
    centres = np.stack(centres).astype(float)
    labels = np.zeros(len(matrix), dtype=int)
    for _ in range(30):
        new_labels = np.argmin(np.linalg.norm(matrix[:, None, :] - centres[None, :, :], axis=2), axis=1)
        if np.array_equal(labels, new_labels) and _ > 0:
            break
        labels = new_labels
        for cluster in range(cluster_count):
            members = matrix[labels == cluster]
            if len(members):
                centres[cluster] = np.mean(members, axis=0)
    sizes = Counter(int(label) for label in labels)
    main_clusters = [item[0] for item in sizes.most_common(2)]
    role = {main_clusters[0]: "team_a", main_clusters[1]: "team_b"}
    assignment = {
        track_id: role.get(int(label), "other_role")
        for track_id, label in zip(ids, labels)
    }
    return assignment, {
        "method": "deterministic k-means (k=4) over upper-torso HSV histograms; two largest clusters treated as teams",
        "cluster_sizes": dict(sorted(sizes.items())),
        "members": dict(Counter(assignment.values())),
        "status": "candidate",
    }


def cluster_teams(
    sequence_dir: Path,
    frames: dict[int, list[Box]],
    meta: dict,
    ball_id: int,
    stride: int,
) -> tuple[dict[int, str], dict]:
    samples: dict[int, list[np.ndarray]] = defaultdict(list)
    for frame in range(1, meta["length"] + 1, stride):
        image = cv2.imread(str(image_path(sequence_dir, frame, meta["extension"])))
        if image is None:
            continue
        for box in frames.get(frame, []):
            if box.track_id == ball_id or box.h < 22:
                continue
            descriptor = shirt_descriptor(image, box)
            if descriptor is not None:
                samples[box.track_id].append(descriptor)
    features = {
        track_id: np.mean(np.stack(values), axis=0)
        for track_id, values in samples.items()
        if len(values) >= 2
    }
    if len(features) < 4:
        raise ValueError("Insufficient real-pixel shirt samples for two-team clustering")
    assignments, report = kmeans_kit_roles(features)
    report["sampled_tracks"] = len(features)
    report["sample_count"] = sum(len(values) for values in samples.values())
    report["assignments"] = {str(key): value for key, value in assignments.items()}
    return assignments, report


def confidence(value: float) -> float:
    return round(max(0.51, min(0.92, value)), 2)


def derive_events(
    frames: dict[int, list[Box]], meta: dict, ball_id: int, teams: dict[int, str]
) -> list[dict]:
    width, height, fps = meta["width"], meta["height"], meta["fps"]
    ball_by_frame: dict[int, Box] = {}
    possessor_by_frame: dict[int, tuple[int, str, float]] = {}
    pressure_by_frame: dict[int, tuple[int, str, list[int]]] = {}

    for frame, boxes in frames.items():
        ball = next((box for box in boxes if box.track_id == ball_id), None)
        if ball is None:
            continue
        ball_by_frame[frame] = ball
        bx, by = ball.center
        candidates = []
        for player in boxes:
            team = teams.get(player.track_id)
            if player.track_id == ball_id or team not in ("team_a", "team_b"):
                continue
            px, py = player.foot
            distance = math.hypot((px - bx) / width, (py - by) / height)
            candidates.append((distance, player, team))
        if not candidates:
            continue
        distance, player, team = min(candidates, key=lambda item: item[0])
        if distance <= 0.072:
            possessor_by_frame[frame] = (player.track_id, team, distance)
            px, py = player.foot
            nearby = []
            for opponent in boxes:
                if teams.get(opponent.track_id) not in ("team_a", "team_b") or teams.get(opponent.track_id) == team:
                    continue
                ox, oy = opponent.foot
                if math.hypot((ox - px) / width, (oy - py) / height) <= 0.105:
                    nearby.append(opponent.track_id)
            if len(nearby) >= 2:
                pressure_by_frame[frame] = (player.track_id, team, nearby)

    events: list[dict] = []

    def add(event_type: str, frame: int, score: float, evidence: dict) -> None:
        events.append({
            "id": f"{event_type.lower()}-{frame:06d}",
            "type": event_type,
            "frame": frame,
            "timestamp_seconds": round((frame - 1) / fps, 2),
            "confidence": confidence(score),
            "status": "candidate",
            "evidence": evidence,
        })

    # Entering either lateral third is observable; attack direction is not assumed.
    prior_zone = None
    for frame in sorted(ball_by_frame):
        x = ball_by_frame[frame].center[0] / width
        zone = "left" if x < 0.33 else "right" if x > 0.67 else "middle"
        if prior_zone == "middle" and zone != "middle":
            add("FINAL_THIRD_ENTRY_CANDIDATE", frame, 0.72, {
                "ball_track_id": ball_id, "pitch_side": zone,
                "rule": "ball centre crossed from middle third into a lateral third",
            })
        prior_zone = zone

    # Stable nearest-player team changes, debounced to reduce annotation jitter.
    stable: list[tuple[int, str, int]] = []
    run_team, run_start, run_length = None, None, 0
    for frame in sorted(possessor_by_frame):
        _, team, _ = possessor_by_frame[frame]
        if team == run_team and run_start is not None and frame <= run_start + run_length + 2:
            run_length += 1
        else:
            if run_team is not None and run_length >= 8:
                stable.append((run_start, run_team, run_length))
            run_team, run_start, run_length = team, frame, 1
    if run_team is not None and run_length >= 8:
        stable.append((run_start, run_team, run_length))
    last_change = -10_000
    for previous, current in zip(stable, stable[1:]):
        if (
            previous[1] != current[1]
            and current[0] - (previous[0] + previous[2]) <= int(fps * 2)
            and current[0] - last_change >= int(fps * 2)
        ):
            player_id, team, distance = possessor_by_frame[current[0]]
            add("POSSESSION_CHANGE_CANDIDATE", current[0], 0.68 + min(current[2], 20) / 100, {
                "from_team_cluster": previous[1], "to_team_cluster": team,
                "nearest_player_track_id": player_id,
                "normalized_ball_distance": round(distance, 4),
                "stable_frames": current[2],
            })
            last_change = current[0]

    # Sustained pressure: at least two opposing tracks close to the ball-nearest player.
    pressure_frames = sorted(pressure_by_frame)
    last_emitted = -10_000
    for frame in pressure_frames:
        window = [item for item in pressure_frames if frame <= item < frame + 8]
        if len(window) >= 5 and frame - last_emitted >= int(fps * 3):
            player_id, team, opponents = pressure_by_frame[frame]
            add("PRESSURE_CANDIDATE", frame, 0.66 + min(len(opponents), 4) * 0.04, {
                "possessor_track_id": player_id, "possessor_team_cluster": team,
                "opponent_track_ids": opponents,
                "supporting_frames": window[:8],
            })
            last_emitted = frame

    # Rapid ball movement over one second; direction is deliberately not inferred.
    ball_frames = sorted(ball_by_frame)
    last_emitted = -10_000
    for frame in ball_frames:
        later = frame + round(fps)
        if later not in ball_by_frame:
            continue
        x1, y1 = ball_by_frame[frame].center
        x2, y2 = ball_by_frame[later].center
        displacement = math.hypot((x2 - x1) / width, (y2 - y1) / height)
        if displacement >= 0.16 and frame - last_emitted >= int(fps * 3):
            add("RAPID_PROGRESSION_CANDIDATE", later, 0.62 + displacement * 0.7, {
                "ball_track_id": ball_id, "start_frame": frame, "end_frame": later,
                "normalized_displacement": round(displacement, 4),
            })
            last_emitted = frame

    # High ball speed close to a lateral goal side is a shot candidate, not a shot claim.
    speeds = []
    for frame in ball_frames:
        previous = frame - 5
        if previous in ball_by_frame:
            x1, y1 = ball_by_frame[previous].center
            x2, y2 = ball_by_frame[frame].center
            speeds.append((math.hypot((x2 - x1) / width, (y2 - y1) / height), frame))
    if speeds:
        threshold = max(0.025, float(np.percentile([item[0] for item in speeds], 93)))
        last_emitted = -10_000
        for speed, frame in speeds:
            x = ball_by_frame[frame].center[0] / width
            if speed >= threshold and (x < 0.28 or x > 0.72) and frame - last_emitted >= int(fps * 3):
                add("SHOT_CANDIDATE", frame, 0.59 + min(speed, 0.2) * 1.4, {
                    "ball_track_id": ball_id, "start_frame": frame - 5, "end_frame": frame,
                    "normalized_speed_over_5_frames": round(speed, 4),
                    "speed_percentile_threshold": round(threshold, 4),
                    "pitch_side": "left" if x < 0.5 else "right",
                })
                last_emitted = frame

    return sorted(events, key=lambda item: (item["frame"], item["type"]))


def main() -> None:
    args = parse_args()
    frames, meta = load_sequence(args.sequence_dir)
    ball_id, ball_report = identify_ball(frames, meta["length"])
    teams, team_report = cluster_teams(
        args.sequence_dir, frames, meta, ball_id, args.sample_stride
    )
    events = derive_events(frames, meta, ball_id, teams)
    counts = Counter(item["type"] for item in events)
    payload = {
        "schema_version": "1.0",
        "source": {"dataset": "SoccerNet/SN-Tracking-2023", "sequence": meta["name"]},
        "method": "tracking geometry + real-pixel kit clustering + deterministic temporal rules",
        "disclaimer": "Outputs are explainable event candidates, not action-recognition ground truth.",
        "ball_track": {"track_id": ball_id, **ball_report},
        "team_clustering": team_report,
        "event_count": len(events),
        "event_counts_by_type": dict(sorted(counts.items())),
        "events": events,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({
        "sequence": meta["name"], "ball_track_id": ball_id,
        "team_clusters": team_report["members"], "events": dict(sorted(counts.items())),
    }, indent=2))


if __name__ == "__main__":
    main()
