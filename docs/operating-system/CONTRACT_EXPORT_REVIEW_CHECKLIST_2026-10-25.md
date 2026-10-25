# OS-to-Sonic contract export: review checklist

Status: LOCKED DESIGN / IMPLEMENTATION PENDING
Date: 2026-10-25

## Immutable boundaries

The private OMEGA-HOUSE-OS repository remains the canonical governance source. Sonic AI V3 remains the implementation repository. No private OS source, unreviewed contracts, secrets, customer data, or access tokens may be committed to Sonic.

## Existing adoption

The already adopted `docs/operating-system/founder_contract_reference.json` pins founder contract v1.1.0 at OS commit `5c23649207b6933a960b640ddc10b116106a5fa7` with SHA-256 `07f190c5c4172deaaa163761c73f5ac6ae4c33bb838814c0f3ac7e59bda48a7b`. Do not silently advance that pin to OS main.

## Export acceptance gate

- [ ] Private-source owner reviews field-level public disclosure and records approval.
- [ ] Only allowlisted non-sensitive fields exported; unknown fields rejected.
- [ ] Contract schema and canonical serialization specified.
- [ ] Full SHA-256 of approved exported bytes checked against an independently reviewed manifest.
- [ ] Negative tests: modified digest, unexpected fields, missing required fields, unsupported version, malformed JSON, and accidental sensitive fields.
- [ ] No network access or implicit fallback to OS main in validation or runtime.
- [ ] Reviewer verifies the diff contains no private OS material.
- [ ] CI green and designated reviewer approves PR before merge.
- [ ] Runtime loader/enforcement remains a separately authorized implementation with fail-closed tests.

## Evidence

At the preceding integration commit `67b97b2b531f01fcb75ebc14f2ee9d0c82e6f7a6`, GitHub reported CI, Runtime baseline, and Veracode workflows completed successfully. These are workflow conclusions, not proof of full contract enforcement.

## Rollback

Revert integration PR commits; no migration of private source, production deployment, or installed plugin binaries is authorized.
