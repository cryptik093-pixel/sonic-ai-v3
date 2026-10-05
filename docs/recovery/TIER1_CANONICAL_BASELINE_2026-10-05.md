# Tier 1 Canonical Recovery Baseline — 2026-10-05

Status: ACTIVE
Recovery branch: `recovery/tier1-canonical-2026-10-05`
Canonical source branch: `main`
Pinned canonical SHA: `19ff3b7648c49f3f81b82dcc5e445028719edaba`

## Non-destructive rules

- Do not force-push, rewrite history, delete branches, or wholesale-merge recovery/feature lines.
- Treat `main` as the canonical Sonic source root until executable evidence supports a deliberate change.
- Preserve branch-only work and compare it against canonical state before cherry-pick or merge decisions.
- Historical reports are evidence, not runtime truth.
- Do not mark any subsystem healthy without reproducible tests, builds, runtime behavior, or CI evidence.

## High-value preserved branch lines observed at Tier 1 start

- `codex/sonic-production-workbench` @ `685407cfa728956e7143ba441c88636a0491b4c5`
- `codex/sonic-v3.5-clean-foundation` @ `05675c34a7c510e8c7d08515dbfd78ea6b01fc4a`
- `recovery/actual-project-state` @ `50592e982b5a4ffb9c8c4dc367c6da4c89b298b8`
- `recovery/runtime-baseline-integration` @ `2625eaee5304de474a5271646b70bce895d58c4b`
- `feat/ohis-foundation-v1` @ `206df3cfd91e6d4d77a2d538e88e1f1354e94edf`
- `feat/studio-drop-002-packaging` @ `8dd39a3454d8bf4696fa86f8bdf606c78df60042`
- `upgrade/midi-musical-coherence` @ `c2dcefb582c65d1d5f7f78dbbe335378725a577e`

## Verified repository contracts

Root package manager: `pnpm@10.28.1`
Node engine: `>=20`
Canonical validation commands:
- `pnpm audit:v3`
- `pnpm build`
- `pnpm lint`
- `pnpm test`
- `pnpm typecheck`

Runtime-baseline CI verifies:
- frozen dependency install
- V3 foundation audit
- web production build
- Python 3.12 API dependency install
- API bytecode compile
- API import and `/health` route presence

Desktop CI verifies:
- API tests
- desktop launcher smoke test
- browser workflow proof
- Windows packaging
- packaged runtime smoke
- native UI smoke
- artifact publication

## Tier 1 findings requiring evidence-based resolution

1. Public repository currently contains tracked root `dev.db` (65,536 bytes). Treat as a security/data-hygiene review item before any release.
2. Root historical status/report files intentionally resolve to compatibility aliases; labels such as FINAL_AUDIT_REPORT are not current runtime proof.
3. Recovery and feature branches contain significant unmerged capability. No blanket merge is authorized.
4. Current mainline must be re-certified through CI/build/test evidence before product expansion.

## Gate order

1. Repository and branch integrity.
2. Frontend boot/build.
3. API/backend boot/import/health.
4. Environment and dependency integrity.
5. Database/auth/user-ownership contracts.
6. Chat pipeline.
7. Agent registry/model configuration.
8. Tool/MCP boundaries.
9. Producer Intelligence Loop.
10. Automated verification and deployment readiness.

## Exit criteria for Tier 1

- exact SHAs and authority roots recorded
- branch-only assets inventoried and compared
- current canonical runtime build/test state captured
- security/data hygiene blockers classified
- recovery fixes remain reversible
- coherent fixes committed only after validation
- no destructive history operation performed


## Branch comparison classification

- `codex/sonic-production-workbench`: 0 ahead / 2 behind. No unique commits remain relative to main; treat as already subsumed, not a recovery source.
- `recovery/runtime-baseline-integration`: 0 ahead / 7 behind. No unique commits remain relative to main; preserve for provenance only.
- `upgrade/midi-musical-coherence`: 1 ahead / 0 behind; 34 changed files. Clean candidate for isolated validation before any integration.
- `codex/sonic-v3.5-clean-foundation`: diverged, 1 ahead / 13 behind; selective extraction only.
- `feat/ohis-foundation-v1`: diverged, 11 ahead / 47 behind; unique OHIS doctrine/schema assets identified; selective recovery only.
- `feat/studio-drop-002-packaging`: diverged, 19 ahead / 69 behind; product packaging plus event-store work present; selective recovery only.
- `recovery/actual-project-state`: diverged, 30 ahead / 69 behind across 149 files; high-risk wholesale merge source. Use as evidence reservoir only until decomposed.

### Immediate decision

Do not merge any divergent line. Next recovery work should separately validate the clean MIDI commit, inventory unique OHIS documents/schemas, and decompose Studio Drop/event-store changes by concern.


## Tier 1 execution update

### Repository data hygiene
- `dev.db` was the only tracked SQLite/database file in the canonical tree.
- Blob SHA: `1c8fda75727c07c340939e57f54a05969a2fc67f`.
- Provenance: introduced by commit `6a86f891e1cd6295d119b5171d069df05d5311e1` ("Add files via upload", 2026-06-20).
- Schema scan identified `users`, `projects`, `assets`, `analyses`, and `producer_profiles`.
- Content scan found no email-like values, UUIDs, URLs, API-key patterns, bearer tokens, JWTs, or password strings.
- Recovery branch removes the tracked local DB and ignores `*.db`, `*.sqlite`, and `*.sqlite3`.

### MIDI candidate
- `upgrade/midi-musical-coherence` remains one clean commit ahead of main.
- Exact candidate SHA `c2dcefb582c65d1d5f7f78dbbe335378725a577e` passed Runtime Baseline, CI, Veracode, and Sonic Desktop workflows.
- Existing draft PR: #28.
- Remaining release gates are Windows packaged/native UI acceptance, FL Studio import verification, and operator listening acceptance; no forced merge is authorized.


### OHIS selective recovery
- Source `feat/ohis-foundation-v1` was 11 ahead / 47 behind and therefore not merged.
- Unique doctrine/schema blobs were transplanted onto canonical main ancestry in `recovery/tier1-ohis-selective-2026-10-05`.
- Recovery commit: `754659ce1ad0571dbca5fa935c7c3c62d6190b97`.
- JSON Schema Draft 2020-12 parsed successfully.
- Runtime Baseline: PASS.
- Draft PR: #30.

### Studio Drop 002 evidence
- Source `feat/studio-drop-002-packaging` was 19 ahead / 69 behind.
- Seven unique product/package documents were preserved verbatim under a recovery-only namespace on `recovery/tier1-studio-drop-002-evidence-2026-10-05`.
- Recovery commit: `810e25d611212aa14a95a207e4be1acba1a342a2`.
- Runtime Baseline: PASS before PR checks.
- Draft PR: #31.
- The historical manifest's `MVP_CERTIFIED` label conflicts with its own unresolved filenames/formats/metadata/checksums/package-validation requirements; recovered docs are evidence, not current release certification.
- Event/runtime files embedded in the Studio Drop branch were verified byte-identical to dedicated Tier-5 branches and excluded from product recovery.

### Tier 5 event foundation
- Historical Gate 1: 13 ahead / 69 behind; old CI passed but old Veracode failed.
- Historical Gate 2: 15 ahead / 69 behind; no recorded workflow evidence.
- Selective recovery branch: `recovery/tier1-tier5-event-contract-2026-10-05`.
- Recovery commit: `bbecbaffb01d06d59ad105c80e3e0d6ddfdfd86c`.
- Recovered only the internal canonical event envelope, validator/bus, durable SQLite store, and tests.
- External events router and Shopify webhook ingestion remain excluded because the historical contract explicitly deferred authentication/signature verification.
- Draft PR: #32.

### Sonic v3.5 foundation classification
- `codex/sonic-v3.5-clean-foundation` is **historical design evidence, not a runtime recovery source**.
- Its repository-state snapshot claims API/web are blocked/package-manifest-only, which is stale relative to canonical main.
- Its local read-only MCP is narrower than current main's authenticated HTTP MCP/workbench surface.
- Agent operating-model concepts may be referenced manually, but the v3.5 state snapshot/server must not replace current runtime truth.
