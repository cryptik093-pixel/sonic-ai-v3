# Sonic AI V3 — Engineering Audit and Handoff

## Executive Verdict

Sonic AI V3 is currently at the **idea / blueprint stage**, not a runnable application. The repository contains only a minimal README and this audit document; there is no frontend, backend, database schema, authentication layer, storage pipeline, AI integration, deployment config, or test suite yet.

The supplied product direction is strong: Sonic AI V3 should become an **AI Producer Operating System** where projects, assets, analyses, generations, decisions, and learning events become structured user-owned data. However, the current codebase does not yet implement that operating system.

## Phase 1 — System Overview

### What Sonic AI Is Intended To Be

Sonic AI is intended to be a persistent AI-native production environment for music producers. Its core purpose is to organize creative work into a user-owned graph and use that graph to personalize future recommendations, analyses, generation, and agent workflows.

### Target User

- Music producers
- Beatmakers
- Songwriters
- Mixing / mastering learners
- Artists who want project memory, asset organization, and AI-guided workflow support

### Main Value

Sonic AI should turn scattered creative files and one-off AI actions into persistent producer intelligence. Instead of acting as a single-purpose audio analyzer or generator, it should become a long-term workspace that remembers user behavior and improves recommendations over time.

### Specific Problem Solved

Music producers typically lose context across projects: BPM preferences, favorite keys, mix targets, arrangement habits, revision history, and generated assets are spread across DAWs, cloud drives, notes, and AI chats. Sonic AI aims to centralize those signals into a structured graph so agents can understand the producer and continue work intelligently.

### Intended Core Features

1. User authentication and profile ownership
2. Project workspaces
3. Sonic Vault for assets
4. Asset upload and storage
5. Metadata extraction for BPM, key, loudness, duration, genre, energy, and tags
6. Immutable analysis records
7. Producer profile / memory engine
8. Search, filtering, tagging, and versioning
9. AI agent context builder
10. MIDI / chord / melody / drum generation
11. Artist development metrics and growth reports
12. Activity timeline across projects and assets

### Differentiation

Sonic AI is differentiated by positioning itself as an operating system rather than a single audio tool. The product thesis is that every action should feed a persistent producer memory layer, enabling personalized workflows and long-term artist development instead of isolated AI outputs.

## Phase 2 — Functionality Breakdown

| Module | Intended Scope | Current Status | Issues / Missing Components | Performance Quality |
|---|---|---:|---|---:|
| Audio processing | Metadata extraction, mix analysis, loudness, arrangement analysis | Not started | No audio libraries, upload path, analysis jobs, or result models | N/A |
| Audio generation | MIDI, chords, melodies, basslines, drums, textures | Not started | No generation service, prompt layer, model adapter, or asset injection flow | N/A |
| AI models | Agent, personalization, generation, analysis recommendations | Not started | No model provider, orchestration, evaluation harness, or prompts | N/A |
| UI / UX | Next.js app, onboarding, project view, vault, reports, agent | Not started | No frontend code, routes, design system, or user journey | N/A |
| Backend APIs | FastAPI modular monolith | Not started | No app package, API routes, domain services, or background workers | N/A |
| File handling | Uploads, exports, formats, storage | Not started | No upload endpoints, MIME validation, Supabase/S3 integration, or export handling | N/A |
| Authentication | User login, ownership, subscriptions | Not started | No auth provider, user model, middleware, or session flow | N/A |
| Payments | Subscription state / billing | Not started | No Stripe or billing integration | N/A |
| Database | PostgreSQL + pgvector user-owned graph | Not started | No schema, migrations, ORM, or seed data | N/A |
| Queue | Redis + Celery background analysis | Not started | No worker, broker config, task contracts, or retry policy | N/A |
| Analytics | PostHog event tracking | Not started | No analytics client, event taxonomy, or privacy handling | N/A |

## Phase 3 — Build and Development Status

### Current Stage

**Idea / blueprint.** The repo is initialized but does not yet contain an application.

### Fully Working Right Now

- Git repository exists.
- Minimal README exists.
- Product blueprint has been converted into this audit / handoff document.

### Partially Working

- Documentation only.

### Broken or Not Implemented

- Frontend application
- Backend application
- Database schema
- Authentication
- Uploads
- Asset storage
- Metadata pipeline
- Sonic Vault
- Memory engine
- Analysis engine
- Generation engine
- Studio Agent
- Artist development engine
- Tests
- Deployment
- CI/CD

### Dependencies / Blockers Preventing Launch

1. No runnable application exists.
2. No package manifests or dependency lockfiles exist.
3. No API server exists.
4. No frontend exists.
5. No persistence layer exists.
6. No storage credentials or integration exists.
7. No environment variable contract exists.
8. No test suite exists.
9. No deployment targets are configured.

## Phase 4 — Testing and Access

### Is Sonic AI Currently Testable?

**No.** There is no runnable frontend or backend in the repository.

### Exact Steps Required To Make It Testable Immediately

1. Scaffold frontend:
   ```bash
   npx create-next-app@latest apps/web --ts --tailwind --eslint --app
   ```
2. Scaffold backend:
   ```bash
   mkdir -p apps/api/app
   cd apps/api
   python3.13 -m venv .venv
   . .venv/bin/activate
   pip install fastapi uvicorn pydantic sqlalchemy alembic psycopg[binary] redis celery python-multipart
   ```
3. Add local infrastructure:
   ```bash
   docker compose up -d postgres redis
   ```
4. Add minimum backend health route:
   ```http
   GET /health
   ```
5. Add minimum frontend home page that calls `/health`.
6. Add `.env.example` with database, Redis, storage, auth, analytics, and AI provider placeholders.
7. Add first tests:
   - Backend: health route test
   - Frontend: smoke render test
   - Integration: project creation happy path

### Local Testing Instructions After Scaffold Exists

Expected future commands:

```bash
# Frontend
cd apps/web
npm install
npm run dev

# Backend
cd apps/api
python3.13 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Infrastructure
docker compose up -d postgres redis
```

### Deployment Status

- Local: Not runnable
- Staging: Not configured
- Live: Not configured

## Phase 5 — Launch Readiness Score

| Category | Score | Reason |
|---|---:|---|
| Product readiness | 2 / 10 | Strong concept and roadmap, but no implemented product |
| Technical stability | 1 / 10 | No application code or tests exist |
| User experience | 1 / 10 | No UI exists |
| Market readiness | 3 / 10 | Clear positioning, but no demo, onboarding, pricing, or proof of value |

### Can This Launch Right Now?

**No.** Sonic AI cannot launch right now because there is no runnable software, no user flow, no backend, no storage, no authentication, no deployment, and no testable MVP.

## Phase 6 — Critical Fixes Before Launch

### Must-Fix Before Any Private Alpha

1. Scaffold monorepo with `apps/web`, `apps/api`, and shared documentation.
2. Implement authentication and user ownership model.
3. Implement project CRUD.
4. Implement asset upload with metadata records.
5. Implement Sonic Vault listing, search, filters, and tags.
6. Implement PostgreSQL schema and migrations.
7. Add local Docker Compose for Postgres and Redis.
8. Add `.env.example` and setup documentation.
9. Add backend and frontend smoke tests.
10. Add deployment configs for Vercel and Railway.

### Must-Fix Before Public Beta

1. Immutable analysis history.
2. Background metadata extraction queue.
3. Producer profile aggregation.
4. Project activity feed.
5. Error handling and upload validation.
6. Billing / subscription gating if monetized.
7. Analytics and event tracking.
8. Basic Studio Agent with project-aware context.
9. Security review for object ownership and signed URLs.
10. Observability for API errors and background jobs.

## Phase 7 — Full Technical Breakdown

### Current Repository Snapshot

```text
sonic-ai-v3/
├── README.md
└── docs/
    └── sonic-ai-audit.md
```

### Current Tech Stack

No tech stack is implemented in code yet.

### Intended Tech Stack

| Layer | Intended Technology |
|---|---|
| Frontend | Next.js 15, TypeScript, Tailwind, shadcn/ui, Framer Motion, TanStack Query |
| Backend | FastAPI, Python 3.13 |
| Database | PostgreSQL, pgvector |
| Storage | Supabase Storage, AWS S3-compatible layer |
| Queue | Redis, Celery |
| Analytics | PostHog |
| Frontend hosting | Vercel |
| Backend hosting | Railway |
| Database hosting | Supabase |

### Recommended File Structure

```text
sonic-ai-v3/
├── apps/
│   ├── web/
│   │   ├── app/
│   │   ├── components/
│   │   ├── lib/
│   │   └── package.json
│   └── api/
│       ├── app/
│       │   ├── main.py
│       │   ├── core/
│       │   ├── auth/
│       │   ├── users/
│       │   ├── projects/
│       │   ├── assets/
│       │   ├── metadata/
│       │   ├── analysis/
│       │   ├── generation/
│       │   ├── vault/
│       │   ├── memory/
│       │   ├── learning/
│       │   ├── analytics/
│       │   └── agent/
│       ├── alembic/
│       ├── pyproject.toml
│       └── tests/
├── docs/
├── infra/
│   └── docker-compose.yml
├── .env.example
└── README.md
```

### Recommended Database Structure

Minimum tables for Sprint 1 and Sprint 2:

```sql
users (
  id uuid primary key,
  email text unique not null,
  subscription_status text,
  created_at timestamptz not null
);

profiles (
  id uuid primary key,
  user_id uuid not null references users(id),
  display_name text,
  preferences jsonb not null default '{}'
);

projects (
  id uuid primary key,
  user_id uuid not null references users(id),
  name text not null,
  description text,
  status text not null default 'active',
  created_at timestamptz not null,
  updated_at timestamptz not null
);

assets (
  id uuid primary key,
  user_id uuid not null references users(id),
  project_id uuid references projects(id),
  type text not null,
  storage_key text not null,
  filename text not null,
  mime_type text,
  size_bytes bigint,
  metadata jsonb not null default '{}',
  created_at timestamptz not null
);

analyses (
  id uuid primary key,
  user_id uuid not null references users(id),
  project_id uuid references projects(id),
  asset_id uuid references assets(id),
  type text not null,
  version text not null,
  result jsonb not null,
  created_at timestamptz not null
);

producer_profiles (
  id uuid primary key,
  user_id uuid not null references users(id),
  favorite_bpm_range int[],
  favorite_key text,
  favorite_genre text,
  master_target_lufs numeric,
  favorite_arrangement text,
  metrics jsonb not null default '{}',
  updated_at timestamptz not null
);

activity_events (
  id uuid primary key,
  user_id uuid not null references users(id),
  project_id uuid references projects(id),
  asset_id uuid references assets(id),
  event_type text not null,
  payload jsonb not null default '{}',
  created_at timestamptz not null
);
```

### Recommended API Surface

```http
GET    /health
POST   /auth/session
GET    /me
PATCH  /me/profile
POST   /projects
GET    /projects
GET    /projects/{project_id}
PATCH  /projects/{project_id}
DELETE /projects/{project_id}
POST   /projects/{project_id}/assets
GET    /projects/{project_id}/assets
GET    /assets
GET    /assets/{asset_id}
PATCH  /assets/{asset_id}/metadata
POST   /assets/{asset_id}/analyze
GET    /assets/{asset_id}/analyses
GET    /vault
GET    /memory/profile
POST   /agent/actions
```

### Key Scripts / Functions Needed

No scripts exist today. The first implementation should add:

| Script | Purpose |
|---|---|
| `npm run dev` | Run frontend locally |
| `npm run build` | Build frontend |
| `npm run lint` | Lint frontend |
| `uvicorn app.main:app --reload` | Run backend locally |
| `pytest` | Run backend tests |
| `alembic upgrade head` | Apply database migrations |
| `celery -A app.worker worker -l info` | Run background jobs |

## Phase 8 — Handoff Code Package

### Clean Architecture Summary

Build Sonic AI as a modular monolith first. The backend should expose module boundaries internally while sharing one FastAPI process and one PostgreSQL database. Every persistent record must include `user_id` and relational context where applicable. Analyses should be immutable. Generated assets should be stored as first-class assets and linked to the originating project, generation request, and activity event.

### Core Domain Contracts

```python
# apps/api/app/assets/schemas.py
from pydantic import BaseModel, Field
from uuid import UUID

class AssetMetadata(BaseModel):
    type: str
    bpm: int | None = None
    key: str | None = None
    genre: str | None = None
    energy: int | None = Field(default=None, ge=0, le=100)
    duration: float | None = None
    tags: list[str] = []

class AssetRead(BaseModel):
    id: UUID
    user_id: UUID
    project_id: UUID | None
    filename: str
    storage_key: str
    metadata: AssetMetadata
```

```python
# apps/api/app/analysis/schemas.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class AnalysisRead(BaseModel):
    id: UUID
    user_id: UUID
    project_id: UUID | None
    asset_id: UUID | None
    type: str
    version: str
    result: dict
    created_at: datetime
```

```python
# apps/api/app/memory/service.py
class ProducerMemoryService:
    def rebuild_profile(self, user_id):
        """Aggregate uploads, analyses, generations, exports, and activity events into deterministic preferences."""
        raise NotImplementedError
```

### Recommended First Sprint Implementation Order

1. Create repo structure.
2. Add Docker Compose for Postgres and Redis.
3. Add FastAPI health route.
4. Add SQLAlchemy models and Alembic migrations for users, profiles, projects, assets, analyses, and activity events.
5. Add project CRUD API.
6. Add asset upload API with placeholder metadata extraction.
7. Add frontend project list and project detail pages.
8. Add Sonic Vault page with asset search and filters.
9. Add smoke tests.
10. Deploy backend to Railway and frontend to Vercel.

### Deployment Instructions To Add

Frontend:

```bash
cd apps/web
npm install
npm run build
vercel deploy
```

Backend:

```bash
cd apps/api
pip install -r requirements.txt
alembic upgrade head
railway up
```

Required environment variables:

```env
DATABASE_URL=
REDIS_URL=
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_STORAGE_BUCKET=
AUTH_SECRET=
POSTHOG_KEY=
OPENAI_API_KEY=
```

### Development Notes

- Do not add AI generation before the data graph works.
- Do not allow assets without metadata records.
- Do not overwrite analyses; create new immutable records for every run.
- Do not generate content without project, producer profile, and memory context.
- Add ownership checks to every project, asset, analysis, and activity route.
- Use deterministic memory first; add embeddings and pgvector only after behavior tracking is reliable.
