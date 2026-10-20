OMEGA HOUSE / THE TRIBE

# Tribal Network(TM): Concept-to-Build Benchmark and Design Comparison Standard

A permanent comparison framework for measuring each real build against the intended final system.

| DOCUMENT CLASS Build Benchmark / Design Control | DATE October 6, 2026 | STATUS Working Canon / Version 1.0 |
| --- | --- | --- |
| PURPOSE Never confuse "what we can build today" with "what the product ultimately is." This benchmark preserves the final conceptual build and creates a disciplined way to measure progress toward it. |
| --- |

## 1. Two-layer documentation model

| Layer | What it contains | Change policy |
| --- | --- | --- |
| North-Star Specification | The intended final product: principles, full capability model, experience goals, architectural boundaries, and definition of done. | Changes only through explicit design decision with rationale. Never silently reduced to match current limitations. |
| Current Build Record | What actually exists today: screens, routes, schemas, integrations, behavior, tests, known defects, and evidence. | Updated continuously as implementation changes. Must be evidence-backed. |

A third layer - the Gap Ledger - compares the two and becomes the source for prioritized build work.

## 2. Status vocabulary

| Status | Meaning |
| --- | --- |
| NORTH-STAR | Required or desired behavior in the intended final system. |
| DESIGNED | Specified clearly enough to implement, but not yet proven in software. |
| IMPLEMENTED | Code/UI/data behavior exists, but may not yet be validated against acceptance criteria. |
| VERIFIED | Observed in the running product and supported by tests, screenshots, data, or reproducible evidence. |
| PARTIAL | Some required behavior exists; meaningful gaps remain. |
| BLOCKED | Known dependency prevents completion. |
| DEFERRED | Intentionally postponed without changing the North-Star requirement. |
| REJECTED | Explicitly removed from the target with recorded design rationale. |

## 3. Comparison dimensions

Every major build review should score the real product against the final intent across the following dimensions. A build can look polished while still being conceptually incomplete, so visual quality is only one dimension.

| Dimension | North-Star question |
| --- | --- |
| Identity | Does the system model a member as an evolving creative identity rather than a static profile card? |
| Project structure | Can serious work be represented as connected project objects with history, people, assets, evidence, releases, and outcomes? |
| Cross-station continuity | Can activity from the other stations become Tribal Network intelligence without duplicate manual reconstruction? |
| Career visualization | Can the member visually understand what they are building and how their career/work is changing over time? |
| Sonic Intelligence | Can intelligence reason over grounded, permissioned history and point back to evidence? |
| Collaboration | Can the Tribe understand who can contribute what, to which projects, with what history and availability? |
| Guild utility | Does the collective network materially improve discovery of capabilities, services, assets, knowledge, or opportunities? |
| Evidence / provenance | Can important claims be traced to attributable work, activity, or outcomes? |
| Metrics | Are metrics useful for development and decisions rather than vanity competition? |
| Creative freedom | Does the system minimize administrative friction and preserve experimentation? |
| Privacy / permissions | Is unfinished/private developmental work appropriately protected? |
| Initiation / development | Can the system support light cyclical reflection and transition without forcing a rigid ladder? |
| UX / spatial feel | Does the interface remain open, calm, premium, compact, and navigable despite information density? |
| Engineering maturity | Are schemas, events, permissions, testing, observability, migrations, and performance strong enough to sustain the model? |

## 4. Scoring rubric

| Score | Interpretation |
| --- | --- |
| 0 - Absent | No meaningful implementation. |
| 1 - Mocked | Visual/static representation with little or no real system behavior. |
| 2 - Functional fragment | One useful behavior works but lacks integration, completeness, or durable structure. |
| 3 - Integrated | Core workflow works with real data across required components. |
| 4 - Reliable | Integrated behavior is tested, permissioned, observable, and usable in routine work. |
| 5 - North-Star quality | Capability fulfills the intended conceptual role with mature UX, intelligence, reliability, and evidence. |

A score is not a grade for the team. It is a navigation instrument. A deliberately minimal V1 can be successful while still scoring 1-2 against the final target.

## 5. Baseline benchmark matrix

| Capability | Final build target | Current build | Gap / next evidence |
| --- | --- | --- | --- |
| Living Profile | Dynamic identity/career mirror generated from connected work. | TO AUDIT | Verify current profile implementation and data model. |
| Project Objects | Full project graph: intent, people, work, assets, evidence, release, outcome, lineage. | TO AUDIT | Inspect current project data structures and UI. |
| Electronic Press | Cross-station events automatically enrich the network record. | TO AUDIT | Identify existing event flows and missing contracts. |
| Career Graph | Time + relationship visualization across projects, releases, collaborators, skills, and transitions. | TO AUDIT | Check whether any timeline/graph exists. |
| Sonic Intelligence | Grounded reasoning over permitted structured history with auditable evidence. | TO AUDIT | Verify current AI integration, context sources, and provenance. |
| Collaboration Graph | Roles, contributions, history, fit, availability, and outcomes. | TO AUDIT | Audit collaboration objects and permissions. |
| Guild Services | Internal service/product/availability discovery connected to member evidence. | TO AUDIT | Audit any offering/marketplace/service model. |
| Development Cycles | Light seasons/reflection/next-threshold support backed by evidence. | TO AUDIT | Verify current initiation/tier UX and avoid premature ceremony. |
| Privacy | Granular private-first visibility with self/collaborator/Tribe/steward layers. | TO AUDIT | Inspect authorization model and default exposure. |
| Metrics | Contextual developmental/project/release signals, not vanity ranking. | TO AUDIT | Inventory currently tracked metrics and their use. |

## 6. Build review protocol

1. Capture the running product as evidence: route, screen, schema, test, API output, event, or reproducible behavior.
2. Describe what actually works without aspirational language.
3. Find the matching North-Star requirement.
4. Assign status and 0-5 maturity score.
5. Record the most important gap preventing the next score.
6. Choose the smallest implementation that closes that gap without violating conceptual invariants.
7. Implement and verify it.
8. Update the Current Build Record and Gap Ledger. Do not rewrite the North-Star to make the score look better.

## 7. Decision-control rule

| NEVER SILENTLY MUTATE THE TARGET If the final concept changes, record a Design Decision: previous intent, proposed change, reason, evidence, consequences, and explicit approval. A technical limitation is not by itself a reason to redefine the product. |
| --- |

## 8. Feature comparison card template

| Field | Required entry |
| --- | --- |
| Feature / system | Name of the capability being reviewed. |
| North-Star intent | What the final system is supposed to accomplish and why it exists. |
| Current implementation | Exactly what exists now. |
| Evidence | Screenshots, routes, commits, tests, schemas, data, recordings, or reproducible steps. |
| Maturity score | 0-5 using the rubric above. |
| Gap | The highest-value missing behavior or quality. |
| Next build action | Smallest validated step that meaningfully closes the gap. |
| Invariant check | Which canonical principles must not be compromised. |
| Decision history | Relevant prior decisions and why the present form exists. |

## 9. Definition of done for the complete Tribal Network vision

The final system should not be declared complete merely because every screen exists. Completion requires the relationships between the screens to work as one coherent intelligence system.

- A member can create and evolve real projects without duplicative administrative work.
- Activity across relevant stations becomes structured, permissioned network knowledge.
- The member can visually understand current work, career history, development, collaboration, contribution, and emerging direction.
- The Tribe can discover useful capabilities, collaborators, services, and contributions from evidence rather than self-promotion alone.
- Sonic Intelligence can retrieve and reason over permitted history with traceable grounding and useful creative restraint.
- Project, release, asset, collaborator, practice, service, evidence, and career relationships remain coherent over time.
- Privacy and permission boundaries are reliable enough for unfinished and sensitive creative work.
- The product remains fast, calm, navigable, and aesthetically coherent despite the depth of information.
- Initiation/development mechanics feel organic and supportive rather than imposed.
- The system has enough engineering maturity - tests, observability, migration discipline, security, performance, and data provenance - to be trusted as a long-lived creative record.

## 10. Working doctrine for future builds

| BUILD-CONTROL DOCTRINE Document the ideal. Build the real. Measure the gap. Preserve the reason. Verify the change. Repeat until the real system and the intended system converge. |
| --- |
