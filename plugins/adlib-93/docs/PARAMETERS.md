# ADLIB-93 parameter and persistence contract

The single production registry is `src/core/Parameters.cpp`; `parameterDefinitions()` returns its fixed 70 entries in stable `Param` order. IDs are never repurposed. All snapshots own exactly 70 floats, are trivially copyable, and contain no strings, pointers, captured audio or allocations.

Values are physical Hz, milliseconds, seconds, dB, BPM or fractions. Pan is −1…1; Mix/width/ping-pong/diffusion are 0…1; feedback is 0….9. UI percentages multiply these fractions by 100. Frequencies below are Hz, including the 6000/8000/6000 Hz de-ess/delay-LP/reverb defaults. Frequency controls use logarithmic host/UI normalization. DSP clamps effective cutoffs to 0.45 Fs while retaining requested stored values.

| IDs | Range | Init |
|---|---|---|
| input.gain | −24…24 dB | 0 |
| gate.enabled | boolean | 0 |
| gate.threshold | −80…−12 dBFS | −50 |
| gate.attenuation | 0…80 dB | 30 |
| gate.attack / gate.hold / gate.release | .5…20 / 0…250 / 20…500 ms | 2 / 50 / 120 |
| deess.enabled / deess.listen | boolean | 0 / 0 |
| deess.frequency | 3000…12000 Hz, logarithmic | 6000 |
| deess.threshold / deess.maxReduction | −60…0 dBFS / 0…12 dB | −24 / 6 |
| character.enabled / character.hpEnabled / character.lpEnabled | boolean | 0 |
| character.mode | 0 clean, 1 soft, 2 hard, 3 asymmetric | 0 |
| character.hp / character.lp | 20…1000 / 1000…20000 Hz, logarithmic | 20 / 20000 |
| character.drive / character.trim | 0…24 / −24…12 dB | 0 / 0 |
| direct.level | branch level, below | 1 (0 dB) |
| double.enabled | boolean | 0 |
| double.delayL / double.delayR | 8…40 ms | 14 / 22 |
| double.depthL / double.depthR | 0…6 ms | .4 / .4 |
| double.rateL / double.rateR | .05…2 Hz | .3 / .3 |
| double.level | branch level | 0 (mute) |
| chorus.enabled | boolean | 0 |
| chorus.delay / chorus.depth / chorus.rate | 5…25 ms / 0…5 ms / .05…5 Hz | 15 / 3 / .8 |
| chorus.level | branch level | 0 (mute) |
| stereo.pan / stereo.width | −1…1 / 0…1 | 0 / 1 |
| delay.enabled / delay.sync | boolean | 0 / 0 |
| delay.time | 10…4000 ms | 250 |
| delay.division | 0 1/32, 1 1/16, 2 1/8, 3 1/4, 4 1/2, 5 bar | 2 |
| delay.modifier | 0 straight, 1 dotted, 2 triplet | 0 |
| delay.manualBpm | 30…300 BPM | 120 |
| delay.feedback / delay.pingpong | 0….9 / 0…1 | 0 / 0 |
| delay.hp / delay.lp | 20…1000 / 1000…20000 Hz, logarithmic | 100 / 8000 |
| delay.diffusion | 0…1 | 0 |
| delay.level | branch level | 0 (mute) |
| delay.throwMode | 0 continuous, 1 throw-only | 0 |
| throw.active / throw.latch | boolean | 0 / 0 |
| reverb.enabled | boolean | 0 |
| reverb.predelay / reverb.decay | 0…150 ms / .2…12 s target RT60 | 20 / 2 |
| reverb.damping | 1000…20000 Hz, logarithmic | 6000 |
| reverb.level / reverb.delaySend | branch level | 0 / 0 (mute) |
| duck.enabled | boolean | 0 |
| duck.threshold / duck.maxReduction | −60…0 dBFS / 0…18 dB | −30 / 6 |
| duck.attack / duck.release | 1…50 / 50…1000 ms | 5 / 250 |
| freeze.active | boolean | 0 |
| mix.amount | 0…1 | 1 |
| routing.mode | 0 Insert, 1 Send | 0 |
| bypass.internal | boolean | 0 |
| output.gain | −24…12 dB | 0 |
| limiter.enabled | boolean | 1 |
| limiter.ceiling / limiter.release | −12…−.1 dBFS / 20…500 ms | −1 / 100 |

Branch levels have stored normalized value `v=0` for exact mute; any `v>0` maps to `−60+60v` dB, then amplitude `10^(dB/20)`. `levelFromDb`, `levelToDb`, and `levelToGain` implement this contract. The limit approaching zero is −60 dB; exact zero is −∞ and produces exactly zero amplitude.

`sanitizeSnapshot` replaces non-finite values with each schema default, clamps continuous ranges and rounds boolean/choice values. Parameter normalization is finite, bounded and logarithmic only where the registry marks it. No sample-rate-dependent changes are written into durable cutoff settings.

## Transfer and state

The VST3 wrapper also exposes JUCE's standard persistent host `Bypass` metadata
parameter. It is separate from the 70-entry product registry and from transient
`bypass.internal`; existing product IDs and their value semantics are unchanged.

`SnapshotMailbox` has four fixed ownership slots with atomic Free/Writing/Ready/Reading state. Producers claim a free slot or replace an unconsumed Ready slot; the single audio consumer claims Ready→Reading before touching the snapshot. Producers cannot mutate Reading slots, and the consumer cannot read Writing slots. Atomic generations select the newest published state. All loops have fixed bounds; no audio locks, heap retirement or data-racing seqlock are used. `tryPublish` can fail when all four slots are actively owned by competing producers; the caller retains its latest request off the callback. Concurrent host/editor producers should be serialized off audio by the adapter, which also owns parameter notifications.

State schema 1 is UTF-8 JSON bounded to 256 KiB and parser depth 32. It contains full processing values, full A/B snapshots, active slot, locks, UI scale/page/preset/modified status. `decodeState` rejects invalid JSON, duplicate keys, invalid numeric types, non-finite/out-of-range/integral-choice values, oversized input and unsupported schema. Missing known fields use Init; unknown fields are parsed and ignored. Invalid state returns `success=false`, useful error text and safe Init; the caller decides how to display an error off audio. Serialization and parsing are off-thread only.

Throw, Freeze, Listen and internal bypass are always off in serialized/recalled snapshots. Captured audio and host-tempo values are never stored. Manual BPM is an ordinary stable parameter. Preservation locks default on for input gain, every gate parameter including enable, and output gain. Preset browsing/A–B use `applyCalibrationLocks`; project recall uses the complete decoded state directly and ignores browsing locks.

## Factory and user presets

`factoryPresets()` exposes 24 immutable complete snapshots with exact approved IDs/names, grouped into Tight, Moving, Atmospheric, Textured, Modulated and Dramatic. All recipes materialize from Init plus the specified factory de-ess base; named modules/filters are enabled and unlisted branches stay muted. Frozen Tail includes its active delay/diffusion/send; Distorted Echo mutes direct and sets Mix=.45. Sonic usefulness remains subject to listening acceptance.

User files live under the OS user-data directory `Omega House Studio/ADLIB-93/Presets`. Display names never form paths. Random 32-hex internal IDs form `.json` filenames; save writes a unique temporary file then atomically replaces its target (Windows `MoveFileExW` with replace/write-through). Reads validate canonical containment, filename and 256 KiB limit before decoding. Unsafe/traversal/reserved Windows display names and malformed parameter values are rejected. File operations are never called by DSP.
