# Sonic AI Current-State Audit

## Phase 1: System overview

**Core purpose:** Sonic AI is intended to become a producer-focused audio asset platform: sign in, create projects, upload audio assets, generate deterministic metadata, search a personal vault, track activity, and build a producer profile from upload behavior.

**Target user:** Music producers, beatmakers, sample-pack creators, and audio-first creators who need an organized vault of project assets and production preferences.

**Specific problem solved:** Producers accumulate loops, samples, demos, exports, reports, and references across disconnected folders. Sprint 1 solves the foundational organization problem before adding AI: authenticated storage, project ownership, metadata, search, and activity history.

**Core features planned for Sprint 1:**

- Supabase-backed sign-in and user synchronization.
- Project CRUD with ownership validation.
- Local disk asset uploads.
- Deterministic metadata stubs.
- SQL-backed vault search.
- Activity timeline.
- Producer profile aggregation.

**Differentiation:** Sonic AI is positioned less as a generic file manager and more as a producer memory layer. Its strongest future differentiator is the combination of asset metadata, creative history, profile aggregation, and later agentic workflows. That differentiation is planned, not yet implemented.

## Phase 2: Functionality breakdown

| Module | Status | Issues / missing components | Performance quality |
| --- | --- | --- | --- |
| Audio processing | Not started | No upload API, no metadata worker, no DSP, no playback/editing/generation. Sprint 1 explicitly uses deterministic metadata only. | Basic planned |
| AI models | Not started | No AI generation, embeddings, agent, model provider, or evaluation pipeline. Correctly deferred to later sprints. | Not applicable |
| UI/UX flow | Not started | No Next.js app, routes, components, login, dashboard, project page, vault, activity, or profile UI. | Not applicable |
| Backend APIs | Not started | No FastAPI app, routers, database session, auth middleware, storage service, event bus, or worker hooks. | Not applicable |
| File handling | Not started | No multipart upload route, file validation, disk writer, checksum, MIME handling, or storage abstraction. | Not applicable |
| Authentication | Not started | Supabase Auth is selected, but routes and JWT/profile synchronization are not implemented. | Not applicable |
| Payment system | Not started | No pricing, billing provider, subscriptions, entitlements, or checkout. Not required for Sprint 1 foundation. | Not applicable |

## Phase 3: Build and development status

**Current stage:** Idea / bootstrap.

**Fully working right now:**

- Monorepo workspace skeleton.
- Root-level setup metadata.
- Sprint 1 implementation plan.

**Partially working:**

- Repository organization exists, but application code is still pending.

**Broken or not implemented:**

- FastAPI app.
- Database models and migrations.
- Supabase Auth integration.
- Project CRUD.
- Asset upload.
- Event bus.
- Metadata worker.
- Vault search.
- Activity feed.
- Producer profile aggregation.
- Next.js frontend.

**Launch blockers:**

- No runnable product surface yet.
- No database schema.
- No authentication path.
- No upload or storage implementation.
- No end-to-end tests.
- No deployment target.

## Phase 4: Testing and access

**Is Sonic AI currently testable?** No, not as an application.

**Immediate steps required to make it testable:**

1. Implement FastAPI foundation with `/health` and `/api/v1/status`.
2. Add PostgreSQL, SQLAlchemy 2.x, Alembic, and initial migrations.
3. Add Supabase JWT verification and `/auth/me` profile sync.
4. Implement project CRUD.
5. Implement local file upload and database asset records.
6. Add in-process events and deterministic metadata generation.
7. Add vault search, activity feed, and producer profile updates.
8. Build minimal Next.js pages for the Sprint 1 user journey.

**Local testing instructions today:**

```bash
corepack enable
pnpm install
```

**Deployment status:** Local bootstrap only. No staging or live deployment exists.

## Phase 5: Launch readiness score

| Category | Score | Reason |
| --- | ---: | --- |
| Product readiness | 1/10 | Clear scope exists, but core flows are not implemented. |
| Technical stability | 1/10 | Skeleton exists; no runtime services yet. |
| User experience | 0/10 | No frontend or authenticated flow yet. |
| Market readiness | 2/10 | Strong problem framing, but no usable product or launch funnel. |

**Can this launch right now?** No. Sonic AI cannot launch because users cannot sign in, create projects, upload assets, view metadata, search the vault, or access a UI.

## Phase 6: Critical fixes before launch

1. Build the FastAPI foundation and health/status endpoints.
2. Add PostgreSQL models and Alembic migrations for Sprint 1 tables only.
3. Implement Supabase Auth JWT verification and profile synchronization.
4. Implement project CRUD with ownership validation.
5. Implement upload storage, asset records, and file validation.
6. Implement event persistence and in-process event dispatch.
7. Implement deterministic metadata generation on `asset.uploaded`.
8. Implement vault search filters and indexed queries.
9. Implement activity feed and producer profile aggregation.
10. Build the Next.js MVP screens and connect them with TanStack Query.
11. Add integration tests for the full Sprint 1 happy path.
12. Add local Docker/PostgreSQL setup and deployment documentation.

## Phase 7: Full technical breakdown

**Current tech stack:**

- Monorepo: pnpm workspaces.
- Frontend planned: Next.js 15, TypeScript, Tailwind, shadcn/ui, TanStack Query.
- Backend planned: FastAPI, Python, SQLAlchemy 2.x, Alembic.
- Database planned: PostgreSQL.
- Auth planned: Supabase Auth.
- Storage planned: local disk at `/storage/uploads`, Supabase Storage later.
- Eventing planned: in-process pub/sub first, Redis later.
- AI/DSP planned: explicitly out of Sprint 1.

**Current file structure:**

```text
apps/web/package.json
apps/api/package.json
apps/worker/package.json
packages/common/package.json
packages/events/package.json
packages/auth/package.json
packages/projects/package.json
packages/assets/package.json
packages/metadata/package.json
packages/memory/package.json
packages/vault/package.json
infrastructure/docker/
infrastructure/supabase/
docs/architecture/current-state-audit.md
docs/planning/sprint-1-implementation-backlog.md
```

**Key scripts:**

- `pnpm install`: installs workspace dependencies.
- `pnpm dev`: planned recursive development command; app-level `dev` scripts still need to be added.
- `pnpm build`: planned recursive build command; app/package build scripts still need to be added.
- `pnpm lint`: planned recursive lint command; app/package lint scripts still need to be added.
- `pnpm test`: planned recursive test command; app/package test scripts still need to be added.
- `pnpm typecheck`: planned recursive typecheck command; app/package typecheck scripts still need to be added.

**APIs and integrations:** None implemented yet. Planned Sprint 1 APIs are documented in the implementation backlog.

**Database structure:** No database exists yet. Planned first tables: `users`, `profiles`, `projects`, `assets`, `asset_metadata`, `memory_events`, and `producer_profiles`.

## Phase 8: Handoff code package

### Clean summarized architecture

Sonic AI should be built as a pnpm monorepo with a FastAPI backend, a Next.js frontend, a lightweight worker/event layer, and shared domain packages. Sprint 1 should keep all intelligence deterministic and SQL-backed. User identity starts in Supabase Auth, synchronizes into local `users` and `profiles` tables, then gates project, asset, vault, activity, and profile operations by ownership.

### Core logic snippets

**Event contract:**

```python
event_bus.publish("asset.uploaded", {"asset_id": asset.id, "user_id": user.id})
```

**Metadata stub:**

```python
metadata = {
    "bpm": 150,
    "musical_key": "F Minor",
    "genre": "Trap",
    "duration_seconds": 120,
    "sample_rate": 44100,
    "lufs": -8.1,
    "peak_db": -0.7,
}
```

**Vault query shape:**

```sql
SELECT assets.id AS asset_id, projects.name AS project_name, asset_metadata.bpm
FROM assets
JOIN projects ON projects.id = assets.project_id
JOIN asset_metadata ON asset_metadata.asset_id = assets.id
WHERE assets.user_id = :user_id;
```

### Setup instructions

```bash
corepack enable
pnpm install
cp .env.example .env
```

### Deployment instructions

Deployment is not ready. Before deployment, add Docker Compose for PostgreSQL/API/web, configure Supabase Auth keys, add production environment variables, and choose a storage volume for `/storage/uploads`.

### Notes for further development

- Execute `docs/planning/sprint-1-implementation-backlog.md` in order.
- Keep Sprint 1 free of AI generation, embeddings, agent behavior, Redis, Celery, pgvector, and DSP-heavy analysis.
- Add integration tests at each milestone rather than waiting for the full frontend.
