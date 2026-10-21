# Submission form copy

Replace bracketed placeholders before submitting.

## Project title

Football Director OS

## Elevator pitch

Football Director OS turns a viewer's natural-language question into a live, explainable match monitor. It ingests synthetic football events, detects the requested pattern with a deterministic temporal engine, and generates evidence-backed insights for fans, analysts and broadcasters. The same verified moment can be presented in different languages, levels of detail and a broadcast-ready 16:9 overlay.

## Problem

Traditional football broadcasts give every viewer the same information even though fans care about different clubs, players and tactical moments. Existing analytics products also tend to show dashboards and metrics without explaining why a moment matters. Director makes match intelligence personal while preserving an auditable link from every narrative back to the source events.

## What we built

- a synthetic real-time football event replay;
- an original broadcast-style training visual with a transparent CV-adapter demonstration;
- natural-language compilation into a constrained monitoring DSL;
- deterministic count, event and ordered-sequence detection;
- evidence-backed fan and analyst narratives;
- multilingual English, Chinese and Spanish output;
- a live-production-style broadcast overlay;
- explicit refusal when available data cannot support an answer;
- versioned monitor persistence, API documentation, automated tests, Docker and CI.

## Microsoft and Azure technology

The backend includes a Microsoft Foundry-compatible structured-output provider boundary. Foundry converts natural-language intent into the constrained monitoring DSL; Pydantic validation and the deterministic temporal engine remain the source of truth. The multi-stage container is designed for deployment to Azure Container Apps. GitHub Actions runs the frontend build and backend regression suite.

Only describe Foundry as actively demonstrated if valid Foundry credentials are configured in the judging deployment.

## Suggested category

Primary: **Best Enterprise Solution**, based on deterministic execution, validation, evidence trails, versioned programs, graceful provider failure and containerized deployment.

Also relevant to the Grand Prize criteria. Do not select the Foundry category unless the final video and deployment visibly demonstrate a working Foundry call.

## Testing instructions

1. Open `https://football-director-os.vercel.app` in a desktop browser.
2. Click **Watch the 90-second demo**.
3. In **Vision** view, follow the illustrated player/ball tracks and the Video → CV Adapter → Rule Engine pipeline. Switch to **Tactical Map** to inspect normalized event locations.
4. Director automatically creates a monitor for three attacking-third possession recoveries inside five minutes.
5. Wait for the third recovery and select the generated insight.
6. Inspect the three source events and computed rolling-window count.
7. Switch between **Fan view** and **Analyst view**.
8. Change the language to Chinese or Spanish.
9. Click **Open Broadcast Overlay**.
10. Return to the homepage by selecting the Director/OS logo.

No account, payment or API key should be required in the final public judging build.

## URLs

- Public GitHub repository: `https://github.com/LinLyra/Football-Director-OS`
- Public demo video: `[PUBLIC_VIDEO_URL]`
- Public working project: `https://football-director-os.vercel.app`
