# Sonic AI v3.5 — agent instructions

## Start here
Read `docs/status/SONIC_PROGRESS.md`, `docs/status/sonic-state.json`, and
`docs/agents/OPERATING_MODEL.md` before acting. Inspect branch, HEAD and diff.
`main` remains canonical; v3.5 is an isolated development foundation until merged.
Preserve the existing README architecture, doctrine, audio code and historical evidence.

## Product and ownership
Sonic is the producer operating system intelligence layer.
Producer → Workspace → Project → Asset → Session → Task → Conversation.
Keep Next.js web, FastAPI API, workers and shared domain packages separate.
Upload → Analyze → Normalize → Audio Analyst → Producer Intelligence → Memory → Retrieve.
Deterministic facts precede model interpretation. Tenant scope precedes retrieval.

## Execution
One task owner; explicit bounded handoffs. Use the registry for intended responsibilities,
not as proof that autonomous agents exist. Read-only tools cannot acquire write authority.
No arbitrary shell, file, SQL or network tools exposed through MCP.
Existing task authorization persists. Financial, destructive and external communication
must have explicit authorization for the action. Never commit secrets or customer data.
Preserve user changes; no force pushes, resets or deletion for cosmetic cleanliness.

## Evidence and progression
Separate observation, inference, recommendation, decision, execution and validation.
Use VERIFIED, INFERRED, UNKNOWN, BLOCKED and COMPLETED with scope and evidence.
A process boot is not proof of integration or deployment. Historical reports are historical.
Update the progress document and machine state when capability changes; append dated
milestone evidence and explicitly supersede stale claims. Keep future gates open until proven.

## Verification
For MCP: `python -m unittest discover -s services/mcp/tests -v` after installing
`services/mcp/requirements.txt`. Tests must include a real protocol handshake and tool calls.
For audio: `python -m unittest discover -s packages/audio-analysis/python -v`.
Run relevant tests; record failures, don't turn missing app scripts into passing product checks.
