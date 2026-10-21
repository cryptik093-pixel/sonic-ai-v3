# Control and synthesis reference
Version 0.3.0 / Drum Shot Supply Co. / Omega House Studio LLC.

## Synthesis and slot identities
The existing single fixed 16-voice modal oscillator/noise engine is extended; there are no eight duplicate engines. Indices remain Kick 0, Snare 1, Closed Hat 2, Cymbal 3, Tom 4, Percussion 5, Clap 6; Open Hat is appended at 7. Eight modes per voice are updated with bounded oscillator recurrences, periodic normalization and decaying excitation. Factory kits set sample blend to zero.

| Voice | PUNCH (0-100%) | TONE (0-100%) | CHARACTER (0-100%) |
|---|---|---|---|
| Kick | Shorter attack, more sweep depth/impact | 38-80 Hz base before tuning; body tail | Pitch sweep 1-6x before depth/impact multipliers; upper body, click/noise, gentle drive |
| Snare | Sharper onset and stronger pitch/body impact | 130-280 Hz body and 45-285 ms modal tail before decay scale | Tonal/noise balance, wire spectrum, transient, sweep |
| Closed Hat | Sharper metallic onset | 650-1550 Hz metallic base; 18-198 ms tail before scale | Metallic/noise balance and spectral damping |
| Open Hat | Sharper metallic onset | Same material family, three times longer modal/noise tails | Metallic/noise balance and spectral damping |
| Tom | Attack and pitch impact | 65-175 Hz times note-dependent tuning; body duration | Membrane partial damping, noise transient, pitch depth |
| Percussion | Sharper impulse and impact | 180-830 Hz base, body duration | Wood/membrane/metal partial-ratio morph, noise and drive |
| Clap | Faster onset and burst impact | Filter/body and burst decay | Three noise bursts with 8-22 ms spacing, tonal/noise balance |
| Cymbal | Stronger resonant impact | 270-750 Hz base, 350-1950 ms modal decay | Inharmonic cymbal-like modes, noise/metal balance and texture |

PUNCH scales the generated impact by 0.6-1.4 and changes minimum attack from 1.2 to 0.2 ms; explicit AMP ATTACK adds to that. On voices with a pitch envelope it also multiplies depth by 0.5-1.5. Above its neutral midpoint CHARACTER gently saturates the voice and affects the original voice-specific noise and damping maps. These controls interact by design; extreme pitch/tuning is Nyquist-bounded.

## Advanced controls
TUNE -24..24 semitones affects synthesis and optional sample. GAIN -60..12 dB and PAN -1..1 apply per slot; hard pan clears the opposite dry channel. AMP ATTACK 0..500 ms shapes new hits. DECAY scale 0.1..3 multiplies original voice-specific modal/noise decay; open-hat factor is applied additionally. PITCH DEPTH 0..2 multiplies the voice's own sweep; hat/clap generators have no pitched sweep, so those two GUI controls are disabled there. PITCH DECAY 2..200 ms controls sweep decay. LOW-PASS 40..20000 Hz filters synthesis (20000 bypasses this extra stage); CHARACTER also changes excitation filters. VELOCITY TO TONE 0..1 adds a bounded velocity-dependent material/pitch offset. Velocity 1..127 always scales amplitude.

SAMPLE BLEND 0..1 crossfades synthesis and the optional layer. SAMPLE LEVEL -60..12 dB, START 0..0.999, END 0.001..1, RELEASE 0..3000 ms and REVERSE shape that layer; sample boundaries/tune/attack/release/reverse are captured on a new hit. Reversed/crossed regions are bounded to at least one source frame. Optional sample interpolation is linear; high-rate/pitched samples can alias and require listening. Supplied samples are source-preserved; category labels are provisional optional suggestions, not human listening approval.

MUTE/SOLO, GAIN, PAN, synthesis macros, filter, tuning, decay and pitch controls update held tails with approximately 20 ms smoothing and 32-frame coefficient refresh. A sample load commits an immutable snapshot on the control worker and clears old voices/tails at the next block. This is intended for kit editing rather than gapless live sample replacement.

CHOKE GROUP 0 disables choking; 1..8 excludes all active voices in that group with a 2 ms fade. Closed and Open Hat default to group 1. Oldest active voice is stolen at the 16-voice limit with a 2 ms residual crossfade. One-shots ignore note-off. PANIC clears voices/ambience and resets the latched clip indicator. Global SPACE is the original fixed-tap stereo diffusion, 0 dry / 1 maximum. OUTPUT is -36..6 dB. Final +/-0.98 hard safety clamp prevents invalid/excessive output; CLIP indicates safety clamp activity. It can distort when overdriven: lower gain/output. It is not a transparent mastering limiter. No host tempo is needed.

## State and interchange
State v3 contains all 181 parameters, editable MIDI/choke maps, kit names, sample references and both A/B banks. .dhpreset uses the same strict bounded JSON. .dhkit contains that JSON plus content-addressed optional user samples; it has no file paths or archive extraction targets. WAV/AIFF input is bounded to 64 MiB, stereo/mono 8-384 kHz, 2 frames..30 seconds; total decoded storage is bounded to 256 MiB per instance. Runtime processing accepts 8-192 kHz and zero-size buffers. GUI/loader work runs outside processBlock; the callback uses fixed voices, atomic parameters/mailboxes and bounded hazard-pointer acquisition.

The legacy first four automation IDs are department/body/character/space. BODY is retained as a global TONE offset and CHARACTER as a global per-slot CHARACTER offset; default .5 is neutral. They remain host-automatable for compatibility. SPACE is visible; the selected drum's PUNCH/TONE/CHARACTER are the three visible macros. See RECOVERY_AND_COMPATIBILITY for migration limits.

Numeric displays use compact category-appropriate precision. Entered values remain full floating-point parameters; display formatting does not quantize host automation. The editor resizes from 960x760 to 1800x1200, hiding the optional waveform in compact mode while keeping synthesis controls accessible.


## Raw comparison, factory kits and export
The visible macros display 0-100%, with 50% neutral. Their stable internal host values remain 0-1; type 50 in a macro text field for the midpoint. Existing parameter IDs and normalized values are preserved. RAW temporarily auditions the neutral Factory Synthesis engine without changing kit parameters. Master gain and editable MIDI assignments remain active. Return to EDITED to hear edits and export. A/B banks separately retain two complete editable kits; RAW is a temporary comparison and is not saved as kit state.

The factory selector offers Factory Synthesis, Hip-Hop Foundation, Boom-Bap Room, Trap Circuit, Electronic Pulse and Experimental Foundry. These contain different synthesis settings and work without external samples. NEW KIT initializes neutral synthesis; FACTORY RESET restores the starting kit. Save before replacing a kit; A/B preserves its own two banks, not a general undo history.

SHOT WAV renders the selected edited drum. KIT WAV renders eight separate sounds into a new numbered directory, with ExportManifest.json containing hashes, measured peaks/RMS and a complete kit-state snapshot. Select 44.1, 48 or 96 kHz. Exports use the production synthesis engine on a separate worker, stereo PCM24 with deterministic TPDF dither, velocity 127, and the captured synthesis/output/optional-layer settings. Per-slot mute/solo are bypassed for sound export. Active playback and kit parameters are preserved. Existing kit export folders are never overwritten; single-shot replacement requires the save dialog's overwrite confirmation.

The renderer captures the tail until 250 ms below -90 dBFS; a 128-second cap ends with a 20 ms fade. The manifest marks capped tails. Missing optional layers can make blend=1 silent, which fails export visibly rather than producing an empty download. Failed kit exports retain a .rendering directory with FAILED status for diagnosis. Variation export uses the current edited parameters: adjust macros and export a new shot or numbered kit. No unrelated sample files are copied as generated audio.
