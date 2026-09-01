# Sonic AI V3 Intelligence Loop — Implementation Order

## Current objective
Move from canonical architecture to an executable, testable longitudinal intelligence loop.

## Layer 1 — Canonical contracts

Complete and validate schemas for:

`Intent → Goal → Milestone → Action → Event → Obstacle → Intervention → Outcome → Evidence → Knowledge → Memory → Creator DNA → Foresight`

## Layer 2 — Event ingestion

All meaningful state changes emit structured events. Events must be append-oriented and traceable to their source.

## Layer 3 — State projection

Build deterministic projections for current intent state, goal progress, milestone status, open obstacles, active interventions, and gate status.

## Layer 4 — Intelligence checkpoint

After meaningful state change:

```text
receive event
→ update projection
→ collect relevant evidence
→ detect contradiction
→ evaluate intent relevance
→ update memory/knowledge candidates
→ evaluate DNA evidence
→ update foresight candidates
→ persist explainable checkpoint
```

The checkpoint should be cheap enough for frequent use and should escalate to deeper analysis only when relevance warrants it.

## Layer 5 — Retrieval

Rank evidence using task relevance, intent relevance, project scope, temporal validity, confidence, provenance, and recency. Retrieval must preserve the distinction between facts, observations, and inference.

## Layer 6 — Human control surface

Expose:

- active intents
- progress/momentum
- gates
- obstacles
- interventions
- evidence
- forecasts
- Creator DNA changes
- unresolved contradictions
- recommended next actions

The user must be able to correct, reject, supersede, or delete eligible intelligence records.

## Layer 7 — Foresight evaluation

Every material forecast receives a later evaluation event. Track calibration and error over repeated predictions.

## Layer 8 — Agent integration

Agents consume the same canonical state/evidence model. They do not maintain shadow versions of user truth.

## Layer 9 — Safe action

Automation requires explicit policy, permission, confidence/risk evaluation, and an auditable action event.

## First end-to-end test

Use **Future Intent Entry 001 — Omega House Legacy Expansion**.

The test should create an intent, update its revenue/portfolio/timing/readiness gates, register a blocker, execute an intervention, capture the creator decision, and later compare forecast to actual outcome.

## Definition of done

Sonic can reconstruct an entire intent trajectory from first capture to outcome without relying on chat transcript memory alone.
