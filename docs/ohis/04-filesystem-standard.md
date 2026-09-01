# OHIS-04 — Filesystem Standard

## Design goal

The filesystem must remain understandable decades from now without depending on one person's memory.

It is intentionally hierarchical at the top level and metadata-driven deeper down.

## Canonical root

```text
OMEGA_HOUSE/
├── 00_SYSTEM/
│   ├── Standards/
│   ├── Naming/
│   ├── Color_System/
│   ├── Templates/
│   ├── Documentation/
│   └── Schemas/
├── 01_PROJECTS/
│   ├── Active/
│   ├── Completed/
│   └── Archived/
├── 02_AUDIO/
│   ├── One_Shots/
│   ├── Samples/
│   ├── Loops/
│   ├── Vocals/
│   ├── Stems/
│   └── Field_Recordings/
├── 03_PRESETS/
│   ├── Instruments/
│   ├── Effects/
│   ├── Chains/
│   ├── Mixer/
│   └── Mastering/
├── 04_MIDI/
│   ├── Melodies/
│   ├── Chords/
│   ├── Bass/
│   ├── Drums/
│   └── Templates/
├── 05_PACKS/
│   ├── Development/
│   ├── Beta/
│   ├── Released/
│   └── Archived/
├── 06_BEATS/
│   ├── Ideas/
│   ├── WIP/
│   ├── Ready/
│   ├── Released/
│   └── Licensed/
├── 07_MIXING/
│   ├── Chains/
│   ├── References/
│   ├── Templates/
│   └── Mastering/
├── 08_VISUAL/
│   ├── Covers/
│   ├── Artwork/
│   ├── Product/
│   └── Marketing/
├── 09_BUSINESS/
├── 10_SONIC_AI/
│   ├── Knowledge/
│   ├── Memory/
│   ├── Schemas/
│   ├── Agents/
│   └── Tools/
└── 99_ARCHIVE/
```

## Numbering policy

Top-level numeric prefixes establish stable human navigation. They should not be renumbered casually because scripts, documentation, and external references may depend on them.

## Lifecycle placement

A file's folder indicates broad domain; lifecycle is tracked explicitly in metadata.

For example, an approved 808 remains under `02_AUDIO/One_Shots/`, with:

```text
state = APPROVED
```

Do not create parallel trees such as `Approved_Audio/`, `Final_Audio/`, and `Good_Audio/` merely to represent state.

## Canonical vs working copies

A project may have local working files, exports, caches, and temporary renders. OHIS only manages intentional canonical assets.

Recommended project structure:

```text
PROJECT/
├── 00_ADMIN/
├── 01_SOURCE/
├── 02_SESSION/
├── 03_AUDIO/
├── 04_MIDI/
├── 05_EXPORTS/
├── 06_REFERENCES/
└── 99_ARCHIVE/
```

## Raw preservation

`01_SOURCE/RAW/` material is immutable by policy.

Derived files receive new versions or child Asset IDs. Never overwrite the only known source of a creative asset.

## Archive policy

Archive means **inactive but retained**, not deleted.

Deprecated assets remain discoverable to Sonic because historical usage can be valuable evidence.

## Backup principle

OHIS is an organizational standard, not a backup system. Canonical assets require independent backup and recovery controls. A directory being well organized does not make it safe.
