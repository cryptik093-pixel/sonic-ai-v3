# Drum Supply Headquarters 0.2.0 engineering contract

The supplied completion prompt and handoff are product references, not fresh validation evidence. This implementation adopts their sample-instrument direction and bounded local scope. Sample-free synthesis remains in `Source/DrumEngine.h` and the complete 0.1.0 wrapper/editor sources are preserved in `legacy/0.1.0`. No extra synthesis mode is exposed.

## Product and identity

Seven-slot Windows x64 VST3 instrument, FL Studio first. Stable manufacturer `OmHs`, product `OhDs`, bundle `com.omegahousestudio.drumsupply`, binary/product name Omega Drum Supply; editor heading Drum Supply Headquarters. The first four parameter IDs/order remain department, body, character, space; 77 per-slot parameters and output are appended. Target: open, play, replace a sample, shape, compare A/B, save and recall without any network/runtime service.

## Data and threading

- Embedded factory WAVs keep the starter kit independent of installation paths. Exactly seven source WAVs from the supplied archive are embedded unchanged. User affirmed ownership and commercial-plugin redistribution permission in this chat on October 19, 2026. Provisional slot classification and musical approval remain separate from this provenance.
- One control worker serializes decoding, kit I/O, cache access and publication. At most one operation is accepted at a time; a second request receives a visible Busy response. Cancellation of a file dialog does not queue work.
- WAV/AIFF only, mono/stereo, 8–384 kHz source rate, 2 frames to 30 seconds, 64 MiB encoded file maximum. Metadata is checked before decoded channel allocation. Per-instance decoded stereo float buffers, including referenced A/B and retained replacement buffers, are bounded to 256 MiB. The input snapshot, codec scratch space and UI/metadata are additional memory.
- Source bytes are hashed and copied to `%APPDATA%/OmegaHouse/DrumSupply/Samples/<sha256>.sample`. Names in state are descriptive only; storage lookup uses validated lowercase 64-character hex hashes or embedded `f0`–`f6` IDs. Host state never embeds PCM or arbitrary file paths.
- The worker publishes immutable snapshots. A sequentially consistent hazard pointer protects the audio snapshot; a bounded three-attempt acquisition avoids waiting. Retired snapshots are collected on the worker before subsequent operations. The callback never owns a shared pointer or destroys a sample buffer. A successful sample/kit change resets voices and ambience at a block boundary with a 2 ms residual fade. This can interrupt a sounding tail; seamless full-tail kit swaps are not promised.
- Host state callbacks are control operations and can wait up to 30 seconds for bounded worker decoding. Processing continues with the previous snapshot until publication. Hosts must not treat state loading as a real-time callback. State parameter setters follow JUCE host notifications; they do not promise sample-accurate batch automation.

## Audio contract

- 16 fixed voices, oldest-voice stealing with a 2 ms residual fade. GM mapping retained; MIDI 60 auditions selected slot. Velocity scales amplitude linearly. Note-off is ignored for one-shot playback. Any new hat hit chokes the existing hat voices in 2 ms, including open-hat notes. CC123/Panic releases voices in 2 ms while ambience decays; CC120 clears voices and ambience immediately.
- Four-point cubic interpolation, source-rate/host-rate compensated at 44.1/48/96/192 kHz. Extreme upward transposition is not bandlimited resampling; aliasing at high tuning needs listening review. No oversampling or unmeasured transparency claim.
- Per-slot tune ±24 semitones, gain -60 to +12 dB, linear stereo balance, normalized region start/end, attack 0–500 ms, end release 0–3000 ms, reverse, mute, solo, low-pass 40–20000 Hz. A crossed/empty region collapses to one source frame; the editor exposes numerical markers. Tune, region, envelope and reverse are captured for a new hit; gain, pan, filter, mute/solo respond during playback. Continuous live controls smooth over approximately 20 ms; expensive coefficients update every 32 samples.
- BODY is global: ±70% low-band contribution and 0.5–1.5 multiplier on the explicit end-release region. CHARACTER is global: multiplies explicit filter cutoff by 0.5–2 and introduces bounded soft drive above midpoint. SPACE is global: send into a fixed stereo 71/113 ms feedback ambience (feedback 0.32, wet 0.35). Macros do not write the detailed parameter values.
- Default slot gain -6 dB and output -6 dB provide single-hit headroom. Dense hits and positive gain can exceed 0 dBFS. The meter measures output sample peaks with a clipping latch; it is not a true-peak meter or a limiter. Only non-finite output is replaced by zero. Mono output averages stereo.
- Algorithmic lookahead latency: zero samples. Tail report: conservative 128 seconds, including 30-second samples slowed by two octaves plus ambience. Driver/interface latency is separate.

## State and portability

Version 2 stores both A/B banks, names, all parameters, relative content references and active bank. Version 1 validates and migrates the four controls onto the factory kit. It does not recreate old synthesis timbres; recover those sessions with the preserved 0.1.0 implementation. Malformed and future states are rejected before current parameters/snapshot change. Missing managed files recall as explicit missing/silent slots and can be relinked using Load Sample.

`.dhpreset` is bounded JSON with local content references. `.dhkit` is a portable container: `DHKIT2\r\n`, little-endian manifest byte length, UTF-8 manifest, little-endian blob count, then 64-byte lowercase hash keys, 64-bit byte lengths and uncompressed original WAV/AIFF bytes. Factory sounds resolve to embedded IDs. No filenames, directories, links or compression are expressible. Duplicate keys, invalid hashes, oversized/truncated/trailing data and invalid state are rejected; ZIP files are rejected. File imports may add valid hash-addressed cache entries before a later error, but never partially replace the current kit. There is no deletion of user cache data. Portable export requires a separate explicit confirmation that all referenced samples in both banks may be redistributed.

## Acceptance budgets declared before sampler measurements

Sustained 10-second wall-time numerical workload, Release x64, 48 kHz, 128 frames, dense 16-voice retriggering: callback p95 <= 0.666667 ms (25% of the 2.666667 ms deadline). Retain p50/p95/p99/max, hardware and exact binary. A p95 pass does not conceal missed maximum deadlines and is not host dropout evidence. Loading-time budget: target under 500 ms for each supplied short WAV on this machine, with observed maxima retained; larger user assets have the hard size/duration bounds above. Peak/RMS and decode metadata must accompany listening examples. No weakening of a failed budget.

## Current gap matrix (execution evidence is recorded separately)

| Requirement | Implementation surface | Acceptance still required |
|---|---|---|
| Starter content | Seven embedded original WAVs + origin manifest | Human musical/category approval |
| Decode/publication | SampleLibrary + worker + hazard pointer | Failure/race/allocation checks |
| Playback/shaping | SampleEngine + 82 stable parameters | Numerical/processor matrix + listening |
| Presets/A/B/portability | v2 state, JSON preset, bounded hash container | Roundtrip and hostile-input tests |
| Native editor | Seven pads, cached waveform, 8 detail controls, 3 global macros, output | Built screenshots, native interaction/DPI and FL Studio |
| Release | Versioned local staging only | Validators, host session, clean-machine, framework eligibility, legal/product terms |

Commercial release is not inferred from implementation. No purchase, signing, publication or installed-release overwrite is authorized by this work.
