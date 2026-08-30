# Sonic AI V3 — Launch Blockers

**Status:** Current release gate  
**Updated:** 2026-08-30  
**Canonical branch:** `main`

## Important

The previous 47-blocker count was a June 2026 snapshot and is superseded. No current blocker count is claimed until the current tree is tested.

## Launch Gate

Sonic AI V3 is not considered production-ready until these gates are verified:

1. Repository and branch integrity.
2. Reproducible dependency installation.
3. Frontend development and production builds.
4. API import/startup and health checks.
5. Database migrations/schema and connection integrity.
6. Authentication and user ownership.
7. Chat end-to-end execution.
8. Agent registry and model configuration.
9. MCP/tool execution and permissions.
10. Memory persistence and retrieval.
11. Producer Intelligence vertical slice.
12. Automated tests and regression coverage.
13. Security review.
14. Deployment configuration and rollback path.
15. Observability and failure reporting.

## Evidence Standard

Each gate must have current reproducible evidence. Historical audit claims, documentation, or the existence of configuration files do not close a gate by themselves.

See `PRODUCTION_CHECKLIST.md`, `SONIC_AI_V3_HEALTH_MAP.md`, and `README.md` for the current baseline.
