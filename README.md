# Sonic AI v3

Sonic AI is a producer-focused platform for storing audio assets, extracting deterministic metadata, searching a personal vault, tracking creative activity, and building a producer profile from real uploads.

Sprint 1 intentionally excludes AI generation, autonomous agents, embeddings, and DSP-heavy analysis. The goal is a stable foundation that supports sign-in, projects, uploads, metadata, search, activity history, and automatic profile aggregation.

## Repository layout

```text
apps/
  web/       Next.js 15 frontend
  api/       FastAPI backend
  worker/    background/event workers
packages/
  common/    shared types and utilities
  events/    event contracts and in-process event bus
  auth/      auth domain helpers
  projects/  project domain contracts
  assets/    asset domain contracts
  metadata/  metadata contracts and stubs
  memory/    activity/memory contracts
  vault/     vault search contracts
infrastructure/
  docker/    local Docker assets
  supabase/  Supabase schema/auth configuration notes
docs/
  architecture/ architecture notes and audits
  rfc/          product and technical RFCs
```

## Prerequisites

- Node.js 20+
- pnpm 10+
- Python 3.12+ for the future FastAPI app
- PostgreSQL 15+ for the future database layer

## Setup

```bash
corepack enable
pnpm install
cp .env.example .env
```

## Current status

The repository is in Sprint 1 bootstrap/planning state. The monorepo workspace is initialized, and the next implementation step is the FastAPI foundation described in `docs/planning/sprint-1-implementation-backlog.md`.

## Sprint 1 scope

End-to-end Sprint 1 success means:

- User signs in with Supabase Auth.
- User creates projects.
- User uploads audio files to local disk storage.
- Asset records are stored in PostgreSQL.
- Deterministic metadata is generated automatically.
- Vault search filters assets by metadata.
- Activity history records user actions.
- Producer profile aggregates uploads automatically.
