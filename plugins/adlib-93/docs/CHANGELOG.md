# ADLIB93 0.1.0 release candidate

- Implements the approved vocal-processing chain and24 editable factory recipes.
- Preserves70 stable parameters, supported mono/stereo layouts, offline operation
  and existing ADLIB-93 manufacturer/product identity.
- Repairs reverb feedback-gain signed arithmetic, manual-tempo bar fallback,
  minimum audible level conversion and Freeze retrigger continuity.
- Preserves loaded user-preset baseline through project recall for lock-aware Reset.
- Completes existing native controls, user preset display names, diagnostic state
  and bounded preset/clear transitions.
- Separates persistent VST3 host bypass from transient internal bypass, and fixes
  corrupted native title/header punctuation through explicit string handling.

Read `docs/VERIFICATION.md` for actual build/validation results and unresolved
release gates. This changelog does not establish FL Studio or listening acceptance.
