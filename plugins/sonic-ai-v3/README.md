# Sonic AI V3 Codex plugin

Version 0.1.0 · Omega House Studio LLC · Productivity · read-only V1.

Uses the existing FastAPI Streamable HTTP MCP endpoint at
`http://127.0.0.1:8000/mcp`; it starts no server. The command-center skill supports
health/readiness reports, individual known projects, and integration decision traces.
See [the complete contract](contracts/read-only-tool-inventory.md).

## Install and open

From the repository root, with the existing API running and the existing
`SONIC_CONTROL_PLANE_TOKEN` securely available in the Codex process environment:

```powershell
codex plugin marketplace add .
codex plugin add sonic-ai-v3@personal
codex -C 'C:\Users\david someone\Desktop\SONIC AI V3\sonic-ai-v3'
```

The repository marketplace uses the official scaffold's `personal` name. Its source
is this repository, not the implicit user marketplace. Installation modifies Codex's
user-level marketplace/plugin registration and plugin cache; it does not modify the
project's existing `sonic` MCP registration. The plugin uses `sonic-command-center`
to avoid a name collision. Both registrations may appear; use the plugin namespace.

In the Codex app, select this checkout and start **New thread** after installation.
Ask: `Use sonic-command-center to check Sonic AI V3 health and surface blockers.`
Existing threads do not prove pickup of newly installed skills/tools. The new process
must inherit the existing token; no credential is bundled or copied into the plugin.

## Capability boundaries

- Five reviewed query tools are client-allowlisted; the inspected server exposes no
  write tools. Skill policy does not create credential-level read-only isolation.
  The shared bearer token can authorize `/integrations/check` outside this plugin.
- Active-project listing, asset retrieval/listing, and producer/workspace-scoped
  memory retrieval are **BLOCKED** by missing MCP tools. No backend repair is included.
- Projects and integration traces are single-operator reads, not tenant-scoped queries.
- Cached provider status does not validate fresh provider requests or webhook delivery.
- Local bearer mode requires the existing compatible API configuration. Partial OAuth
  configuration fails closed; this plugin does not configure public URLs or OAuth.

## Validation

Run the official installed `plugin-creator/scripts/validate_plugin.py` against this
directory and `skill-creator/scripts/quick_validate.py` against
`skills/sonic-command-center`. The plugin validator checks manifest/MCP container
shape; it does not deeply validate MCP server options. The scaffold's
`load_validated_marketplace` and `read_marketplace_name.py` validate the marketplace
structure/name, and the Codex marketplace/install parser supplies runtime validation.

The `.mcp.json` shape follows installed GitHub plugin evidence (`mcpServers`, `type`,
`url`, `bearer_token_env_var`), the installed computer-use plugin's `enabled_tools`,
and this repository's `.codex/config.toml` bearer/allowlist configuration.

Validation snapshot: 2026-09-15 UTC (2026-09-14 America/Chicago). `/health` returned
200 with `healthy: true`; unauthenticated MCP returned 401; authenticated initialize
and tools/list returned 200. System status reported API/database `VALIDATED`, OpenAI
`CONFIGURED`, Shopify/ingestion `NOT_CONFIGURED`, and `provider_checks_fresh: false`.
These are local observations, not public endpoint or provider validation. No write
tool or provider-refresh route was invoked. No API or Next.js process was stopped.

All three status tools returned successful MCP results. Invalid project ID and trace
UUID probes returned the expected validation errors; successful record retrieval was
not tested because no known record IDs were supplied. Official plugin/skill validation,
marketplace loader/name checks, and placeholder/secret scans passed. Codex CLI 0.154.0
registered this repository marketplace and installed `sonic-ai-v3@personal` version
0.1.0 with `ON_INSTALL` authentication policy. Fresh-thread tool pickup still requires
opening a new thread; installation alone does not prove that client connection.
