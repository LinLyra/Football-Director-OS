# Curated real-video demo scenes

The public demo should contain three preprocessed clips rather than arbitrary uploads. Each scene must include the original authorized clip, `tracked.mp4`, `tracks.jsonl`, normalized events, a manifest and source attribution.

| Scene | Target duration | Required observable signal | Director story |
| --- | ---: | --- | --- |
| High press | 15–25 s | repeated recoveries in the attacking third | pressure is disrupting build-up |
| Fast transition | 10–20 s | recovery followed by forward progression and a shot candidate | counter-press creates immediate danger |
| Shot surge | 20–30 s | three verified shot candidates in a rolling window | match becomes open and end-to-end |

Do not assign these stories by clip timestamp alone. The normalized events must be derived from model output, include confidence and frame evidence, and be accepted by the same deterministic Director rule engine used elsewhere.

## Acceptance gate

- Football-specific player/goalkeeper/referee/ball detector, with model license recorded.
- Stable tracking after camera-motion compensation; report ID switches on an annotated sample.
- Team clustering validated on at least 50 player crops per scene.
- Pitch keypoints and homography visually checked.
- Every semantic event links to the source frames and tracks that caused it.
- Low-confidence semantic events are labelled candidates or withheld.
