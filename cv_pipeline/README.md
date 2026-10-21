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

The default `yolo11n.pt` model detects people and ByteTrack maintains identities. It does not detect the ball or infer passes, shots, team identity or possession. Those claims require a football-specific detector plus event logic and must not be represented as completed until evaluated.

`example-manifest.json` records an actual 300-frame MPS run completed on 21 October 2026. It proves that the inference/export path executes, while documenting why this baseline is not yet accurate enough for semantic football claims. See `SCENES.md` for the three-clip acceptance gate.

## Demo asset policy

Keep raw videos, model weights and generated outputs out of Git. Only publish clips for which redistribution and public demo use are documented. Record title, source URL, creator, license and crop timestamps next to every published clip.
