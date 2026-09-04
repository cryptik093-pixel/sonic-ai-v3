# OH-M02 — Audio Defect Taxonomy & Severity Semantics v1

**Control ID:** `OH-M02`  
**Phase:** Sonic AI V3 Phase 2 Runtime Hardening  
**Owner:** Audio Analyzer / Metadata / Intelligence Core  
**Status:** implemented / awaiting CI evidence  
**Depends on:** validated `OH-M04` deterministic measurement baseline  
**Doctrine links:** `OH-DR-TRUTH-001`, `OH-DR-AI-001`, `OH-DR-RESCUE-001`, `OH-DR-LOWEND-005`

## Purpose

OH-M02 gives Sonic AI a stable vocabulary for production problems without allowing measurements to masquerade as diagnoses.

The taxonomy separates five things that must never be collapsed:

1. **observation** — what was measured or directly observed;
2. **signal** — an observation that warrants review;
3. **candidate defect** — a possible production failure that still needs context or comparison;
4. **confirmed defect** — a production failure supported by sufficient evidence;
5. **cause** — the mechanism believed to have produced the defect.

A confirmed defect may still have an unknown cause. A deterministic signal is not automatically a defect.

## Defect lifecycle

| State | Meaning | May drive automatic repair? |
|---|---|---|
| `signal` | noteworthy observation only | no |
| `candidate` | plausible issue requiring confirmation | no |
| `confirmed` | evidence supports a real production failure | only under a separate permission/policy gate |
| `resolved` | confirmed issue has passed its verification test | not applicable |
| `accepted_exception` | issue is intentional or consciously retained | no |

The v1 executable layer emits **candidate** records only.

## Severity scale

Severity is impact, not confidence.

| Severity | Meaning |
|---|---|
| `unrated` | insufficient context to assign production impact |
| `minor` | perceptible or measurable issue with low consequence |
| `material` | meaningfully degrades hierarchy, translation, usability or reproducibility |
| `major` | strongly compromises the intended asset/release in an important playback or workflow context |
| `critical` | blocks release, destroys required content, violates rights/integrity, or creates an unrecoverable/unsafe downstream state |

Candidate signals default to `unrated`. Sonic must not infer severity from a raw measurement alone unless an accepted asset-class tolerance or context-specific rule exists.

## Confidence is separate from severity

Future confirmed records should carry a confidence field independently from severity.

Example: a subtle but certain metadata mismatch can be high-confidence/minor, while a possible low-end translation collapse may be low-confidence/major.

## Cause status

Allowed cause states:

- `unknown`
- `suspected`
- `supported`
- `confirmed`

No OH-M04 measurement is sufficient by itself to set a production cause above `unknown`.

## Evidence classes

| Evidence class | Meaning |
|---|---|
| `deterministic_observation` | reproducible numeric/header/hash observation |
| `comparative_observation` | controlled A/B, reference or translation comparison |
| `contextual_evidence` | asset role, production intent, lineage, render settings, monitoring constraints |
| `producer_assessment` | human/producer judgment |
| `runtime_outcome` | observed result after an action or rollback |

A confirmed defect should normally include more than one evidence class when interpretation is involved.

## Canonical category families

### Dynamics — `DYN`

Covers sample-level overload signals, crest/transient behavior, clipping/limiting distinctions, and loudness/true-peak relationships.

Initial code:

- `OH-DEF-DYN-FS-001` — **Digital full-scale sample incidence**.
  - Trigger: OH-M04 exact full-scale sample count > 0.
  - State: candidate.
  - Cause: unknown.
  - Prohibited inference: "the mix clipped" or "a limiter caused this".

### Stereo / spatial — `ST`

Covers correlation, center authority, mono hierarchy preservation, phase/polarity risk and excessive decorrelation.

Initial code:

- `OH-DEF-ST-NEG-001` — **Negative stereo correlation risk**.
  - Trigger: measured two-channel OH-M04 correlation < 0.
  - State: candidate.
  - Required confirmation: mono/center or comparative evidence.
  - Prohibited inference: "the mix fails in mono" from correlation alone.

### Signal integrity — `SIG`

Covers missing signal, unintended silence, truncation, corrupt render, discontinuity and channel loss.

Initial code:

- `OH-DEF-SIG-SIL-001` — **Digital silence present**.
  - Trigger: duration > 0 and OH-M04 silent-sample ratio = 1.0.
  - State: candidate.
  - Required confirmation: asset role/intent.
  - Prohibited inference: silence is defective if the asset is intentionally silent.

### Low-end — `LOW`

Reserved for kick/808 ownership, sub translation, low-frequency masking, uncontrolled sustained energy and low-end phase relationships.

No v1 automatic code is emitted until OH-M03 fixtures and an accepted low-end evidence contract exist.

### Masking / spectral — `MSK`

Reserved for target-masker relationships, resonant obstruction and frequency competition. Recommendations must name competing objects, not only frequency bands.

No v1 automatic code is emitted from a single full-mix spectrum.

### Temporal / transient — `TMP`

Reserved for transient smearing, timing conflict, tail interference, groove degradation and envelope-related failures.

### Translation — `TRN`

Reserved for failures that are actually demonstrated across controlled playback contexts or mono/reference tests.

### Export / delivery — `EXP`

Reserved for render mismatch, truncated remainder, wrong asset-class format, missing channel, unexpected silence padding and post-render verification failures.

### Metadata / lineage — `META`

Reserved for missing production IDs, invalid derivative lineage, absent hashes, rights inheritance gaps, missing render evidence and reproducibility failures.

## Record invariants

Every defect/signal record must preserve:

- stable `defect_code`;
- taxonomy version;
- lifecycle `state`;
- severity independent from confidence;
- cause state;
- evidence class;
- exact evidence field/reference;
- observed value where applicable;
- rationale;
- required confirmation when not confirmed.

## v1 executable bridge

Implementation:

`packages/audio-analysis/python/defect_taxonomy.py`

Tests:

`packages/audio-analysis/python/test_defect_taxonomy.py`

The executable bridge intentionally emits only three conservative candidate signals from validated OH-M04 measurements. This is a vocabulary and evidence-control layer, not an AI mixing diagnosis engine.

## Acceptance conditions

OH-M02 v1 passes when CI proves that:

1. ordinary OH-M04 measurements can produce no defect candidates;
2. full-scale incidence produces `OH-DEF-DYN-FS-001` without claiming clipping or limiter causation;
3. negative stereo correlation produces `OH-DEF-ST-NEG-001` without claiming mono failure;
4. complete digital silence produces `OH-DEF-SIG-SIL-001` but remains context-dependent;
5. every emitted candidate is `severity: unrated` and `cause_status: unknown`;
6. non-OH-M04 measurement input is rejected.

## Next dependency

OH-M05 should now define the canonical asset/measurement/defect metadata envelope so OH-M04 measurements and OH-M02 records can persist and travel through Backend, Memory and Producer Intelligence without losing provenance.
