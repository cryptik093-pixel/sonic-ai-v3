# Sonic AI V3 Integration Control Plane

Audit date: 2026-09-05. State: **PARTIALLY VALIDATED**. This document describes the active `apps/api/main.py` application, not the backup API or the old scaffold described by some repository documents.

## Runtime and boundaries

FastAPI, SQLAlchemy/SQLite, Python 3.14.7; Next.js 14.2.15; Node 24.19.0; pnpm 10.28.1 were observed locally. The root Python virtual environment is `.venv`. The API entrypoint is `apps.api.main:app`; the frontend entrypoint is `apps/web/app`. API dependencies are in `apps/api/requirements.txt`, workspace dependencies in `pnpm-lock.yaml`. The new transport uses the official MCP Python SDK, pinned to 1.29.1; no Agents SDK migration was introduced.

`apps/api/integrations` owns configuration, normalized status, provider reads, operator authorization, MCP registration, webhook normalization, and evidence persistence. The existing OpenAI chat client is preserved. Its exceptions now exclude raw provider responses, which could contain sensitive content.

| Surface | Behavior | Authorization |
| --- | --- | --- |
| `GET /health` | Existing `{ "healthy": true }` contract | Existing public local route |
| `GET /integrations/status` | Local DB probe plus timestamped cached provider checks | Operator bearer or OAuth `sonic:read` |
| `POST /integrations/check` | Harmless live reads; durable evidence records; 30-second coalescing per process | Operator bearer or OAuth `sonic:check` |
| `/mcp` | SDK Streamable HTTP, initialization, discovery, five read-only tools | Same server-side authorization; OAuth `sonic:read` |
| `POST /integrations/shopify/webhooks` | Product create/update events only | Raw-body Shopify HMAC, shop/topic/version validation |
| `GET /.well-known/oauth-protected-resource/mcp` | Resource discovery when OAuth is configured | Public metadata |

Provider results expire after 60 seconds. Expired status retains prior check/success/error timestamps but clears current authentication/reachability claims. A server restart clears the live cache; durable decisions remain. Run the check endpoint to refresh. The CLI probe persists its own records and does not populate another API process's cache. Database health checks `SELECT 1`; it does not establish backup integrity or database write permissions. In-process locks/coalescing are intended for this single-instance SQLite deployment, not fleet-wide throttling.

`IntegrationStatus` distinguishes configuration, authentication, reachability, requested/granted/required scopes, permissions, API version, model metadata availability, runtime availability, check times, error codes, latency, degradation, and validation status. Unknown values are `null`, never assumed false or true. Validation is per check capability, not a blanket declaration of production readiness.

## Provider checks

OpenAI reuses `SONIC_OPENAI_API_KEY` (fallback `OPENAI_API_KEY`), `SONIC_OPENAI_MODEL`, and `SONIC_OPENAI_BASE_URL`. Process environment takes precedence over `apps/api/.env`. The health adapter accepts the official OpenAI base URL only; custom compatible endpoints remain untouched in the existing chat client and explicitly unvalidated by this OpenAI check. Authenticated model listing and configured-model retrieval generate no tokens. Model metadata access does **not** prove inference execution, billing capacity, or every runtime permission. `runtime_available` remains `null`.

Shopify uses only `SONIC_SHOPIFY_SHOP_DOMAIN`, `SONIC_SHOPIFY_ACCESS_TOKEN`, `SONIC_SHOPIFY_API_VERSION`, and `SONIC_SHOPIFY_REQUESTED_SCOPES`. No store domain is inferred from branding or a storefront domain. The API version defaults to the explicitly verified `2026-07`; other versions are rejected by this adapter until reviewed. The check reads shop identity and `currentAppInstallation.accessScopes`, compares required `read_products` against actual grants (including implied read access from write scopes), and runs a minimal product-ID query when permitted. It checks the response API-version header. Requested scopes are operator-supplied intent; no Shopify app manifest was found. This task does not change installations or grants. No write scope is required.

HTTP errors, GraphQL errors, missing configuration, transport failures, model failures, missing scopes, identity mismatch, and version drift have distinct sanitized results. Checks have an eight-second HTTP timeout per request and do not follow redirects. Provider response bodies and credentials are never returned or persisted.

## MCP and remote ChatGPT

Tools: `sonic_system_status`, `sonic_integration_status`, `sonic_shopify_status`, `sonic_project_get`, and `sonic_decision_trace_get`. They read local data/cached evidence; no tool calls providers or writes business state. Annotations declare read-only, non-destructive, idempotent, closed-world behavior. Positive integer project IDs and UUID trace IDs are validated. These are single-operator tools; the current project model has no tenant ownership. OAuth users granted Sonic scopes must therefore be trusted operators of this installation.

Local mode uses `SONIC_CONTROL_PLANE_TOKEN`. Missing configuration returns 503; missing/wrong credentials return 401. The token must be supplied by the operator; none was generated or saved. `.codex/config.toml` references this environment variable, allowlists exactly five tools, and prompts for tool approval. There are no write tools. Shopify `apply` is disabled even if callers supply `approved=true`. Before future mutations are enabled, implement a durable proposal, validation, approval bound to actor/content/version, execution, read-back verification, and decision record; a client approval prompt alone is insufficient.

Optional remote mode uses `SONIC_PUBLIC_MCP_URL`, `SONIC_OAUTH_ISSUER`, and `SONIC_OAUTH_JWKS_URL`. All three must be valid HTTPS URLs; partial configuration fails closed. The MCP URL must have path `/mcp`. Server verification uses configured JWKS with RS256 only, issuer, audience equal to the MCP URL, expiry, issued-at, subject, and operation scopes. Enabling remote mode disables acceptance of the local static token. Resource metadata and 401 discovery challenges are implemented. The identity provider must supply an authorization-code + PKCE flow and supported client registration; this repository does not create an authorization server. Configure these values before starting the API and restart after changing configuration.

Host validation protects MCP against DNS rebinding. Browser Origin headers are rejected on operator routes. For remote deployment, expose only `/mcp` and its metadata through the authenticated HTTPS ingress; expose the HMAC webhook route separately if needed. **Do not publish the entire legacy API:** existing project/chat/upload/intelligence routes remain unauthenticated and the upload handler trusts its filename. Those pre-existing surfaces require separate hardening before general internet exposure. No public URL, DNS, OAuth client, subscription, or ChatGPT connection was created in this task.

Current stages: **MCP SERVER READY (isolated local transport validated)**; **PUBLIC ENDPOINT NOT CONFIGURED**; **CHATGPT CONNECTION MANUAL STEP REQUIRED**; **CHATGPT CONNECTION NOT VALIDATED**.

## Event and decision persistence

The existing `packages/events` canonical envelope and `apps/api_legacy_event_layer/event_store.py` SQLite table design were reused. The hardened active store is `apps/api/integrations/store.py`; the legacy unauthenticated generic ingestion router remains unmounted. `SONIC_EVENT_DB` can point to an existing event database; the default is ignored `apps/api/storage/sonic_events.sqlite3`. Application data remains in its original SQLite location unless `SONIC_DB_PATH` is explicitly set. No existing rows were removed or migrated.

The boundary verifies the HMAC over raw bytes using constant-time comparison, limits the body to 1 MiB, validates the configured shop/version, supported topic, UUID event ID, and product ID. It normalizes `products/create` and `products/update` into `product_created` and `product_updated`. Event IDs are namespaced by shop/topic/provider ID. A transaction atomically inserts the event and a `PROPOSED` catalog-review decision. Replays return the original trace; a reused identity with a different body hash returns 409. Persistence failure returns 503 for provider retry. Occurrence time is explicitly receipt time, not a fabricated provider timestamp.

Only product ID, provider event ID, correlation ID, body hash, canonical event type, and the review proposal are retained; arbitrary descriptions and customer data are discarded. Routing currently ends in a deterministic review proposal, with no autonomous execution. Decision records retain trace ID, UTC timestamp, actor/service, provider, operation, concise evidence, validation/result state, external-side-effect status, and the normalized provider result for health checks. They contain no hidden model reasoning.

Admin product webhooks do not measure product views, carts, or checkout behavior. Customer-behavior events require an appropriately consented Web Pixels/customer-events source. Shopify Flow requires its own authenticated adapter and configured workflow; it was not found or implemented here. No generic endpoint accepts arbitrary external events.

## Validation and known limits

See [CONNECTION_MATRIX.md](CONNECTION_MATRIX.md) for observed results and [SETUP_CHECKLIST.md](SETUP_CHECKLIST.md) for reproducible commands. Baseline collection failed on a missing asset repository. Three small database-backed components expected by existing edits were restored: asset persistence, checkpoint reads, and Creator DNA signal reads. These expose existing records without inventing signals. Test storage is isolated before collection because existing tests clear tables.

The application DB SHA-256 remained `1F7E5323965269D471BCF562F8E817D587705DEB533D4F9F206BDEDDB34AA46C` through validation. Existing frontend edits and unrelated files were preserved. No full DSP, upload, frontend browser, or production audit is implied by the integration tests.

## Official references checked

- [OpenAI model retrieval](https://developers.openai.com/api/reference/resources/models/methods/retrieve)
- [Codex MCP configuration](https://learn.chatgpt.com/docs/config-file/config-reference)
- [ChatGPT MCP authentication](https://developers.openai.com/plugins/build/auth)
- [Official MCP Python SDK server integration](https://github.com/modelcontextprotocol/python-sdk/blob/v1.x/docs/server.md)
- [Shopify installed application scopes](https://shopify.dev/docs/api/admin-graphql/latest/queries/currentAppInstallation)
- [Shopify versioning](https://shopify.dev/docs/api/usage/versioning)
- [Shopify webhook verification](https://shopify.dev/docs/apps/build/webhooks/verify-deliveries)
