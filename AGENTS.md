# Sonic AI V3 Agent Instructions

## Project Identity

This repository is Sonic AI V3.

Sonic AI V3 is the AI Producer Operating System. It is not V1, not V2, not an audio analyzer, not a MIDI generator, not a sample generator, and not a plugin. Analysis, generation, samples, reports, and agent workflows are modules inside the operating system.

## Canonical Source

The root of this repository is canonical:

```text
C:\Users\david someone\Desktop\sonic-ai-v3-main
```

Nested folders named `sonic-ai-v3-codex-*` are generated scaffold snapshots. Do not implement inside them unless the user explicitly says to. Treat them as quarantine/defer candidates.

## Phase 0 Rule

Define the platform before writing product features.

Sprint 1 builds Sonic Core only:

1. Authentication and user ownership
2. Projects
3. Asset storage
4. Sonic Vault
5. Metadata engine
6. Producer profile and memory foundation

Do not add AI generation, autonomous agents, embeddings, pgvector, Redis, Celery, or DSP-heavy analysis before the data graph works.

## Data Ownership Rule

Every persistent object must belong to a user. When applicable, records must also connect to projects, assets, metadata, analyses, reports, memory events, vault entries, or producer profile state. Never create isolated data.

## Development Rules

- Read `README.md`, `docs/sonic-ai-audit.md`, `docs/architecture/current-state-audit.md`, and `docs/planning/sprint-1-implementation-backlog.md` before coding.
- Make one focused change at a time.
- Keep root docs and package manifests aligned with the locked V3 direction.
- Preserve Sprint 1 boundaries unless the user explicitly widens scope.
- Run `node scripts/validate-v3-foundation.mjs` after scaffold or documentation changes.
- If `pnpm` is available, also run `pnpm test`.
