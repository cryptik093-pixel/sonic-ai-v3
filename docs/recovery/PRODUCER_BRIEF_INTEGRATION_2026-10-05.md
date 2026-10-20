# Producer Brief Intelligence — Tier 1 Integration Recovery

Date: 2026-10-05

Historical source head: `687632a159bf468a99ad115a727afd255170b21d` (`codex/producer-brief-intelligence`)
Canonical main at recovery start: `19ff3b7648c49f3f81b82dcc5e445028719edaba`

## Topology

The historical Producer Brief line was 4 commits ahead and 1 commit behind current main.
The only main-side file added after their common parent was:

- `docs/releases/FIELD-ONE-DELUXE.md`

This recovery commit preserves both parents and the validated Producer Brief tree while retaining that current-main release record.

## Historical evidence

The source head passed:
- Runtime Baseline
- deterministic CI
- Sonic Desktop, including Linux/browser and Windows packaged/native UI checks
- Veracode workflow (workflow success; historical delivery notes state configured scan steps were not a completed security scan)

## Recovery rule

This branch is an integration candidate only. Current workflows must revalidate the merged tree before any merge decision.
