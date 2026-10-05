# OHIS Selective Recovery — 2026-10-05

Source branch: `feat/ohis-foundation-v1`
Source branch state versus canonical main at recovery start: 11 commits ahead / 47 behind.
Canonical parent: `19ff3b7648c49f3f81b82dcc5e445028719edaba`

## Recovery method

This branch does **not** merge or rebase the divergent OHIS history.

Only the unique OHIS doctrine/schema files identified by compare analysis are transplanted onto the current canonical Sonic main tree by blob provenance. Historical code/configuration from the divergent branch is intentionally excluded.

## Recovered surfaces

- OHIS ontology
- naming standard
- color/routing standard
- filesystem standard
- asset metadata contract
- lifecycle/provenance standard
- Sonic integration doctrine
- implementation roadmap
- OHIS README
- asset JSON schema
- future intent/memory/DNA architecture reference

## Validation rule

Documentation/schema recovery is not equivalent to runtime implementation. Any future code claiming OHIS compliance must be validated independently against these contracts.
