# CODEX FIRST TASK — Paste this entire text into Codex with the ZIP attached

You are the lead C++/DSP/VST3 engineer for Omega House Studio LLC. Build **OMEGA SONIC ORGANISM**, a playable professional Windows x64 VST3 synthesis instrument, using the attached architecture and contracts. Treat `AGENTS.md` and `docs/MASTER_BLUEPRINT.md` as binding requirements. Start by reading every file in this package and auditing the actual repository/toolchain, not by guessing its structure.

## First execution stage (do this NOW)
1. Locate canonical repository, identify branch and uncommitted changes, and isolate new work within `plugins/omega-sonic-organism/` without modifying unrelated plugin sources or existing media. Verify MSVC, Windows SDK, CMake, Steinberg VST3 SDK availability and installed SDK version. If the SDK isn't present and network use is permitted, fetch official `steinbergmedia/vst3sdk` with its submodules; pin a tested revision and preserve MIT notices. Do not install paid tooling.
2. Run the supplied standalone core tests using CMake and CTest. Repair actual defects, but do not rewrite source purely to improve appearances. Check `contracts/parameters.json`, `contracts/preset.schema.json` and numeric IDs for consistency.
3. Integrate the independent DSP core into a REAL VST3 instrument using the Steinberg SDK: separate `IComponent`/`IAudioProcessor` and `IEditController`, stable class IDs provided in `docs/HOST_INTEGRATION.md`, stereo audio output, one event input, MIDI note-on/off, note velocity, deterministic voice stealing, mono/poly rendering, sample-accurate parameter changes, host state save/load. First iteration may use the host's generic parameter editor: prioritize audible instrument and host compliance ahead of custom GUI.
4. Build `Release` on Windows x64, run CTest and Steinberg validator where tools are available, then open in FL Studio if an authorized host runtime exists. A report with the exact observed evidence is required. Never say host verified if FL Studio was not actually opened.
5. Stop the first stage after a functioning audible VST3 and report known gaps vs full specification. Do not quietly implement future external-audio listening, agent hooks, cloud sync, or sample import.

## Targeted P1 outcome
- A `.vst3` bundle the host recognizes as an **instrument** with a stereo output and a MIDI/event input.
- All five distinct timbral regions are audible and continuous morph control alters synthesis structure while held notes remain active.
- Stable parameter IDs are exported from the registry, host automation changes occur at precise offsets, and presets/state survive close/reopen.
- Standalone DSP unit tests and (where available) VST3 validator pass.
- The product is clearly labeled `alpha` and is not described as commercially releasable until `docs/TEST_RELEASE_GATES.md` passes.

## Critical implementation checks
- MIDI events and parameter changes at the same sample offset must apply in deterministic order; prefer parameter updates then note events at that sample.
- Do not automatically scan or read studio recordings, Shopify data, Tribal Network assets or Sonic AI repositories outside the task.
- Do not create new paid services or require API keys.
- Request only genuinely unavailable access (e.g. the authorized Windows host) after completing all available local work.
