# ADLIB-93 host processor

Implementation status: source implemented; native compile and execution results are recorded by the coordinator in `VERIFICATION.md`. This document does not certify FL Studio, listening quality or release readiness.

`PluginProcessor` adapts the production `Transitions` engine to JUCE. It exposes all 70 IDs from `ParameterRegistry` without renaming, reordering or repurposing them. APVTS atomics contain physical values: Hz, ms, dB, seconds, BPM and fractional percentages. Frequency normalization uses the registry logarithmic mapping. Branch levels retain exact mute at zero and display dB elsewhere. One inert host program avoids host program callbacks loading presets or emitting UI gestures from the audio thread.

## Audio boundary

The 70 product parameters include transient `bypass.internal`. It deliberately
does not implement VST3's persistent host bypass. JUCE supplies its standard
wrapper-owned `Bypass` parameter in addition to those 70 product IDs and stores
that host value in its private wrapper state. Host bypass invokes the existing
`processBlockBypassed` path; internal bypass still resumes off on project recall.
This separation repairs the official validator's bypass controller/persistence
failure without changing any product parameter ID or processing algorithm.

Only mono→mono, mono→stereo and stereo→stereo are accepted. There is one main input and output, no sidechain, no MIDI and no instrument bus. Mono input is duplicated at unity. Mono output uses the arithmetic mean of the internal stereo pair. In-place samples are read before their destinations are overwritten. Oversized buffers use fixed prepared-size chunks; zero-frame callbacks service only the bounded transition controller. The adapter allocates no scratch buffer inside processing and reports zero algorithmic through-path latency. The declared normal tail is 180 seconds; held Freeze is intentionally indefinite and requires a deliberate export endpoint/release.

Host timing is used only when JUCE supplies a position and finite positive tempo/valid signature. Otherwise the engine resolves the stored manual BPM and 4/4 fallback. Internal bypass and host `processBlockBypassed` both reach the production engine's Insert/Send-aware bypass behavior, output gain and limiter. No network, file, GUI, state serialization, parameter notifications or state mutex occurs in `processBlock`.

## Transactions and persistence

UI/state/preset operations serialize through an off-audio mutex. A revision counter brackets each complete APVTS update. Processing reads raw atomics once, applies automation only if the revision remained stable/even, and receives complete preset/state changes through the fixed-size ownership mailbox. A transaction is requested before applying its snapshot to the transition controller, preserving the outgoing engine during the incoming clear/crossfade. Rapid requests coalesce; no engine allocation or queue node retirement occurs in the callback. Lifecycle prepare/reset are bulk operations and require the host to suspend processing, as with JUCE's normal lifecycle contract.

The version-1 JSON codec rejects more than 256 KiB before reading and validates malformed types/ranges/schema. Full host recall restores durable parameters, A/B, locks and UI metadata irrespective of browsing locks. Throw, Freeze, Listen and internal bypass are omitted/reset by persistence. Invalid host state preserves current values and exposes an off-audio error. Audio buffers and captured vocal audio are never serialized.

Factory/user browsing honors input/gate/output calibration locks. Before browsing, the current complete durable snapshot is placed in the inactive A/B slot, so the outgoing edit remains recoverable. A/B switches capture the outgoing slot and apply calibration locks to the incoming slot. Copy duplicates the current durable values. Reset applies the loaded preset baseline under current locks; explicit Full Reset clears locks and selects Init. An optional backward-compatible schema-1 `presetBaseline` map stores the original full recipe separately from modified active values. It uses the same range/type validation and strips transient performance values. New host saves preserve user-preset Reset after reopening without rereading a user file. Old state files lacking the optional map resolve known factory baselines by name and otherwise use their saved complete snapshot. Persistence does not imply unlimited undo history or save captured audio.

User Save As and Load run outside processing through `PresetStore` in its OS-resolved per-user directory. Files use safe generated IDs, bounded JSON and atomic replacement. No application sessions, recordings or installed plugins are overwritten by this adapter.

## Measurements and testing limits

Input/output values are actual per-callback peak maxima after trim/limiter; reductions are measured maxima from the production engine. Correlation uses a preallocated, rolling 300 ms output history and double-precision running sums/covariance. It remains unavailable until a complete window is present, below −80 dBFS in either channel, on constant/zero-variance data, or for mono output. All meter fields transfer through lock-free atomics; fields are independently sampled and do not imply a transactional multi-field display snapshot. Editor refresh is capped at 30 Hz.

`Processor.Parameters`, `Processor.Layouts`, `Processor.State`, `Processor.Realtime`, `Processor.Meters`, `Processor.ConcurrentRecall` and `Processor.Editor` exercise actual production APIs. `State.PresetBaseline` covers the optional codec extension and old-file fallback. The callback hook counts C++ `new/new[]/delete/delete[]` on the calling thread; it does not instrument C allocation, aligned allocation, locks, operating-system I/O or a host's own implementation. Source review supplements it. Offscreen JUCE snapshots exercise the native component, not FL Studio loading, Windows DPI interaction or listening. Those checks remain PENDING until performed and recorded.
