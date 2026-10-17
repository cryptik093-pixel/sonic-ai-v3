# Browser studio local integration — ACTIVE EXPERIMENTAL (2026-10-14)

This feature branch adds a demo studio WebSocket and a separate Next.js /studio page; the existing Windows producer workbench and / redirect remain unchanged. Nothing is deployed. The new studio **does not** access FL Studio, imported stems or real customer projects.

## Implementation

- Typed StudioState with optimistic revision and copy-on-write mutations. Pydantic rejects invalid IDs, ranges and excess fields.
- FastAPI /ws/studio: local Host and Origin restrictions, first-frame token authorization (SONIC_DESKTOP_TOKEN or SONIC_CONTROL_PLANE_TOKEN), per-connection synthetic state, structured messages and revision conflicts. No wild-card CORS, public bind, external network transfer or stored token.
- Minimal Next.js /studio chat and Canvas timeline, displaying BPM, track mute/volume/pan, regions and effect settings. Web Audio oscillator audition uses AudioContext.currentTime to schedule synthetic MIDI notes. 60 FPS is a target, not a claim.
- Deterministic local parser supports a deliberately small set of commands. It is not a LangGraph or OpenAI integration and makes no model calls.
- Bitcrusher parameter changes are **configuration only**; no WASM, AudioWorklet or compiled C++ processing is present.
- Session state is ephemeral, not persisted. A reconnect loads a new synthetic demo. Changes to MIDI regions during an active audition are visual until playback restarts. There is no master limiter or real file playback.

## Local verification

Run the repo's usual API dependencies and tests, including:

    PYTHONPATH=. python -m pytest apps/api/tests/test_studio_socket.py

With the API started on 127.0.0.1:8000, a configured local control token, and the existing Next dev app started on port 3000, open http://127.0.0.1:3000/studio. Enter the token manually and Connect, then submit "crush drums hard", "make drums quieter and pan left" and "move bass 2 seconds later". Start audio at low monitor volume.

Do not configure this proof-of-concept for public traffic or store credentials in the frontend. WebSockets authenticate after handshake before any project state is transmitted. Production use requires owner-scoped persistent sessions, first-class identity, upload sandboxing, asset authorization, DSP worklet validation, audio QA, measured latency and operational monitoring.
