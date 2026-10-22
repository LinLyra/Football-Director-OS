# Curated real-video demo scenes

The public demo should contain three preprocessed clips rather than arbitrary uploads. Each scene must include the original authorized clip, `tracked.mp4`, `tracks.jsonl`, normalized events, a manifest and source attribution.

| Scene | Target duration | Required observable signal | Director story |
| --- | ---: | --- | --- |
| Goal threat — `SNMOT-101` | 30 s | final-third entry followed by a shot candidate | the attack has produced a goal-level threat |
| Fast transition — `SNMOT-068` | 30 s | possession-change candidate followed by forward progression | the phase has opened into a rapid transition |
| Pressure and turnover — `SNMOT-099` | 30 s | multiple nearby defenders followed by a possession-change candidate | pressure has disrupted the attacking phase |

Do not assign these stories by clip timestamp alone. The normalized events must be derived from model output, include confidence and frame evidence, and be accepted by the same deterministic Director rule engine used elsewhere.

All three sequences have now been downloaded from the official public tracking subset and processed with the baseline pipeline. `derive_events.py` identifies the persistent small-object ball candidate, clusters kits from real upper-torso pixels, and derives conservative semantic candidates from spatial and temporal evidence. The full generated files stay beside the local video outputs under `cv_outputs/`; `scene-catalog.json` records their measured counts.

Run the event adapter after downloading a sequence:

```bash
python cv_pipeline/derive_events.py \
  --sequence-dir cv_data/soccernet/SNMOT-101 \
  --output cv_outputs/snmot-101/events.json
```

Each event includes its source frame, timestamp, confidence, status, track IDs and the deterministic rule that fired. Team labels are anonymous clusters (`team_a`, `team_b`), not asserted club identities. Officials and atypical kits are held in `other_role` where the clustering separates them.

`render_event_overlay.py` turns the same evidence into a reviewable 1280×720
H.264 clip. The three local outputs are each 30 seconds and contain 16, 17 and
10 rendered event candidates respectively; they are deliberately not committed
with the code.

## Acceptance gate

- Football-specific player/goalkeeper/referee/ball detector, with model license recorded. The current adapter uses SoccerNet's annotated tracks and explicitly labels its ball choice as a candidate.
- Stable tracking after camera-motion compensation; report ID switches on an annotated sample.
- Team clustering validated on at least 50 player crops per scene. Current runs use 300+ sampled crops but still need human label validation.
- Pitch keypoints and homography visually checked.
- Every semantic event links to the source frames and tracks that caused it.
- Low-confidence semantic events are labelled candidates or withheld.
