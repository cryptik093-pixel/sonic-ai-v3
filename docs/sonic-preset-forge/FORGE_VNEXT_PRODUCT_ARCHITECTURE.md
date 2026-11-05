# Sonic Preset Forge — VNext Engineering Architecture / Signature-to-State System
Date: 2026-11-05 | Status: architecture and execution proposal, not implemented capability
Owner: Omega House Studio LLC | Application: Sonic AI V3 | Workstation: Windows FL Studio

## Product promise
Given an authorized audio example, a producer's creative language and a verified DAW/plugin environment, produce an **original, audible, editable, native FL Studio processing state** whose sonic identity, plugin dependency manifest, control mappings, source provenance and reproducibility are independently validated. Do not equate a plan, binary hash or loudness change with a verified sound.

## Nonnegotiable system design
- Preserve `tools/fst_generator` instead of replacing it or creating an unrelated planner. Reuse current SQLite/design/analysis/native records, evolve them with versioned additive contracts.
- User's local FL Studio is the authoritative authoring and serialization host for the initial native adapter. Do not pretend Image-Line provides undocumented arbitrary Patcher-graph APIs.
- Separate deterministic audio analysis/rules and host capabilities from optional LLM creative assistance. Default to no billable calls.
- All graph/parameter execution targets a disposable QA project and verified installed plugin IDs; protect active FL sessions.
- Preserve native source files and test renders with byte hashes; never repurpose a reference as a new generated variation.
- All public GitHub materials must be source/provenance/rights reviewed. User audio, DBs, secrets, installers, plugin licenses and third-party states stay local.

## Contract: one typed artifact progression
`CreativeBriefV1` → `SourceEvidenceV1` → `PluginCapabilityProfileV1` → `ChainGraphIRV1` → `HostExecutionJobV1` → `NativeStateRecordV1` + `RenderPairV1` → `AcceptanceReportV1` → `ReleaseCandidateV1`.

Minimum common fields: schema_version, immutable artifact ID, parent ID, project/session scope, input/source hashes, author, provenance, host FL build, tested plugin identity/version, role and load target, intended vs observed settings, consent/rights status, test fixture, test output hashes, timestamps, evidence paths, status and failure reason.

### Section A — Creative DNA & Signature Composer
Input: source role, genre DNA, artist/producer aesthetic adjectives, expressive intensity, target emotion, audible contrast, fixed vs adaptive parameter intentions, sonic identity constraints. Derived dimensions: *tonal color, dynamic envelope, stereo/spatial staging, temporal movement*. Each proposed recipe must state WHY every node exists, how it changes the sound, what it sacrifices, and what a macro musically controls. The engine generates a small candidate set and can choose "no processing" as a legitimate baseline. Retain specific Omega House terminology without falsely claiming exact named-artist signal chains.

### Section B — Audio Intelligence / Signal Lab
Measure format/hash, segment-level peak/RMS, clipping samples, noise/silence, DC, crest, stereo correlation, mid/side energy and spectrum with a versioned analysis engine. Add gated BS.1770 integrated/short-term LUFS and true peak only after verified meter implementation/conformance. Flag uncertain tempo/key, unknown wet/dry status and missing reference; never manufacture metadata. Include dynamics/sibilance/transient/stereo compatibility profiles per source role, distinct from artistic judgment.

### Section C — Plugin Registry & Real Host Allowlist
Maintain separate `disk_observed`, `host_instantiated`, `license_confirmed`, `automation_exposed`, `save_reopen_verified`, and `commercial_dependency_approved` flags. Plugin identity includes exact name, vendor, location, architecture, host build, version, normalized controls with readback mapping, parameter units/ranges, rescan date, installed/effect-type proof, exception history. Native stock, ADLIB93, Omega House EQ/Reflector EQ, Sonic Organism and external plugins are distinct; never swap one for another silently. Missing dependencies fail closed and offer a supported fallback graph before execution.

### Section D — Routing & Patcher Graph Forge
Support typed serial, parallel wet, multiband, mid/side, sidechain and send buses **only where the export format can actually retain their topology**. Explicit graph ports and signal domain prevent doubled dry paths, accidental feedback and phase-incompatible summing. Patcher Control Surface macro bindings require observed target index, range, tapers and reversible readback. Auto-created curves are design suggestions until the host confirms them. A master chain demands conservative peak/safety rules; an ad-lib creative insert permits higher contrast. Whole-project sends requiring routing outside one mixer FST must use a project template or clearly labeled manual routing, not a deceptive single-track export.

### Section E — FL Studio Native Execution Bridge
Durable state machine: proposed → preflight → queued → host_ready → applying → readback_passed → host_saved → reloaded → rendered → accepted / failed / blocked. Jobs carry payload hashes, idempotency keys, execution trace and an exclusive user-approved isolated test-project target. Never execute arbitrary browser shell text. Host adapter must compare exact seed/template hashes, actual plugin instances, macro readbacks, bypass state, wet ratios, order and settings. Implement safe bounded rollback. File receipts require authenticated atomic transport or explicit existing interpreter fallback, not invented successful save. FL Studio must perform the native export; preserve the original project untouched.

### Section F — Audition & Audio QA Bench
Audio controls display exact media provenance: dry source, original host render, candidate host render, reload render, not a simulated silence/player placeholder. Confirm a *real audible* render on Windows through the selected output device, not just successful HTTP decode. Use loudness-matched A/B for assessment separately from unadjusted export playback; record gain offset. Test level, silence, transient integrity, audible clipping/artifacts, polarity, stereo collapse/mono compatibility, CPU, latency, automation/bypass, persistence after host reopen and repeat-render variation. Include an optional producer listening rubric (identity, musical fit, usability, loudness-neutral improvement, problem severity).

### Section G — Learning, Tribal Network & Sonic Intelligence
Each workshop exercise links an original fixture, submitted graph, hypothesis, host artifact, measured before/after, producer decision and outcome. Sonic Intelligence tracks provenance and contradictions, never promotes an unverified assertion to a plugin fact. Tribal Workshop can teach stock FL controls and capture feedback, but does not silently gain production/edit permissions. Reference 606 prior FSTs for private comparison only where usage rights allow; do not redistribute or clone third-party state.

### Section H — Product Bank/Release Factory
Generate 1 serious pilot → 3 genuinely distinct variants → 10 role-specific certified presets. Count **unique audio-and-state-evidenced outputs**, not filenames or recipe objects. For each new candidate require canonical asset ID, same-source test fixture, fully restored host state, plugin dependency matrix, listening approval, ZIP CRC and individual SHA-256. Release folders: `01_PRESETS`, `02_AUDIO_DEMOS`, `03_DOCUMENTATION`, `04_PLUGIN_DEPENDENCIES`, `05_LICENSE`, `06_ARTWORK`, `07_QA_REPORTS`, `manifest.json`. Shopify handoff is read-only by default and production publication requires approval.

## Category-specific quality boundaries
| Role | Identity goal | Distinct proof required |
| --- | --- | --- |
| Main vocal | presence, color, musical compression, diction | sibilance/attack stability, gain-matched phrase A/B |
| Ad-lib | aggressive alter-ego color, temporal/spatial movement | clear contrast from main vocal; formant/pitch only with actual available processor |
| Recording | low-latency stable cue sound | measured round-trip latency/monitoring, no unsupported zero-latency claims |
| 808 & bass | weight, pitch audibility, phase stability | low-frequency translation, harmonic contrast, mono/sub integrity |
| Drum/kick/snare | transient and groove identity | transient delta, timing/crest/peak, parallel routing sanity |
| Guitar, melodies, bells, one-shots, loops | harmonic/timbre identity with intact articulation | sustain/attack/noise/tail and polyphonic compatibility |
| Experimental/hyperpop | intentional motion and controlled destruction | deliberate modulation, preset recall, output safety |
| Sends | space/movement and predictable wet-only gain | wet-only render and dry-path duplication test; project routing proof |
| Mix bus | cohesive glue without hiding defects | dynamic interaction and stem-independent translation |
| Master | final tonal translation and consistent delivery | measured loudness/true-peak only with conformant meter, conservative clipping/mono/codec QA |

## UX acceptance — no fake controls
Navigation: Design → Configure → Hear → Build in FL → Verify → Save → Export. Every pane must show exact truth state: `DESIGN_ONLY`, `NATIVE_COPY`, `NEW_NATIVE_UNVERIFIED`, `DAW_VERIFIED`, `LISTENING_APPROVED`, `RELEASE_CLEARED`. Audio Play is disabled with explanation until an actual decodable media file exists; errors state whether decoding, output-device, server session, waveform, permission or host rendering failed. Recovery restores unsaved brief without silently re-running mutations. No orphaned progress spinners.

## Delivery phases, gates, and stop conditions
**M0 / Preservation + documentation (this increment):** working tree and hash baseline; unified indexes and evidence links. No code/sound changes.
**M1 / Crown Center v002 true host acceptance:** confirm stock plugin host instances, calibrate four macro controls, build distinct working graph in disposable FL project; save 1 new FST; reload; render identified same source; record A/B and actual listening; preserve original. Stop if any macro has unknown mapping, no sound, incompatible reload, or failed project isolation.
**M2 / Audio UX:** instrument browser play/pause/device and matched A/B using recorded host output; tests include eight review takes and absent-media failure paths.
**M3 / Three real variants + batch engine:** unique audible targets with versioned hashes and source-aware bounded variation; no renamed duplicates. Validate idempotency/failure rollback.
**M4 / Role-led 10-presets pilot:** select one commercially coherent role, perform independent QA on each of ten. Expand roles serially only after acceptance rate and audio quality are observed.
**M5 / Release factory and measured business workflow:** dependency installer guidance, license, previews, delivery ZIP, customer installation test, approved storefront draft.

### Acceptance targets (goals, NOT observed results)
- 100% of released assets: complete rights/host/dependency/source manifest and actual save-reload proof.
- 0 unverified installed-plugin substitutions in approved preset graph.
- 0 silent/phantom player states labeled as audio success.
- 100% of candidate files: unique content checksum, with sonic differentiation assessed independently.
- Host acceptance repeatable at 44.1 and 48 kHz on an explicitly certified FL build; numerical tolerances calibrated from actual baseline, not assumed.
- Demonstrated secure abort and source preservation after failed build; no writing to a production session.

## Immediate highest-value unit
Calibrate and host-verify **one** original Crown Center v002 Patcher state. This establishes the working conversion `Intent → Graph → Actual Sound → Native File → Same Sound After Reload`. Do not invest first in another 90 text recipes or a speculative giant UX rewrite.
