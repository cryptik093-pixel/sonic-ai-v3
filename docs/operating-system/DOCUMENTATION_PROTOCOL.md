# Sonic AI V3 Documentation Protocol

**Status:** LOCKED  
**Scope:** Sonic AI V3 + Omega House Intelligence architecture

## Purpose

Sonic maintains two complementary documentation surfaces because humans and software agents consume information differently.

Documentation is therefore treated as an architectural interface, not merely project notes.

## Two-Layer Documentation Model

### Layer H — Human-readable Markdown

Markdown is the canonical surface for people.

Use it for:

- architecture explanations
- decisions and rationale
- operating procedures
- implementation guides
- milestones
- audits
- recovery reports
- onboarding
- human review
- strategic context

Human documentation should optimize for clarity, hierarchy, narrative context, and decision comprehension.

### Layer M — Machine-readable contracts

Structured files such as JSON, YAML, JSON Schema, or typed source contracts are the canonical surface for software and agents where deterministic parsing is required.

Use them for:

- protocol definitions
- event contracts
- state models
- agent capabilities
- tool contracts
- policy rules
- checkpoints
- workflow definitions
- machine-verifiable configuration
- status and evidence fields
- identifiers and relationships

Machine-readable documentation should optimize for deterministic parsing, validation, versioning, and execution.

## Relationship Between Layers

The two layers are complementary, not competing.

```text
Human Markdown
     ↕
Meaning / rationale / operating context
     ↕
Machine-readable contract
     ↕
Schemas / state / rules / execution
     ↕
Runtime behavior
     ↕
Evidence
     ↺
```

When both describe the same system behavior, they must not silently disagree.

## Source-of-Truth Rules

1. **Runtime state is authoritative for what the system actually does.**
2. **Machine-readable contracts are authoritative for deterministic interfaces and validation rules.**
3. **Markdown is authoritative for human rationale, operating procedures, and explanatory context.**
4. When a machine contract changes behavior, the relevant human documentation must be updated in the same change set when practical.
5. When a Markdown document proposes behavior that is not implemented, it must be clearly marked as proposed, planned, or target behavior.
6. Documentation must never be used to conceal an unverified implementation state.

## Agent Consumption Rules

Agents should prefer machine-readable contracts when making deterministic decisions and use Markdown when they need rationale, context, operating guidance, or architectural intent.

An agent should not infer an executable contract solely from prose when a structured contract exists.

Conversely, an agent should not discard architectural rationale simply because it is not represented in a schema.

## Checkpoint Integration

Every meaningful architecture or workflow milestone should be capable of producing:

- a human-readable explanation of the milestone
- machine-readable state/evidence where deterministic tracking is required
- a provenance reference to the implementation or event that produced the state

This makes documentation part of the intelligence loop rather than a separate after-the-fact activity.

## Quality Gate

Before considering a foundational architecture change complete, ask:

```text
Is the behavior implemented?
Is the behavior testable?
Is the deterministic contract represented structurally?
Is the human rationale documented?
Can an agent discover and interpret the state?
Can a human understand why it exists?
Can the system recover the relevant state later?
```

If any answer is no, the documentation/architecture milestone is not fully closed.
