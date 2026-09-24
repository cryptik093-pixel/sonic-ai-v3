# Sonic v3.5 agent operating model

This is the current implementation guide under the existing
[Agent Constitution](../architecture/OMEGA_HOUSE_AGENT_CONSTITUTION.md).
It replaces the former root recovery instructions; the constitution's authority limits remain.
The registry is descriptive policy, not a scheduler, model configuration or authorization engine.

| Role | Owns | Allowed in this foundation | Next gate |
|---|---|---|---|
| Orchestrator | objective, scope, handoff | read status and registry, propose next task | durable task lifecycle |
| Audio analyst | deterministic measurement interpretation | propose from cited measurements | authenticated asset pipeline |
| Sonic Intelligence | evidence, decision, validation | propose evidence-backed decisions | scoped persistent memory |
| Repository engineer | implementation and tests | task-authorized branch changes outside MCP | validated PR |
| Validator | acceptance evidence | reproduce tests; report limits | integrated runtime checks |

No role has commerce, messaging, financial, arbitrary filesystem or shell authority via this MCP.
Model/provider binding is intentionally unset. These are responsibilities, not running agents.

Every handoff includes handoff_id, objective, from_agent, to_agent, entity scope,
allowed_actions, artifact references, constraints, expected_output, finish_condition,
timeout_at and return_to. Task lifecycle: proposed → accepted → running →
succeeded/failed/blocked/cancelled. The constitution's broader project lifecycle remains intact.
Blocked requires a concrete missing dependency. Only one owner may change a record;
future writes must use version checks and deduplication keys.

Sonic Intelligence records objective, owner, observations (source and observed_at),
inferences, recommendation, confidence basis, assumptions, risks, authorization,
execution evidence, next validation, status and supersedes. Accepted records are append-only;
new evidence supersedes rather than erases earlier decisions. No private reasoning traces.
