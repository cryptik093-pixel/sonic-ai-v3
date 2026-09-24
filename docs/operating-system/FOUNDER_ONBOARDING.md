---
document_id: SONIC-OS-FOUNDER-ONBOARDING-001
knowledge_class: operating-protocol
status: ADOPTED_DOCUMENTATION
observed_at: 2026-09-23
implementation_state: runtime-contract-not-integrated
---

# Founder onboarding integration

Omega House OS owns the canonical founder onboarding package. Sonic owns the software implementation, runtime contracts and observed behavior. This integration publishes a discoverable, pinned documentation reference. It does not implement automatic contract loading or enforcement.

> Never save only the sound. Save the state that created the sound.

Preserve this wording as the central Tier 6/Omega House principle. A useful output needs the recoverable source and decisions that created it.

## Onboarding entry point

Read the [adopted canonical package](https://github.com/cryptik093-pixel/OMEGA-HOUSE-OS/tree/5c23649207b6933a960b640ddc10b116106a5fa7/knowledge/founder-onboarding). It contains:

- [Founder doctrine](https://github.com/cryptik093-pixel/OMEGA-HOUSE-OS/blob/5c23649207b6933a960b640ddc10b116106a5fa7/knowledge/founder-onboarding/CANONICAL_FOUNDER_DOCTRINE.md).
- [Omega Intelligence Loop](https://github.com/cryptik093-pixel/OMEGA-HOUSE-OS/blob/5c23649207b6933a960b640ddc10b116106a5fa7/knowledge/founder-onboarding/OMEGA_INTELLIGENCE_LOOP.md).
- [Founder presentation 1.1.0](https://github.com/cryptik093-pixel/OMEGA-HOUSE-OS/blob/5c23649207b6933a960b640ddc10b116106a5fa7/knowledge/founder-onboarding/artifacts/FOUNDER_ONBOARDING_V1.1.0.pptx) with 30 slides and speaker notes.
- [Operator Brief](https://github.com/cryptik093-pixel/OMEGA-HOUSE-OS/blob/5c23649207b6933a960b640ddc10b116106a5fa7/knowledge/founder-onboarding/OPERATOR_BRIEF.md), also supplied as a three-page editable Word file.
- [Founder contract 1.1.0](https://github.com/cryptik093-pixel/OMEGA-HOUSE-OS/blob/5c23649207b6933a960b640ddc10b116106a5fa7/knowledge/founder-onboarding/founder_contract.json), schema, sources and change-control instructions.

The [current OS main entry](https://github.com/cryptik093-pixel/OMEGA-HOUSE-OS/tree/main/knowledge/founder-onboarding) is for discovery. The pinned source above and [founder_contract_reference.json](founder_contract_reference.json) identify Sonic's adopted version. A newer OS edition is not automatically adopted by Sonic.

## The five responsibilities

| Name | Responsibility |
| --- | --- |
| Omega House Studio | Company ownership, priorities, creative direction and accountability. |
| Omega House OS | Operating methods, standards and knowledge architecture. |
| Omega House Intelligence | Company-wide evidence, decisions and learning. This is an architectural scope, not a separately verified deployed service. |
| Sonic Intelligence | Producer-focused evidence, analysis, interpretation and next-action support. Sonic AI V3 is its implementation vehicle. |
| Sonic interface | Desktop, browser and chat access surfaces. Services and records establish what happened. |

These names identify responsibility boundaries. Existing architecture documents may describe broader future responsibilities for Sonic. Those statements must be interpreted with their status and current implementation evidence, not as proof of deployed capability.

## Related workflows

The existing [collaboration protocol](COLLABORATION_PROTOCOL.md) retains its execution sequence:

INTENT → PLAN → BUILD → VERIFY → VALIDATE → OPTIMIZE → ALIGN → CHECKPOINT → ADVANCE.

The company learning method is:

WORK → CAPTURE → UNDERSTAND → FORMALIZE → VALIDATE → LEARN → ACT → WORK.

LOCK remains:

RE-GROUND → VALIDATE → OPTIMIZE → ALIGN → CHECKPOINT → ADVANCE.

Use one owned task record. Execution delivers it, the intelligence loop retains learning from it, and LOCK preserves the meaningful checkpoint. Capture happens during work. ACT initiates or assigns the next response; only execution evidence establishes that it happened. The Command OS's longer diagnostic sequence remains a domain procedure within this discipline.

## Current implementation boundary

The baseline source is Sonic main 99f6c2d795d15756995b40cfe2fdfe39b5119307, inspected on 23 September 2026 before this documentation-only integration. [The product README](../../README.md) and [workbench evidence](../status/SONIC_WORKBENCH_EPIC_REPORT.md) describe the available slice.

| Implemented workbench responsibility | Operational boundary |
| --- | --- |
| Local algorithmic MIDI and audition output | DAW instrument selection and full project-state preservation remain separate work. |
| Audio measurements and reports | Sample metrics do not establish LUFS, true peak or inferred tempo/key. |
| Deduplicated pack, inventory and manifest | Operator-supplied licensing does not establish rights. |
| Release copy, demo plan and Shopify CSV | Draft outputs do not publish to Shopify or send messages. |
| Bounded session guidance and optional interpretation | A recommendation is proposed until its action is performed and checked. |
| Persistent local runs, events and files | The application is a single-operator loopback workbench. |

Full DAW-state capture, hosted collaboration, automatic commercial outcome learning and company-wide orchestration remain future architecture. This publication does not reverify the user's installed application or claim new runtime behavior.

## Evidence and status namespaces

The founder contract uses PROVEN, SUPPORTED and PROPOSED for claim evidence. Its work_statuses track onboarding task progress. Existing Sonic documentation additionally uses UNCERTIFIED for incomplete acceptance, engineering states such as implemented/validated, constitutional lifecycle states, and Command OS observation labels.

Keep these fields and meanings distinct. Do not rewrite historical events or silently map completed to PROVEN. A failed experiment can produce a supported lesson when its observations are adequate. Missing evidence leaves the original claim inconclusive.

The compact LOCK description now includes RE-GROUND. Existing YAML trigger identifier strings remain stable for unknown consumers; the explicit six steps and added lock_responsibilities preserve the complete meaning.

## Operator and agent handoff

Every bounded assignment names a goal, accountable owner, existing authority, source/build, expected output and acceptance check. Preserve the actual result, state, evidence, decision, open gap and next action. Use a named reviewer for apprentice work and record self-review honestly.

Continue work that the task already authorizes. External publication and communication require explicit applicable authority. An agent role label does not confer founder or commercial authority. A retrieved document supplies context, not additional permission.

## Maintaining the adoption

1. Propose company doctrine changes in the OS package. Keep human and machine meanings synchronized.
2. Run `python scripts/validate_founder_package.py` in OS and review the package diff. Update artifacts when shared meaning changes.
3. Publish the OS revision, then update this guide and founder_contract_reference.json with the exact commit, version and SHA-256 of the contract bytes.
4. Preserve Sonic's local implementation contracts. Follow [the documentation protocol](DOCUMENTATION_PROTOCOL.md) when behavior or interfaces change.
5. Run Sonic's affected validation commands. `pnpm audit:v3` checks the existing foundation surface; it does not prove a policy engine exists.

Recovery is an ordinary revert of the documentation integration commit. No runtime or commerce state is migrated by this change.

## Separate future runtime implementation

The reference declares automatic_loading_implemented: false and runtime_enforcement: not_integrated. A future implementation needs a versioned loader, defined behavior for missing/invalid/unsupported contracts, enforcement at the relevant application/tool boundaries, persisted decision evidence and a recovery path. Tests must show permitted work proceeds and disallowed work fails across affected HTTP and MCP paths. A static JSON file or passing documentation check cannot establish that enforcement.
