# Sonic AI V3 — MIDI Studio design

Date: 2026-10-01. Owner: Daniel / Omega House Studio LLC.
Status: proposed written specification; feature direction approved, specification review pending.

## Outcome and scope

Extend the existing Sonic workbench into a controllable composition and revision system that produces usable melody, harmony, bass and drum MIDI for Omega House workflows. Preserve the local, single-operator desktop experience and shared Python service boundary used by desktop, HTTP and MCP. Save the state that created each composition.

This specification covers MIDI generation, prompt resolution, revisions, preview, export, generation history and evidence-bearing next-step guidance for the resulting run. Large folder ingestion, catalog scaling and general project conversation are separate follow-on designs. Establish asset-compatible IDs and metadata here without claiming those later subsystems are implemented.

## Inspected baseline

Sources: cryptik093-pixel/sonic-ai-v3 main: AGENTS.md, README.md, apps/api/workbench/{schemas.py,midi.py,models.py,service.py}. Omega House OS main: README.md, knowledge/tier-6/README.md and knowledge/founder-onboarding/README.md. Inspection occurred on 2026-10-01 through GitHub; no local runtime was exercised. Re-read the implementation revision before coding.

Current MidiCommand exposes title, key, four scales, three styles, BPM 60–200, bars 4/8/16, seed and density. Composition uses a small fixed motif bank, style-based progressions and automatic humanization. It exports four MIDI parts, an arrangement, audition WAV, Composition.json and FL Studio instructions. Runs already have ownership, request fingerprints, durable status and hashed artifacts. Preserve these behaviors and existing callers.

Tier 6 requires reproducible source, performance, processing and output state. Founder documentation explicitly states runtime enforcement is not integrated. Adopt relevant versioned metadata in this capability; do not claim full doctrine enforcement.

## Architecture

Use incremental extensions, rather than replacing the runtime. Separate prompt resolution, composition, revision, validation and export into focused services. The shared workbench service orchestrates them through the existing staged run lifecycle.

Flow: prompt and controls → validated resolved settings → local seeded composition → musical/technical report → staged artifacts → committed run → audition and revision.

Prompt interpretation is optional. An explicit Interpret action proposes settings; the operator reviews and edits them before Generate. A configured cloud provider returns a typed settings proposal, never executable code or authoritative notes. Offline interpretation recognizes documented supported instructions and reports unhandled text; it must not pretend to understand unsupported requests. Generate always uses displayed resolved settings. Explicit user controls win over prompt suggestions.

## Settings contract

Preserve existing fields and defaults. Add an optional versioned settings block; absent settings select legacy v1 behavior so old requests remain reproducible. New Studio requests select composition_v2. Unknown fields and invalid values are rejected.

| Control | Initial supported values or range |
| --- | --- |
| Prompt | 0–2,000 characters; stored as operator input |
| Length | 4, 8, 16, 32 bars in 4/4 |
| Progression | style default or 1–16 explicit scale degrees, each 1–7, cycled at a selected 1/2/4-bar harmonic rate |
| Chord type | triad, seventh, ninth |
| Voicing | close, open; smooth voice leading on/off |
| Track selection | melody, chords, bass, drums; at least one enabled |
| Pitch range | per pitched track MIDI 0–127, lower ≤ upper; feasible voicing required |
| Melody density | sparse, balanced, busy |
| Contour | balanced, ascending, descending, arch |
| Motif variation | 0–100%; 0 retains the phrase motif while following selected harmony |
| Rhythmic syncopation | 0–100% |
| Swing | 50–67%; 50 is straight, applied to eligible offbeat subdivisions |
| Timing humanization | 0–30 milliseconds, clamped to arrangement boundaries |
| Velocity | base 1–127 per track; variation 0–20, clamped to 1–127 |
| Chord spread | 0–40 milliseconds of strum offset |
| Bass mode | sustained, rhythmic |
| Drum feel | half-time, backbeat; hat subdivisions eighth or sixteenth |
| Phrase ending | tonic resolution or open |
| Seed | existing integer bounds |

Expose common controls immediately and advanced controls in a collapsible panel. Show units and resolved values. Do not offer controls that the engine ignores. Key aliases normalize to canonical supported spellings; unsupported scales remain explicit validation errors. V2 initially retains the four existing scales and three styles.

Use distinct stable pseudo-random streams for each track and musical function, derived from seed and engine version with a stable hash. Adding a drum setting cannot silently change chord notes. Voice leading scores ordered pitches with register and leap penalties; unsupported voicings fail before output generation. Melody develops a recurring phrase through rhythmic transformation, contour and bounded variation, with phrase breaths and configurable endings. Bass follows resolved harmony. Drum variation respects selected feel and phrase boundaries.

## Revisions and lineage

Each revision creates a new immutable run. Inputs include parent_run_id, selected tracks to regenerate, seed and settings patch. Parent must be a succeeded MIDI run in the current ownership scope. Copy locked tracks' note records exactly. A track-specific change affects only selected tracks.

Changing global key, scale, BPM or bar count while any enabled parent track remains locked is rejected with an actionable explanation; require unlocking all affected tracks. Track-specific ranges apply only to regenerated tracks. Report changed settings, regenerated tracks and preserved tracks. Preserve parent records and files.

Composition.json schema v2 records owner/workspace/project, run ID, parent ID, prompt, resolved settings, interpretation method, engine version, notes, track IDs, validation report and artifact hashes through the run manifest. No fabricated instrument/preset state: record these as unspecified until provided by the operator. Generated MIDI is performance material; WAV preview is a derived audition asset.

## Export and visible behavior

Retain existing output names and download behavior for legacy requests. Studio exports selected individual tracks, combined type-1 arrangement, Audition.wav, Composition.json, Quality_Report.json and FL_Studio_Readme.md. Include tempo and 4/4 metadata, explicit end markers and key metadata when representable. Drums use GM channel 10; describe note mapping in the readme. Export a checksummed ZIP through the existing artifact mechanism.

The result screen shows settings, source/parent, generation method, selected tracks, validation results, preview playback and downloads. Provide Regenerate, Revise selected tracks and Reuse settings. Preserve form state after errors. Busy state prevents accidental duplicate submission; retries reuse the same request ID and identical payload. An edited request receives a new ID.

Audition remains an explicitly labeled simple synthesis preview. Professional composition quality is evaluated independently of preview timbre. No mastering or finished-recording claims.

## Evidence and next action

Provide measured facts: note count, pitch ranges, pitch-class distribution, rhythm density, maximum melodic leap, adjacent chord movement and phrase repetition. Label musical interpretations as heuristic. Any next-step recommendation includes evidence references, assumption, proposed action and a listening check. Examples: audition the phrase ending, compare a less dense melody, or choose an FL Studio instrument. Do not mark a composition commercially approved from algorithmic checks.

## HTTP/MCP and failure model

Extend the existing MIDI command additively and introduce explicit interpret and revise capabilities. Before defining concrete route/tool names, inspect existing router and MCP registration patterns. Both invoke shared services and return versioned schemas. Read-only history queries do not mutate. Generation and revision persist local runs; interpretation proposals do not generate assets.

Preserve authorization, owner/workspace scoping and request fingerprinting. Duplicate identical request IDs return the original run; conflicting inputs fail. Reject missing parents, invalid settings, unsupported output requests and infeasible pitch ranges before staging. Provider failures return explicit unavailable interpretation status while manual local generation remains usable. Persist sanitized errors, never credentials or provider response bodies.

Keep staged file generation and atomic publication. Recovery marks incomplete jobs interrupted. Downloads remain constrained to recorded artifacts. Treat prompt text as data; models cannot select arbitrary filesystem paths or execute commands. Use existing runtime limits for preview duration and impose a documented maximum note budget of 50,000 notes per run.

## Verification and acceptance

1. Legacy fixtures reproduce existing notes for representative cloud, trap and soul requests.
2. V2 runs with identical settings, seed and engine version reproduce note records and MIDI bytes; provenance timestamps are excluded from byte-equivalence claims.
3. Parse all MIDI with mido: every note-on has its matching note-off, durations are positive, velocities and pitches are valid, delta times nonnegative, notes stay inside the requested arrangement and pitched notes respect the chosen scale/range.
4. Verify note lifecycles using event simulation, including repeated same-pitch notes and same-tick off/on ordering. Monophonic melody/bass must not create unintended overlapping same-pitch voices.
5. Parameter variations demonstrate actual effects for every exposed control. Test all styles/scales, each length, extreme density, seeds 0/93/max and narrow feasible ranges; impossible ranges return errors.
6. Revisions preserve locked notes exactly, parent remains unchanged, and forbidden global changes fail. Test invalid ownership, missing parent and failed parent.
7. API/MCP tests cover validation, authorization, idempotent replay, conflict, provider timeout, partial export failure and interrupted-job recovery.
8. Desktop/browser checks exercise interpretation, edits, generation, playback, revision and all downloads through the real UI; verify state remains after errors.
9. Import representative part and arrangement files into FL Studio on Windows; confirm tempo, bar length, track separation and endings. This requires access to Daniel's Windows environment and is a distinct external verification gate.
10. Daniel compares six paired legacy/v2 phrases with identical style/key/BPM/length using equivalent instrument sounds. Rate harmonic coherence, melody development, groove and usefulness 1–5. Target: v2 mean improvement ≥0.5 overall, no dimension average below 3, and at least four v2 phrases judged worth continuing. Record revisions when the target is missed; no professional-quality claim before this evaluation.

## Delivery and next stages

Implementation order: baseline tests → additive contracts → composition v2 → lineage/revision → export/validation → UI and MCP → local integration tests → Windows/FL Studio and listening evaluation. Inspect existing desktop UI, MCP registration, dependency versions and tests before finalizing file-level implementation tasks.

Catalog follow-on: resumable folder ingestion, configurable byte budgets, persistent relative paths, pagination/search, collections and raw/processed/preset lineage. Assistant follow-on: project-scoped conversation and retrieval, ranked next actions and outcome tracking. Both consume immutable generation IDs and evidence from MIDI Studio.

This design does not publish repository changes or build a new Windows release. Those actions and any external verification must be reported separately from local implementation. Repository commit/push is not inferred from design approval.
