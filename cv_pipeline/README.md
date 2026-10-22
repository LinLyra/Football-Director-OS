# Real-video CV pipeline

This optional offline pipeline performs genuine frame-by-frame inference. It is intentionally separate from the lightweight Vercel frontend.

## Run

```bash
python3 -m venv .cv-venv
.cv-venv/bin/pip install -r cv_pipeline/requirements.txt
.cv-venv/bin/python cv_pipeline/run_tracking.py \
  --input cv_data/source/your-authorized-clip.mp4 \
  --output-dir cv_outputs/clip-01
```

Outputs:

- `tracked.mp4`: browser-compatible H.264 video with genuine model detections;
- `tracks.jsonl`: every detection, confidence, track ID and normalized foot point;
- `manifest.json`: model, device, performance and explicit limitations.

For a SoccerNet tracking sequence with ground-truth tracks, derive explainable
event candidates from the real frames and geometry:

```bash
.cv-venv/bin/python cv_pipeline/derive_events.py \
  --sequence-dir cv_data/soccernet/SNMOT-101 \
  --output cv_outputs/snmot-101/events.json
```

`events.json` records the ball-track selection method, anonymous kit clusters,
event confidence and exact source frames/tracks. These remain candidates: the
adapter does not turn geometric heuristics into asserted action ground truth.

Render those results back onto the real frames for a reviewable 16:9 demo clip:

```bash
.cv-venv/bin/python cv_pipeline/render_event_overlay.py \
  --sequence-dir cv_data/soccernet/SNMOT-101 \
  --events cv_outputs/snmot-101/events.json \
  --output cv_outputs/snmot-101/event-overlay.mp4
```

The renderer draws every annotated track, anonymous team role, ball trail and
event banner with confidence and evidence frame. It exports H.264/yuv420p with
fast-start metadata so the result is directly playable in a browser. Generated
clips remain ignored until their redistribution permission is documented.

## Download one public SoccerNet sequence

The repository includes a range-based downloader that extracts one sequence from SoccerNet's large public ZIP without downloading the entire 5–10 GB archive:

```bash
.cv-venv/bin/python cv_pipeline/fetch_soccernet_sequence.py \
  --split train \
  --sequence SNMOT-101
```

On 21 October 2026, `SNMOT-101` was downloaded from the official `SoccerNet/SN-Tracking-2023` dataset and processed end to end: 750 1080p frames, 6,334 detections and a 14.01 FPS effective MPS rate. See `soccernet-snmot101-manifest.json`. The source frames and generated video remain ignored because dataset access does not by itself establish permission to redistribute match footage through this repository or a public demo.

The default `yolo11n.pt` model detects people and ByteTrack maintains identities. It does not detect the ball or infer passes, shots, team identity or possession. The separate event adapter currently uses SoccerNet's annotated tracks, not YOLO's person-only tracks, and labels all semantic output as candidates. Replacing that dependency still requires a football-specific detector and evaluation.

`example-manifest.json` records an actual 300-frame MPS run completed on 21 October 2026. It proves that the inference/export path executes, while documenting why this baseline is not yet accurate enough for semantic football claims. See `SCENES.md` for the three-clip acceptance gate.

## Demo asset policy

Keep raw videos, model weights and generated outputs out of Git. Only publish clips for which redistribution and public demo use are documented. Record title, source URL, creator, license and crop timestamps next to every published clip.
