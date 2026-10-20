# OHIS-03 — Color & Routing Semantics

## Principle

Omega House DAW colors encode **signal-path topology**, not instrument category.

Color answers:

> Where is this processing stage in the signal architecture?

The channel label answers:

> What does this stage do?

The folder answers:

> What domain does this asset belong to?

## Canonical depth map

| Depth | Color | Semantic meaning | Typical topology |
|---|---|---|---|
| D1 | Pink | First insert / primary processing | Channel → Insert 1 |
| D2 | Green | Second processing stage / first channel-to-bus relationship | Channel → Insert 2 → Bus 1 |
| D3 | Blue | Third processing stage / second channel-to-bus relationship | Channel → Insert 3 → Bus 2 |
| D4+ | Custom | Advanced or non-linear topology | Parallel, nested, sidechain, return, or custom |

## Important distinction

Color is **not** a substitute for routing metadata.

For example, a green channel means `D2`; it does not by itself prove which physical bus receives the signal. Sonic must inspect or receive actual routing information where available.

## Label format

Recommended DAW label:

```text
[D#] ROLE — FUNCTION
```

Examples:

```text
[D1] 808 — TONE
[D2] 808 — SATURATION
[D3] 808 — CLIP
[D2] DRUM BUS — GLUE
[D3] MASTER — LIMIT
```

The label should describe function, not plugin brand alone.

Prefer:

```text
[D2] 808 — HARMONIC DRIVE
```

over:

```text
[D2] Decapitator
```

Plugin names belong in metadata.

## D4+ custom rule

After D3, OHIS intentionally avoids assigning a universal fixed color sequence. D4+ often represents topology that is more useful to identify semantically than by arbitrary color.

Examples:

```text
[D4] 808 — PARALLEL DISTORT
[D4] VOCAL — SIDECHAIN RETURN
[D5] MIX BUS — PARALLEL COMP
```

The producer may choose an intuitive color. Sonic records the semantic reason separately.

## Routing graph model

A DAW chain should be representable as a graph:

```text
SOURCE
  ↓
D1 / PINK
  ↓
D2 / GREEN
  ↓
BUS-1
  ↓
D3 / BLUE
  ↓
BUS-2
  ↓
MASTER
```

Parallel example:

```text
SOURCE
 ├──► DIRECT
 │
 └──► D4 / CUSTOM / PARALLEL FX
          ↓
       RETURN BUS
          ↓
       MIX BUS
```

## Preset standard

Mixer presets and chains should preserve, where technically possible:

- channel role
- routing depth
- bus relationships
- insert order
- plugin identity
- plugin parameter state
- bypass state
- send/return relationships
- color semantics
- label semantics

If a DAW format cannot preserve a field, OHIS stores the missing information in its external metadata record rather than silently losing it.

## Anti-patterns

Do not use color to encode five unrelated concepts simultaneously.

Bad:

```text
Pink = vocals
Green = drums
Blue = bass
```

when pink/green/blue are also supposed to mean processing depth.

Good:

```text
Pink = D1
Green = D2
Blue = D3
```

while:

```text
ROLE = VOCAL / DRUM / BASS
```

is encoded independently.
