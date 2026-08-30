# Sonic AI V3 — Critical Blockers

**Status:** Current recovery blocker register  
**Updated:** 2026-08-30  
**Canonical branch:** `main`

## Important

The previous 18-blocker report was based on the June 2026 repository state. Its numerical count is superseded.

## Current Blocker Policy

A blocker is current only when it is reproduced against the current `main` tree and recorded with evidence.

### Tier 1 — Cannot Boot

- Frontend cannot install/build/start.
- API cannot import/start.
- Required environment configuration is invalid or missing.

### Tier 2 — Cannot Function

- Database/auth contract is broken.
- Critical API routes fail.
- Chat pipeline fails end-to-end.
- Agent registry/model configuration fails.
- Tool/MCP boundary fails.
- Memory/retrieval path fails.

### Tier 3 — Cannot Advance Safely

- Tests do not cover the affected capability.
- User ownership/security boundaries are unverified.
- Deterministic analysis contracts are inconsistent.
- Documentation makes unsupported completion/readiness claims.

## Current Priority

```text
Boot → API → Data/Auth → Chat → Agents/Tools → Memory
→ Producer Intelligence Loop → Tests → Deployment
```

Do not assign a blocker count until the current repository has been tested. See `SONIC_AI_V3_HEALTH_MAP.md` for the canonical recovery gates.
