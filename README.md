# Sonic AI V3

**Sonic AI V3 is the intelligence layer for a producer operating system.**

It is being built as a persistent, testable, deployable platform that combines a producer workspace, audio/asset intelligence, structured memory, event-driven workflows, and an agent layer capable of analyzing work, retrieving context, making recommendations, and eventually executing approved actions.

> **Canonical repository:** `cryptik093-pixel/sonic-ai-v3`
>
> **Primary branch:** `main`
>
> **Current objective:** recover and maintain a canonical, bootable, testable, deployable Sonic AI V3 platform without losing the frontend, backend, chat pipeline, memory, or agent architecture.

---

## Product Vision

Sonic AI V3 is not intended to be a generic chatbot. It is an intelligence system built around the producer's actual creative workflow and accumulated data.

The long-term loop is:

```text
Producer
   ↓
Workspace / Chat
   ↓
Projects + Audio + Assets
   ↓
Deterministic Analysis
   ↓
Producer Intelligence
   ↓
Memory + Knowledge
   ↓
Agent Reasoning
   ↓
Recommendations / Actions
   ↓
New Events + Outcomes
   ↺
```

The system should become more useful as the producer uploads more work, records more decisions, completes more workflows, and generates more measurable outcomes.

---

## Core System

Sonic AI V3 is organized as a monorepo with application services and shared domain packages.

```text
apps/
  web/              Producer-facing frontend
  api/              FastAPI application/API layer
  worker/           Background and event-processing workers

packages/
  common/           Shared types and utilities
  events/           Event contracts and event infrastructure
  auth/             Authentication/domain helpers
  projects/         Project domain
  assets/           Audio/asset domain
  metadata/         Deterministic metadata contracts and processing
  memory/           Activity, memory, and retrieval contracts
  vault/            Asset/vault search contracts

aInfrastructure/
  docker/           Local infrastructure assets
  supabase/         Database/auth configuration

docs/
  architecture/     Architecture and system design
  rfc/              Product and technical RFCs
  operating-system/ Human/AI operating and documentation protocols

*.md                Audit, readiness, milestone, health, and recovery reports
```

### Runtime responsibilities

| Layer | Responsibility |
|---|---|
| **Web** | Producer UI, projects, uploads, vault, activity, chat and intelligence surfaces |
| **API** | Authentication-aware application boundary, domain APIs and orchestration |
| **Worker** | Background processing, durable event handling and asynchronous jobs |
| **Packages** | Shared contracts so services agree on the same domain model |
| **Memory** | Persistent context, activity history and retrieval primitives |
| **Agent layer** | Reasoning, tool use, planning and controlled execution |
| **Infrastructure** | Database, authentication, local development and deployment support |

---

## Foundational Operating Protocols

Sonic AI V3 now treats the human-AI collaboration loop and its documentation model as first-priority operating architecture.

### `LOCK` — execution checkpoint

`LOCK` means:

```text
RE-GROUND
  ↓
VALIDATE
  ↓
OPTIMIZE
  ↓
ALIGN
  ↓
CHECKPOINT
  ↓
ADVANCE
```

It is not a request for reassurance. It requires the current state to be re-evaluated before the next action is selected. Completion claims must be distinguished as **PROVEN**, **SUPPORTED**, or **PROPOSED** according to their evidence level.

### Human + machine documentation

Sonic maintains two complementary documentation layers:

- **Markdown / human layer:** architecture, rationale, procedures, audits, decisions, and strategic context.
- **Machine-readable layer:** YAML/JSON/JSON Schema/typed contracts for deterministic state, rules, interfaces, validation, and agent execution.

Neither layer replaces the other. Runtime behavior remains authoritative for what the system actually does; machine contracts define deterministic interfaces; Markdown preserves human rationale and operating context.

Canonical protocol documents:

- `docs/operating-system/COLLABORATION_PROTOCOL.md`
- `docs/operating-system/DOCUMENTATION_PROTOCOL.md`
- `docs/operating-system/collaboration_protocol.yaml`

The same checkpoint principle is intended to govern Sonic's internal intelligence loop: meaningful state changes should trigger reassessment, relevance evaluation, durable state preservation, and selection of the next appropriate action rather than blind continuation.

---

## Producer Intelligence Architecture

The foundational intelligence path is designed as a vertical slice:

```text
UPLOAD
  ↓
ANALYZE
  ↓
NORMALIZE
  ↓
AUDIO ANALYST
  ↓
PRODUCER INTELLIGENCE
  ↓
MEMORY
  ↓
RETRIEVE
  ↓
ACT
```

This architecture separates deterministic computation from model reasoning. Audio facts, metadata, events, identifiers and system state should be generated from reproducible application logic wherever possible. Models should reason over structured evidence rather than becoming the source of truth for system state.

---

## Event-Driven Foundation

Important business and creative actions are represented as structured events. Examples include:

- `product_viewed`
- `add_to_cart`
- `checkout_started`
- `order_created`
- `refund`
- `customer_updated`
- project creation
- asset upload
- metadata extraction
- vault activity
- producer profile updates

The event layer is intended to support both real-time processing and batch/replay workflows.

The long-term intelligence system can consume these events to understand:

- what happened
- when it happened
- which entity changed
- what caused the action
- what outcome followed
- what should happen next

---

## Chat + Agent Layer

Chat is a first-class interface to the system, not a separate chatbot bolted onto the application.

The target architecture is:

```text
Chat UI
  ↓
Conversation / Context Manager
  ↓
Agent Registry
  ↓
Model Configuration
  ↓
Tool / MCP Boundary
  ↓
Application Services
  ↓
Events + Memory
  ↓
Observed Result
```

Agents should operate through explicit tools and contracts. They should not directly mutate arbitrary application state or bypass domain boundaries.

The system is being developed toward a registry-driven agent architecture so agents, tools, models, permissions and execution policies remain inspectable and testable.

---

## Memory + Knowledge

Sonic AI V3 treats memory as infrastructure.

Memory should distinguish between:

1. **System state** — authoritative records such as projects, assets, users and orders.
2. **Activity history** — what the user or system did.
3. **Structured knowledge** — normalized facts derived from assets, projects and workflows.
4. **Long-term producer context** — durable preferences, patterns and decisions.
5. **Retrieval context** — the bounded information supplied to an agent for a particular task.

The goal is persistent intelligence without allowing conversational context to become the database.

---

## Current Development Priorities

### Phase 0 — Trust the foundation

- Canonicalize the repository and branch state.
- Verify frontend/backend boot paths.
- Verify environment configuration.
- Verify API contracts.
- Verify agent registry and model configuration.
- Verify MCP/tool boundaries.
- Establish reliable tests and health checks.

### Phase 1 — Producer Intelligence Loop

Build and validate the complete vertical slice:

```text
Upload → Analyze → Normalize → Audio Analyst
→ Producer Intelligence → Memory → Retrieve
```

### Subsequent phases

Expand the intelligence layer into project assistance, creative analysis, workflow automation, business intelligence, and controlled autonomous execution while preserving deterministic state and human approval boundaries.

---

## Development Requirements

Recommended baseline for the current repository:

- Node.js 20+
- pnpm 10+
- Python 3.12+
- PostgreSQL 15+
- Git

> Use the versions declared by the repository's package/tool configuration when they are more specific than these minimums.

---

## Local Bootstrap

From the repository root:

```bash
corepack enable
pnpm install
```

Create the local environment from the example configuration when needed:

```bash
cp .env.example .env
```

On Windows PowerShell, use:

```powershell
Copy-Item .env.example .env
```

Start the development workspace using the repository's current package scripts:

```bash
pnpm dev
```

The frontend and backend should be validated independently as well as through the integrated development path. Do not treat a successful frontend boot as proof that the complete platform is healthy.

---

## Verification Standard

A change is not considered complete merely because it compiles.

Minimum verification should cover the affected layer:

```text
Install
  ↓
Type / Syntax Validation
  ↓
Unit Tests
  ↓
Integration Tests
  ↓
API / Contract Checks
  ↓
Frontend Boot
  ↓
Backend Boot
  ↓
End-to-End Critical Path
```

For recovery work, the critical path is:

```text
Repository → Web → API → Database/Auth → Chat → Agent/Tools
```

Any broken dependency in that chain must be recorded explicitly rather than hidden behind a green-looking frontend.

---

## Recovery / Audit Documents

The repository contains dedicated reports for diagnosing and recovering the platform, including:

- `SONIC_AI_V3_HEALTH_MAP.md`
- `BOOT_FAILURE_REPORT.md`
- `FRONTEND_FAILURE_REPORT.md`
- `RUNTIME_FAILURES.md`
- `CRITICAL_BLOCKERS.md`
- `LAUNCH_BLOCKERS.md`
- `PRODUCTION_CHECKLIST.md`
- `PRODUCTION_READINESS_REPORT.md`
- `ALPHA_DEPLOYMENT_READINESS.md`
- `FINAL_AUDIT_REPORT.md`
- `PROJECT_AUDIT.md`
- `SPRINT_1_COMPLETION_SUMMARY.md`
- `PHASE_4_COMPLETION_REPORT.md`
- `PHASES_5_7_IMPLEMENTATION_REPORT.md`
- `PHASE_6_7_IMPLEMENTATION_REPORT.md`

These documents are evidence and diagnostics. The source code, tests, configuration and runtime behavior remain the authoritative implementation state.

---

## Engineering Principles

### 1. Deterministic before generative

If a fact can be computed reliably by software, compute it deterministically before asking a model to infer it.

### 2. Contracts before convenience

Shared schemas, events, APIs and tool contracts prevent individual services from silently developing incompatible assumptions.

### 3. Memory is infrastructure

Persistent memory must be structured, scoped and retrievable. Conversation history alone is not an intelligence architecture.

### 4. Agents operate through tools

Agents should reason, plan and execute through explicit capabilities with permissions, observability and failure handling.

### 5. Evidence over claims

Health, readiness and completion states must be supported by tests, logs, runtime checks or other reproducible evidence.

### 6. Recovery preserves capability

When repairing the platform, restore the existing architecture before replacing it. Do not delete functional frontend, backend, chat, memory or agent capabilities merely because one layer is currently failing.

### 7. Main is canonical

The `main` branch is the canonical product baseline. Experimental work should be isolated in feature/recovery branches and merged only after verification.

---

## Security

Never commit real credentials, API keys, access tokens, private keys or production secrets.

Use `.env` for local secrets and `.env.example` for documented configuration shape.

See `SECURITY.md` for repository-specific security guidance.

---

## Project Status

**Sonic AI V3 is under active development and recovery toward a canonical bootable platform.**

The repository should be evaluated by actual runtime capability, tests and verified integration paths—not by the presence of documentation or historical completion reports.

The immediate engineering objective is simple:

> **Restore the complete Sonic AI V3 system as one coherent, bootable, testable platform, then continue advancing the intelligence loop without losing the foundation.**
