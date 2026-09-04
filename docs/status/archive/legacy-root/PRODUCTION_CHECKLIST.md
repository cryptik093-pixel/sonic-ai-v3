# Sonic AI V3 — Production Readiness Checklist

**Status:** Not certified  
**Updated:** 2026-08-30  
**Canonical branch:** `main`

> The previous percentage-based checklist was a June 2026 snapshot and is superseded.

## Gate 1 — Repository

- [ ] `main` is the canonical baseline.
- [ ] Expected source tree is present.
- [ ] No required capability was lost during recovery.

## Gate 2 — Build / Boot

- [ ] Dependencies install reproducibly.
- [ ] Frontend development server boots.
- [ ] Frontend production build succeeds.
- [ ] API imports and starts.
- [ ] Worker starts when required.

## Gate 3 — Data / Auth

- [ ] Database connection works.
- [ ] Schema/migrations are reproducible.
- [ ] Authentication works.
- [ ] User ownership is enforced.
- [ ] Asset/project relationships are valid.

## Gate 4 — Intelligence Platform

- [ ] Chat works end-to-end.
- [ ] Agent registry loads.
- [ ] Model configuration is valid.
- [ ] Tools/MCP execute through explicit contracts.
- [ ] Memory persists and retrieves correctly.

## Gate 5 — Producer Intelligence Loop

- [ ] Upload.
- [ ] Analyze.
- [ ] Normalize.
- [ ] Audio Analyst.
- [ ] Producer Intelligence.
- [ ] Memory.
- [ ] Retrieve.

## Gate 6 — Quality / Security

- [ ] Unit tests pass.
- [ ] Integration tests pass.
- [ ] Critical end-to-end tests pass.
- [ ] No known critical security issue remains.
- [ ] Secrets are not committed or exposed.
- [ ] Failure handling and observability are adequate.

## Gate 7 — Deployment

- [ ] Production configuration is documented.
- [ ] Deployment path is reproducible.
- [ ] Health checks exist.
- [ ] Rollback procedure exists.
- [ ] Monitoring/error reporting is available.

## Release Rule

Production readiness is **NOT CERTIFIED** until all required gates have current executable evidence. Do not infer readiness from historical completion reports.
