# Read-only tool inventory

Snapshot: 2026-09-15 UTC / 2026-09-14 America/Chicago. All five tools below were
returned by authenticated live `tools/list` and reviewed against
`apps/api/integrations/gateway.py`. No other tool is authorized in V1.

## Evidence and enforcement

Repository sources (relative to checkout root): `apps/api/integrations/gateway.py`,
`service.py`, `store.py`, `models.py`, `auth.py`, and `apps/api/schemas/project.py`.
The registry is fixed to five query handlers. They use SELECT/status reads and no
business-data write or external-provider call. Request/access logging and transient
connection state may occur. EventStore initialization writes schema at server startup;
these tool calls reuse the running store and do not initialize it.

All tools advertise `readOnlyHint: true`, `destructiveHint: false`,
`idempotentHint: true`, `openWorldHint: false`. These annotations are not enforcement.
The current server exposes no write tool and rejects unregistered tool names; the
plugin additionally specifies `enabled_tools`. This does not prove a future server
version safe. Skill restrictions are policy-enforced, and the shared static bearer
credential is not read-scoped: it also authorizes the separate HTTP integration-check
route, which persists decision records. Hard credential-level read-only isolation is
not provided. A dedicated read authorization boundary would require backend work
and is BLOCKED in this V1. Never test that limitation by invoking a write operation.

Memory requires producer AND workspace scope. No memory query exists. Known-project
and integration-trace reads have no tenant filter and cannot satisfy tenant-isolated
retrieval. Project listing and asset retrieval are also BLOCKED. Do not infer missing
relationships along Producer -> Workspace -> Project -> Asset -> Session -> Task -> Conversation.

## Shared output contracts

The live server publishes no `outputSchema`. Successful results use MCP `content`
text containing serialized JSON (clients may additionally expose structured content).
Decode JSON and inspect `isError` before interpreting it. Tool errors are not empty
successful results. The shapes below are source-derived, not enforced JSON schemas.

**Status**: `checked_at`, `provider_checks_fresh`, `provider_check_ttl_seconds`,
`trace_ids`, `integrations` (api, database, openai, shopify, mcp, event_ingestion).
Each **IntegrationStatus** contains `provider`, `configured`, nullable
`authenticated`, `reachable`, `permissions_proven`, `api_version`, `model_available`,
`runtime_available`, `checked_at`, `last_successful_check`, `last_error`, `latency_ms`;
arrays `requested_scopes`, `granted_scopes`, `required_scopes`, `missing_scopes`,
`ungranted_requested_scopes`, `degraded_capabilities`, `evidence`; and
`validation_status` (NOT_CONFIGURED, CONFIGURED, VALIDATED, DEGRADED, FAILED, NOT_TESTED).
Null authentication/reachability is unknown. Provider evidence has a 60-second TTL;
status never refreshes providers. Ingestion evidence proves a store query, not delivery.

**Project**: `id`, `name`, `artist`, `genre`, `bpm`, `key`, `notes`, `status`
(draft/active/archived), `created_at`, `updated_at`. No assets or tenant ownership fields.

**Decision**: persisted integration-check/webhook decision JSON. Expected fields:
`trace_id`, `timestamp`, `provider`, `requested_operation`, `evidence`,
`validation_status`, `agent_service`, `actor`, `resulting_state`, `external_side_effect`,
and optional `integration_status`. The handler returns stored JSON without schema
revalidation. No producer/workspace-scoped memory or hidden reasoning is exposed.

## Tools

### `sonic_system_status`

- Purpose: Read current API/database health and cached provider evidence. Does not call external providers or change business data.
- Authority: READ / query. Allowed in read-only V1: **yes**, within the single-operator scope above.
- Output/evidence: Status; live API/database and cached provider evidence.
- Side effects: no business writes or provider requests; local reads and possible infrastructure logging only.
- Exact advertised input schema:

```json
{
  "properties": {},
  "title": "sonic_system_statusArguments",
  "type": "object"
}
```

### `sonic_integration_status`

- Purpose: Read normalized integration states, check timestamps and trace IDs; configuration is not live validation.
- Authority: READ / query. Allowed in read-only V1: **yes**, within the single-operator scope above.
- Output/evidence: Status; same handler behavior as system status.
- Side effects: no business writes or provider requests; local reads and possible infrastructure logging only.
- Exact advertised input schema:

```json
{
  "properties": {},
  "title": "sonic_integration_statusArguments",
  "type": "object"
}
```

### `sonic_shopify_status`

- Purpose: Read cached Shopify authentication and required/requested/granted scope evidence. Never mutates the store.
- Authority: READ / query. Allowed in read-only V1: **yes**, within the single-operator scope above.
- Output/evidence: One IntegrationStatus for Shopify; cached/configuration evidence only.
- Side effects: no business writes or provider requests; local reads and possible infrastructure logging only.
- Exact advertised input schema:

```json
{
  "properties": {},
  "title": "sonic_shopify_statusArguments",
  "type": "object"
}
```

### `sonic_project_get`

- Purpose: Read one local operator-owned project by positive integer ID. This installation is single-operator, not multi-tenant.
- Authority: READ / query. Allowed in read-only V1: **yes**, within the single-operator scope above.
- Output/evidence: Project; positive project_id required by handler (not expressed as a JSON-schema minimum). Errors: invalid ID, Project not found, Project storage unavailable.
- Side effects: no business writes or provider requests; local reads and possible infrastructure logging only.
- Exact advertised input schema:

```json
{
  "properties": {
    "project_id": {
      "title": "Project Id",
      "type": "integer"
    }
  },
  "required": [
    "project_id"
  ],
  "title": "sonic_project_getArguments",
  "type": "object"
}
```

### `sonic_decision_trace_get`

- Purpose: Read an integration check or webhook proposal evidence record by UUID trace ID. Contains no hidden reasoning or provider response bodies.
- Authority: READ / query. Allowed in read-only V1: **yes**, within the single-operator scope above.
- Output/evidence: Decision; trace_id must parse as UUID (not expressed as JSON-schema format). Errors: invalid UUID, Trace not found, Decision storage unavailable.
- Side effects: no business writes or provider requests; local reads and possible infrastructure logging only.
- Exact advertised input schema:

```json
{
  "properties": {
    "trace_id": {
      "title": "Trace Id",
      "type": "string"
    }
  },
  "required": [
    "trace_id"
  ],
  "title": "sonic_decision_trace_getArguments",
  "type": "object"
}
```
