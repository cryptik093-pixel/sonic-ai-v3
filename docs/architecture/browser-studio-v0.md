# Browser Studio experimental vertical slice (2026-10-14)

**Authority: ACTIVE prototype**, not the shipped Windows producer workbench.

## Existing integration and boundaries

- The existing `/workbench` desktop/static UI and all saved jobs remain unchanged.
- Next.js `/studio` is a separate route. Its socket connects to `/workbench/ws/studio`.
- WebSocket authenticates using a local operator token in the initial AUTH message, never a URL parameter. Loopback Host and browser Origin are checked independently of HTTP middleware.
- PROMPT requests use the established **read-only** production-brief compiler; STATUS_UPDATE and SUCCESS refer to a preview, **not** to altered tracks or a committed session.
- The sample form imports through the existing authenticated `POST /workbench/api/imports` endpoint and retrieves `GET /workbench/api/studio/assets/{asset_id}/metadata`. The existing importer enforces 100 MB, 20-minute, decoding and content-hash protections.
- Audio metadata uses optional librosa for first-90-second estimates: BPM, chroma-profile key hypothesis and spectral-centroid timbre hint. Returns unknown for silent/ambiguous evidence. The 12-element normalized chroma descriptor is **handcrafted DSP**, not CLAP, not a text-audio embedding and not proof of genre or musical key.
- Source audio remains unchanged. No automatic mastering, no writes to a timeline, no cloud model access and no new fees.
- A canonical timeline JSON, reversible executor, multi-track state mutations, true semantic embeddings and exported complete projects are **not included**.

## Source development

From the repository root, install the existing dependencies and optional analyzer:

```bash
python -m pip install -r apps/api/requirements-audio-analysis.txt
```

Configure a nonempty `SONIC_CONTROL_PLANE_TOKEN` in the local API environment, then start `uvicorn apps.api.main:app --host 127.0.0.1 --port 8000`. In another terminal run `pnpm --filter @sonic-ai/web dev` after installing the workspace's pinned packages with `pnpm install --frozen-lockfile`. Open `http://localhost:3000/studio`; supply the local API URL and token.

If the desktop launcher allocated a different loopback port, use that exact port instead of 8000. The desktop and the Next dev server must point at the same local API process.

## Validation

Run `python -m pytest apps/api/tests/test_studio_pipeline.py -q`. The baseline test suite exercises the HTTP auth and socket preview boundaries. The silent-audio DSP test is conditional on optional librosa; install the optional requirements to exercise it. The runtime CI checks the Next build and API import/compile. No browser E2E, verified Windows run, neural embedding inference or real-time session-mutation test is claimed by this document.

## Recommended next vertical slice

Add **project export**, beginning with a versioned session JSON and immutable SHA-256 inventory plus stem/MIDI references, then a ZIP with checksums. The existing run-artifact/archive download API is reusable, but it is not a complete DAW session export. After a tested restore/export round-trip, add reversible timeline state mutations and then mastering.
