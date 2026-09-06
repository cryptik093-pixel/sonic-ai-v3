# SONIC_AGENT_ENVELOPE v1

Status: Proposed contract
Purpose: Common communication envelope for Sonic agents, Codex execution, guardians, commerce agents, and future MCP workflows.

```json
{
  "protocol": "SONIC_AGENT_ENVELOPE",
  "version": "1.0",
  "task_id": "",
  "parent_task_id": null,
  "agent": "",
  "intent": "",
  "context": [],
  "permissions": [],
  "inputs": {},
  "expected_outputs": {},
  "validation": [],
  "result": {},
  "evidence": [],
  "confidence": 0.0,
  "status": "pending",
  "next_action": null
}
```

## Required design properties
- explicit intent
- bounded permissions
- traceable parent/child tasks
- machine-readable inputs/outputs
- validation evidence
- confidence separated from factual result
- deterministic status
- explicit next action

## Intended flow
`ChatGPT/Codex/Shopify Agent/Audio Analyst/Repo Guardian -> Agent Envelope -> Sonic Intelligence`
