# OMEGA HOUSE STUDIO
## STUDIO DROP.002 — STEM MAP

### REBELLION VOL. ONE | CINEMATIC MELODIES & STEMS

**Product ID:** `OH-SD002`  
**Version:** `1.0`  
**Classification:** `STUDIO_DROP`  
**Release Class:** `MVP_CERTIFIED`  
**Status:** `MVP CERTIFIED`

---

## 01 — PURPOSE

This Stem Map defines the organizational and semantic contract for the separated audio components included with Studio Drop.002.

Its purpose is to make every stem:

- identifiable by role;
- easy for a customer to locate and understand;
- usable in a DAW without unnecessary guesswork;
- traceable to the parent product and version;
- machine-resolvable by Sonic AI V3;
- suitable for future automated validation and analysis.

The actual filenames and technical values remain asset-derived and must be populated from the final production files rather than assumed.

---

## 02 — STEM INVENTORY CONTRACT

| Field | Requirement |
|---|---|
| Parent Product ID | `OH-SD002` |
| Parent Version | `1.0` |
| Stem Asset ID | Unique per stem |
| Stem Role | Required |
| Filename | Exact release filename |
| Format | Verified from file |
| Key | Verified where applicable |
| BPM | Verified where applicable |
| Duration | Verified from file |
| Sample Rate | Verified from file |
| Bit Depth | Verified from file |
| Channels | Verified from file |
| Checksum | SHA-256 required for final release |
| Provenance | Required |
| License Association | Required |

---

## 03 — STEM ROLE TAXONOMY

Each stem should have one primary semantic role. Additional tags may be added by Sonic after inspection.

Recommended role vocabulary:

```text
MELODIC
HARMONIC
RHYTHMIC
BASS
DRUMS
PERCUSSION
TEXTURE
AMBIENCE
FX
VOCAL
TRANSITION
OTHER
```

The taxonomy is intentionally extensible. Sonic AI V3 may assign additional descriptors after deterministic or analytical inspection without changing the original customer-facing identity of the asset.

---

## 04 — RELEASE STEM INVENTORY

The following records establish the required structure. Exact filenames and technical metadata are populated only after inspection of the actual customer-ready files.

### Stem Record Template

```yaml
stem_id: OH-SD002-STEM-XXX
parent_product_id: OH-SD002
parent_version: "1.0"
role: PENDING_VERIFICATION
filename: PENDING_ACTUAL_FILENAME
format: PENDING_VERIFICATION
technical_metadata:
  key: null
  bpm: null
  duration_seconds: null
  sample_rate_hz: null
  bit_depth: null
  channels: null
provenance:
  source: Omega House Studio
  product_id: OH-SD002
  version: "1.0"
  origin_status: PENDING_VERIFICATION
checksum:
  algorithm: SHA-256
  value: PENDING
license:
  required: true
  governing_document: LICENSE/
validation_status: PENDING_ASSET_INSPECTION
```

**Rule:** One record must exist for every actual stem in the final package. A stem directory alone is not sufficient inventory evidence.

---

## 05 — NAMING STANDARD

Where filenames are created or normalized, use a predictable structure that exposes product identity and functional role without requiring Sonic to resolve the file first.

Recommended pattern:

```text
OH-SD002_[ROLE]_[DESCRIPTOR]_[INDEX].[EXT]
```

Example structure only:

```text
OH-SD002_MELODIC_MAIN_01.wav
OH-SD002_BASS_MAIN_01.wav
OH-SD002_TEXTURE_01.wav
```

These examples are **not declarations of the actual Studio Drop.002 filenames** and must not be inserted into the final manifest unless they are the real files.

---

## 06 — DAW ACCESSIBILITY

The stem package should support a straightforward customer workflow:

```text
UNZIP
  ↓
PRODUCTION/STEMS
  ↓
IDENTIFY STEM ROLE
  ↓
IMPORT INTO DAW
  ↓
ALIGN TO PROJECT TEMPO / MUSICAL CONTEXT
  ↓
MUTE / SOLO / EDIT / PROCESS
  ↓
RECONSTRUCT
```

Where the source material has a verified BPM, key, or timing reference, that information should be surfaced through the Asset Manifest and metadata rather than hidden in filename conventions alone.

---

## 07 — SONIC AI V3 SEMANTIC MODEL

Sonic should represent each stem as a child asset of the Studio Drop product entity.

```text
OH-SD002
└── STEMS
    ├── STEM-001
    │   ├── ROLE
    │   ├── AUDIO_METADATA
    │   ├── PROVENANCE
    │   ├── LICENSE
    │   └── CHECKSUM
    ├── STEM-002
    └── STEM-N
```

Recommended machine attributes:

```yaml
sonic:
  entity_type: AUDIO_ASSET
  parent_entity: OH-SD002
  asset_class: STEM
  semantic_role: PENDING_VERIFICATION
  metadata_source: DETERMINISTIC_ANALYSIS_WHERE_POSSIBLE
  provenance_required: true
  checksum_required: true
  license_binding_required: true
```

Sonic may subsequently enrich a stem with characteristics such as spectral profile, loudness, transient behavior, harmonic content, texture, energy, instrumentation, and creative-use tags. Such enrichment must remain distinguishable from original declared metadata.

---

## 08 — PROVENANCE & RIGHTS

A stem inherits its product relationship but does not create independent rights beyond the governing license.

Every stem record must resolve to:

```text
STEM
  ↓
PRODUCT ID: OH-SD002
  ↓
VERSION: 1.0
  ↓
LICENSE
  ↓
CERTIFICATION
```

If a stem is modified, processed, renamed, replaced, or regenerated for a future release, the package version and provenance record must be evaluated before the asset is treated as the same release object.

---

## 09 — VALIDATION GATES

Before final distribution:

### Gate A — Inventory
- Every stem has a unique asset ID.
- Every actual file has exactly one manifest record.
- No manifest record points to a missing file.

### Gate B — Technical Integrity
- Files open successfully.
- Audio duration is readable.
- Format and channel information are verified.
- Timing/key metadata is verified where applicable.

### Gate C — Identity
- Product ID resolves to `OH-SD002`.
- Version resolves to `1.0`.
- Stem role is consistent with the asset.

### Gate D — Provenance
- Origin is recorded.
- SHA-256 checksum is recorded.
- License relationship is recorded.

### Gate E — Customer Package
- Stems are located under `PRODUCTION/STEMS/`.
- Filenames are understandable.
- No unrelated development files are present.

---

## 10 — LOCK STATE

```yaml
stem_map:
  structure: LOCKED
  taxonomy: LOCKED
  sonic_semantics: LOCKED
  validation_contract: LOCKED
  actual_stem_inventory: PENDING_ASSET_INSPECTION
  technical_metadata: PENDING_ASSET_INSPECTION
  checksums: PENDING_FINAL_PACKAGE
```

This document locks the **semantic and validation architecture** without pretending that uninspected files have already been verified.

---

**OMEGA HOUSE STUDIO**  
**Studio Drop.002**  
**OH-SD002**  
**MVP CERTIFIED**