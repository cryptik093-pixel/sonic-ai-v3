# Knowledge Archive Manifest

**Archive ID:** `OH-KA-2026-09-04-001`  
**Source:** `OH_CIRICULME.001.zip`

This manifest is the normalized index for the immutable source bundle. Original filenames are preserved for provenance; professional names below define how future derivatives should be labeled.

| Source file | Class | Lifecycle | Recommended derivative ID |
|---|---|---|---|
| `Omega_House_Production_Doctrine_First_Edition.pdf` | doctrine | canonical Phase 1 | `OH_DOCTRINE_PRODUCTION_FIRST_EDITION_v1.0_CANONICAL` |
| `Omega_House_Production_Doctrine_First_Edition.docx` | doctrine | canonical editable source | `OH_DOCTRINE_PRODUCTION_FIRST_EDITION_v1.0_SOURCE` |
| `Omega_House_Production_Doctrine_First_Edition-1.pdf` | doctrine | duplicate | `OH_DOCTRINE_PRODUCTION_FIRST_EDITION_v1.0_DUPLICATE` |
| `Omega_House_Full_System_Audit_2026.pdf` | audit | evidence | `OH_AUDIT_FULL_SYSTEM_2026_EVIDENCE` |
| `Omega_House_Unified_Production_Doctrine.pdf` | doctrine | historical/reference | `OH_DOCTRINE_UNIFIED_PRODUCTION_HISTORICAL` |
| `Omega_House_Core_Production_Asset_Pipeline_v1.0_Technical_Edition.pdf` | curriculum/audio | reference | `OH_AUDIO_CORE_ASSET_PIPELINE_v1.0_REFERENCE` |
| `Omega_House_Beat_Mix_Rescue.pdf` | curriculum/audio | reference | `OH_AUDIO_BEAT_MIX_RESCUE_REFERENCE` |
| `Drum architecture omega house premiere.pdf` | curriculum/audio | reference | `OH_AUDIO_DRUM_ARCHITECTURE_PREMIERE_REFERENCE` |
| `Dubstep bass chain presets.pdf` | curriculum/audio | reference | `OH_AUDIO_DUBSTEP_BASS_CHAIN_REFERENCE` |
| `Omega_House_Knowledge_Tier1_Section1_Chapter1.docx` | curriculum | reference | `OH_CURRICULUM_T1_S1_C1_REFERENCE` |
| `Omega_House_Elite_Audio_Engineering_LMS_SCORM.zip` | LMS | packaged curriculum | `OH_LMS_ELITE_AUDIO_ENGINEERING_SCORM_v1` |
| `Omega_House_STUDIO_DROP_001_FLAGSHIP_PACKAGING_AUDIT.zip` | product-metadata/audit | evidence | `OH_PRODUCT_STUDIO_DROP_001_PACKAGING_AUDIT_EVIDENCE` |
| `omega-house.online-Unparsable structured data-Validation-2026-08-23.zip` | metadata/audit | historical validation evidence | `OH_METADATA_STRUCTURED_DATA_VALIDATION_2026-08-23_EVIDENCE` |
| `Sonic_AI_Strategic_Blueprint_Prelaunch_2026.docx` | strategy | historical | `SONIC_STRATEGY_PRELAUNCH_BLUEPRINT_2026_HISTORICAL` |
| `Sonic_AI_30_Day_Execution_Roadmap_April-May_2026.docx` | strategy | historical | `SONIC_STRATEGY_30_DAY_ROADMAP_2026_HISTORICAL` |
| `Sonic_AI_Investor_Projection_Model_April_2026.xlsx` | strategy/finance | historical projection | `SONIC_FINANCE_INVESTOR_PROJECTION_2026_HISTORICAL` |
| `omega_house_investor_package.docx` | strategy/investor | historical | `SONIC_INVESTOR_PACKAGE_HISTORICAL` |
| `Omega_House_Investor_Pitch-1.docx` | strategy/investor | historical | `SONIC_INVESTOR_PITCH_HISTORICAL` |
| `Chat gpt simulation review.pdf` | strategy/research | historical simulation | `SONIC_RESEARCH_AI_SIMULATION_REVIEW_HISTORICAL` |
| `OMEGA HOUSE STIDIO LLC DEVELOPMENT.pdf` | strategy/development | historical | `OH_DEVELOPMENT_RECORD_HISTORICAL` |

## Duplicate control

`Omega_House_Production_Doctrine_First_Edition.pdf` and `Omega_House_Production_Doctrine_First_Edition-1.pdf` have identical SHA-256 content in the captured source bundle. Only the non-suffixed PDF should be indexed as the canonical rendered edition.

## Ingestion metadata contract

Every future extracted Markdown/JSON knowledge object should carry at minimum:

```yaml
archive_id: OH-KA-2026-09-04-001
source_file: <original filename>
canonical_id: <normalized derivative ID>
document_class: <taxonomy>
lifecycle: <canonical|historical|evidence|superseded|draft|validated>
phase: <phase-1|phase-2|historical>
source_hash_sha256: <full hash>
derived_at: <ISO-8601>
validated_against_runtime: false
```

This prevents historical strategy, marketing, curriculum, and doctrine from collapsing into one undifferentiated retrieval corpus.