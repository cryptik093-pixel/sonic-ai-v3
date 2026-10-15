# Omega House ADLIB-93 — Engineering Specification v1

Date: 2026-10-15 · Owner: Omega House Studio LLC / Daniel Webster Sutton

Status: consolidated design for written-spec review. Product purpose, routing, initial preset recipes and interface direction have conversational approval. The implementation details and acceptance budgets below are proposed engineering requirements. No plugin binary, DSP measurement, listening validation or Windows host test is claimed by this document.

## 1. Product contract

ADLIB-93 is a local vocal multi-effects VST3 audio effect for recording and mixing vocal ad-lib tracks. It transforms an incoming human vocal performance. It does not generate words, voices, performances or ad-libs. Its 24 factory presets are combinations of shared, editable DSP modules, not 24 unrelated algorithms.

Primary platform: Windows x64, FL Studio. Support mono→mono, mono→stereo and stereo→stereo main buses; reject unsupported layouts explicitly. Mono output is the arithmetic average of the internally processed stereo output. No MIDI input/output, external sidechain, instrument hosting, cloud inference, account system or paid service dependency in V1. The 1993 reference describes an original pedal-inspired appearance, not hardware emulation or a claim of historical authenticity.

Success: a vocalist can load the effect on an ad-lib track, choose a distinct useful preset, adjust it, automate throws, record while monitoring, save/reopen the project and render the same processing offline.

V1 excludes pitch/formant shifting, pitch correction, voice cloning, MIDI refinement, stem separation, convolution IR management and a mastering/true-peak guarantee. Distortion aliasing is an audible quality risk because V1 has no oversampling; evaluate it explicitly before release.

## 2. Signal contract

Let x be input after input trim. Mono input is duplicated at unity to the internal stereo pair. Let c be gate→de-esser→character(x). Branches derived from c are direct character, double, chorus, delay and reverb. Reverb receives c plus a separately scaled delay return. Double and chorus do not enter the delay. Diffusion is inside the delay feedback network. Normal delay feedback comes from its filtered/diffused return, before branch level, ducking or output limiting.

Wet sum = positioned direct character + double + chorus + ducked(delay + reverb) + frozen layer. Branch gains are linear amplitude gains converted from dB. A stereo position stage applies pan/width to the complete wet sum; dry remains unchanged. The frozen layer is not fed back to delay/reverb or recorded into its own capture history.

Insert output before gain/limiting = (1−mix)×x + mix×wet. Use linear crossfade, not equal-power: when clean direct wet equals dry, blend must not create a midpoint gain bump. At 0% Mix the original trimmed vocal remains; at 100% Mix the direct processed voice remains unless its branch is muted.

Send mode forces effective Mix to 100% and direct character level to mute. UI shows these effective overrides without destroying stored Insert values. Returning to Insert restores them. Do not add the dry vocal during internal bypass in Send mode: stop new wet input and let tails decay to silence. Insert bypass transitions to x while tails decay. Both paths retain output gain and enabled limiter. Host bypass is host-dependent and must be tested separately.

Final order: blend→output gain→optional stereo-linked sample-peak limiter→meter. No output gain follows the limiter. Limiter is enabled in Init and all factory presets.

Ducking detector: stereo-linked peak envelope of x, after input trim and before gate/de-esser/character. No lead-vocal sidechain is implied. Only delay/reverb returns are ducked; their internal feedback is unchanged. Frozen layer is not ducked in V1.

## 3. Parameters and neutral initialization

All ranges refer to physical units, not undocumented normalized knob values. Stable IDs below must never be repurposed after release. Numeric input clamps to supported ranges and rejects non-finite values. Level controls use normalized value 0 for exact mute and map remaining travel monotonically over −60…0 dB, showing −∞ at mute. Branch Init levels are muted except direct=0 dB.

Frequency controls are logarithmic. Effective cutoff is clamped to min(requested, 0.45×sampleRate); display the effective value when clamped. Init character filters are explicitly bypassed, not assumed inaudible at range endpoints. Coefficient updates and gains are smoothed.

| ID | Range / options | Init |
|---|---|---|
| input.gain | −24…+24 dB | 0 |
| gate.enabled | boolean | off |
| gate.threshold | −80…−12 dBFS | −50 |
| gate.attenuation | 0…80 dB | 30 |
| gate.attack | 0.5…20 ms | 2 |
| gate.hold | 0…250 ms | 50 |
| gate.release | 20…500 ms | 120 |
| deess.enabled | boolean | off |
| deess.frequency | 3…12 kHz | 6 |
| deess.threshold | −60…0 dBFS | −24 |
| deess.maxReduction | 0…12 dB | 6 |
| deess.listen | boolean, diagnostic, non-persistent | off |
| character.enabled | boolean | off |
| character.mode | clean / soft / hard / asymmetric | clean |
| character.hpEnabled | boolean | off |
| character.hp | 20…1,000 Hz | 20 |
| character.lpEnabled | boolean | off |
| character.lp | 1…20 kHz | 20 |
| character.drive | 0…24 dB | 0 |
| character.trim | −24…+12 dB | 0 |
| direct.level | mute or −60…0 dB | 0 |
| double.enabled | boolean | off |
| double.delayL / delayR | 8…40 ms | 14 / 22 |
| double.depthL / depthR | 0…6 ms | 0.4 / 0.4 |
| double.rateL / rateR | 0.05…2 Hz | 0.3 / 0.3 |
| double.level | mute or −60…0 dB | mute |
| chorus.enabled | boolean | off |
| chorus.delay | 5…25 ms | 15 |
| chorus.depth | 0…5 ms | 3 |
| chorus.rate | 0.05…5 Hz | 0.8 |
| chorus.level | mute or −60…0 dB | mute |
| stereo.pan | −100…+100% | 0 |
| stereo.width | 0…100% | 100 |
| delay.enabled | boolean | off |
| delay.sync | boolean | off |
| delay.time | 10…4,000 ms | 250 |
| delay.division | 1/32, 1/16, 1/8, 1/4, 1/2, bar | 1/8 |
| delay.modifier | straight / dotted / triplet | straight |
| delay.manualBpm | 30…300 BPM | 120 |
| delay.feedback | 0…90% | 0 |
| delay.pingpong | 0…100% | 0 |
| delay.hp | 20…1,000 Hz | 100 |
| delay.lp | 1…20 kHz | 8 |
| delay.diffusion | 0…100% | 0 |
| delay.level | mute or −60…0 dB | mute |
| delay.throwMode | continuous / throw-only | continuous |
| throw.active | boolean performance state | off |
| throw.latch | UI gesture mode | off |
| reverb.enabled | boolean | off |
| reverb.predelay | 0…150 ms | 20 |
| reverb.decay | 0.2…12 s target RT60 | 2 |
| reverb.damping | 1…20 kHz | 6 |
| reverb.level | mute or −60…0 dB | mute |
| reverb.delaySend | mute or −60…0 dB | mute |
| duck.enabled | boolean | off |
| duck.threshold | −60…0 dBFS | −30 |
| duck.maxReduction | 0…18 dB | 6 |
| duck.attack | 1…50 ms | 5 |
| duck.release | 50…1,000 ms | 250 |
| freeze.active | boolean performance state | off |
| mix.amount | 0…100% | 100 |
| routing.mode | insert / send | insert |
| bypass.internal | boolean | off |
| output.gain | −24…+12 dB | 0 |
| limiter.enabled | boolean | on |
| limiter.ceiling | −12…−0.1 dBFS | −1 |
| limiter.release | 20…500 ms | 100 |

Clear Tails is an edge-triggered command, not a continuously retriggered boolean parameter. Expose it as an automatable command edge only if host testing confirms reliable reset semantics; a visible UI action is mandatory. Selection of detail page, UI scale, locks and preset provenance are non-audio state.

## 4. DSP module requirements

### Cleanup

Gate: linked stereo detector, fixed 3 dB hysteresis; opens at threshold, closes after hold once below threshold−3 dB. Smooth gain to 0 dB on attack and to negative attenuation on release. Opening does not cut existing spatial tails. No lookahead. Detector uses a causal peak follower; the detector and gain envelopes must have explicitly documented time-constant conventions in implementation tests.

De-esser: complementary low/high crossover from one state-variable/one-pole low-pass and its residual high band, dynamically attenuating only the high band. Use identical coefficients for stereo and a linked detector from high-band peak. Fixed attack 1 ms, release 80 ms. Reduction dB = min(maxReduction, max(0, detectorDb−threshold)×0.75). This is a high-band dynamic attenuation design, not an AI sibilance classifier. At zero reduction low+high must reconstruct input to numerical tolerance. Listen auditions the detector high-band signal through output protection, overriding the normal blend; conspicuous diagnostic indicator required. Listen is excluded from presets and recall.

### Character

First high-pass then low-pass using 12 dB/octave Butterworth biquads when enabled, then saturation, then trim. Clean mode passes the filtered audio with trim and ignores Drive (disable its editor). With g=10^(driveDb/20): soft=tanh(gx); hard=clamp(gx,−1,1); asymmetric=tanh(gx+0.2)−tanh(0.2). A 10 Hz DC blocker follows saturation. No automatic loudness matching is implied by these functions. Factory trims require measurement and may be revised after audition. Hard/asymmetric modes must be auditioned for aliasing at 44.1 kHz.

### Movement and stereo

Double: two fractional-delay voices, initial LFO phases 0 and π/2, independent sinusoidal rates/depths, one voice per output channel. Chorus: two fractional-delay voices with shared rate and 90-degree phase offset. These branches contain delayed signals only, no hidden direct voice. Effective delay is clamped to at least one sample; interpolation is linear in V1. Stereo inputs retain separate L/R source channels; mono input feeds both. Reset LFO phases on prepare/reset, not every processing block.

Width: M=(L+R)/2, S=(L−R)/2; L'=M+wS, R'=M−wS, w in [0,1]. Pan is an attenuation-only stereo balance control: centered unity; moving right attenuates L to zero and vice versa. It does not synthesize stereo from mono. Mono fold-down may alter modulated/comb-filtered tone; measure and audition rather than promise mono transparency.

### Delay and diffusion

Allocate the full four-second buffer for both channels during prepare, not during audio processing. Delay time changes use two read taps with a 100 ms linear crossfade, not a sudden read-pointer jump. Modulated movement delays may smoothly interpolate their read positions. Repeated time changes must coalesce to the latest target without unbounded additional taps.

Feedback matrix = f×[(1−p)I+pX], where X swaps channels, f≤0.9 and p is ping-pong amount. Injection at p=0 is independent stereo; toward p=1 pan the mono sum into the left delay input, so a centered/mono vocal actually produces alternating repeats. Interpolate injection smoothly; explicitly test stereo input and mono fold-down. Filters and diffusion precede the feedback matrix. Add a bounded soft-saturation safeguard in the feedback path, defined as 4×tanh(x/4), rather than relying on the final output limiter for internal stability.

Diffusion: four serial all-pass sections per channel, nominal L times 3.1/4.7/7.3/11.3 ms and R times 3.7/5.3/8.3/12.7 ms, feedback coefficient magnitude ≤0.65. Amount crossfades unprocessed and diffused returns. Coefficients/times are fixed in V1; do not reinterpret the Diffuse knob as an unstable feedback multiplier.

Sync: quarter-note milliseconds=60000/BPM. Whole-bar timing uses current time signature: numerator×4/denominator quarter notes. Manual fallback assumes 4/4. Dotted multiplies by 1.5; triplet by 2/3. Clamp resulting time to [10,4000] ms and show a CLAMP indicator. Use a finite positive host tempo where available, otherwise displayed manual tempo. No host position/tempo state may be dereferenced without validity checks.

Throw-only mode normally closes delay input. Throw opens it to the current delay-send level with a 5 ms ramp, leaving feedback unchanged. In continuous mode Throw temporarily raises delay input send by 6 dB while held; this gives the button an audible function in every delay preset. Throws affect new input only. Dotted Throw loads in continuous mode, so the preset has audible echoes immediately; users can select throw-only for word isolation.

### Reverb and ducking

Use an original eight-delay feedback delay network with orthogonal Householder mixing, distinct nominal delay times 29.7/37.1/41.1/43.7/53.1/59.3/67.7/71.9 ms, stereo output sign patterns and per-line one-pole damping. Convert times to distinct sample counts during prepare. For desired RT60 T and line delay d seconds, initial line gain=10^(−3d/T). Filtering affects actual decay, so label T as target until measurements support the calibration. Do not attach a seconds label to an arbitrary room-size control. Input and output injection vectors must be normalized and documented; modulation is excluded from the reverb network in V1.

Ducking gain reduction dB=min(maxReduction,max(0,detectorDb−threshold)×0.75), using attack/release smoothing. Delay→reverb send taps the delay after its branch level but before ducking, preventing the duck detector from changing reverb excitation unintentionally.

### Freeze, transitions and clearing

Keep a preallocated rolling 250 ms stereo history of the combined delay/reverb return after ducking and before the frozen layer. On Freeze rising edge, capture a stable completed history window through an audio-thread state-machine/buffer handoff; do not copy a 250 ms buffer in one callback. The held voice loops that window using 20 ms complementary overlap crossfades, at unity gain. Crossfade the normal spatial return to the frozen voice over 50 ms, suppress new delay/reverb excitation, and continue decaying the underlying network while held. Frozen audio is not recursively captured or fed back. No pitch preservation promise: this is a short texture loop.

On Freeze release, fade the frozen voice out and resume normal spatial input/return over 250 ms. Freeze on silence stays silent. Clear Tails uses a 20 ms fade, resets spatial buffers through a bounded per-block clearing process, then restores normal input; never clear large buffers in one real-time callback. Disable controls that conflict during this short clear transition and show status.

Preset selection/A–B: use two preallocated complete effect engines, incoming initialized and zeroed incrementally on the audio thread before transition, then a 50 ms linear crossfade. Coalesce rapid requests to the latest snapshot. No dynamic engine allocation. Old tails fade with the old engine; they are not promised to survive preset changes. Single-parameter automation uses module smoothing and does not instantiate a second engine. Filter/mode/module changes crossfade or smoothly transition with bounded state. Freeze/Throw release when manually loading presets or changing A/B; automation can re-engage afterward.

### Limiter and exceptional data

Zero-lookahead stereo-linked sample-peak protection: p=max(abs(L),abs(R)); requiredGain=min(1,ceilingLinear/max(p,epsilon)); gain attacks immediately to a lower required gain and releases exponentially toward unity, never exceeding the current required gain. This bounds output samples at the ceiling but may distort transients. It is not a transparent mastering limiter and does not guarantee reconstructed intersample peaks. Non-finite input samples are replaced with zero. If a DSP state becomes non-finite, mute/reset that module through a bounded recovery and expose a diagnostic count outside the audio callback. No audio-thread logging. Denormals must be suppressed.

## 5. Factory bank

Factory base is Init with de-esser enabled, frequency 6 kHz, threshold −24 dBFS, max reduction 4 dB; Insert mode, Mix=100%, gate off, limiter on at −1 dBFS. Whenever a recipe names an effect, its enable flag is on; named character filters also enable Character in Clean mode unless a saturation mode is named. Unlisted effect branches remain muted/disabled. Any named ducking uses base threshold −30 dBFS, attack 5 ms and release 250 ms unless overridden. Reverb predelay defaults 20 ms, damping 6 kHz. Delay filters default HP=100 Hz/LP=8 kHz. Double depth/rate defaults 0.4 ms/0.3 Hz per voice, width=100%. Delay→reverb send is muted unless explicitly changed. All recipes have Throw/Freeze off, delay mode continuous, internal bypass off and diagnostic Listen off.

Numbers are starting recipes, not validated sonic outcomes. Factory input/output gain=0 dB; revise internal branch levels/character trims after level-matched audition. Persist a complete parameter map per preset rather than a partial delta, to prevent settings leaking between presets.

| ID / name | Exact overrides from factory base | Intended identity |
|---|---|---|
| 01 Pocket Double | Double delays 14/22 ms, depth 0.4/0.4 ms, rates 0.3/0.3 Hz, level −12 dB; width 70% | Close reinforcement |
| 02 Short Slap | Delay 90 ms, feedback 8%, level −12 dB, LP 6 kHz | Dark slap |
| 03 Tight Answer | Delay synced 1/16 straight, feedback 18%, level −10 dB; duck max 6 dB | Compact rhythmic reply |
| 04 Dry Bite | HP 120 Hz, LP 9 kHz, soft drive 6 dB, trim −4 dB; Mix 65% | Forward mild grit |
| 05 Left–Right Reply | Delay synced 1/8 straight, feedback 30%, ping-pong 100%, level −10 dB; width 100% | Alternating repeats |
| 06 Quarter Bounce | Delay synced 1/4 straight, feedback 38%, ping-pong 75%, level −12 dB; duck max 8 dB | Slow stereo bounce |
| 07 Dotted Throw | Delay synced 1/8 dotted, feedback 35%, ping-pong 100%, level −9 dB | Syncopated echoes; Throw adds emphasis |
| 08 Stereo Orbit | Chorus delay 18 ms, depth 4 ms, rate 0.22 Hz, level −9 dB; delay synced 1/8 straight, level −18 dB, feedback 20% | Slow animated width |
| 09 Ghost Room | Direct −6 dB; reverb predelay 12 ms, decay 1.8 s, level −8 dB; character HP 180 Hz; Mix 85% | Soft distance |
| 10 Diffused Halo | Delay synced 1/8 straight, feedback 35%, diffusion 75%, level −14 dB; reverb decay 3.5 s, level −12 dB | Dense halo |
| 11 Long Goodbye | Delay synced 1/4 straight, feedback 55%, level −12 dB; reverb decay 6 s, level −14 dB; duck max 10 dB | Long post-phrase bloom |
| 12 Frozen Tail | Direct −6 dB; reverb decay 8 s, level −8 dB; delay enabled, time 250 ms, feedback 0%, diffusion 85%, level −18 dB, delay→reverb send −6 dB | Long diffused texture ready to hold |
| 13 Phone Booth | HP 450 Hz, LP 3.2 kHz, soft drive 4 dB, trim −3 dB | Narrow phone tone |
| 14 Radio Bite | HP 250 Hz, LP 4.5 kHz, asymmetric drive 10 dB, trim −7 dB; delay 70 ms, level −16 dB, feedback 5%; Mix 90% | Rough broadcast tone |
| 15 Worn Tape | HP 100 Hz, LP 6.5 kHz, soft drive 7 dB, trim −5 dB; chorus delay 12 ms, depth 0.6 ms, rate 0.35 Hz, level −6 dB; Mix 85% | Dark gentle instability |
| 16 Broken Speaker | HP 350 Hz, LP 3.8 kHz, hard drive 16 dB, trim −12 dB; Mix 70% | Deliberate abrasion |
| 17 Chorus Crowd | Double delays 19/31 ms, level −9 dB; chorus delay 15 ms, depth 3 ms, rate 0.8 Hz, level −12 dB; width 100% | Ensemble-like thickness |
| 18 Uneven Double | Double delays 11/34 ms, rates 0.27/0.41 Hz, depths 0.8/1.3 ms, level −8 dB | Asymmetric doubling |
| 19 Slow Drift | Chorus delay 20 ms, depth 4 ms, rate 0.08 Hz, level −6 dB; reverb decay 2 s, level −18 dB | Floating modulation |
| 20 Metallic Reply | Delay 12 ms, feedback 65%, diffusion 0%, level −12 dB, HP 500 Hz, LP 8 kHz; Mix 80% | Comb resonance |
| 21 Tunnel Call | HP 200 Hz, LP 5 kHz; delay 160 ms, feedback 42%, level −12 dB; reverb decay 4 s, level −10 dB | Enclosed distance |
| 22 Distorted Echo | Asymmetric drive 12 dB, trim −8 dB; direct muted; delay synced 1/8 straight, feedback 40%, level −6 dB; Mix 45% | Original plus driven repeats |
| 23 Ducked Cathedral | Reverb predelay 45 ms, decay 9 s, level −6 dB; duck max 12 dB, attack 5 ms, release 450 ms | Large post-phrase space |
| 24 Feedback Bloom | Delay synced 1/4 straight, feedback 78%, diffusion 60%, level −14 dB; reverb decay 5 s, level −16 dB; duck max 10 dB | Accumulating bounded texture |

Frozen Tail clarification: the approved recipe requested 85% diffusion but had no active delay path, so that knob would have been inaudible. The explicit low-level diffused delay and delay→reverb send above make it functional. This is a proposed technical correction to review, not a measured tuning result.

## 6. Interface and interactions

Base 1040×680 logical pixels, proportional scale 75–150%. Charcoal metal, dark rubber rails, bone-white labels, restrained cyan accents, amber preset display, ribbed knobs, three broad performance switches. Original artwork; no copied hardware branding or nonfunctional jacks/controls. Minimum-scale labels must remain readable at Windows display scaling 100/150/200%; permit scrolling of detail content rather than shrinking text below 12 logical pixels.

Top: preset number/name, previous/next, searchable factory/user browser grouped into Tight / Moving / Atmospheric / Textured / Modulated / Dramatic, modified marker, Save As, Reset, A/B, Copy A→B or B→A, Insert/Send, input trim and preservation locks.

Main row 1: Gate threshold / De-ess max reduction / Drive / Double level / Echo level. Main row 2: Diffuse amount / Space reverb level / Duck max reduction / Mix / Output gain. Each knob controls precisely the named parameter; module enable is separate. Clicking the label opens its detail page. Drag, fine modifier, keyboard adjustment, numeric entry and double-click default supported. Disabled/overridden controls show why; changing a branch level does not silently bypass another module.

Fixed detail area tabs: Clean (gate/deess/listen); Character (mode/filters/trim); Movement (double/chorus/pan/width); Echo (time/sync/feedback/ping-pong/filters/diffusion/throw); Space (reverb/send/duck); Output (direct level/limiter/locks).

Bottom: Bypass, Throw and Freeze; separate smaller Clear Tails. Throw momentary by default, with visible latch option; release on lost focus in momentary mode. Freeze latches with unmistakable held indicator. Listen prominently marked. All interactive controls have keyboard focus, accessible names and visible state beyond color.

Meters: input peak, output peak, peak-hold reset, gate attenuation, deess reduction, limiter reduction, stereo correlation, host/manual tempo, clamp and diagnostic status. Input meter is after input trim; output meter is after limiter. Refresh ≤30 Hz using atomic snapshots, no UI polling of mutable DSP buffers. Correlation window 300 ms; display neutral/unavailable below −80 dBFS or in mono-output mode rather than inventing stereo information. Sample peaks are labeled as such.

Preset browser navigation alone does not load; click/Enter loads. Dirty preset changes remain recoverable through A/B or Save As; do not imply a complete undo history. Reset restores preset values under current preservation locks; offer an explicit full reset that clears locks only when requested. Locks cover input trim, all gate parameters including enable, and output gain; default on for factory/user browsing. Project recall ignores browsing locks and restores full saved state exactly. A/B changes effect settings, honoring the same calibration locks.

## 7. State, architecture and threading

Recommended build: C++17, CMake, JUCE, Windows x64 VST3. Inspect the actual Codex repository and available VST-builder skill first; preserve existing plugin IDs and approved projects. If no project exists, use a new isolated ADLIB-93 folder. Do not invent a plugin-builder skill or claim it was invoked. Pin an exact tested framework revision in the eventual implementation plan; select the applicable JUCE license before distributing binaries. No paid dependencies are authorized.

Boundaries:

| Component | Responsibility / interface |
|---|---|
| ParameterRegistry | IDs, ranges, text conversions, defaults; single source of truth |
| StateCodec | Versioned snapshots, validation, migrations; no audio-thread serialization |
| PresetBank / PresetStore | 24 complete factory maps; atomic user file writes off thread |
| AdlibEngine | prepare(sampleRate,maxBlock,layout), reset(), process(block,parameterSnapshot) |
| Cleanup / Character / Movement / Echo / Space / Freeze / Output | Owned buffers and bounded DSP only |
| TransitionController | Two-engine preset transition and coalesced pending request |
| MeterBridge | Atomic measurements from audio thread to editor |
| PluginProcessor | JUCE/VST3 buses, host tempo/state/latency integration |
| PluginEditor | Native JUCE controls/rendering, no WebView/network dependency |
| DspHarness | Standalone test executable using the exact production DSP |

Parameter values can be read from framework-provided atomics; audio engine owns mutable DSP state. Preset/state decoding happens off the audio thread and transfers a fixed-size validated snapshot via a bounded lock-free mailbox. Host parameter notification and UI changes follow framework threading requirements, not calls from inside DSP. Avoid calling state copy/replace/serialization from processBlock.

No allocation/deallocation, blocking mutexes, disk/network calls, logging, resizing buffers, exceptions or GUI work in the audio callback. Allocate both engines and capture history in prepare. Process arbitrary host block sizes using bounded chunks if larger than prepared maximum. Handle zero-sample blocks and changing sample rates through lifecycle preparation. No parallel worker scheduling dependency on a real-time callback.

State schema version=1 includes full parameters, routing, preset identity/modified status, preservation locks, A/B snapshots, UI scale/tab and last manual BPM. Save parameters, not circular audio buffers. Throw, Freeze, Listen and internal bypass resume off on restore; capture memory is not saved. Distinguish stable processing settings from transient performance state in tests. Tempo comes from the host at playback, not a stale saved host BPM.

User presets: versioned UTF-8 JSON in the OS per-user application-data area, safe filename handling, atomic replace, maximum 256 KiB read size; reject malformed types/non-finite values; fill missing known parameters from schema defaults; ignore unknown future fields while flagging incompatible major schema versions. Corrupt host state falls back safely without crashes or audio-thread filesystem reads. Display a useful error off thread. No raw vocal audio is written by preset/project persistence.

## 8. Latency and tail policy

Target zero added algorithmic through-path latency: no lookahead, oversampling or block FFT. Intentional echo/double/reverb timing is not through-path latency. Report actual processing latency to the host; never report zero merely to meet marketing. Device/driver/DAW monitoring latency remains separate and must be measured on the user's verified hardware.

Declare a conservative finite 180-second normal tail upper bound after input stops: fade/reset residual normal spatial state during the last second if it has not decayed below −100 dBFS. This avoids a false infinite tail from high feedback, filtering or safety saturation. Freeze is an intentional indefinite hold; full frozen duration must be automated with release or manually bounded by the host export range. Host tail APIs cannot replace setting a deliberate song/render end. Verify that FL Studio does not suspend held freeze audio and document its actual render-tail setting. Clear Tails explicitly ends the hold.

## 9. Acceptance plan — required evidence, not completed tests

Build output must include source, Windows Release .vst3 bundle, build instructions, dependency/license notices, complete preset definitions, test logs and an honest verification report. If Windows/FL Studio are unavailable, those checks are PENDING, not inferred from a Linux build or DSP unit tests.

| Test | Method and proposed pass criterion |
|---|---|
| Layouts/lifecycle | Exercise 1→1, 1→2, 2→2; reject others; repeated prepare/release/editor open/close; no crash |
| Sample/block matrix | 44.1/48/88.2/96 kHz; block sizes 1,16,64,128,256,512,1024 and changing/zero-size blocks; finite output |
| Dry identity | Insert, mix=0, gains=0, limiter off: max absolute error ≤1e−6 float for input within ±1 |
| Blend identity | All effects off, direct unity: mix 0/25/50/75/100% differs from dry ≤1e−6 |
| Causal latency | Neutral impulse first output at same sample, zero reported latency; distinguish intentional wet delays |
| Limiter ceiling | Stereo sweeps/transients up to +24 dBFS: abs(output)≤ceilingLinear+1e−6 when limiter on; no claim about intersample peaks |
| Stereo linking | Unequal L/R peaks produce identical limiter/gate/deess gain envelopes across channels |
| Deess reconstruction | Max reduction=0: max reconstruction error ≤1e−6; high-frequency reduction bounded by configured max within 0.2 dB on steady tones |
| Gate timing | Above/below-threshold bursts verify hold/hysteresis; gain reaches within 1% of target after five configured time constants; no spatial tail cut |
| Echo timing | Diffusion=0, feedback=0: first repeat within ±1 sample of requested time; sync tested at 60/90/120/180 BPM and 3/4,4/4,6/8 |
| Ping-pong | Mono impulse, 100% ping-pong: successive un-diffused repeats alternate dominant channels; centered input must not collapse to identical repeats |
| Feedback stability | All delay extremes and filter/diffusion combinations, limiter off: no NaN/Inf; internal states bounded; normal tail ends by 180 s |
| Reverb decay | Impulse response energy-decay analysis, mid-band nominal damping open: target RT60 within ±25% for 0.5/2/6/12 s; document frequency-dependent damping |
| Ducking | Detector tone steps: attenuation never exceeds max+0.2 dB and returns smoothly; delayed-tail feedback unchanged |
| Freeze | Captures silence silently, holds without growth, no recapture recursion, releases in 250 ms; repeated capture/clear under all blocks |
| Parameter/preset stress | 10,000 bounded random changes; rapid A/B/preset/Throw/Freeze operations; finite output, bounded callback time, no crash |
| Automation transitions | Render sustained sine and vocal under moves/switches; inspect residuals and listen for clicks; crossfades follow documented durations |
| Real-time discipline | Instrument production processing for allocation/free and forbidden locks/I/O; zero violations after prepare, including preset and freeze transitions |
| CPU budget | On recorded reference machine, 48 kHz/128 samples: one instance normal processing p99 <20% callback deadline; dual-engine transitions p99 <40%; maximum <100% over 10 min. Targets, not universal hardware guarantees |
| Memory | Stable memory over 1,000 preset switches; working DSP buffer budget ≤64 MiB at 96 kHz for both engines; separately report GUI/process footprint |
| Persistence | Full state round trip restores settings/A–B/locks within parameter precision; transient performance states off; malformed states handled safely |
| Render consistency | Same DSP, reset initial phases, equivalent parameter schedule: real-time/offline comparison within 1e−5 max absolute error; test irregular block partitions |
| Validators | Steinberg VST3 validator passes; external pluginval strictness ≥5 passes, then strictness 10 before release; archive tool versions/logs |
| FL Studio | Scan/load, all layouts actually supported by host, recording monitoring, automation, save/reopen, offline WAV export, tail handling, multiple instances and host bypass verified on Windows |
| UI | 75/100/150% plugin scale at Windows 100/150/200% DPI; no clipped essential controls; keyboard/numeric entry/labels verified |
| Preset sound | All 24 on spoken, whispered, shouted, sibilant and sung ad-libs; solo and in mix, stereo and mono; owner accepts identity/usefulness |

CPU deadline at 48 kHz/128 is 2.667 ms; 20%=0.533 ms and 40%=1.067 ms. Report CPU model, OS, compiler/build flags, framework revision, sample rate/block size, plugin count and measurement method. A failure triggers optimization or an explicit revised design budget, never an invented pass.

Preset audition set: user's cleared dry vocal recordings where available; synthetic signals are for engineering only. For perceived-level comparisons, audition at matched active-phrase RMS within 0.5 dB and monitor limiter reduction; preserve intended tails rather than automatically normalizing them away. Compare against bypass and another simple chain. No acoustic listening results exist yet.

## 10. Handoff sequence and completion boundary

1. Review this written specification, especially technical clarifications: Frozen Tail active diffusion path; continuous-mode Throw emphasis; transient Freeze capture; Send bypass; finite tail bound; test budgets.
2. After written-spec approval, prepare a separate staged implementation plan and final Codex prompt. Do not substitute a generic one-shot 'build a professional plugin' request.
3. Codex first inventories repository, existing skills, compiler, CMake, framework, Windows runtime and host availability; pins exact dependencies and produces a minimal scan/load/state build.
4. Implement and test cleanup/output, then character/movement, then delay/diffusion/reverb, then performance states/presets/UI. Preserve source sessions and other approved plugins.
5. Validate Windows VST3/FL Studio and audition factory presets. Only then claim a usable binary or publish before/after demonstrations.

Pre-Codex design work does not certify a commercial release. Release claims must be backed by a real build, host tests and listening acceptance. Pricing, checkout and marketing claims are outside this engineering spec; the useful eventual proof asset is a dry/wet ad-lib demonstration recorded through the actual plugin.

## 11. Primary technical references

These support framework/host capabilities, not the unmeasured audio quality of the proposed algorithms. Retrieved 2026-10-15.

- JUCE state/parameters: https://docs.juce.com/master/classjuce_1_1AudioProcessorValueTreeState.html
- JUCE delay line and modulation: https://docs.juce.com/master/classdsp_1_1DelayLine.html
- JUCE delay buffer allocation restriction: https://github.com/juce-framework/JUCE/blob/master/modules/juce_dsp/processors/juce_DelayLine.h
- JUCE latency/tail interfaces: https://docs.juce.com/master/classjuce_1_1AudioProcessor.html
- JUCE smoothing: https://docs.juce.com/master/classjuce_1_1SmoothedValue.html
- JUCE licensing entry point: https://juce.com/get-juce/
- Steinberg VST3 validator: https://steinbergmedia.github.io/vst3_dev_portal/pages/What%2Bis%2Bthe%2BVST%2B3%2BSDK/Validator.html
- Tracktion pluginval: https://github.com/Tracktion/pluginval

## 12. Design review record

Conversational approvals: purpose/scope; routing/control ranges; 24 starting recipes; pedal interface direction. Written-spec review remains pending. Local document checks are allowed; implementation/build/testing of the product is deferred to the approved Codex plan. No automated audio tests were run during this design session.
