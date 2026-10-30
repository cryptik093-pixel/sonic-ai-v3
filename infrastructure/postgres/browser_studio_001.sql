-- Browser Studio foundation, PostgreSQL only (opt-in migration candidate).
-- Do NOT run on today's SQLite-backed Sonic Desktop. First migrate the existing
-- projects and workbench_assets tables, preserving their primary keys and files.
-- Requires PostgreSQL, pgvector installed on the server, and a privileged
-- migration role. Does not expose an HTTP endpoint or switch database engines.
BEGIN;

DO $$
BEGIN
  IF to_regclass('public.projects') IS NULL THEN
    RAISE EXCEPTION 'Migrate existing projects before browser studio tables';
  END IF;
  IF to_regclass('public.workbench_assets') IS NULL THEN
    RAISE EXCEPTION 'Migrate existing workbench_assets before browser studio tables';
  END IF;
END;
$$;

CREATE EXTENSION IF NOT EXISTS vector;

-- The existing projects table remains the only project identity source.
CREATE TABLE studio_project_members (
  project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  principal_id VARCHAR(120) NOT NULL,
  role VARCHAR(16) NOT NULL CHECK (role IN ('owner', 'editor', 'viewer')),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (project_id, principal_id)
);
CREATE INDEX idx_studio_members_principal ON studio_project_members(principal_id, project_id);

CREATE TABLE studio_project_states (
  project_id INTEGER PRIMARY KEY REFERENCES projects(id) ON DELETE CASCADE,
  owner_id VARCHAR(120) NOT NULL,
  workspace_id VARCHAR(120) NOT NULL,
  revision BIGINT NOT NULL DEFAULT 0 CHECK (revision >= 0),
  state JSONB NOT NULL CHECK (
    jsonb_typeof(state) = 'object'
    AND state ->> 'schema_version' = 'sonic.studio-state/1.0'
  ),
  state_sha256 CHAR(64) NOT NULL CHECK (state_sha256 ~ '^[0-9a-f]{64}$'),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Durable, idempotent collaboration mutations; Redis is not the event store.
CREATE TABLE studio_mutation_events (
  event_id UUID PRIMARY KEY,
  project_id INTEGER NOT NULL REFERENCES studio_project_states(project_id) ON DELETE CASCADE,
  actor_id VARCHAR(120) NOT NULL,
  client_mutation_id UUID NOT NULL,
  base_revision BIGINT NOT NULL CHECK (base_revision >= 0),
  revision BIGINT NOT NULL CHECK (revision = base_revision + 1),
  operation VARCHAR(100) NOT NULL,
  payload JSONB NOT NULL CHECK (jsonb_typeof(payload) = 'object'),
  committed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (project_id, revision),
  UNIQUE (project_id, actor_id, client_mutation_id)
);
CREATE INDEX idx_studio_events_replay ON studio_mutation_events(project_id, revision ASC);

-- Periodic state checkpoints bound replay time. Do not store audio blobs here.
CREATE TABLE studio_state_checkpoints (
  project_id INTEGER NOT NULL REFERENCES studio_project_states(project_id) ON DELETE CASCADE,
  revision BIGINT NOT NULL CHECK (revision >= 0),
  state JSONB NOT NULL CHECK (
    jsonb_typeof(state) = 'object'
    AND state ->> 'schema_version' = 'sonic.studio-state/1.0'
  ),
  state_sha256 CHAR(64) NOT NULL CHECK (state_sha256 ~ '^[0-9a-f]{64}$'),
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (project_id, revision)
);

-- Match asset_id + owner_id + workspace_id to the same migrated asset row.
-- The existing workbench asset primary key remains unchanged.
CREATE UNIQUE INDEX ux_workbench_assets_identity_scope
  ON workbench_assets(id, owner_id, workspace_id);

-- Asset IDs refer to existing workbench imports; CLAP embeddings are derived
-- metadata, not a substitute for the original asset and its SHA-256 lineage.
-- 512 applies only to a verified CLAP encoder with a 512-d output; other models
-- require a new dimension-specific table or an explicit migration.
CREATE TABLE studio_asset_embeddings (
  asset_id VARCHAR(36) NOT NULL,
  owner_id VARCHAR(120) NOT NULL,
  workspace_id VARCHAR(120) NOT NULL,
  model_id VARCHAR(120) NOT NULL,
  model_version VARCHAR(80) NOT NULL,
  source_sha256 CHAR(64) NOT NULL CHECK (source_sha256 ~ '^[0-9a-f]{64}$'),
  embedding vector(512) NOT NULL,
  indexed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (asset_id, model_id, model_version),
  FOREIGN KEY (asset_id, owner_id, workspace_id)
    REFERENCES workbench_assets(id, owner_id, workspace_id) ON DELETE CASCADE
);
CREATE INDEX idx_studio_embedding_owners ON studio_asset_embeddings(owner_id, workspace_id, model_id, model_version);
CREATE INDEX idx_studio_embedding_cosine ON studio_asset_embeddings
  USING hnsw (embedding vector_cosine_ops);

-- Fail closed for normal application roles. Verified server authentication must
-- set LOCAL sonic.principal_id within the SAME transaction; do not derive it
-- from arbitrary WebSocket payloads or trust a client-provided owner/workspace.
ALTER TABLE studio_project_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE studio_project_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE studio_mutation_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE studio_state_checkpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE studio_asset_embeddings ENABLE ROW LEVEL SECURITY;

CREATE POLICY studio_members_self_read ON studio_project_members
  FOR SELECT USING (principal_id = current_setting('sonic.principal_id', true));

CREATE POLICY studio_state_read ON studio_project_states FOR SELECT USING (
  EXISTS (SELECT 1 FROM studio_project_members AS m
          WHERE m.project_id = studio_project_states.project_id
            AND m.principal_id = current_setting('sonic.principal_id', true))
);
CREATE POLICY studio_state_update ON studio_project_states FOR UPDATE
  USING (EXISTS (SELECT 1 FROM studio_project_members AS m
                 WHERE m.project_id = studio_project_states.project_id
                   AND m.principal_id = current_setting('sonic.principal_id', true)
                   AND m.role IN ('owner', 'editor')))
  WITH CHECK (EXISTS (SELECT 1 FROM studio_project_members AS m
                     WHERE m.project_id = studio_project_states.project_id
                       AND m.principal_id = current_setting('sonic.principal_id', true)
                       AND m.role IN ('owner', 'editor')));

CREATE POLICY studio_event_read ON studio_mutation_events FOR SELECT USING (
  EXISTS (SELECT 1 FROM studio_project_members AS m
          WHERE m.project_id = studio_mutation_events.project_id
            AND m.principal_id = current_setting('sonic.principal_id', true))
);
CREATE POLICY studio_event_insert ON studio_mutation_events FOR INSERT WITH CHECK (
  actor_id = current_setting('sonic.principal_id', true)
  AND EXISTS (SELECT 1 FROM studio_project_members AS m
              WHERE m.project_id = studio_mutation_events.project_id
                AND m.principal_id = current_setting('sonic.principal_id', true)
                AND m.role IN ('owner', 'editor'))
);

CREATE POLICY studio_checkpoint_read ON studio_state_checkpoints FOR SELECT USING (
  EXISTS (SELECT 1 FROM studio_project_members AS m
          WHERE m.project_id = studio_state_checkpoints.project_id
            AND m.principal_id = current_setting('sonic.principal_id', true))
);
CREATE POLICY studio_checkpoint_insert ON studio_state_checkpoints FOR INSERT WITH CHECK (
  EXISTS (SELECT 1 FROM studio_project_members AS m
          WHERE m.project_id = studio_state_checkpoints.project_id
            AND m.principal_id = current_setting('sonic.principal_id', true)
            AND m.role IN ('owner', 'editor'))
);

CREATE POLICY studio_embedding_read ON studio_asset_embeddings FOR SELECT USING (
  owner_id = current_setting('sonic.principal_id', true)
);
CREATE POLICY studio_embedding_insert ON studio_asset_embeddings FOR INSERT WITH CHECK (
  owner_id = current_setting('sonic.principal_id', true)
);

COMMIT;
