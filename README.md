# Football Director OS

> Your match. Your questions. Live answers.

Football Director OS turns a fan's natural-language question into a live, explainable match director. The primary public demo replays genuine CV output from licensed football footage, composes low-level candidates into an evidence-bounded key moment, and produces audience-specific commentary, replay selection and broadcast-ready output.

Built for the **Microsoft × Premier League Inside the Game Developer Hackathon**.

## Why it matters

Every viewer cares about something different, but traditional broadcasts give everyone the same feed. Director lets a fan, analyst or producer describe the moment they care about and receive an answer only when the source events prove it happened.

## Demo flow

1. Ask: `Find a high-tempo passage with rapid ball travel and repeated player involvement.`
2. Director compiles the request into a constrained monitoring program.
3. Ten timestamped candidates from the licensed CV run enter the deterministic temporal engine as the video plays.
4. A composite window selects a high-tempo passage without claiming unsupported actions such as a shot or goal.
5. Director creates a replay range, commentary cue and broadcast overlay.
6. The exact source events, tracks, timestamps, confidence and computation remain available for audit in English, Chinese or Spanish.

Use **Watch the 90-second demo** on the homepage for the guided experience. See [DEMO_SCRIPT.md](DEMO_SCRIPT.md) for the submission-video script.

The homepage also opens a **Real Vision Lab**. Its public scene shows the genuine
YOLO + ByteTrack output for an 18-second Pexels-licensed football clip, all ten
derived candidates, their confidence and their frame/track evidence.

## Features

- licensed real-video replay with genuine person/ball detections;
- ten timestamp-synchronized ball-contact and rapid-movement candidates;
- evidence-bounded semantic composition into a high-tempo Director moment;
- automatic replay-range selection and commentary cue;
- optional synthetic event-stream sandbox with passes, shots, tackles, recoveries and pressure;
- natural-language monitoring instructions;
- count-threshold, player-event and ordered-sequence detection;
- rising-edge and cooldown duplicate suppression;
- evidence-backed insights with event IDs and computed values;
- Fan and Analyst presentation modes;
- English, Chinese and Spanish storytelling;
- 16:9 broadcast overlay;
- explicit refusal when requested analysis is unsupported by available data;
- SQLite-backed versioned monitor registry;
- Microsoft Foundry-compatible structured-output provider boundary;
- Docker and GitHub Actions support.

## Architecture

```text
Natural-language request
        |
        v
Microsoft Foundry / deterministic fallback
        |
        v
Validated monitoring DSL
        |
        v
Temporal rule engine <--- timestamped real CV event replay
        |
        +----> semantic moment composer
        +----> replay selection + evidence ledger
        +----> fan / analyst narrative
        +----> multilingual broadcast overlay
```

The model may propose a monitoring program, but it never decides whether a match event occurred. Every program is validated locally and every emitted insight is calculated by deterministic code.

See [ARCHITECTURE.md](ARCHITECTURE.md) for component and trust-boundary details.

## Run locally

Requirements: Node.js 20+ and Python 3.11+.

```bash
npm install
npm run dev
```

Open `http://127.0.0.1:5174`.

The browser demo remains fully functional without external credentials by using the safe deterministic compiler.

### Optional API

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000
```

API documentation: `http://127.0.0.1:8000/docs`

### Optional Microsoft Foundry configuration

```bash
cp .env.example .env
```

Set `FOUNDRY_ENDPOINT`, `FOUNDRY_API_KEY`, and `FOUNDRY_MODEL` locally. Never commit `.env`.

## Test and build

```bash
npm run build
PYTHONPATH=backend pytest -q backend/tests
```

The repository includes ten regression tests and an eight-case reference intent benchmark at `GET /api/evaluation/benchmark`.

## Docker

```bash
docker build -t football-director-os .
docker run --rm -p 8000:8000 football-director-os
```

## Deploy the judging frontend to Vercel

Import this public GitHub repository in Vercel. The included `vercel.json` selects Vite, runs `npm run build`, and publishes `dist`.

The public frontend uses the deterministic browser compiler when `VITE_API_BASE_URL` is not configured, so the complete guided demo works without credentials or a separate API. To connect a hosted FastAPI service later, add `VITE_API_BASE_URL` in the Vercel project settings and redeploy.

## Data and rights

The public real-video demo uses a Pexels-licensed clip credited to Luis Quintero. It includes no Premier League match footage, official club marks, proprietary event feeds or copyrighted music. The separate tactical sandbox uses fictional clubs, players and synthetic events.

CV inference is run offline and its normalized output is committed for reproducible judging; the browser does not rerun YOLO. During playback, the saved events are streamed at their exact video timestamps through the same deterministic rule engine, semantic composer, evidence ledger and output renderers. Semantic outputs remain explicitly labelled as candidates and never claim unsupported ground truth.

An optional offline [real-video CV pipeline](cv_pipeline/README.md) now runs genuine YOLO inference and ByteTrack tracking, exporting annotated H.264 video, frame-level JSONL tracks and a reproducibility manifest. For SoccerNet tracking sequences, a second adapter uses annotated tracks plus real-frame kit pixels to produce auditable ball, pressure, progression, possession-change and shot candidates. These candidates are not yet wired into the public storyline and are not presented as action-recognition ground truth; the remaining acceptance gates are documented in [SCENES.md](cv_pipeline/SCENES.md).

## Submission status

See [SUBMISSION_CHECKLIST.md](SUBMISSION_CHECKLIST.md). Before submission, the repository must be public and the judging build must be accessible through an unrestricted URL, or the testing instructions must include working credentials.

## License

MIT — see [LICENSE](LICENSE).
