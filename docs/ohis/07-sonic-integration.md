# OHIS-07 — Sonic AI Integration

## Role

OHIS supplies Sonic AI with a stable creative-world representation. Sonic is the intelligence layer; OHIS is the organizational and semantic contract it reasons over.

## Target pipeline

```text
FILE / DAW EVENT
      ↓
INGEST
      ↓
IDENTIFY
      ↓
ANALYZE
      ↓
NORMALIZE
      ↓
OHIS RECORD
      ↓
PROVENANCE GRAPH
      ↓
MEMORY / KNOWLEDGE
      ↓
RETRIEVAL
      ↓
AGENT REASONING
      ↓
RECOMMENDATION / APPROVED ACTION
```

## Deterministic vs inferential data

### Deterministic

Examples:

- duration
- sample rate
- bit depth
- channels
- file hash
- BPM when read from a trusted DAW/project source
- MIDI note data
- filename
- Asset ID
- explicit routing information from a supported DAW integration

### Inferential

Examples:

- mood
- perceived warmth
- similarity
- creative intent
- likely use case
- stylistic relationships

Inferential values require confidence and provenance.

## Relevance checkpoint

After every meaningful state-changing operation, Sonic should evaluate whether new information materially changes the current creative context.

```text
ACTION
 ↓
OBSERVE NEW STATE
 ↓
VALIDATE
 ↓
RELEVANCE SCORE
 ↓
PERSIST HIGH-VALUE STATE
 ↓
UPDATE CONTEXT / CREATOR DNA
```

This prevents memory from becoming an indiscriminate event dump.

## Creator DNA

OHIS provides grounded evidence from which Sonic can reconstruct evolving producer patterns.

Potential evidence:

- repeated sound selections
- accepted/rejected recommendations
- recurring BPM/key ranges
- processing choices
- favorite chains
- project structures
- naming language
- asset ratings
- pack composition decisions

Creator DNA is a derived intelligence layer, not a replacement for authoritative asset records.

## Agent boundary

Agents must not bypass OHIS to mutate canonical asset state.

Preferred pattern:

```text
Agent
 ↓
Tool
 ↓
Domain Service
 ↓
Validation
 ↓
State Mutation
 ↓
Event
 ↓
OHIS / Memory Update
```

## Future implementation targets

1. File scanner and metadata extractor.
2. Canonical Asset ID service.
3. Naming normalizer.
4. OHIS metadata persistence.
5. DAW project/routing parser where technically supported.
6. Provenance graph.
7. Semantic search over assets.
8. Quality/rating evidence model.
9. Producer pattern extraction.
10. Controlled workflow automation.
