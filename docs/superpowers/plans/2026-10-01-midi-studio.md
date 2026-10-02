# Sonic MIDI Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Deliver editable, reproducible MIDI composition and track-preserving revisions through Sonic's existing desktop, HTTP and MCP workbench.

**Architecture:** Extend shared Python services with versioned contracts and focused composition, interpretation, revision and validation modules. Preserve the v1 engine and staged run persistence. Extend the existing static UI served to desktop and development browser.

**Tech Stack:** Python, FastAPI, Pydantic 2, SQLAlchemy, mido 1.3.3, NumPy, soundfile, existing vanilla JavaScript UI; pytest and Playwright for verification.

**Spec:** [Approved design](../specs/2026-10-01-midi-studio-design.md), approved 2026-10-01.

## Global Constraints

- Single-operator, local desktop; preserve owner/workspace/project boundaries and authorization.
- Existing requests without Studio settings retain composition_v1 behavior, output names and reproducibility.
- Store prompt, resolved settings, engine version, seed, parent and validation with every Studio run.
- 4/8/16/32 bars, 4/4; existing BPM 60–200 and seed 0–2147483647.
- Maximum 50,000 notes per run. Prompt maximum 2,000 characters.
- No dependencies required beyond existing runtime packages; existing Playwright verification remains a development dependency.
- Preserve original files and records; no resets, stashes, automatic database replacement or secret exposure.
- Technical validity does not establish musical or commercial approval.
- Commit/push and Windows release publication are separate operations; do not infer authorization from implementation approval.

## Review Focus

1. Drum-only compositions must render without an empty pitched-note canvas crash (Task 7).
2. Very narrow register requests must either yield legal voicings or a useful error (Task 2).
3. Unicode and HTML-like prompt/title text must remain safe display data (Tasks 5 and 7).
4. A timeout followed by retry must not generate a second run (Tasks 6 and 7).
5. Legacy parent revisions must upgrade explicitly while preserving locked note records (Task 4).

## File structure

Modify `apps/api/workbench/schemas.py` (contracts), `midi.py` (v1 dispatch/export reuse), `service.py` (run orchestration), `router.py` (HTTP), `mcp_tools.py` (MCP), and `static/{index.html,app.js,style.css}` (one shared UI).

Create `apps/api/workbench/midi_studio.py` (v2 composer), `midi_quality.py` (validation and metrics), `midi_revision.py` (immutable revision resolution), `midi_prompt.py` (typed interpretation). Add focused tests under `apps/api/tests/` after confirming repository test discovery and fixtures. Extend `scripts/verify-workbench-browser.py` rather than introducing a competing UI test runner. Update `README.md`, `apps/desktop/QUICK_START.txt` and the approved documents under `docs/superpowers/` in the implementation checkout.

## Task 1: Backward-compatible contracts and baseline

**Files:** schemas.py; new apps/api/tests/test_midi_studio_contracts.py; new apps/api/tests/fixtures/midi_v1_notes.json.
**Interfaces:** `MidiCommand.settings: StudioSettings | None`; `StudioSettings` version 2; `MidiRevisionCommand(Command)` with parent_run_id UUID, regenerate_tracks and settings_patch; `MidiInterpretCommand(BaseModel)` with prompt and current MidiCommand; `MidiInterpretResult` with method, status, proposed_settings, unresolved and warnings. Track names are `Melody`, `Chords`, `Bass`, `Drums`. Patches resolve into a complete validated MidiCommand before composition.

- [x] Inspect checkout HEAD/status, applicable AGENTS.md, test fixtures and test configuration; capture v1 note fixtures from current compose for the three styles, four scales and seeds 0/93/max. Run existing tests and record baseline failures separately.
- [x] Add failing contract tests: absent settings preserves legacy requests; 32 bars requires settings v2; invalid ranges/unknown controls reject; enabled track list cannot be empty; regeneration tracks must be enabled and nonempty.
- [x] Run `python -m pytest apps/api/tests/test_midi_studio_contracts.py -q`; confirm new contract tests fail before implementation.
- [x] Implement typed nested settings. Copy every range/value from the approved spec. Initial pitched ranges: Melody 60–88, Chords 45–79, Bass 24–47. Default velocity: Melody 80, Chords 65, Bass 88, Drums 75; variation 6, timing 8 ms, spread 15 ms, swing 50%, motif variation 25%, syncopation 30%, progression rate 2 bars, triads, close/smooth, balanced contour, rhythmic bass, half-time eighth hats, tonic ending. Existing style/density/key/scale remain top-level. Engine identity derives from settings presence.
- [x] Re-run contracts and fixture equality; confirm PASS and document defaults.

## Task 2: Composition v2

**Files:** new midi_studio.py; midi.py; new apps/api/tests/test_midi_studio_composition.py.
**Interfaces:** `compose_studio(command: MidiCommand) -> list[dict]` returns the existing track/pitch/start/duration/velocity note shape; `track_rng(seed: int, track: str, purpose: str) -> random.Random` uses SHA-256-derived integer seeds including engine version `local_composition_v2`.

- [x] Add failing tests for reproducible notes; independent drum changes leave melody/chords/bass unchanged; each selected track and range is honored; impossible seventh/ninth voicings raise ValueError. Test all four lengths and all existing styles/scales.
- [x] Run `python -m pytest apps/api/tests/test_midi_studio_composition.py -q`; observe missing-v2 failures.
- [x] Implement progression cycling, chord extensions, constrained voicing and smooth movement; recurring motif and contour; phrase variation, breaths and ending; bass patterns and feel-specific drum patterns. Use bounded independent random streams and reject oversized note budgets before preview rendering.
- [x] Apply swing before timing offsets; convert ms to beats using BPM. Clamp starts/ends, velocity and ranges. Resolve same-pitch monophonic overlap by shortening the earlier note, not dropping its note-off. Preserve v1 composer unchanged.
- [x] Run composition tests plus contract/v1 fixture tests; verify each exposed control changes the intended measurable behavior across a fixed seed set. Assert 0 humanization/velocity variation has no jitter and 50% swing is straight.

## Task 3: Quality and exports

**Files:** new midi_quality.py; midi.py; new apps/api/tests/test_midi_studio_exports.py.
**Interfaces:** `validate_notes(notes: list[dict], command: MidiCommand) -> dict`; `measure_notes(notes: list[dict], command: MidiCommand) -> dict`; `export_studio(command: MidiCommand, notes: list[dict], folder: Path, provenance: dict) -> dict`. Provenance contains run/parent/owner/workspace/project and interpretation method.

- [x] Add failing tests parsing exported MIDI: balanced note lifecycles, off-before-on at equal ticks, nonnegative deltas, positive durations, range/scale validity, exact tempo/4/4/end boundaries, GM drum channel. Test repeated pitches and a 32-bar dense arrangement.
- [x] Run `python -m pytest apps/api/tests/test_midi_studio_exports.py -q`; confirm missing exporter/validator failures.
- [x] Implement selected part exports and combined arrangement; reuse existing synthesis with bounds and drum-only support. Write v2 Composition.json, Quality_Report.json and FL Studio instructions. Report metrics as facts and musical heuristics explicitly as interpretations. Include stable track IDs derived from run ID and track name, unspecified instrument/preset state, and audition derivation metadata.
- [x] Add byte-equivalence tests for repeat MIDI exports; metadata timestamps are excluded. Assert legacy filenames/output remain unchanged and disabled parts are absent.
- [x] Run exports/composition/contracts tests; confirm every artifact is readable and report checks are true. Use the existing archive endpoint and run artifact hashes for checksummed ZIP delivery; do not add a duplicate ZIP inside the ZIP.

## Task 4: Immutable revisions

**Files:** new midi_revision.py; new apps/api/tests/test_midi_studio_revision.py.
**Interfaces:** `resolve_revision(parent: dict, command: MidiRevisionCommand) -> tuple[MidiCommand, list[dict], dict]`; metadata returns parent_run_id, changed_settings, regenerated_tracks and preserved_tracks. Parent is obtained through the owning service, never arbitrary client notes.

- [x] Add failing tests: selected tracks differ, locked tracks match exactly, parent unchanged, infeasible ranges fail, missing/failed/non-MIDI parents reject, and global key/scale/BPM/bars changes reject when enabled parent tracks stay locked.
- [x] Run `python -m pytest apps/api/tests/test_midi_studio_revision.py -q`; confirm failures.
- [x] Resolve settings patches into Task 1 contracts; use Task 2 only for regenerated tracks and copy locked parent notes exactly. Legacy parents require explicit v2 settings; do not silently reinterpret them. New selected tracks may be generated; removal of a locked parent track rejects. Keep title changes cosmetic and seed changes limited to regenerated tracks.
- [x] Run revisions and exports; verify exact copied note equality and parent file hashes unchanged.

## Task 5: Prompt settings proposals

**Files:** new midi_prompt.py; new apps/api/tests/test_midi_studio_prompt.py; reuse apps/api/services/llm_service.py without changing unrelated provider behavior.
**Interfaces:** `interpret_prompt(command: MidiInterpretCommand) -> MidiInterpretResult`. This returns a proposal and does not persist a run or generate files.

- [x] Add failing tests for supported offline BPM/key/style/length/density instructions, unsupported text retained in unresolved, contradictory instructions flagged, explicit controls retained, and HTML/Unicode text preserved as data. Provider mocks cover malformed JSON, invalid settings, timeout and missing credentials.
- [x] Run `python -m pytest apps/api/tests/test_midi_studio_prompt.py -q`; confirm failures.
- [x] Implement local supported vocabulary and optional configured cloud JSON proposal through existing LLMService; schema-validate all provider output. Return unavailable/partial status and sanitized warnings on errors. Manual generation remains available; never invoke code or paths from prompt/provider content.
- [x] Run prompt tests; verify no generation service calls and no secrets in result/log fixtures. Store interpretation method only when the operator explicitly applies a proposal to a generated command.

## Task 6: Durable services, HTTP and MCP

**Files:** service.py; router.py; mcp_tools.py; new apps/api/tests/test_midi_studio_api.py and test_midi_studio_mcp.py.
**Interfaces:** extend `service.generate_midi(command)`; add `service.revise_midi(command)` and `service.interpret_midi(command)`. HTTP: existing POST /workbench/api/midi; new POST /workbench/api/midi/revise and /workbench/api/midi/interpret. MCP: preserve sonic_generate_midi; add sonic_revise_midi and sonic_interpret_midi_prompt.

- [x] Add failing API/MCP tests for identical request replay, changed-payload conflict, auth denial, OAuth read-mode mutation denial, scoped parent lookup, failed staging cleanup, timeout/retry and startup interrupted recovery.
- [x] Run `python -m pytest apps/api/tests/test_midi_studio_api.py apps/api/tests/test_midi_studio_mcp.py -q`; confirm new endpoint failures.
- [x] Dispatch v1/v2 through shared services; thread generated run ID into builder provenance through an optional context-aware execute path while preserving all existing builder callers. Keep revisions kind=midi for history/pack compatibility. Persist parent and settings in request/result JSON, requiring no destructive schema migration.
- [x] Register interpretation with annotations reflecting optional external provider use: read-only local state, non-idempotent and open-world. Revision/generation retain local mutation annotations and request IDs. Reuse existing bearer enforcement and OAuth restrictions. No raw local paths returned.
- [x] Persist evidence-bearing next-step guidance: facts, source run refs, heuristic assumption, proposed action, confidence label and listening verification. Studio pack integration derives musical metadata from resolved settings and includes only selected existing MIDI artifacts.
- [x] Run API/MCP plus prior tests and existing workbench tests. Inspect partial-publication failures; a failed run must never offer success downloads.

## Task 7: Shared workbench UI

**Files:** static/index.html; static/app.js; static/style.css; scripts/verify-workbench-browser.py.
**Interfaces:** `readStudioCommand(form)` builds Task 1 input; `applyStudioSettings(command)` restores nested controls; `showRun` displays Studio provenance/report/revision controls. Use existing command retry IDs and download/native save bridges.

- [x] Extend browser tests to fail for advanced settings, Interpret/apply/edit, locked-track revision, reuse settings, all downloads, disabled track selection and drum-only piano view.
- [x] Run `python scripts/verify-workbench-browser.py`; confirm new selector failures before UI changes.
- [x] Add prompt and basic controls, collapsible advanced per-track controls with units and bounds; show resolved settings before Generate. Add selected-track revision controls, parent display, Regenerate and Reuse settings. Save/restore checkboxes and nested controls correctly. Safely recover malformed localStorage and preserve user form values after errors.
- [x] Render facts/heuristics separately, neutral drum-only canvas, escaped title/prompt, explicit simple audition label. Reuse existing status/run/download calls and disable duplicate submissions. Show unsupported prompt text and provider failure without blocking manual generation.
- [x] Run real browser tests: generate/play/download/revise/reload, mobile width 390, zero page errors. Simulate delayed response/retry and assert one run ID; verify edited payload obtains a new request ID. Test every UI field round-trips to saved resolved settings.

## Task 8: Integrated evidence and operator evaluation

**Files:** README.md; apps/desktop/QUICK_START.txt; docs/status/MIDI_STUDIO_VALIDATION.md; new scripts/prepare-midi-studio-listening.py.
**Interfaces:** listening script writes six paired v1/v2 arrangements and a CSV with style/key/BPM/bars/seed, hashes and blank operator score columns to an explicit output directory; never fabricates ratings.

- [x] Run `python -m pytest apps/api/tests -q`, `python scripts/verify-workbench-browser.py` and `python apps/desktop/launcher.py --smoke-test smoke.json` from the checkout using isolated temporary databases/data. Report baseline unrelated failures separately.
- [x] Generate listening pairs for cloud/trap/soul with seeds 93/194 at C minor, 130 BPM, 8 bars and balanced density. Include instructions to use identical FL Studio sounds for each pair. Validate the script's filenames, settings and MIDI parse results.
- [x] Record local evidence: checkout SHA, commands, results, artifact hashes, screenshots and any failed gates. Update documentation to match observed behavior and preserve limitations.
- [ ] Run Windows native Generate/revision/export and FL Studio import checks when that environment is accessible; otherwise label this gate unverified, with reproducible operator steps.
- [ ] Obtain Daniel's 1–5 scores for harmonic coherence, melody development, groove and usefulness. Acceptance: v2 average improvement ≥0.5 overall, each dimension mean ≥3, at least four v2 phrases worth continuing. If unmet, diagnose paired results and revise composer before claiming musical-quality acceptance.
- [x] Inspect final diff/status; report task-owned files, checks and outstanding external gates. Commit/push or Windows release only if separately authorized.

## Execution handoff

Recommended: native execution in this session using executing-plans, because the tasks depend closely on shared contracts and the existing single service/UI. A fresh whole-change review follows implementation. Alternative: subagent-driven execution with task-level implementation and review handoffs, requiring more context transfers. Both preserve the same acceptance gates.

Plan self-review: all design sections map to Tasks 1–8; signatures and track names are consistent; five review-focus cases have assigned tests; legacy behavior, MIDI export, prompt fallback, revision ownership, UI and external listening checks are covered. Folder ingestion and general chatbot expansion remain the next separately designed stages.

Execution status: local implementation and independent-review correction pass complete. External Windows/FL Studio/listening gates remain open. Repository changes are uncommitted and unpublished pending integration choice.
