# Codex Repository Orientation Prompt

## Purpose
Force repository truth discovery before modification.

## Prompt

```text
SONIC AI V3 — REPOSITORY ORIENTATION

You are operating inside the Sonic AI V3 production repository.

Do not modify anything yet.

1. Inspect:
   - git status
   - current branch
   - recent commits
   - repository structure
   - AGENTS.md / README / architecture docs
   - test configuration
   - backend/frontend entry points
   - existing MCP/plugin/agent infrastructure

2. Identify:
   - current known-good state
   - dirty/untracked files
   - unfinished implementations
   - failing tests
   - architectural conflicts
   - existing functionality relevant to the next task

3. Do not overwrite existing work.

4. Produce:

REPOSITORY_STATE
CURRENT_BRANCH
DIRTY_STATE
RELEVANT_ARCHITECTURE
KNOWN_FAILURES
SAFE_CHANGE_SURFACE
RECOMMENDED_NEXT_ACTION

Do not implement until the intended change has been validated.
```

## Gate
No implementation begins until repository state and safe change surface are explicit.
