# Connection matrix

Observed 2026-09-05 on `recovery/actual-project-state`. Overall: **PARTIALLY VALIDATED**. “Local test” means isolated fixtures, not the production provider or a ChatGPT account.

| System | Code Exists | Config Exists | Credential Reference | Authentication Proven | Network Proven | Permissions Proven | End-to-End Proven | State |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Sonic API | Yes | Yes | Legacy routes have no auth | New operator boundary: local tests | Loopback `/health` and `/dashboard` HTTP 200 | Operator scopes: local tests | API boot and representative routes | VALIDATED locally |
| Sonic frontend | Yes | Yes, default API URL | No established frontend auth | No | Next.js starts; `/dashboard` HTTP 200 | No | Browser journey untested | PARTIALLY VALIDATED |
| OpenAI | Existing runtime + new health adapter | Existing API env configured | `SONIC_OPENAI_API_KEY`, fallback `OPENAI_API_KEY` | Yes, live | Yes, live | Model metadata accessible; inference rights unproven | Health check only, no generation | PARTIALLY VALIDATED |
| Shopify | New read-only adapter | Template; actual domain/token absent | `SONIC_SHOPIFY_ACCESS_TOKEN` | No live proof | No live proof | Mocked scope retrieval/comparison only | No live proof | BLOCKED on store configuration |
| MCP | Official SDK; five tools | Project config exists; operator token absent | `SONIC_CONTROL_PLANE_TOKEN`; optional OAuth JWKS | Local bearer/JWT tests | Official client over loopback HTTP | Discovery, calls, rejected mutations tested | Local fixture loop only; no actual Codex/ChatGPT attachment | PARTIALLY VALIDATED |
| Database | Existing SQLAlchemy SQLite | Existing file | None for local SQLite | Not applicable | Local `SELECT 1`; network not applicable | Test DB writes; production DB read only | Existing repository tests and live local read | VALIDATED for local read |
| Event ingestion | Promoted/hardened store + HMAC bridge | Template; webhook secret absent | `SONIC_SHOPIFY_WEBHOOK_SECRET` | Synthetic signed deliveries only | Local handler tests | Shop/topic/version restrictions tested | Atomic ingestion/proposal and replay tested locally | PARTIALLY VALIDATED |

## Evidence

- Baseline: copied active API to temporary storage and ran existing tests; collection failed because `apps.api.repositories.asset_repository` was missing. No user data was cleared.
- Python: `.venv/Scripts/python.exe -m pytest apps/api/tests -q --disable-warnings --tb=short` — **50 passed**, 14 warnings, 43.51 seconds on the final run. Warnings include existing naive UTC datetime usage.
- Workspace: `pnpm test` — 3 event tests passed.
- Dependency verification: `.venv/Scripts/python.exe -m pip check` — no broken requirements found.
- Security review: 26 task files plus the tracked Git diff scanned; zero configured-credential matches; API/root `.env` files are untracked. `git diff --check` passed. The application database hash remained unchanged. Test servers were stopped after verification.
- Live provider check: authenticated OpenAI model listing and configured-model retrieval succeeded at approximately 11:40 UTC. No generation request was sent. Shopify reported missing/invalid configuration without making a request.
- The local CLI probe persisted OpenAI trace `93315ed5-1eaf-4ac4-b936-f28d51fc27cc` and Shopify trace `dc9ac55b-c4c3-4203-b376-bf297ce5a318` in the ignored event database. These initial records precede the final addition of the full normalized status field; subsequent probes store that field too.
- Uvicorn booted on loopback; `/health` returned the preserved JSON and `/dashboard` returned 200. `/integrations/status` returned 503 with `control_plane_auth_not_configured`, accurately reflecting the missing operator credential.
- MCP tests use the real SDK client over TCP: initialize, discover five tools, call status and read a project; separate tests verify decisions, rejection of unregistered mutations, auth, and Host restrictions.
- Documentation gate `node scripts/validate-v3-foundation.mjs` could not run: the script referenced by `docs/AGENTS.md` is absent in this checkout. No replacement validator was fabricated.

## Forensics scope

Active source, API env variable names/presence, manifests, tests, integration-related docs, canonical events, and the legacy event store were inspected. `agents.md` applies at the root; `docs/AGENTS.md` additionally applies to these docs. No deeper instructions were found in active API/packages. The user's explicit integration-control-plane request widens the old Sprint 1 documentation scope.

No active Agents SDK, MCP server, Shopify adapter, webhook subscription, Shopify Flow integration, or server-side API authentication was found before this work. Memory and decision tables/services existed, but not normalized provider connection evidence. The root `.env` contains editor-style settings and is not loaded by the API. No credentials were inferred from it or imported from Codex connectors. A Shopify connector in Codex is not proof that Sonic itself has credentials or connectivity.

## Files changed by this task

- Updated: `apps/api/main.py`, `apps/api/config.py`, `apps/api/database.py`, `apps/api/requirements.txt`, `apps/api/services/llm_service.py`.
- Added: `apps/api/integrations/{__init__,auth,config,gateway,models,providers,service,store,webhooks}.py`.
- Restored missing dependencies: `apps/api/repositories/asset_repository.py`, `apps/api/repositories/relevance_repository.py`, `apps/api/services/creator_dna_service.py`.
- Added tests: `apps/api/tests/conftest.py`, `test_integrations.py`, `test_mcp_http.py`.
- Added setup: `apps/api/.env.example`, `.codex/config.toml`, `scripts/check_integrations.py`, and the three documents in this directory.

All pre-existing unrelated dirty files remain. The tracked application database was already dirty and remained byte-identical during this task. New operational evidence is in ignored event storage, not source control.
