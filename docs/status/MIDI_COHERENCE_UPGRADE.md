# MIDI coherence upgrade — implementation and release gates

Validated 2026-10-01 America/Chicago. Canonical remote baseline: `19ff3b7648c49f3f81b82dcc5e445028719edaba`. The upgrade includes the earlier local MIDI Studio implementation (`0a42b39`), which was absent from remote main. Work is isolated on `upgrade/midi-musical-coherence`; the installed Windows app has not been replaced.

## Deficiencies found and behavior delivered

| Observed deficiency | Delivered behavior |
| --- | --- |
| Legacy generator offered four basic parts and few controls | Shared desktop/HTTP/MCP Studio contracts, progression, registers, voicing, performance controls, selected-track revisions and reproducible exports |
| Melody could choose arbitrary scale tones on strong beats | Triad-tone anchors on beats 1/3; motif-derived preferences between anchors |
| Greedy pitch choices could strand longer phrases before the cadence | Whole-phrase dynamic programming enforces the chosen maximum interval (3–12 semitones) and ending while optimizing movement and motif preferences |
| Melody tonic landing could conflict with final harmony | Shared per-bar harmonic timeline; Resolve changes the final bar to I/i; Loop preserves the exact progression |
| Bass mostly repeated roots | Rhythmic root/fifth movement and diatonic pickups toward the next root; sustained option retained |
| No counter-melody part | Optional Countermelody track, separate MIDI channel 4, range and velocity; response fills lead rests, parallel accompanies the lead |
| Constant hats and flat articulation | Phrase-end hat rolls, snare fill, beat accents, swing and bounded performance variation |
| Counter-melody absent from pack path and piano-roll colors | Five-part download/export, pack inventory and distinct piano-roll color verified |
| New harmony settings could falsely describe locked notes | Dependency-aware revision restrictions; response lead and counter must be unlocked together; historical engines retain their original track provenance |

The Studio engine is `local_composition_v3`; settings remain backward-compatible contract version 2. Calls without settings keep legacy v1 and exact fixture coverage. Previously recorded note data is never silently regenerated. A new Studio generation uses the current engine, so a historical seed alone is insufficient to reproduce a different engine version.

Chords retain triad/seventh/ninth, open/close voicing and range-aware voice leading. All tonal material uses the selected diatonic scale. This is a local algorithmic composition engine; cloud interpretation only proposes typed musical settings. It does not synthesize or execute code.

## Current reproducible evidence

- Complete Python suite: **361 passed, 5 subtests passed**, 14 existing framework/UTC deprecation warnings.
- New musical/export regression checks cover three transposition roots, all four scales, three styles and three densities; check monophony, strong-beat harmony, leap limits, tonic endings, reproducibility, response spacing and decoded MIDI events.
- Additional parameter sweep: **1,296 successful five-part compositions, zero failures and zero response overlaps** across all 12 keys, four scales, three styles, three densities and three seeds at 16 bars with default humanization.
- Independent Standard MIDI File readback confirms exact pitch, onset ticks, duration ticks, velocity, channel and complete note-off lifecycles for each of the five parts; combined file has one conductor plus five part tracks.
- Real Chromium browser verification: **22 checks passed**, including interpretation/apply, generation, audition playback, revision lineage, downloads, saved state, retries, five-part counter download and five-part pack inventory.
- Desktop launcher HTTP smoke: passed HTTP boot, bundled UI, MIDI parsing, archive download and authorization.
- JavaScript syntax and whitespace checks: passed.

Tests ran with Python 3.12 and repository dependencies in an isolated local application/database context. Chromium 134 headless shell succeeded; full Chromium was blocked by the environment's Unix socket restriction. The fallback CDN supplied the pinned browser successfully. These environment details do not establish Windows application behavior.

## Release blockers and practical limits

1. **Windows delivery:** build the PR through the existing Sonic desktop CI; verify the packaged native UI and save dialogs before replacing the installed Sonic.exe. Local HTTP smoke is not a native Windows test.
2. **FL Studio:** import combined and individual files; verify tempo, exact bar length, instrument separation, MIDI channel 10 drum mapping (36/38/42), counter part, and preserved revisions. Standard MIDI parser acceptance is not an FL Studio integration certificate.
3. **Musical acceptance:** run six paired examples from `scripts/prepare-midi-studio-listening.py` with identical DAW sounds. Target: mean Studio improvement ≥0.5/5, each dimension mean ≥3/5, four of six phrases worth continuing. Ratings remain unscored until listening occurs. Also audition response/parallel counter-melody in the five-part workflow.
4. **Scope limits:** only 4/4, three supported style grammars and four scales; no borrowed chords, audio-conditioned generation, expressive CC automation or instrument/preset state capture. Audition remains simple synthesis.
5. **Constrained requests:** impossible pitch ranges/leap limits or a response request with no usable lead rests produce an explicit preflight error. Widen the range/leap, reduce lead density or use Parallel. The tool never substitutes a fake successful artifact.
6. **Cloud optionality:** live configured provider behavior has not been tested here; the local generator requires no provider or quota.

## Reproduce

```bash
python -m pytest -q
python scripts/verify-workbench-browser.py
python apps/desktop/launcher.py --smoke-test /tmp/sonic-midi-smoke.json
node --check apps/api/workbench/static/app.js
node --check apps/api/workbench/static/studio.js
python scripts/prepare-midi-studio-listening.py EMPTY_OUTPUT_DIRECTORY
```

Install the repository API/test requirements and pinned Chromium first. On Windows, use a Windows path for the smoke JSON.

## Sonic Intelligence decision record

- Objective: upgrade usable, exportable MIDI while preserving Sonic V3 architecture and saved work.
- Owner: Daniel / local producer; implementation authorized by the task.
- Decision: use a deterministic shared harmonic timeline and constrained melody planning inside the existing shared service layer.
- Evidence: source inspection, musical property checks, decoded exports, full regression suite, browser workflow and desktop HTTP smoke.
- Confidence: high for the tested technical and structural constraints; musical acceptance and native DAW behavior remain unassessed.
- Assumptions: scale-based grammar and operator-chosen instruments suit this release scope.
- Risks: stylistic repetition, restricted harmony, audition timbre bias and unverified native import behavior.
- Next validation: Windows package plus FL Studio import and paired listening.
- Status: implemented and locally validated; commercial release acceptance pending.
