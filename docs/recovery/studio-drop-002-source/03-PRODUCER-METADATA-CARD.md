# OMEGA HOUSE STUDIO
## STUDIO DROP.002 — PRODUCER METADATA CARD

### REBELLION VOL. ONE | CINEMATIC MELODIES & STEMS

**Product ID:** `OH-SD002`  
**Version:** `1.0`  
**Classification:** `STUDIO_DROP`  
**Release Class:** `MVP_CERTIFIED`  
**Certification:** `MVP CERTIFIED`  
**Source:** Omega House Studio

---

## 01 — CREATIVE IDENTITY

| Attribute | Value |
|---|---|
| Product | REBELLION VOL. ONE |
| Descriptor | CINEMATIC MELODIES & STEMS |
| Product Family | Studio Drop |
| Drop Number | Studio Drop.002 |
| Product ID | OH-SD002 |
| Version | 1.0 |
| Release Class | MVP_CERTIFIED |
| Intended User | Music producers, composers, beatmakers, sound designers |
| Primary Use | Creative reconstruction, arrangement, resampling, layering, sound design |
| Source | Omega House Studio |

---

## 02 — CREATIVE PURPOSE

**REBELLION VOL. ONE** is a structured production starting point built around melodic material and separated production components.

The product is intended to give the producer multiple creative entry points rather than force a single finished arrangement. The included materials can be approached as source material for reconstruction, transformation, resampling, layering, arrangement, and original production, subject to the accompanying license.

The package should be understood as a **creative source system**, not merely a collection of playback files.

---

## 03 — CREATIVE ENTRY POINTS

### MIDI

Use MIDI as the editable musical-control layer where applicable. It provides a starting point for changing instrumentation, voicing, timing, register, and arrangement.

### Melody

Use the melody asset as the direct melodic source layer for auditioning, editing, resampling, chopping, or rebuilding the musical idea within the granted rights.

### Stems

Use stems as separated production components. Stems provide greater control over arrangement, processing, spatial placement, layering, and reconstruction than a single stereo bounce.

### Reconstruction Path

```text
MIDI
  ↓
MELODY
  ↓
STEMS
  ↓
EDIT / RESAMPLE / PROCESS
  ↓
ARRANGEMENT
  ↓
ORIGINAL PRODUCTION
```

---

## 04 — PRODUCER WORKFLOW ATTRIBUTES

```yaml
workflow:
  mode: CREATIVE_RECONSTRUCTION
  entry_points:
    - MIDI
    - MELODY
    - STEMS
  transformations:
    - EDIT
    - ARRANGE
    - RESAMPLE
    - LAYER
    - PROCESS
    - RESTRUCTURE
    - SOUND_DESIGN
  output_goal: ORIGINAL_PRODUCTION
  rights_dependency: LICENSE
```

These attributes describe intended workflow behavior. They do **not** grant rights beyond the governing license.

---

## 05 — MUSICAL / TECHNICAL METADATA

The following fields are intentionally maintained as verified metadata rather than assumptions.

| Field | Value | Status |
|---|---|---|
| Key | `PENDING_VERIFICATION` | Requires asset inspection |
| BPM | `PENDING_VERIFICATION` | Requires asset inspection |
| Time Signature | `PENDING_VERIFICATION` | Requires asset/project inspection |
| Sample Rate | `PENDING_VERIFICATION` | Requires audio inspection |
| Bit Depth | `PENDING_VERIFICATION` | Requires audio inspection |
| Channels | `PENDING_VERIFICATION` | Requires audio inspection |
| Duration | `PENDING_VERIFICATION` | Requires asset inspection |
| Audio Format | `PENDING_VERIFICATION` | Requires asset inspection |
| MIDI Format | `PENDING_VERIFICATION` | Requires asset inspection |

**Rule:** Sonic AI V3 should populate these values from deterministic asset analysis whenever possible. Human-entered metadata should be identified separately from machine-derived metadata.

---

## 06 — SONIC AI V3 ATTRIBUTES

This product is designed to become a first-class object in the Sonic AI V3 knowledge and asset system.

```yaml
sonic:
  entity_type: PRODUCT
  product_id: OH-SD002
  version: "1.0"
  classification: STUDIO_DROP
  release_class: MVP_CERTIFIED
  asset_roles:
    - MIDI
    - MELODY
    - STEMS
  metadata_mode: DETERMINISTIC_WHERE_POSSIBLE
  provenance_required: true
  license_required: true
  certification_required: true
  validation_required: true
```

### Intended intelligence relationships

```text
PRODUCT
├── ASSETS
├── METADATA
├── PROVENANCE
├── LICENSE
├── CERTIFICATION
└── CREATIVE WORKFLOW
      ├── EDIT
      ├── ARRANGE
      ├── RESAMPLE
      ├── LAYER
      ├── PROCESS
      └── SOUND DESIGN
```

Sonic may use these relationships to support asset retrieval, contextual recommendations, provenance-aware analysis, Creator DNA reconstruction, and future producer workflow automation.

---

## 07 — PROVENANCE PRINCIPLE

Every machine-resolved attribute should retain a distinction between:

- **Declared** — supplied by the product documentation or producer.
- **Derived** — calculated or extracted from the actual asset.
- **Verified** — independently validated against the package or source asset.
- **Pending** — not yet established from authoritative evidence.

This distinction prevents Sonic from treating assumptions as facts.

---

## 08 — CUSTOMER LEGIBILITY

A customer does not need Sonic AI V3 to use this product.

The metadata card exists to make the package understandable and professionally identifiable while simultaneously establishing a structured information contract for future machine intelligence.

A customer should be able to determine:

1. What the product is.
2. What assets are included.
3. What each asset is intended to do.
4. How the assets relate to a production workflow.
5. Where technical metadata is authoritative.
6. Where rights are defined.
7. How the product is identified and versioned.

---

## 09 — GOVERNING DOCUMENTS

The metadata card does not supersede the governing rights documentation.

**Authority hierarchy:**

```text
LICENSE
  ↓
CERTIFICATION / PRODUCT IDENTITY
  ↓
ASSET MANIFEST
  ↓
PRODUCER METADATA CARD
  ↓
MARKETING / DESCRIPTIVE COPY
```

Where descriptive copy conflicts with the license, the license controls.

---

## 10 — RELEASE VALIDATION STATE

```yaml
validation:
  identity: VERIFIED
  classification: VERIFIED
  release_class: VERIFIED
  creative_workflow_model: VERIFIED
  asset_level_technical_metadata: PENDING_ASSET_INSPECTION
  provenance: DEFINED
  license_linkage: REQUIRED
  certification_linkage: REQUIRED
  final_package_validation: REQUIRED
```

This document is therefore **structurally locked** while asset-derived technical fields remain intentionally pending until the actual release files are inspected.

---

**OMEGA HOUSE STUDIO**  
**Studio Drop.002**  
**OH-SD002**  
**MVP CERTIFIED**