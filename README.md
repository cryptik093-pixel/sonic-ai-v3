# Sonic AI V3

Sonic AI V3 is a producer workbench with local MIDI creation, measured audio checks, asset packaging, release preparation and a scoped Sonic Intelligence layer. The current code version is **0.6.0**.

The production path is the Windows desktop app. It launches a local FastAPI service and a bundled workbench UI. The same services power the HTTP API and local MCP server, so the app and tools produce the same saved outputs.

## What works now

| Workflow | What Sonic saves | Current boundary |
| --- | --- | --- |
| **Producer brief → MIDI** | Four MIDI parts, a multitrack MIDI arrangement, WAV audition, composition JSON with mapped prompt evidence and SHA-256 lineage, and DAW import notes | Deterministic local composition; no generative model or network call is required |
| **Audio check** | Imported source, measured peak/RMS/DC/silence/stereo evidence, JSON and Markdown report | Does not claim tempo, key, LUFS or true peak for imported audio |
| **Pack assets** | Deduplicated ZIP, inventory, source IDs and file hashes | Supplied license text is preserved; rights are not legally validated |
| **Prepare a release** | Inventory-grounded copy, demo plan, A/B test and an unpublished Shopify draft CSV | Does not publish a Shopify product, send a message or spend money |
| **Focus session** | One bounded proposed action and saved session record | A proposed action is not recorded as completed |
| **Ask Sonic** | An optional recommendation grounded in a saved run | Optional provider call; it does not generate the MIDI |

## Create from a producer brief

Open **Create MIDI**, describe the musical direction, preview Sonic's interpretation, then generate and audition it. Sonic maps only explicit supported controls: key/scale, style, mood, tempo, length and density. It shows the phrases it mapped, field sources, defaults and warnings before generation. Unmapped language remains attached as creative context; it is not treated as a measured or inferred musical fact.

The interpreter recognizes common key/scale forms such as `C# minor`, `in F major`, and `key of D dorian`; BPM; 4, 8 or 16 bars; cloud/ambient, soul/R&B, or trap/hip-hop direction; dark, hopeful, dreamy, tense or uplifting mood; and sparse, balanced or busy density. An explicitly adjusted structured control wins over the prompt. The full accepted command and the compiled brief are stored with the output.

A generated MIDI can be marked **Keep this direction** or **Not for me**. Sonic stores that decision against the run. A later request must refer to a kept/saved direction or ask for continuity before Sonic reads saved composition settings. The preview reveals which saved run and fields it would reuse. Feedback is local to this single-operator workspace.

The generated `.mid` files are standard MIDI files with separate melody, chord, bass and drum parts plus a combined arrangement. The included WAV is a simple synthesized audition, not a finished or mastered recording. The engine uses reproducible rules and a seed; musical quality remains a listening decision.

## Sonic Intelligence and asset lineage

The intelligence layer is a deterministic decision record rather than an opaque chat response:

1. Preserve the producer's original brief and explicit control values.
2. Map supported phrases to typed composition settings and retain the source phrase for each mapping.
3. Apply the documented precedence: explicit controls, supported prompt signals, explicitly requested saved continuity, then defaults.
4. Expose assumptions, continuity source and warnings in a no-write preview.
5. Generate local MIDI/WAV outputs from the resolved settings and persist the run.
6. Record the operator's explicit feedback as a workspace-scoped event for future, explicitly requested continuity.

`Composition.json` includes compiler and composer versions, prompt evidence, resolved parameters, source/run references, rights status (`not_assessed`), and checksums for production outputs. The lineage contract follows the principles in [Omega House metadata and packaging lineage](docs/knowledge/metadata/METADATA_PACKAGING_LINEAGE_V1.md). A prompt, checksum or generated file is not proof of rights ownership or legal clearance.

## Runtime and local data

This release is a **single-operator local desktop tool**, not a hosted or multi-tenant service. Workbench runs use the fixed local owner `local-producer` and workspace `omega-house-studio`. SQLite and output files persist on the machine. The packaged desktop app uses `%LOCALAPPDATA%\OmegaHouse\Sonic`; source runs default to `apps/api/data`. Files imported into a pack are copied; the workbench does not overwrite the originals.

- **Windows app:** the [Sonic Desktop workflow](https://github.com/cryptik093-pixel/sonic-ai-v3/actions/workflows/sonic-desktop.yml) builds a Windows x64 artifact after its native checks pass. Extract the full ZIP and open `Sonic.exe`; WebView2 is required. The build is unsigned.
- **Run from source:** install `apps/api/requirements.txt` and `apps/desktop/requirements.txt`, then launch `python apps/desktop/launcher.py` from the repository root.
- **API smoke test:** `python apps/desktop/launcher.py --smoke-test /tmp/sonic-smoke.json` exercises the local service and writes a proof file. On Windows, choose a path that exists and is writable.
- **Web development shell:** `apps/web` is a Next.js redirect to the API-hosted workbench. It is not a second implementation; start the API on port 8000 before using that redirect.

For direct API development, see [.env.example](.env.example). The desktop launcher manages its local token and chooses a free loopback port. The MCP address shown in the UI is read from the live API address, including when port 8000 is occupied.

## HTTP and MCP

The local workbench is served at `/workbench`. Its API is under `/workbench/api`; the current routes and authentication boundary are documented in the [current-state audit](docs/architecture/current-state-audit.md). `/mcp` exposes typed tools backed by the same workbench services. Read-only tools include `sonic_compile_production_brief`; `sonic_generate_midi` creates output; `sonic_record_workbench_feedback` records an operator decision. OAuth read-only contexts cannot call local write tools.

## Repository map

- `apps/desktop/` — Windows launcher, native app and packaging checks
- `apps/api/workbench/` — HTTP routes, local job service, MIDI/audio workflows, prompt compiler, MCP tools and bundled UI
- `apps/api/tests/` — API, composition, persistence, authorization and MCP contracts
- `apps/web/` — development redirect to the API-served UI
- `docs/architecture/current-state-audit.md` — dated runtime truth and known limits
- `docs/knowledge/` — production doctrine, lineage and requirements that inform the runtime
- `docs/status/` — dated evidence and historical reports, not timeless runtime truth

## Documentation authority

Runtime behavior, schemas and tests establish what works. The [current-state audit](docs/architecture/current-state-audit.md) records the verified boundary. Older Sprint, launch and recovery reports are preserved as historical evidence and are not current status. The [documentation index](docs/README.md) describes the authority order.
