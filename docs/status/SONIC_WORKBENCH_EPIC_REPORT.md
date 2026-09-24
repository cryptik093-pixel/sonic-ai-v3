# Sonic Production Workbench — epic report

Date: 2026-09-22. Repository: `cryptik093-pixel/sonic-ai-v3`. Delivery PR: [#25](https://github.com/cryptik093-pixel/sonic-ai-v3/pull/25).

**Lifecycle:** historical 0.5 workbench baseline. The 0.6 producer brief, interpretation preview, feedback continuity and expanded MCP contracts are described in [the 2026-09-23 delivery record](SONIC_PRODUCER_BRIEF_INTELLIGENCE_2026-09-23.md) and [current-state audit](../architecture/current-state-audit.md).

## Outcome

This epic replaces the recovered placeholder experience with an output-producing desktop workbench. It connects creation, deterministic measurement, packaging, release preparation, session guidance and optional cloud interpretation through shared HTTP/MCP services and persistent local state.

The target user path is: open Sonic → generate and audition a phrase → export MIDI to FL Studio → package selected assets → prepare evidence-grounded release drafts. A low-energy session begins with one small proposed action and a bounded timer.

**Verification status: passed.** All 80 API tests passed on clean Linux and Windows runners. The 12-check real-browser workflow, packaged Windows HTTP/output checks, native Windows window/Generate-button check, frozen Linux executable check, frozen pnpm install and production web build passed.

**Download:** [Sonic-Windows-x64](https://github.com/cryptik093-pixel/sonic-ai-v3/actions/runs/35721229933/artifacts/10692450374) (43,814,804-byte ZIP). Extract the entire ZIP, keep `_internal` beside `Sonic.exe`, then open `Sonic.exe`. Choose **Create MIDI → Generate MIDI & audition**. No Git, Python, Node or terminal commands are required.

The download was built from source commit `c390daa0f14d307d79d46dc8508fca76622d806b`; the subsequent delivery commit adds documentation only. GitHub reports ZIP SHA-256 `d8f2cc2865c9f6fb2546d8d74b6e6ca5a9db0622125a6c1eebfab3f29e70a778`. Artifact retention expires on 2026-12-21; the repository workflow can reproduce the build. GitHub sign-in/repository access may be required for the download. This session did not install or alter the instance already open on the user's PC.

Evidence: [desktop CI run](https://github.com/cryptik093-pixel/sonic-ai-v3/actions/runs/35721229933), [Windows proof JSON](https://github.com/cryptik093-pixel/sonic-ai-v3/actions/runs/35721229933/artifacts/10691622330), [browser proof and screenshots](https://github.com/cryptik093-pixel/sonic-ai-v3/actions/runs/35721229933/artifacts/10691282117), [clean install/web build](https://github.com/cryptik093-pixel/sonic-ai-v3/actions/runs/35721229949). Screenshots are captured by the tested browser workflow; they were not separately visually inspected in this session.

## What was actually wrong

- Canonical `main` at `dd0af2e` contained package manifests and architecture/history but lacked executable API and web application sources.
- There were 50 remote branches, representing 23 distinct heads. Eighteen evolution branches shared one head and ten Shopify ingestion branches shared another. The full observed grouping is in `workbench-branch-audit.json`.
- `recovery/runtime-baseline-integration` restored API code but its web page was a boot placeholder. Its ten original tests passed while a live `/dashboard` request returned HTTP 500 because the imports pointed outside the API package.
- MCP transport/authentication, provider evidence and durable asset repository work existed on `codex/ship-sonic-integrity`, separate from the recovery baseline.
- The recovered dependency manifest omitted runtime dependencies such as `python-dotenv`. The pnpm lockfile still described dependencies removed from package manifests, so a frozen install failed.
- The legacy upload service used a supplied filename directly as a storage path. The old asset service held its records only in memory.

## Implemented user capabilities

| Capability | Inputs | Persisted, usable output |
| --- | --- | --- |
| MIDI studio | Key, scale, tempo, length, style, density, seed | Four individual type-0 MIDI files, one type-1 arrangement, audition WAV, composition JSON, FL Studio import notes |
| Audio check | Imported mono/stereo audio | Measured sample peak, RMS, crest factor, DC offset, near-full-scale samples, silence fraction and stereo correlation; JSON and Markdown review |
| Pack builder | Imported asset IDs and/or a completed MIDI set; optional approved license | ZIP with category folders, deduplicated assets, source lineage, SHA-256 manifest, CSV inventory and readme |
| Release preparation | Completed pack, audience, price, product URL | Two caption angles, demo shot list, bounded A/B test, UTM link and unpublished Shopify draft CSV |
| Focus session | Available time, energy, goal, completed work | One proposed next action, definition of done, timer and saved session card; low-energy plans cap at 15 minutes |
| Sonic insight | Completed output and question | Optional model interpretation grounded in the run; a useful local next step if no key exists or the provider fails |
| Output history | Local workspace | Reopen results after refresh/restart; export individual files or whole runs |

MIDI uses scale-constrained motifs, voice-led chord inversions, seeded performance variation and explicit note-off events. It is an algorithmic composition engine, not a claim of neural audio generation. The WAV is a simple synth audition to assess rhythm and harmony before choosing DAW instruments.

Audio reports distinguish sample measurements from musical judgments. Filename-based pack folders are hints. A missing license is marked explicitly; supplying text is not treated as legal validation or proof that a pack is cleared for sale. No commercial readiness is invented.

## Runtime and recovery decisions

- Preserved `main` as the canonical base through the existing recovery branch's history. Reconciled specific functional MCP and asset-persistence code rather than merging every historical branch. No historical branches were deleted.
- The actual workbench UI is served by FastAPI and bundled into a pywebview Windows app. The native app starts and stops its local API. Next.js routes development users to the same UI, so there are not two divergent workflow implementations.
- Packaged users need neither Git, Node nor Python. Windows 10/11 x64 with WebView2 is the intended desktop target. The build is unsigned.
- New desktop data lives in `%LOCALAPPDATA%\OmegaHouse\Sonic`, away from the development checkout. Existing development databases and original music files are not overwritten or silently migrated.
- The legacy project/chat/memory/event routes remain. Asset persistence is restored, the dashboard import failure is fixed and legacy uploads now use the bounded durable import service.
- The lockfile was reconciled; a clean frozen dependency install and Next.js production build passed.

## Sonic Intelligence and MCP contracts

New records carry explicit `local-producer` and `omega-house-studio` ownership; runs optionally attach to an existing project. This is a single-operator installation, not a multi-tenant hosting architecture.

Each command uses a UUID request ID. Repeating the same ID and inputs returns the same run; changing inputs under the same ID is rejected. Files are generated in staging before atomic promotion to the run directory. The successful run and completion event are persisted together. Failures are durable and do not claim success. Interrupted runs are marked on process startup. Read endpoints do not repair or mutate records.

The MCP server has 13 inspectable tools: five restored integration/project/trace reads, three new workspace reads and five new local-output commands.

| New tool | Authority and effect |
| --- | --- |
| `sonic_workbench_runs` | Read recent operator-owned runs |
| `sonic_workbench_assets` | Read imported asset IDs, hashes and metadata |
| `sonic_workbench_run_get` | Read one run, output manifest and evidence |
| `sonic_generate_midi` | Create a local composition and output records |
| `sonic_analyze_audio` | Create measurement reports for an imported asset |
| `sonic_build_pack` | Copy selected workspace assets into a ZIP; preserve originals |
| `sonic_draft_release` | Create local drafts; no external store mutation |
| `sonic_plan_session` | Save a proposed action; do not mark it completed |

Bearer authentication protects the workbench and MCP. Browser origins and hosts are checked; artifact downloads are restricted to the output manifest. Local commands are denied to OAuth read-only contexts. External Shopify mutations and outbound messages are not exposed. A local MCP URL does not establish a remote ChatGPT connection automatically.

Cloud interpretation is explicit and optional. A user's question and selected run evidence go to the configured provider. Windows credentials use the OS credential store; if it is unavailable, the key remains session-only. Provider errors are sanitized and a local recommendation remains available.

## Verification evidence

| Gate | Verified result |
| --- | --- |
| Original recovery tests | 10 passed; live dashboard request exposed a failure beyond those tests |
| API tests after implementation | 80 passed locally; original plus recovered integration and new workflow tests |
| MIDI boundary | Parsed saved files, checked balanced note-on/off events, scale membership and exact arrangement duration |
| Audio boundary | Known 24-bit sine fixture measured at approximately -6.02 dBFS sample peak and -9.03 dBFS RMS; inverse stereo measured -1 correlation; silence and NaN behavior tested |
| Pack/release boundary | Downloaded ZIP checksums and lineage verified; missing-license and draft-only CSV behavior verified |
| MCP | Official client initialization over real TCP; discovery, calls, idempotent creation and denied authority tested |
| Persistence/failure | Reopened database/file results; failed jobs and provider quota errors retained useful, truthful outcomes |
| Desktop source launcher | Actual loopback API, bundled UI assets, MIDI generation/parsing, archive download and unauthorized-request rejection passed |
| Install/web build | Frozen pnpm install, foundation validation and production Next.js build passed locally and in GitHub Actions |
| Real Chromium workflow | Passed: automatic connection, Generate button, piano roll, audition decoding/playback, parsed MIDI download, pack manifest, release CSV, audio import/analysis, bounded focus timer, persistent history, mobile overflow and zero JavaScript exceptions |
| Frozen Linux executable | Passed actual bundled HTTP/UI, MIDI parsing, archive and authentication checks |
| Packaged Windows HTTP/output | Passed: bundled UI, authenticated HTTP, parsed MIDI, downloaded ZIP and clean process exit |
| Native Windows window | Passed: actual native window, automatic connection, Generate button, audition audio loaded, clean exit |

The first fresh CI run exposed a brittle inherited test that assumed machine uptime exceeded 60 seconds. The test now constructs an actually expired monotonic interval. Its health-expiry assertion remains intact.

The packaged verification also checks clean process exit. Windowed startup exceptions now produce diagnostic JSON in smoke mode instead of an unattended dialog; normal startup failures show a concise native message. Temporary log and SQLite handles are closed before Windows cleanup. Artifact paths are resolved under their run directory using stored, validated manifest names, and both CI workflows use read-only repository permissions.

Reproducible checks live in `apps/api/tests`, `scripts/verify-workbench-browser.py` and the packaged app's smoke modes. The Windows job uploaded the desktop artifact only after both executable-level HTTP/output checks and the native-window Generate-button check succeeded.

## Scope and remaining limits

- No live cloud inference is claimed without a real configured credential and successful request; mocked failure checks validate the fallback contract.
- No physical FL Studio installation is accessible in this environment. Standard MIDI parsing, channel conventions and timing are tested; actual instrument choice and musical taste remain listening decisions.
- This is not a VST, DAW controller, stem separator, neural audio model, hosted multi-user platform, or a fully automated Shopify sales system.
- Measurements are not true peak/LUFS; tempo and musical key are deliberately left unknown for imported audio.
- Draft products require delivery attachment, rights review and a purchase/delivery check before publication. No sales or revenue outcome is claimed by this epic.
- Unsigned Windows distribution and the WebView2 runtime are practical installation constraints. Existing local Sonic databases are preserved, not automatically consolidated.

## Implementation references

- [Official MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk): SDK transport and tool registration; installed MCP version 1.29.1.
- [Mido standard MIDI files](https://mido.readthedocs.io/en/latest/files/midi.html): standard file/track/time semantics; installed Mido version 1.3.3.
- [pywebview packaging](https://pywebview.flowrl.com/guide/freezing) and [installation](https://pywebview.flowrl.com/guide/installation): native window/runtime packaging.
- [Shopify product CSV documentation](https://help.shopify.com/en/manual/products/import-export/using-csv): explicit draft/unpublished status; documented backward compatibility for the column names used.
