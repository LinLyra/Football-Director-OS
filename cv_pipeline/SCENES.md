# Curated real-video demo scenes

The public demo should contain three preprocessed clips rather than arbitrary uploads. Each scene must include the original authorized clip, `tracked.mp4`, `tracks.jsonl`, normalized events, a manifest and source attribution.

| Scene | Target duration | Required observable signal | Director story |
| --- | ---: | --- | --- |
| Goal threat — `SNMOT-101` | 30 s | final-third entry followed by a shot candidate | the attack has produced a goal-level threat |
| Fast transition — `SNMOT-068` | 30 s | possession-change candidate followed by forward progression | the phase has opened into a rapid transition |
| Pressure and turnover — `SNMOT-099` | 30 s | multiple nearby defenders followed by a possession-change candidate | pressure has disrupted the attacking phase |

Do not assign these stories by clip timestamp alone. The normalized events must be derived from model output, include confidence and frame evidence, and be accepted by the same deterministic Director rule engine used elsewhere.

All three sequences have now been downloaded from the official public tracking subset and processed with the baseline pipeline. `scene-catalog.json` records the measured run statistics and deliberately marks semantic event adapters as pending.

## Acceptance gate

- Football-specific player/goalkeeper/referee/ball detector, with model license recorded.
- Stable tracking after camera-motion compensation; report ID switches on an annotated sample.
- Team clustering validated on at least 50 player crops per scene.
- Pitch keypoints and homography visually checked.
- Every semantic event links to the source frames and tracks that caused it.
- Low-confidence semantic events are labelled candidates or withheld.
