# Drum Supply Headquarters

Windows x64 VST3 sample drum instrument, version 0.2.0 engineering candidate.

The seven pads select and audition Kick, Snare, Hi-Hat, Cymbal, Tom, Percussion and Clap. The starter sounds are embedded. Their musical approval and provisional categories still require the creator's listening review. Replace any slot with an appropriate personal WAV or AIFF; its original filename and duration appear above the waveform. Loading preserves the current sound until the new sample has decoded successfully.

## Sound controls

| Control | Range / behavior |
|---|---|
| Tune | -24 to +24 semitones; captured when a hit starts |
| Gain | -60 to +12 dB for this slot; default -6 dB |
| Pan | Stereo balance from -1 left to +1 right |
| Start / End | Fractions of the source file; vertical waveform markers; a crossed region becomes one source frame |
| Attack | 0–500 ms; applies to a new hit |
| Release | 0–3000 ms fade approaching the sample's region end; BODY multiplies its length |
| Low-pass | 40–20000 Hz; CHARACTER multiplies the cutoff; bounded by the host Nyquist limit |
| Reverse | Plays from the region end toward its start; applies to new hits |
| Mute / Solo | Smoothly suppresses this slot, or suppresses slots that are not soloed; existing ambience can decay |
| BODY | Global low-frequency weight and end-release length; midpoint is the reference setting |
| CHARACTER | Global filter colour and soft drive above midpoint; it does not overwrite the detailed filter knob |
| SPACE | Global send into a real stereo ambience; zero stops the send, while the existing tail decays |
| Output | -36 to +6 dB after the mix; default -6 dB |

Double-click sliders to reset their defaults. Values can be typed into their boxes, controls have keyboard focus and tooltips, and attachments send host parameter gestures. These are implemented native controls; actual host keyboard, accessibility and Windows scaling acceptance remains in the verification matrix.

The output meter displays sample peak dBFS. CLIP latches when the output reaches 0 dBFS; PANIC clears the latch and releases active voices over 2 ms. There is no transparent limiter or hard clamp. Multiple overlapping hits or positive gain can exceed full scale; lower slot/output gain when necessary. A mono host output averages the stereo channels.

## MIDI

GM notes route to the seven slots; MIDI 60 always auditions the selected slot. Velocity scales amplitude. This is a one-shot instrument: note-off does not cut a hit short. A new hi-hat hit chokes older hat voices over 2 ms, including open-hat notes. CC123 releases voices and leaves the ambience tail; CC120 immediately clears voices and ambience. Sixteen voices are available, with oldest-voice stealing and a short residual fade.

Playback compensates for source and host sample rates. Four-point cubic interpolation supports pitching and the declared host-rate tests, but is not a bandlimited resampler. Extreme upward tuning needs listening review. Reported algorithmic lookahead latency is zero; driver/interface latency remains separate. The conservative 128-second tail report allows for a 30-second source slowed by two octaves and its ambience.

## Loading and recall

Use LOAD / RELINK SAMPLE or drop a single WAV/AIFF on a pad. Sources must be mono/stereo, 8–384 kHz, between 2 frames and 30 seconds, and at most 64 MiB encoded. The per-instance decoded stereo sample pool is limited to 256 MiB, including factory, A/B and safely retained replacement buffers. File-reading and codec scratch memory are additional. If the memory limit prevents loading, reset the kit or use shorter files; allow a processing block to retire an old sounding snapshot. Files are decoded on the plugin's worker, and a failed replacement preserves the previous playable sample.

Imported files are copied to managed local storage, so moving the original personal source does not break local recall. Keep `%APPDATA%/OmegaHouse/DrumSupply/Samples` with your backups. DAW state stores hashes rather than audio data. Missing cached files are shown as MISSING and remain silent until you select the slot and relink it. A sample/kit replacement stops the previous voices and ambience with a 2 ms residual fade; it is not a seamless full-tail crossfade.

## Kits and comparison

Double-click the kit name to rename. EDITED indicates unsaved changes. SAVE KIT stores a local `.dhpreset`; LOAD KIT accepts local presets and portable `.dhkit` files. The file chooser writes the exact selected filename; use these suffixes to make kit files easy to identify. STARTER resets both comparison banks.

A/B retains two full sample assignments and shaping states, including the selected slot. Switching banks preserves the edits in the bank you leave. Both banks are saved with a DAW project or preset. Host state loads are control operations and may wait for worker decoding; they are not real-time audio operations.

EXPORT PORTABLE packages the original referenced sample files from both banks with the preset manifest. You must confirm permission to redistribute every included sample. Loading a personal file does not itself grant that permission. The container uses validated hash keys and uncompressed blobs; it does not extract user-controlled filenames or directories. ZIP files are not kit-import files. Failed imports do not partially replace the kit, though verified hash-addressed cache files may have been added safely before a later failure.

Version-1 sessions migrate their four controls to the sample starter kit. The old synthesized timbres require the preserved 0.1.0 recovery build. See INSTALLATION.md before upgrading an old project.

## Evidence and support handoff

See the verification report for the exact artifact hash and executed checks. Native FL Studio scan, routing, automation, save/reopen, offline bounce and Windows scaling require the host checklist. Listening approval, clean-machine installation, commercial licensing eligibility and final customer terms are separate release gates. No purchase, activation service, telemetry or online dependency is added by this candidate. A public support channel, refund terms and binding end-user terms must be set by the product owner before a commercial launch.
