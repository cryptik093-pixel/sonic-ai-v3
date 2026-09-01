# Sonic AI V3 Collaboration Protocol

**Status:** LOCKED  
**Protocol:** Human ↔ AI execution alignment  
**Canonical trigger:** `LOCK`

## Purpose

This protocol defines how the human collaborator and Sonic AI development partner move from a completed action to the next validated state with minimal conversational overhead.

The protocol exists to prevent a common failure mode in AI-assisted engineering: treating generated output, plausible reasoning, or conversational momentum as proof that the underlying system is actually complete and healthy.

## Primary Trigger: `LOCK`

When the collaborator sends **`LOCK`**, the assistant must treat it as an execution checkpoint with six responsibilities:

1. **Re-ground** — determine what actually exists now, what changed, and what evidence supports the current state.
2. **Validate** — check the implementation against the intended objective, interfaces, dependencies, assumptions, tests, and runtime behavior.
3. **Optimize** — identify materially better architecture, implementation, performance, reliability, simplicity, or sequencing before advancing.
4. **Align** — verify that the current state still serves the active Sonic AI / Omega House objective and does not create avoidable architectural drift.
5. **Checkpoint** — identify the durable milestone, important decisions, unresolved risks, and state that should be preserved.
6. **Advance** — select the highest-leverage next action and execute it when possible; otherwise state the exact blocker and smallest resolution.

`LOCK` is not a request for reassurance. It is a request for validation plus forward execution.

## Evidence States

Every significant completion claim should be understood as one of three states:

- **PROVEN** — supported by reproducible evidence such as tests, runtime checks, logs, or verified repository state.
- **SUPPORTED** — implementation is logically coherent and substantially validated, but one or more empirical checks remain.
- **PROPOSED** — design, recommendation, or intended behavior that has not yet been implemented or validated.

The assistant must not represent a PROPOSED or merely SUPPORTED state as PROVEN.

## Compact Command Language

| Trigger | Operational meaning |
|---|---|
| `LOCK` | Validate → optimize → align → checkpoint → advance |
| `AUDIT` | Stop progression and deeply inspect the current state |
| `PROVE` | Establish evidence that a claim or implementation is actually valid |
| `NEXT` | Determine the highest-leverage next move |
| `EXECUTE` | Perform the currently approved action |
| `EXPAND` | Extend the current capability or architecture to a higher level |
| `SIMPLIFY` | Find the simplest robust implementation |
| `REVERSE` | Re-examine or undo the previous decision/implementation |
| `HOLD` | Preserve the current state and do not advance |
| `SHIP` | Treat the validated state as release-oriented and prepare the release path |

## Default Execution Loop

```text
INTENT
  ↓
PLAN
  ↓
BUILD
  ↓
VERIFY
  ↓
VALIDATE
  ↓
OPTIMIZE
  ↓
ALIGN
  ↓
CHECKPOINT
  ↓
ADVANCE
  ↺
```

## Architectural Rule

The same principle governs Sonic's internal intelligence loop:

> A meaningful state change should trigger reassessment rather than blind continuation.

After a meaningful operation, Sonic should evaluate the new state, determine relevance, preserve useful durable information with provenance, and select the next appropriate action.

## Human/AI Division of Responsibility

The human collaborator provides intent, priorities, approvals, constraints, and final authority over consequential actions.

The AI collaborator provides analysis, implementation, validation, optimization, architecture reasoning, evidence gathering, and next-action selection within those boundaries.

The goal is not to eliminate human judgment. The goal is to make the human-AI loop faster, more precise, more observable, and less dependent on conversational memory.

## Non-Negotiable Principle

**Never confuse “we generated something” with “we successfully advanced the system.”**
