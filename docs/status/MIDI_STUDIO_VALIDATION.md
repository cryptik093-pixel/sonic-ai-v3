# MIDI Studio local validation (earlier implementation)

Superseded for the current engine by [MIDI coherence upgrade](MIDI_COHERENCE_UPGRADE.md). Counts below describe the earlier local v2 implementation, not the current build.

Date: 2026-10-01. Base: `19ff3b7648c49f3f81b82dcc5e445028719edaba`.
Integration: approved for local `main` merge; no push or new Windows release. See Git history for the integration commit.

## Final observed evidence

| Check | Result |
| --- | --- |
| Original API baseline | 80 passed; 14 existing deprecation warnings |
| Current API suite | 227 passed after review regressions |
| Complete Python suite (`python -m pytest -q`) | 247 passed, 5 subtests passed, 14 warnings |
| Real Chromium browser (`python scripts/verify-workbench-browser.py`) | Passed: interpretation/apply, generation, audition playback, revision lineage, downloads, reuse, drum-only, safe text display, reload state, corrupt-storage recovery, packaging, release, audio, focus, mobile layout |
| Desktop HTTP smoke (`python apps/desktop/launcher.py --smoke-test smoke.json`) | Passed: HTTP boot, static assets, MIDI parse, ZIP download, authorization |
| JavaScript syntax (`node --check` app.js and studio.js) | Passed |
| Diff whitespace (`git diff --check`) | Passed |
| Six paired listening sets | Generated with hashes; ratings blank |

Runtime validation used an isolated Python 3.12 virtual environment and temporary databases. Test browser uses repository-declared Playwright 1.51 / Chromium 134. The newest Playwright browser download was invalid; the pinned version succeeded. Warnings originate from existing UTC timestamp calls and the installed FastAPI/Starlette test-client compatibility notice.

## Important behavior

Requests without Studio settings preserve v1 note fixtures and persisted retry fingerprints. V2 streams separate tracks; selected tracks export independently. Revision parent lookup is ownership-scoped and locked notes are copied exactly. Prompt output is a typed settings proposal; unsupported text and provider failures are visible. File hashes live in the run manifest; Composition.json references that manifest instead of inventing a self-hash.

## Remaining external gates

- Native Windows application window and save dialogs with the new UI.
- FL Studio imports: tempo, bar length, track separation, drum mapping and phrase endings.
- Daniel's ratings using identical instruments: mean improvement ≥0.5, every dimension mean ≥3 and at least four of six Studio phrases worth continuing.
- Live configured cloud request. Local tests use a provider boundary mock for success/malformed/timeout behavior.

The source changes do not upgrade an already installed Sonic.exe. Rebuild and validate a new Windows distribution before replacing the installed version. This implementation does not complete large-folder/catalog scaling or general project conversation.

## Reproduce

Install `apps/api/requirements.txt` and `apps/desktop/requirements-test.txt` in an isolated environment. Install Chromium via `python -m playwright install chromium`. Run the commands above from the repository root. Generate comparison material with `python scripts/prepare-midi-studio-listening.py EMPTY_OUTPUT_DIRECTORY`.

## Independent review and corrections

A fresh read-only reviewer independently ran the suite and reproduced four Important defects: revision/regeneration retry duplicates, newly enabled empty tracks, sparse tonic endings and stale proposals overwriting edits. The reviewer also identified chord-movement measurement error, malformed saved-state boot failure and malformed revision validation. Those three were treated as Important because they respectively produce false evidence, prevent app initialization and bypass the API validation boundary.

All seven were fixed in one pass with failing regression cases followed by passing cases. Added real-browser regressions verify explicit revision seed, lost responses for both revision and regeneration, newer BPM preservation, valid-null storage recovery and newly enabled track selection/export. The complete suite then passed with 247 tests plus 5 subtests. `python scripts/verify-midi-studio-review.py` and the main browser verifier passed; desktop HTTP smoke also passed. No deferred review findings remain.

Locked-track state is now explicit through `track_generation_state`. Changes to musical controls affecting locked tracks require unlocking them, preventing a saved seventh-chord setting from describing preserved triads. Legacy locked tracks retain their original engine/settings provenance.

The reviewer did not certify Windows/FL Studio behavior, musical quality, live provider reliability, arbitrary external Markdown renderers or multiworker deployment. These remain outside the proven local surface.
