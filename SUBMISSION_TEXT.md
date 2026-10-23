# Submission form copy

Replace bracketed placeholders before submitting.

## Project title

Football Director OS

## Elevator pitch

Football Director OS is an explainable AI match director. A viewer describes the kind of moment they want to see; Director watches licensed football footage, combines verified match context with timestamped computer-vision evidence, selects a matching replay window, and prepares audience-specific commentary and a broadcast-ready graphic. Every output remains linked to its source, exact frames, tracks, confidence values and rule computation.

## Problem

Football broadcasts are produced for one mass audience even though fans, analysts and production teams care about different moments. Finding, clipping and explaining those moments is still manual or dependent on opaque analytics. Director turns a natural-language editorial brief into an automatically selected, explainable replay without allowing a language model to invent what happened on the pitch.

## What we built

- an offline CV pipeline using YOLO 11 and ByteTrack on licensed goal-area footage;
- a provenance-aware adapter separating human-verified scene context from player and ball CV candidates;
- natural-language compilation into a constrained monitoring DSL;
- deterministic count, confidence and composite-window detection;
- automatic key-moment and replay-window selection;
- evidence-backed fan and analyst narratives linked to frame and track evidence;
- multilingual English, Chinese and Spanish output;
- a live-production-style broadcast overlay;
- explicit refusal when available data cannot support an answer;
- versioned monitor persistence, API documentation, automated tests, Docker and CI.

## Microsoft and Azure technology

The FastAPI backend includes a Microsoft Foundry-compatible structured-output provider boundary. When configured, Foundry converts a natural-language editorial brief into the constrained monitoring DSL. Pydantic validation and the deterministic temporal engine remain the source of truth for whether a moment occurred. The container is ready for Azure Container Apps, while GitHub Actions runs the frontend build and backend regression suite.

The current public Vercel build uses the deterministic browser fallback and does not make a live Foundry call. Do not claim live Microsoft Foundry usage unless the judging deployment is connected to a working Foundry endpoint.

## Suggested category

Primary: **Best Enterprise Solution**, based on explainable editorial automation, deterministic execution, validation, evidence trails, versioned programs, graceful provider failure and containerized deployment.

Also relevant to the Grand Prize criteria. Do not select the Foundry category unless the final video and deployment visibly demonstrate a working Foundry call.

## Testing instructions

1. Open `https://football-director-os.vercel.app` in a desktop browser.
2. Click **See a real example**.
3. Director automatically installs the brief: “Find an attack near goal that is worth replaying.”
4. Let the licensed 12-second video play. The result normally appears after the video reaches 5.67 seconds; allow extra time for the first media load.
5. When **Goal-area replay ready** appears, click **Play the attack**.
6. In **Use this moment**, open **Why did Director choose this?** to inspect the verified context, two CV evidence events, timestamps, confidence and composite-sequence calculation.
7. Change the language to Chinese or Spanish.
8. Click **Create live graphic**.
9. Optionally open **How the video was analysed** from the homepage for the complete ten-event CV evidence ledger.
10. Return to the homepage by selecting the Director/OS logo.

No account, payment or API key should be required in the final public judging build.

## URLs

- Public GitHub repository: `https://github.com/LinLyra/Football-Director-OS`
- Public demo video: `[PUBLIC_VIDEO_URL]`
- Public working project: `https://football-director-os.vercel.app`
