# Machine-Readable Agent Result

## Purpose
Turn agent output into state Sonic can consume instead of relying on conversational claims.

```json
{
  "task_id": "SONIC-042",
  "agent": "codex",
  "objective": "implement producer intelligence event",
  "status": "validation_failed",
  "files_created": [],
  "files_modified": [],
  "tests": {
    "passed": 25,
    "failed": 2
  },
  "validation": {
    "repository_integrity": false,
    "feature_contract": true
  },
  "commit_allowed": false,
  "evidence": [],
  "recommended_next_action": ""
}
```

## Status principle
`validation_failed` can represent correct system behavior when the agent successfully detects a failed gate and refuses unsafe promotion.
