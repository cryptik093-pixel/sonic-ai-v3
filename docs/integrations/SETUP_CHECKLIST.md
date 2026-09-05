# Verifiable setup checklist

Run PowerShell from the repository root. Supply secrets through approved local environment/secret management; never paste them into commands, documentation, Codex config, or chat. The API reads `apps/api/.env` and process variables; existing process values win. Restart after configuration changes. `apps/api/.env.example` lists names only; optional blank values use documented defaults.

## Local prerequisites

| Check | Command or proof | Pass condition |
| --- | --- | --- |
| API dependencies | `.\.venv\Scripts\python.exe -m pip install -r apps/api/requirements.txt` | Install succeeds |
| Backend boot | `.\.venv\Scripts\python.exe -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000` | Startup complete |
| Existing health contract | `Invoke-RestMethod http://127.0.0.1:8000/health` | `healthy: true` |
| Tests use isolated storage | `.\.venv\Scripts\python.exe -m pytest apps/api/tests -q` | All tests pass; user DB unchanged |
| Event package tests | `pnpm test` | All tests pass |
| Frontend startup | `pnpm --filter @sonic-ai/web dev --hostname 127.0.0.1` | HTTP page loads; browser journey is a separate check |
| Provider/database CLI probe | `.\.venv\Scripts\python.exe scripts/check_integrations.py` | Inspect each status; exit 0 only if both providers validate, 2 if either remains unvalidated |

## Operator and providers

1. Supply an operator-controlled `SONIC_CONTROL_PLANE_TOKEN` to both the API and the Codex process. None was created in this audit. Verify missing/wrong tokens receive 401, while a correctly configured bearer can read `/integrations/status`. With no server credential, 503 is expected.
2. Preserve the existing OpenAI credential. Run the provider probe or authenticated `POST /integrations/check`. Require `openai.authenticated=true`, `reachable=true`, and `model_available=true`. This proves metadata access; `runtime_available=null` is expected until a separately approved small inference smoke is performed.
3. Obtain the existing app's actual `.myshopify.com` domain and Admin API token through the store's approved configuration process. Set `SONIC_SHOPIFY_SHOP_DOMAIN` and `SONIC_SHOPIFY_ACCESS_TOKEN`. Use `SONIC_SHOPIFY_API_VERSION` matching the pinned version. Set `SONIC_SHOPIFY_REQUESTED_SCOPES` to the existing application's requested scopes, not invented grants.
4. Re-run the check. Require shop identity match, authenticated/reachable true, retrieved grants, confirmed API version, and a successful minimal products query. If `missing_scopes` includes `read_products`, authorize that read capability on the existing app and recheck. Do not request write scopes for this release.

After the token is already securely available in the PowerShell process, these commands reference it without displaying it:

```powershell
$sonicHeaders = @{ Authorization = ('Bearer ' + $env:SONIC_CONTROL_PLANE_TOKEN) }
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/integrations/check -Headers $sonicHeaders
Invoke-RestMethod -Uri http://127.0.0.1:8000/integrations/status -Headers $sonicHeaders
```

## Codex and ChatGPT

1. Trust/open this repository in Codex so the project `.codex/config.toml` can be loaded. Ensure Codex inherits the operator token; an API `.env` file does not configure the Codex process. Start the API, reload the MCP connection, discover exactly five tools, and call `sonic_system_status`. The audit tested the SDK loop, not this manual Codex attachment.
2. For remote ChatGPT, select the real approved HTTPS hostname and OAuth issuer/JWKS endpoint. Set `SONIC_PUBLIC_MCP_URL`, `SONIC_OAUTH_ISSUER`, and `SONIC_OAUTH_JWKS_URL`. Do not invent a public endpoint or expose the unauthenticated legacy API. Configure HTTPS ingress for `/mcp` and `/.well-known/oauth-protected-resource/mcp` only.
3. Configure the existing identity provider for RS256 access tokens, audience equal to the exact MCP URL, operator-only `sonic:read` (and separately `sonic:check` if needed), authorization code + PKCE S256, and supported client registration. Verify metadata, token issuer/audience/expiry, and missing-scope denial. Partial OAuth configuration must return 503. Static local tokens are rejected in OAuth mode.
4. In the available ChatGPT app/connector setup, enter the actual HTTPS MCP endpoint and complete OAuth consent using the callback URI shown there. Discover tools and call a read-only tool. Only successful calls from that ChatGPT connection justify **CHATGPT CONNECTION VALIDATED**. A local SDK test or DNS entry does not.

## Shopify events

1. Supply the existing application's webhook signing secret as `SONIC_SHOPIFY_WEBHOOK_SECRET`; use the validated shop domain. Obtain authorization to register product create/update deliveries to the actual HTTPS `/integrations/shopify/webhooks` endpoint. No subscription was created during this audit.
2. Deliver an authentic product event using the pinned webhook API version and `X-Shopify-Event-Id`. Require `accepted=true`, then read the returned trace through MCP and verify the `PROPOSED` catalog review. Repeat the same delivery: require `duplicate=true` and the same trace ID.
3. Confirm an invalid signature returns 401, unsupported topics return 422, and a persistence failure returns 503. Reopen the event store to confirm persistence. Local automated tests cover these cases; a real Shopify delivery remains necessary.
4. Use Web Pixels/customer events for consented storefront behavior, and a separate approved adapter for Flow. Do not send those payloads to this product-webhook endpoint.

## Remaining production boundaries

No production hostname, OAuth interaction, Shopify installation/grant change, live webhook subscription, or ChatGPT attachment was performed. Live write tools are unavailable. Existing legacy API authorization, upload filename handling, full browser flows, and deployment hardening require separate work before broader exposure. The old foundation validator is missing; resolve that repository documentation/tooling mismatch separately.
