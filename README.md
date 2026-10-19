# Football Director OS

**Don't just watch the game. Direct it.**

Football Director OS is a hackathon MVP that compiles natural-language viewing preferences into constrained, inspectable football monitoring programs. Those programs run deterministically against a synthetic event stream and emit evidence-backed insights.

## Run locally

```bash
npm install
npm run dev
```

The current vertical slice is browser-only and deliberately has no external API dependency. It includes:

- deterministic synthetic match replay;
- natural-language-to-JSON compilation for four supported intent families;
- count-threshold, player-event and ordered-sequence execution;
- rising-edge/cooldown duplicate suppression;
- active program pause/delete controls;
- evidence-backed insight inspection;
- Casual Fan and Tactical Analyst presentations;
- explicit refusal of requests unsupported by the available event fields.

The repository also contains a typed FastAPI reference backend with strict Pydantic validation, deterministic replay evaluation, OpenAPI documentation and regression tests.

## Run the API

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=backend uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/docs` for the generated API explorer.

## Test

```bash
PYTHONPATH=backend pytest -q backend/tests
```

## Supported demo prompts

1. `Alert me when East United wins possession in the attacking third three times within five minutes.`
2. `Follow every shot involving Player 7.`
3. `Tell me when East United recovers possession and takes a shot within 15 seconds.`
4. `Notify me when there are at least three shots in five minutes.`
5. `Tell me when the left-back is leaving too much space behind him.` (intentional refusal demo)

## Architecture

The current compiler is deterministic so the replay remains independently testable. The planned provider boundary will add Microsoft Foundry structured output without making the model the source of truth for event detection.

```text
Natural language -> constrained compiler -> validated program
                                              |
Synthetic event replay -> temporal rule engine+-> structured insight -> presentation
                                                     |
                                                  evidence
```

All teams, players and events are fictional. No match footage or proprietary football data is used.

## Microsoft Foundry integration

Copy `.env.example` to `.env` locally and provide `FOUNDRY_ENDPOINT`, `FOUNDRY_API_KEY`, and `FOUNDRY_MODEL`. Never commit the `.env` file. When configured, the API uses Foundry for structured intent compilation and then validates every response against the local Pydantic DSL. If no provider is configured, the deterministic compiler keeps the full demo operational.

## Quality evidence

- deterministic engine and API regression tests;
- eight-case reference intent benchmark at `GET /api/evaluation/benchmark`;
- SQLite-backed versioned program registry;
- GitHub Actions production-build and test gate;
- multi-stage Docker image ready for Azure Container Apps;
- fail-safe local compilation when the model endpoint is unavailable.
