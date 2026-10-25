# Omega House OS → Sonic AI V3: Connected Repository Contract Gate

Status: PROPOSED / REVIEW REQUIRED
Date: 2026-10-25
Change type: Documentation-only; no runtime loading, deployment, or private-source import.

## Repository boundaries

- Canonical governance source: private `cryptik093-pixel/OMEGA-HOUSE-OS`.
- Sonic application: `cryptik093-pixel/sonic-ai-v3`.
- Never vendor, mirror, publish, or copy private OS source into this public repository.
- Sonic may consume only explicitly reviewed and approved public-safe contracts. A reference to an OS commit is not permission to disclose its contents.

## Pinned provenance (audit snapshot)

- OS main: `28bb3605c67d5b744d583ea6d3ce652966346fa1`.
- Sonic V3 main at audit: `7d2a2b90d9ab730790aa28b3cfaf1b9faf797a43`.
- Existing Sonic references: `docs/operating-system/FOUNDER_ONBOARDING.md` and `docs/operating-system/founder_contract_reference.json`. These remain authoritative for previously adopted references; do not replace their pins without review.

## Approval and validation workflow

1. Review OS canonical contract changes privately against the pinned OS commit.
2. Classify each field as public-safe, private, secret, or uncertain; default uncertain to excluded.
3. Produce a minimal, separately approved export with schema version, source commit, digest, ownership, and explicit public-disclosure approval.
4. Verify export against an allowlisted schema, test fixtures, and SHA-256 integrity. Reject unknown fields, credentials, customer information, private paths, and unapproved content.
5. Open a separate PR containing only approved export material and tests. Require human review before merge.
6. Runtime contract loading and enforcement are out of scope until separately implemented and tested.

## Acceptance criteria

- Both Git repositories and histories remain separate.
- No private OS files, tokens, or personal/customer data are included.
- No runtime changes or deployments.
- Any future integration is opt-in, versioned, reproducible, and fails closed on invalid contracts.

## Related approved architecture

Omega House OS governs operations; Sonic AI V3 implements production workflows; Sonic Intelligence records evidence and decisions. This document does not claim those handoffs are live.
