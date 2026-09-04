# Omega House Production Doctrine - Canonical Runtime Derivative V1

**Canonical ID:** `OH_DOCTRINE_PRODUCTION_CANONICAL_V1`  
**Source authority:** Omega House Production Doctrine, First Edition (2026)  
**Source archive:** `OH-KA-2026-09-04-001`  
**Lifecycle:** canonical derivative  
**Authority:** normative production doctrine  
**Runtime validation:** not implied by this document

This document converts the First Edition doctrine into a stable, machine-readable set of principles and requirements for Sonic AI V3. It does not replace the textbook. It exists so production intelligence, tests, schemas, agents, and UI behavior can reference durable requirement IDs instead of vague prose.

## 1. Governing primitive

Omega House engineering treats production as a closed learning system:

```text
EVENT -> STATE -> DECISION -> ACTION -> OUTCOME -> LEARNING
```

A plugin setting is not a decision by itself. A valid engineering decision identifies a defect, forms a causal hypothesis, performs a controlled intervention, compares the result under appropriate listening conditions, and records the outcome.

### Core requirements

- `OH-DR-TRUTH-001` - Separate observation, interpretation, proposed action, and proven outcome.
- `OH-DR-TRUTH-002` - Store evidence state with material engineering claims.
- `OH-DR-TRUTH-003` - Never infer completion solely from documentation, UI presence, or generated language.
- `OH-DR-TRUTH-004` - Preserve a rollback-safe source before destructive or irreversible action.
- `OH-DR-TRUTH-005` - Record unresolved defects rather than hiding them behind completion language.

## 2. Evidence states

The canonical doctrine uses four evidence states:

| State | Meaning |
|---|---|
| `PROVEN` | Reproducible evidence exists: render, test, file, log, measured result, checksum, verified repository state, or equivalent. |
| `SUPPORTED` | Reasoning is coherent and substantially evidenced, but at least one empirical check remains. |
| `PROPOSED` | Designed or recommended but not implemented and verified. |
| `UNCERTIFIED` | Relevant work may exist, but the complete acceptance gate remains open. |

### Requirements

- `OH-DR-EVID-001` - Evidence state must travel with durable conclusions.
- `OH-DR-EVID-002` - A louder or more exciting comparison is not sufficient evidence of improvement.
- `OH-DR-EVID-003` - Runtime behavior outranks narrative claims about software capability.
- `OH-DR-EVID-004` - `implemented` status cannot be promoted to `validated` without reproducible evidence.

## 3. Pass Gate and Ship Gate

A **Pass Gate** authorizes progression inside the work. A **Ship Gate** authorizes release outside the work.

Every gate must identify required evidence, unacceptable defects, and a rollback point.

- `OH-DR-GATE-001` - Each production stage must define an explicit Pass Gate.
- `OH-DR-GATE-002` - Published assets require an explicit Ship Gate.
- `OH-DR-GATE-003` - Gate failure returns to the responsible stage, not automatically to the beginning.
- `OH-DR-GATE-004` - Product release requires lineage, rights, technical integrity, and destination validation in addition to sound quality.

## 4. Critical listening and bias control

The doctrine treats hearing as adaptive and comparative. Level, order, duration, fatigue, and context can bias judgment.

- `OH-DR-LISTEN-001` - Material A/B comparisons should be level matched when possible.
- `OH-DR-LISTEN-002` - Comparison questions must be specific enough to falsify a hypothesis.
- `OH-DR-LISTEN-003` - Mono checks evaluate hierarchy preservation, not preservation of stereo width.
- `OH-DR-LISTEN-004` - Low-frequency authority must not depend on fragile side information.
- `OH-DR-LISTEN-005` - Monitoring practice must account for fatigue and listening safety.

## 5. Beat Mix Rescue control system

The 45-minute rescue is a bounded diagnostic workflow, not a claim that all mixes can be completed in 45 minutes.

Canonical stage order:

```text
REFERENCE + TRIAGE
        -> GAIN + BALANCE
        -> LOW-END OWNERSHIP
        -> MASKING / ROLE SEPARATION
        -> STEREO + MONO
        -> REVERB / DEPTH
        -> DYNAMICS / PEAK CONTROL
        -> TRANSLATION
        -> EXPORT VERIFICATION
```

- `OH-DR-RESCUE-001` - Rank the dominant failures before processing.
- `OH-DR-RESCUE-002` - Correct gain and hierarchy before downstream tonal or dynamics decisions.
- `OH-DR-RESCUE-003` - Resolve kick/808 ownership before master-bus dynamics are trusted.
- `OH-DR-RESCUE-004` - Prefer arrangement, register, onset, envelope, and level repairs before excessive surgical EQ.
- `OH-DR-RESCUE-005` - Translation failure should trigger targeted rollback to the responsible subsystem.
- `OH-DR-RESCUE-006` - The exported file must be auditioned; the DAW session alone is not the released product.
- `OH-DR-RESCUE-007` - Preserve a compact rescue record containing production ID, source, reference, ranked failures, actions, A/B result, translation notes, export settings, and final evidence state.

## 6. Low-end ownership

- `OH-DR-LOWEND-001` - Kick and 808 roles must be deliberately assigned rather than allowed to compete by default.
- `OH-DR-LOWEND-002` - Envelope, onset timing, note duration, register, and arrangement are first-class low-end controls.
- `OH-DR-LOWEND-003` - Ducking is conditional behavior, not a universal requirement.
- `OH-DR-LOWEND-004` - Bass translation may require controlled harmonic information, but the intervention must preserve role and intent.
- `OH-DR-LOWEND-005` - Low-frequency monitoring limitations must be considered when confidence is assigned.

## 7. Masking and spectral role

- `OH-DR-MASK-001` - Diagnose target/masker pairs in musical context.
- `OH-DR-MASK-002` - Avoid treating narrow solo sweeps as final mix decisions.
- `OH-DR-MASK-003` - Prefer role separation and dynamic arrangement over stacked corrective notches when they solve the cause more naturally.
- `OH-DR-MASK-004` - Sonic AI recommendations should name the likely competing objects, not merely a frequency band.

## 8. Stereo, depth, dynamics, and loudness

- `OH-DR-STEREO-001` - Preserve center authority for foundational elements.
- `OH-DR-STEREO-002` - Width changes that depend on phase or timing require mono/correlation awareness.
- `OH-DR-DEPTH-001` - Reverb is a depth and density decision, not an automatic polish stage.
- `OH-DR-DYN-001` - Compressor behavior must be reasoned in terms of envelope and role.
- `OH-DR-DYN-002` - Clipping, limiting, loudness, and true-peak decisions must be distinguished rather than collapsed into one concept of loudness.
- `OH-DR-DYN-003` - Numerical values are starting observations unless a validated target contract says otherwise.

## 9. Translation and export

- `OH-DR-TRANS-001` - Translation evidence should include more than one playback context when the decision is consequential.
- `OH-DR-TRANS-002` - Cross-system failure must be described as an observable defect before repair is prescribed.
- `OH-DR-EXPORT-001` - Render configuration is part of the production evidence packet.
- `OH-DR-EXPORT-002` - The rendered deliverable must be verified independently of the source session.
- `OH-DR-EXPORT-003` - Asset-class tail, silence, alignment, bit depth, sample rate, and file-completeness rules belong in explicit contracts rather than undocumented habit.

## 10. Production lineage and asset architecture

The canonical production law is:

> One source should generate multiple legitimate assets without unnecessary reconstruction.

The repo-native implementation specification is `docs/production/OMEGA_HOUSE_CORE_PRODUCTION_ASSET_PIPELINE_V1.0.md`.

- `OH-DR-LINEAGE-001` - Every production receives a stable production ID.
- `OH-DR-LINEAGE-002` - Derived assets retain their relationship to the authoritative source.
- `OH-DR-LINEAGE-003` - Presets and master/engineering chains are durable assets when required to reproduce the source.
- `OH-DR-LINEAGE-004` - MIDI must represent the musical performance that produced the audio and should not be cosmetically cleaned at the expense of intent.
- `OH-DR-LINEAGE-005` - Asset replacement must define downstream invalidation behavior.
- `OH-DR-LINEAGE-006` - Final assets and manifests should support content-addressed integrity through hashes.
- `OH-DR-LINEAGE-007` - Rights and license inheritance must remain attached to derivatives.

## 11. Sonic AI production intelligence

The doctrine requires separation between deterministic facts, interpretation, producer-specific memory, and action.

```text
UPLOAD / SOURCE
   -> DETERMINISTIC ANALYSIS
   -> NORMALIZATION
   -> MUSICAL / ENGINEERING INTERPRETATION
   -> PRODUCER INTELLIGENCE
   -> MEMORY CANDIDATE
   -> RETRIEVAL
   -> ACTION / OUTCOME
   -> LEARNING
```

- `OH-DR-AI-001` - Deterministic measurements and model interpretation must remain distinguishable.
- `OH-DR-AI-002` - Recommendations should expose the evidence, rule, or uncertainty that produced them.
- `OH-DR-AI-003` - Producer-specific tendencies belong to Artist/Producer DNA and must not silently become universal rules.
- `OH-DR-AI-004` - Durable memory requires provenance and confidence.
- `OH-DR-AI-005` - Contradictory evidence must be resolved or preserved as conflict, not overwritten silently.
- `OH-DR-AI-006` - Agent/tool actions require explicit permissions, observable failure states, auditability, and safe retry/idempotency behavior.
- `OH-DR-AI-007` - Software documentation is specification context; current runtime capability must be proven independently.

## 12. Commerce and learning

- `OH-DR-COM-001` - Commercial performance is a downstream observation, not proof of audio quality.
- `OH-DR-COM-002` - Product version, asset lineage, campaign/event context, customer action, refund/payout state, and experiment identity should be joinable when commerce learning is used.
- `OH-DR-COM-003` - Correlation must not be presented as causal proof.
- `OH-DR-COM-004` - A shipped outcome should create a successor learning objective.

## 13. Twelve system laws

The normalized doctrine can be enforced as twelve system-level laws:

1. Evidence outranks assertion.
2. Observation is not interpretation.
3. A decision must name the defect it is meant to solve.
4. Pass Gates control progression; Ship Gates control release.
5. Roll back to the responsible state, not the entire system.
6. Preserve the authoritative source.
7. Preserve lineage through every derivative.
8. Separate deterministic facts from inference and preference.
9. Use the smallest sufficient intervention that survives comparison.
10. Documentation cannot certify runtime capability.
11. One source may produce multiple legitimate assets without unnecessary reconstruction.
12. Learning closes the loop after outcome evidence returns.

## 14. Sonic AI V3 module ownership

| Requirement family | Primary owner | Supporting modules |
|---|---|---|
| `TRUTH`, `EVID`, `GATE` | Intelligence Core | Backend, Frontend, Memory |
| `LISTEN`, `RESCUE`, `LOWEND`, `MASK`, `STEREO`, `DEPTH`, `DYN`, `TRANS`, `EXPORT` | Audio Analyzer | Intelligence Core, Frontend |
| `LINEAGE` | Backend / Pipelines | MIDI Engine, Memory, Metadata |
| `AI` | Intelligence Core | Artist DNA, Memory, Agents, Backend |
| `COM` | Event/Commerce pipeline | Intelligence Core, Analytics, Memory |

## 15. Validation rule

This file defines normative requirements only. A requirement becomes runtime-validated only when its record in `docs/knowledge/requirements/PHASE_2_REQUIREMENT_REGISTER.md` contains reproducible evidence.
