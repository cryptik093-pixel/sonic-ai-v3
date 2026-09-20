# Sonic v3.5 — progressive state

## What this version means
A clean operational starting point on the existing architecture. Version 3.5 names the
new foundation; it does not certify a complete application. The original documents,
domain packages, production doctrine and audio fixtures remain available.
Source baseline: `main@dd0af2ee1efefab0d884be58206dd756b169b0d1`, inspected 2026-09-20.

## Current evidence
Web, API and worker each contain only a package manifest on this baseline.
Audio measurement, defect-taxonomy and metadata-envelope Python code exists.
The former `audit:v3` command refers to a missing script. Recovery-branch and Windows
runtime claims are not evidence for this main-branch checkout. No database contents
were inspected or migrated. No public endpoint or production connection is validated.
Machine-readable component state: [sonic-state.json](sonic-state.json).

## Progress gates
| Gate | Acceptance evidence | State |
|---|---|---|
| 0 — Clean contract foundation | docs, registry, local MCP protocol tests | locally verified |
| 1 — Application foundation | API/web boot, auth denial and cross-owner isolation tests | open |
| 2 — Producer loop | upload → measurement → interpretation → memory → retrieval test | open |
| 3 — Agent execution | explicit models, scoped tools, durable handoffs and failure tests | open |
| 4 — Remote MCP | authenticated transport, tenant isolation, timeout and revocation tests | open |
| 5 — Release | integrated critical path, rollback, deployment evidence | open |

## Next action
Compare the recovery branch against this baseline and recover the API/auth vertical slice
with tests. Do not overwrite the existing local Windows project or merge unverified bulk recovery.

## Update rules
Append milestones below with date, changed capability, commands, results and limitations.
Update the JSON snapshot in the same commit. Never relabel historical audits as current proof.
Supersede claims explicitly. MCP reads this snapshot; it does not probe deployed services.

## Milestones
- 2026-09-20: v3.5 foundation initiated from the inspected main baseline, by Daniel's request.

- 2026-09-20: MCP validation: 4 tests passed, including actual stdio initialize,
  tool discovery and invocation, rejected unknown command, repeated reads,
  missing/corrupt/schema-invalid records and symlink denial. Python 3.12, mcp 1.30.0.
- 2026-09-20: Existing audio suite: 20 tests passed (measurement, golden fixtures,
  defect taxonomy, metadata lineage). No application or deployment claim follows.
- 2026-09-20: Daniel reported a possible local/Git overwrite. Cause remains UNKNOWN.
  Verified retained API/domain source at recovery/actual-project-state@50592e982b5a4ffb9c8c4dc367c6da4c89b298b8.
  A second candidate is recovery/runtime-baseline-integration@2625eaee5304de474a5271646b70bce895d58c4b.
  No recovery branch was merged or modified. Local Windows reflog and working tree remain uninspected.
