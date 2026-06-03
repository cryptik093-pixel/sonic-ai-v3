# Sprint 1 Implementation Backlog

## Sprint 1 goal

By the end of Sprint 1, a user can sign in, create projects, upload audio files, store assets, view deterministic metadata, search the vault, view activity history, and build a producer profile automatically.

## Non-goals

- No AI generation.
- No autonomous agent.
- No embeddings or pgvector.
- No Redis or Celery.
- No DSP-heavy analysis.
- No generated assets.

## Execution rules for Codex

1. Work milestones in order unless a later task is explicitly unblocked.
2. Keep each pull request scoped to one milestone or one vertical slice.
3. Add tests with every backend module.
4. Prefer deterministic fixtures over mocks where possible.
5. Do not introduce deferred Sprint 2 infrastructure.
6. Every protected query must filter by authenticated `user_id`.
7. Every user action that changes state should emit and persist an activity event.

## Milestone 1: Repository bootstrap

**Status:** Complete for initial skeleton.

### Files created / maintained

- `package.json`
- `pnpm-workspace.yaml`
- `.editorconfig`
- `.gitignore`
- `.env.example`
- `README.md`
- `apps/web/package.json`
- `apps/api/package.json`
- `apps/worker/package.json`
- `packages/*/package.json`
- `infrastructure/docker/`
- `infrastructure/supabase/`
- `docs/architecture/`
- `docs/rfc/`

### Acceptance checks

```bash
pnpm install
```

## Milestone 2: FastAPI foundation

### Build files

- `apps/api/pyproject.toml`
- `apps/api/README.md`
- `apps/api/app/__init__.py`
- `apps/api/app/main.py`
- `apps/api/app/core/__init__.py`
- `apps/api/app/core/config.py`
- `apps/api/app/core/database.py`
- `apps/api/app/core/security.py`
- `apps/api/app/modules/auth/router.py`
- `apps/api/app/modules/projects/router.py`
- `apps/api/app/modules/assets/router.py`
- `apps/api/app/modules/metadata/router.py`
- `apps/api/app/modules/memory/router.py`
- `apps/api/app/modules/vault/router.py`
- `apps/api/tests/test_health.py`

### Implementation tasks

1. Create a FastAPI app factory or module-level `app` in `app/main.py`.
2. Add `GET /health` returning `{ "status": "ok" }`.
3. Add `GET /api/v1/status` returning `{ "status": "ok" }`.
4. Add settings loading in `core/config.py` from environment variables.
5. Add placeholder database session dependency in `core/database.py`.
6. Add placeholder auth dependency in `core/security.py`.
7. Register empty routers for Sprint 1 modules under `/api/v1` where appropriate.
8. Add pytest coverage for health and status endpoints.

### Acceptance checks

```bash
cd apps/api
uvicorn app.main:app --reload
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/status
pytest
```

## Milestone 3: Database layer

### Build files

- `apps/api/alembic.ini`
- `apps/api/alembic/env.py`
- `apps/api/alembic/versions/<revision>_create_sprint_1_tables.py`
- `apps/api/app/db/__init__.py`
- `apps/api/app/db/base.py`
- `apps/api/app/db/session.py`
- `apps/api/app/models/__init__.py`
- `apps/api/app/models/user.py`
- `apps/api/app/models/profile.py`
- `apps/api/app/models/project.py`
- `apps/api/app/models/asset.py`
- `apps/api/app/models/asset_metadata.py`
- `apps/api/app/models/memory_event.py`
- `apps/api/app/models/producer_profile.py`
- `apps/api/tests/test_migrations.py`

### Tables

- `users`
- `profiles`
- `projects`
- `assets`
- `asset_metadata`
- `memory_events`
- `producer_profiles`

### Required indexes

- `users.supabase_user_id` unique.
- `profiles.user_id` unique.
- `projects.user_id`.
- `assets.user_id`.
- `assets.project_id`.
- `assets.asset_type`.
- `asset_metadata.asset_id` unique.
- `asset_metadata.bpm`.
- `asset_metadata.musical_key`.
- `asset_metadata.genre`.
- `memory_events.user_id`.
- `memory_events.created_at`.
- `producer_profiles.user_id` unique.

### Acceptance checks

```bash
cd apps/api
alembic upgrade head
pytest
```

## Milestone 4: Authentication

### Build files

- `apps/api/app/modules/auth/router.py`
- `apps/api/app/modules/auth/schemas.py`
- `apps/api/app/modules/auth/service.py`
- `apps/api/app/core/security.py`
- `apps/api/tests/modules/auth/test_auth_me.py`
- `apps/api/tests/modules/auth/test_profile_sync.py`

### Routes

- `POST /auth/login`
- `POST /auth/logout`
- `GET /auth/me`

### Implementation tasks

1. Verify Supabase JWTs from the `Authorization: Bearer <token>` header.
2. Extract Supabase subject, email, and user metadata.
3. Upsert `users` by Supabase user id.
4. Upsert `profiles` by local user id.
5. Return profile data from `/auth/me`.
6. Keep `/auth/login` and `/auth/logout` as API-compatible pass-through endpoints if the frontend uses Supabase client-side auth.

### Acceptance checks

```bash
cd apps/api
pytest apps/api/tests/modules/auth
curl -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" http://localhost:8000/auth/me
```

## Milestone 5: Projects module

### Build files

- `apps/api/app/modules/projects/router.py`
- `apps/api/app/modules/projects/schemas.py`
- `apps/api/app/modules/projects/service.py`
- `apps/api/tests/modules/projects/test_projects.py`

### Routes

- `POST /projects`
- `GET /projects`
- `GET /projects/{id}`
- `PATCH /projects/{id}`
- `DELETE /projects/{id}`

### Implementation tasks

1. Create Pydantic schemas for project create, update, and response.
2. Implement ownership-filtered list and detail queries.
3. Enforce ownership for update and delete.
4. Emit `project.created` and `project.updated` events.
5. Persist activity records for create, update, and delete.

### Acceptance checks

```bash
cd apps/api
pytest apps/api/tests/modules/projects
```

## Milestone 6: Asset upload system

### Build files

- `apps/api/app/modules/assets/router.py`
- `apps/api/app/modules/assets/schemas.py`
- `apps/api/app/modules/assets/service.py`
- `apps/api/app/modules/assets/storage.py`
- `apps/api/tests/modules/assets/test_upload.py`

### Route

- `POST /assets/upload`

### Supported types

- `audio`
- `midi`
- `sample`
- `report`
- `export`

### Implementation tasks

1. Accept multipart file uploads with `project_id` and `asset_type`.
2. Validate project ownership before writing files.
3. Store files under `${UPLOAD_STORAGE_PATH}/{user_id}/{project_id}/{asset_id}/original_filename`.
4. Create an `assets` row with storage path, filename, MIME type, byte size, and asset type.
5. Publish `asset.uploaded`.
6. Persist an `asset.uploaded` memory event.

### Acceptance checks

```bash
cd apps/api
pytest apps/api/tests/modules/assets
```

## Milestone 7: Event bus

### Build files

- `apps/api/app/events/__init__.py`
- `apps/api/app/events/bus.py`
- `apps/api/app/events/contracts.py`
- `apps/api/app/events/subscribers.py`
- `apps/api/tests/events/test_event_bus.py`

### Events

- `asset.uploaded`
- `project.created`
- `project.updated`
- `asset.metadata.created`
- `metadata.generated`

### Implementation tasks

1. Implement `publish(event_name, payload)`.
2. Implement `subscribe(event_name, handler)`.
3. Support multiple handlers per event.
4. Keep execution in-process and synchronous for Sprint 1.
5. Wire `asset.uploaded` to the metadata stub handler.
6. Wire event persistence without adding Redis.

### Acceptance checks

```bash
cd apps/api
pytest apps/api/tests/events
```

## Milestone 8: Metadata worker

### Build files

- `apps/api/app/modules/metadata/schemas.py`
- `apps/api/app/modules/metadata/service.py`
- `apps/api/app/modules/metadata/subscribers.py`
- `apps/api/tests/modules/metadata/test_metadata_generation.py`

### Deterministic metadata payload

```json
{
  "bpm": 150,
  "musical_key": "F Minor",
  "genre": "Trap",
  "duration_seconds": 120,
  "sample_rate": 44100,
  "lufs": -8.1,
  "peak_db": -0.7
}
```

### Implementation tasks

1. Subscribe to `asset.uploaded`.
2. Create one `asset_metadata` row per asset.
3. Publish `asset.metadata.created` and/or `metadata.generated`.
4. Persist a metadata activity event.
5. Ensure duplicate upload events do not create duplicate metadata rows.

### Acceptance checks

```bash
cd apps/api
pytest apps/api/tests/modules/metadata
```

## Milestone 9: Sonic Vault

### Build files

- `apps/api/app/modules/vault/router.py`
- `apps/api/app/modules/vault/schemas.py`
- `apps/api/app/modules/vault/service.py`
- `apps/api/tests/modules/vault/test_vault_search.py`

### Route

- `GET /vault/search`

### Filters

- `bpm`
- `key`
- `genre`
- `asset_type`
- `project_id`

### Response shape

```json
[
  {
    "asset_id": "...",
    "project_name": "...",
    "bpm": 150
  }
]
```

### Implementation tasks

1. Join `assets`, `projects`, and `asset_metadata`.
2. Always filter by authenticated user id.
3. Add optional filters for bpm, key, genre, asset type, and project id.
4. Return stable sorted results by newest asset first.
5. Add tests proving users cannot search other users' assets.

### Acceptance checks

```bash
cd apps/api
pytest apps/api/tests/modules/vault
```

## Milestone 10: Memory and activity feed

### Build files

- `apps/api/app/modules/memory/router.py`
- `apps/api/app/modules/memory/schemas.py`
- `apps/api/app/modules/memory/service.py`
- `apps/api/tests/modules/memory/test_activity_feed.py`

### Route

- `GET /activity`

### Implementation tasks

1. Persist `memory_events` for project creation, project update, asset upload, and metadata generation.
2. Return authenticated user's events newest first.
3. Include event name, timestamp, entity references, and compact payload.
4. Add pagination parameters.

### Acceptance checks

```bash
cd apps/api
pytest apps/api/tests/modules/memory
```

## Milestone 11: Producer profile engine

### Build files

- `apps/api/app/modules/profiles/__init__.py`
- `apps/api/app/modules/profiles/schemas.py`
- `apps/api/app/modules/profiles/service.py`
- `apps/api/app/modules/profiles/subscribers.py`
- `apps/api/tests/modules/profiles/test_producer_profile.py`

### Aggregates

- Uploaded BPMs.
- Uploaded keys.
- Uploaded genres.
- Loudness preferences.

### Output shape

```json
{
  "favorite_bpm_min": 140,
  "favorite_bpm_max": 155,
  "favorite_key": "F Minor",
  "favorite_genre": "Trap",
  "preferred_lufs": -8
}
```

### Implementation tasks

1. Subscribe to `asset.metadata.created`.
2. Recompute profile aggregates from all user metadata rows.
3. Upsert `producer_profiles` by user id.
4. Expose profile data through `/auth/me` or a future profile endpoint.
5. Test profile changes after multiple uploads.

### Acceptance checks

```bash
cd apps/api
pytest apps/api/tests/modules/profiles
```

## Milestone 12: Frontend MVP

### Build files

- `apps/web/package.json`
- `apps/web/next.config.ts`
- `apps/web/tsconfig.json`
- `apps/web/app/layout.tsx`
- `apps/web/app/page.tsx`
- `apps/web/app/login/page.tsx`
- `apps/web/app/dashboard/page.tsx`
- `apps/web/app/projects/page.tsx`
- `apps/web/app/projects/[id]/page.tsx`
- `apps/web/app/vault/page.tsx`
- `apps/web/app/activity/page.tsx`
- `apps/web/app/profile/page.tsx`
- `apps/web/components/ProjectList.tsx`
- `apps/web/components/ProjectCard.tsx`
- `apps/web/components/UploadAssetDialog.tsx`
- `apps/web/components/VaultTable.tsx`
- `apps/web/components/ActivityFeed.tsx`
- `apps/web/components/ProducerProfileCard.tsx`
- `apps/web/lib/api.ts`
- `apps/web/lib/supabase.ts`
- `apps/web/lib/query.tsx`

### Pages

- `/`
- `/login`
- `/dashboard`
- `/projects`
- `/projects/[id]`
- `/vault`
- `/activity`
- `/profile`

### Implementation tasks

1. Initialize Next.js 15 with TypeScript and Tailwind.
2. Add shadcn/ui components required for cards, tables, buttons, inputs, dialogs, and forms.
3. Configure Supabase browser client.
4. Configure TanStack Query provider.
5. Implement login flow.
6. Implement dashboard links to projects, vault, activity, and profile.
7. Implement project list/create/detail/update/delete flows.
8. Implement upload dialog on project detail.
9. Implement metadata display after upload.
10. Implement vault filters and table.
11. Implement activity feed.
12. Implement producer profile card.

### Acceptance checks

```bash
cd apps/web
pnpm lint
pnpm typecheck
pnpm build
```

## End-to-end Sprint 1 acceptance test

### User journey

1. User signs in.
2. User creates a project.
3. User uploads an audio asset.
4. Asset appears in local storage.
5. Asset row exists in PostgreSQL.
6. Metadata row exists with deterministic stub values.
7. Vault search finds the asset by bpm, key, genre, asset type, and project id.
8. Activity feed shows project and asset events.
9. Producer profile reflects uploaded metadata.

### Suggested automated test

- `apps/api/tests/e2e/test_sprint_1_happy_path.py`

### Final acceptance checks

```bash
pnpm install
pnpm lint
pnpm test
pnpm build
```
