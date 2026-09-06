# Parallel Agent Workstreams

## Purpose
Use Codex parallelism without allowing agents to collide on the same code surfaces.

## Proposed workstreams

```text
AGENT A — Repository Guardian
tests
CI
repository integrity
regression detection

AGENT B — Sonic Intelligence
decisions
confidence
provenance
evidence
memory

AGENT C — Producer Intelligence
audio analysis
metadata
recommendations
project intelligence

AGENT D — Commerce Intelligence
Shopify
products
conversion
orders
revenue signals

AGENT E — MCP Infrastructure
tools
resources
agent communication
permissions

AGENT F — Frontend
dashboard
projects
assets
intelligence visualization
```

## Ownership contract example

```yaml
agent: producer-intelligence

owns:
  - apps/api/services/audio/**
  - apps/api/services/producer/**
  - apps/api/schemas/audio/**

may_read:
  - apps/api/**
  - docs/**

may_not_modify:
  - infrastructure/**
  - commerce/**
  - frontend/**
```

## Rule
Parallel agents may share context, but should not share uncontrolled write ownership.
