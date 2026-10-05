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
