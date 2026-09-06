# Sonic Execution Contract Template

## Purpose
Translate strategy and intent into an implementation contract before Codex changes code.

```text
GOAL
[What measurable outcome must exist?]

WHY
[Why does this capability need to exist?]

SUCCESS CONDITION
[Observable definition of success.]

INPUTS
[Required data, paths, schemas, services, or state.]

OUTPUTS
[Expected artifacts, APIs, JSON, files, events, or UI.]

CONSTRAINTS
- preserve existing work
- no destructive git operations
- no commit on validation failure
- tests required
- do not expand scope without evidence

VALIDATION
[Tests, builds, audits, contracts, regression checks.]

FAILURE BEHAVIOR
- fail closed
- record evidence
- do not commit/push when gates fail
- return exact blocker and recommended next action
```

## Example
```text
GOAL
Make Sonic automatically validate repository integrity.

WHY
Autonomous agents cannot safely modify Sonic if repository state cannot be independently verified.

SUCCESS CONDITION
A deterministic Repo Guardian returns structured validation results.

INPUTS
repository path
baseline
validation policy

OUTPUTS
RepoGuardianResult JSON

VALIDATION
backend tests
frontend tests
repository integrity
manifest validation
```
