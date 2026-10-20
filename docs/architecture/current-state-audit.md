# Sonic AI V3 Current-State Audit

**Observed:** 2026-09-23
**Repository:** `cryptik093-pixel/sonic-ai-v3`
**Implementation:** producer brief intelligence vertical slice, API version 0.6.0
**Evidence status:** implementation claims are limited to checked source, tests and generated artifacts; see the dated delivery record for this change.

## Product state

The repository contains a runnable single-operator production workbench. The Windows desktop app starts a loopback FastAPI service and opens its bundled UI. The same service layer backs the HTTP and MCP interfaces. The current release is a local producer tool; this audit does not claim a hosted, multi-user, commercially certified or autonomously publishing platform.

The flagship workflow is free-text producer brief → inspectable composition plan → downloadable MIDI/WAV files. It extends the existing deterministic MIDI generator; it is not neural music generation. Optional cloud coaching is a separate capability that sends the question and selected saved-run evidence to the configured provider.

## Verified workflow surfaces

| Surface | Route / artifact | Behavior and boundary |
| --- | --- | --- |
| Desktop UI | `GET /workbench` | Bundled workbench; desktop starts the local service and supplies its private token |
| Health | `GET /health` | Process health only; does not establish provider, audio or commerce health |
| Workbench status | `GET /workbench/api/status` | Version, local capability list, runs, assets and live MCP base URL |
| MIDI preview | `POST /workbench/api/midi/preview` | Read-only interpretation; reads saved state only for an explicit continuity request; creates no run or file |
| MIDI generation | `POST /workbench/api/midi` | Locally writes separate parts, arrangement, audition and metadata; request ID makes identical retries return the same run |
| Feedback | `POST /workbench/api/runs/{run_id}/feedback` | Saves an idempotent keep/not-for-me event on a completed MIDI run |
| Import | `POST /workbench/api/imports` | Copies supported audio/MIDI source into the local workspace, deduplicating exact content |
| Audio analysis | `POST /workbench/api/analysis` | Saves measured audio evidence; does not infer musical key or BPM |
| Pack / release | `POST /workbench/api/pack`, `POST /workbench/api/release` | Writes a local ZIP or unpublished Shopify CSV; does not validate legal rights or publish |
| Focus / coach | `POST /workbench/api/focus`, `POST /workbench/api/coach` | Saves a proposed bounded next step or a grounded run recommendation |
| Run retrieval | `GET /workbench/api/runs/{run_id}` | Returns the saved run, artifact records and its feedback history |
| File / archive retrieval | `GET /workbench/api/runs/{run_id}/files/{filename}`, `GET /workbench/api/runs/{run_id}/archive` | Serves only files recorded in the run's output manifest |
| MCP | `POST /mcp` | Authenticated local MCP endpoint; read queries and local write tools use the same services |

Workbench routes require the local bearer token and reject non-loopback hosts/origins. The desktop launcher chooses a free port and the status response derives its MCP URL from the request address. The app uses that returned URL when showing its connection details.

## Producer brief intelligence

`apps/api/workbench/intelligence.py` compiles only supported, explicit control signals. It preserves the full producer brief but does not reinterpret unmatched adjectives as facts. Prompt signals include key/scale, style, mood, BPM, bar count, density and quoted title. Seed is a structured setting or an explicitly derived variation value; it is not extracted from prose. The MIDI engine supports 4/8/16 bars, 60–200 BPM, four scales, three style patterns, six mood patterns and three density patterns.

Resolution order is explicit operator control → recognized prompt signal → continuity explicitly requested from an eligible saved run → documented default. The preview returns the resolved parameters, source per field, matched prompt excerpt, assumptions, continuity reference and warnings. A plain language request without a supported control is retained as context and calls out the defaults. The parser is deterministic; it does not contact an LLM.

Feedback is scoped to `local-producer` / `omega-house-studio` and stored as versioned `workbench.feedback_recorded` events. A prompt that explicitly refers to a kept/saved direction selects the most recent run with a current `keep` decision. An explicit variation/continuation request without that wording uses the most recent successful MIDI run. Ordinary prompts reuse no saved run. A later `not_for_me` decision supersedes that run's earlier feedback state. The compiler does not search across other owners or workspaces.

The persisted `Composition.json` includes the source brief, compiler version, parsed evidence, resolved values, composer version and lineage references. The SHA-256 and byte length for each MIDI/WAV production output match the run's artifact manifest. Rights status is explicitly `not_assessed`, following [Omega House metadata/packaging lineage V1](../knowledge/metadata/METADATA_PACKAGING_LINEAGE_V1.md). A file hash proves byte identity, not ownership or license clearance.

## Architecture

```text
Producer UI / MCP
        ↓
Typed FastAPI / MCP command
        ↓
Brief compiler + continuity reader
        ↓
Seeded MIDI composer / measured audio services
        ↓
SQLite runs + local files + scoped events
        ↓
Run manifest, evidence and downloadable output
```

The UI, HTTP routes and MCP tools call `apps/api/workbench/service.py`. The compiler and MIDI engine are local. Run creation uses request IDs, input fingerprints, a staging directory and durable success/failure records. SQLite is the workbench system of record. The desktop API binds to loopback. This is a coherent local vertical slice, not a queue-backed multi-process platform.

The MCP server currently exposes 15 tools across integration, project and workbench queries and local output commands, including `sonic_compile_production_brief`, `sonic_generate_midi` and `sonic_record_workbench_feedback`. Contract tests pin the tool set and annotations. Local write tools reject OAuth read-only contexts. `sonic_compile_production_brief` is a query; generation and feedback are commands.

## Runtime configuration and storage

- Source mode defaults to SQLite at `apps/api/data/sonic_ai.db`; workbench output defaults under `apps/api/data/workbench/`.
- The packaged desktop app stores data under `%LOCALAPPDATA%\OmegaHouse\Sonic`.
- `SONIC_DATA_DIR`, `SONIC_DB_PATH` and `SONIC_EVENT_DB` can override paths.
- `SONIC_CONTROL_PLANE_TOKEN` protects direct local API use. The desktop launcher manages its own token.
- `SONIC_OPENAI_API_KEY` is optional and is used for grounded coaching, not MIDI generation.
- The workbench release flow exports a draft CSV. It performs no live store mutation, publication, email delivery or ad spend.

See [.env.example](../../.env.example) for actual configuration names. Postgres, Redis, S3, Supabase Auth and a hosted multi-user service are not dependencies of the production workbench. Other historical/legacy API modules remain in the repository; their presence does not establish that they are integrated into the desktop workflow or ready for hosted operation.

## Known limits

- Prompt parsing is a deterministic controlled vocabulary, not general semantic understanding. Unsupported language is carried as context and may not influence the composition.
- The MIDI is seeded algorithmic output. It is valid downloadable MIDI with musical note patterns, but a human still judges whether it sounds good and chooses instruments in a DAW.
- The audition WAV uses basic synthesized tones, not production instruments or a mastered mix.
- Imported audio analysis is limited to the documented measured fields; it does not identify key, tempo, true peak or LUFS.
- One fixed local owner/workspace is implemented. Multi-user identity, tenant isolation and remote deployment require further architecture and tests.
- The optional model coach depends on a configured provider and network. Configuration alone is not proof that a live call will succeed.
- Generated or imported assets are not legally certified. Commercial release requires separate rights, license, QC and delivery validation.
- A source change does not itself create a Windows installer; use the artifact from the successful desktop workflow run for the matching commit.

## Evidence and docs

The implementation-specific test command is `python -m pytest apps/api/tests`. The producer brief delivery record lists the observed result and contract coverage. Historical reports under `docs/status/` describe their original observation dates and do not override this audit or current source/tests.
