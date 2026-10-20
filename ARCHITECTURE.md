# Architecture and trust boundaries

## Components

| Component | Responsibility | Deterministic |
| --- | --- | --- |
| Browser experience | Guided demo, Studio, pitch replay, insight feed and broadcast overlay | Yes |
| Intent provider | Converts supported natural-language requests into a constrained DSL | No; optional AI provider |
| Program validator | Rejects malformed or unsupported programs using Pydantic schemas | Yes |
| Temporal engine | Evaluates event matching, rolling windows and ordered sequences | Yes |
| Evidence ledger | Preserves source event IDs, timestamps, locations and computed values | Yes |
| Narrative layer | Presents the same verified result for different audiences and languages | Template-based in the demo |
| Program repository | Stores versioned monitors and activation status in SQLite | Yes |

## Core safety decision

The language model is not the source of truth for football events. It may translate a viewer's request into a program, but:

1. the output must validate against the local DSL;
2. the temporal engine evaluates the program against observable events;
3. every conclusion includes its evidence and calculation;
4. unsupported questions are refused rather than guessed;
5. the deterministic fallback keeps the demonstration available without an external model.

## Event pipeline

```text
Synthetic event
  -> normalization
  -> active monitor evaluation
  -> threshold / sequence state update
  -> rising-edge and cooldown checks
  -> structured insight
  -> evidence-backed narrative
  -> fan, analyst or broadcast renderer
```

## Supported monitor families

- `EVENT_MATCH`: a matching event involving a player or team;
- `COUNT_THRESHOLD`: at least N matching events inside a rolling time window;
- `ORDERED_SEQUENCE`: event A followed by event B within a maximum gap.

## Failure behavior

- Foundry unavailable: use the deterministic compiler for supported demonstration prompts.
- Invalid structured output: reject before activation.
- Missing input fields: explain why the requested analysis cannot be supported.
- Duplicate match state: rising-edge and cooldown controls prevent repeated alerts.
- Empty evidence: do not emit a verified insight.

## Deployment path

The included multi-stage Dockerfile can package the frontend and FastAPI service for Azure Container Apps. A production deployment should add managed identity, Azure Key Vault, centralized telemetry, persistent storage and an event broker.
