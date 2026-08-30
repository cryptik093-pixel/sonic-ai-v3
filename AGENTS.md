# Sonic AI V3 Agent Instructions

## Project Identity

Sonic AI V3 is the intelligence layer for a producer operating system. The platform combines the producer workspace, audio/assets, deterministic analysis, structured memory, event-driven workflows, chat, agents, tools/MCP, and controlled automation.

Do not treat Sonic AI V3 as only an audio analyzer, MIDI generator, sample generator, chatbot, or plugin. Those capabilities are modules within the larger operating system.

## Canonical Source

The canonical repository is:

```text
cryptik093-pixel/sonic-ai-v3
```

The canonical product baseline is the `main` branch.

Do not assume a local filesystem path, generated scaffold, archive, or historical snapshot is canonical. Verify the active repository and branch before making recovery decisions.

## Current Recovery Objective

Restore and maintain one coherent, bootable, testable, deployable platform without losing previously established frontend, backend, chat, memory, event, or agent capabilities.

The current priority order is:

1. Repository/branch integrity.
2. Frontend boot path.
3. API/backend boot path.
4. Environment and dependency integrity.
5. Database/auth contracts and user ownership.
6. Chat pipeline.
7. Agent registry and model configuration.
8. Tool/MCP boundaries.
9. Producer Intelligence Loop.
10. Automated verification and deployment readiness.

## Producer Intelligence Loop

The target vertical slice is:

```text
Upload → Analyze → Normalize → Audio Analyst
→ Producer Intelligence → Memory → Retrieve
```

Do not bypass deterministic facts with model-generated state. Models should reason over structured evidence produced by the application.

## Data Ownership Rule

Every persistent user-owned object must have an explicit ownership boundary. When applicable, records must connect to projects, assets, metadata, analyses, reports, memory events, vault entries, or producer profile state.

Never create isolated persistent data that cannot be attributed to its owner and domain context.

## Agent / Tool Rules

- Agents operate through explicit tools and application contracts.
- Agents must not bypass authorization or mutate arbitrary state.
- MCP/tool capabilities must remain inspectable and permission-aware.
- Model configuration must be explicit and testable.
- Tool execution must produce observable outcomes and failures.
- Human approval boundaries must be preserved for consequential actions until explicitly verified safe.

## Documentation Rules

- `README.md` is the primary product/architecture overview.
- Historical audit, milestone, and phase reports are evidence, not current runtime truth.
- Never mark a subsystem healthy, production-ready, complete, or deployed without current reproducible evidence.
- When implementation changes invalidate an audit, update or supersede the affected document immediately.
- Keep documentation aligned with actual repository structure, package manifests, scripts, configuration, and runtime behavior.

## Development Rules

- Make focused, reversible changes.
- Preserve working capability during recovery.
- Verify the affected layer after every material change.
- Prefer deterministic validation over assumptions.
- Run the repository's available validation/test commands after documentation or scaffold changes.
- Do not introduce architecture that conflicts with the current canonical README without explicitly updating the architecture documentation.

## Security

Never commit secrets. Keep local credentials in `.env` and document configuration shape in `.env.example`.

Treat authentication, authorization, user ownership, file uploads, database access, agent execution, tool/MCP boundaries, and external integrations as security-sensitive.
