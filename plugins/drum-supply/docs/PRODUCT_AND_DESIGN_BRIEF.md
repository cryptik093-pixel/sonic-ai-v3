> HISTORICAL HANDOFF REFERENCE: superseded by the 0.3.0 synthesis specification. See MANUAL.md and RECOVERY_AND_COMPATIBILITY.md.

# Drum Supply Headquarters â€” sample instrument completion brief

## Product promise

Open a small ready-to-play drum kit, replace any one-shot with your own, shape the sound quickly, and recall the kit reliably in your DAW.

The sample-based direction is confirmed by the user. The detailed controls, layout, seven-sound count, and portability requirements below are proposed completion defaults supplied with this prompt; they are not represented as prior user-approved specifications.

## Essential workflow

1. Open the factory starter kit and play from MIDI.
2. Select Kick, Snare, Hi-Hat, Cymbal, Tom, Percussion, or Clap.
3. Drop a WAV/AIFF onto that slot or use Load Sample.
4. Adjust the waveform region, tune, envelope, gain, pan, filter, and reverse.
5. Shape BODY, CHARACTER, and SPACE with understandable audible results.
6. Compare A/B, save a user kit, and reopen the DAW session.
7. Export a portable kit when sample rights permit; relink missing assets explicitly.

## Layout

Proposed default 1100x720; minimum 900x600. Exact sizing should follow native host checks.

```text
+---------------------------------------------------------------------+
| OMEGA HOUSE / DRUM SUPPLY HEADQUARTERS | Kit name * | Save | A/B       |
+---------------------------------------------------------------------+
| KICK | SNARE | HI-HAT | CYMBAL | TOM | PERCUSSION | CLAP              |
| Selected / loaded / missing / muted states; trigger activity          |
+---------------------------------------------------------------------+
| Selected sound name                  | Load Sample | Audition         |
| Waveform with start/end markers; duration; loading/relink feedback    |
| Tune | Gain | Pan | Start/End | Attack/Release | Reverse | Filter      |
+---------------------------------------------------------------------+
|          BODY               CHARACTER                SPACE          |
|    brief musical label     brief musical label     ambience/send     |
+---------------------------------------------------------------------+
| Mute/Solo | MIDI mapping | Import/Export Kit | Panic | Output + meter  |
+---------------------------------------------------------------------+
```

Use dark graphite #111519, elevated panels #1C232A, warm brass #D5AD68, ivory #F2EEE5, and warning red #E46B65 as starting tokens. Use clear local typography, consistent spacing, large pad targets, restrained animation, and native custom-painted controls. Prioritize the waveform, selected drum, and macros. Provide accessible names and keyboard interaction. Do not rely on color alone for status.

Keep primary controls visible; use a compact details section for precise shaping if space is tight. Every visible control must connect to real behavior. No waveform before a sample exists, fake activity, decorative CPU meter, disabled future-feature buttons, or technical backend language in the producer interface.

## Starter sample qualification

Default to seven total factory one-shots, one per slot. Require successful decode, supported format, documented sample rate/channels/bit depth/duration, finite output, intentional start/end, sensible headroom, absence of unintended DC/clicks, and usable tails. Preserve deliberate transient character. Record origin, author, permitted redistribution, any processing, file hash, and listening status. Technical checks do not establish musical quality or legal rights.

Use existing owned assets only when rights are documented. Otherwise create candidates from original synthesis offline and review their provenance and sound. Do not ship silence, placeholders, or unlicensed third-party drums to satisfy a count.

## Completion boundary

Include loading, sample playback/shaping, factory kit, presets, A/B, portable kit import/export, session recall, native design, and validation. Exclude sequencing, AI generation, cloud libraries, commerce, huge content bundles, and extra formats. Preserve old synthesis work without turning it into an additional live mode.
