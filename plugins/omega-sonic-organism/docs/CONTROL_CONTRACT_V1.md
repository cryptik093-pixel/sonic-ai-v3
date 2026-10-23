> V4 extension: contract version 2 adds IDs 115 Step Depth, 116 Step Pattern and
> 117 Chamber Coupling. Default new values retain exact OSO1 bytes; enabled V4
> state uses explicitly versioned OSO2. See [integration details](V4_INTEGRATION_2026-10-23.md).
> The v1 description below records the retained legacy subset.

# Host control contract v1

Contract name: `omega-sonic-organism.host-control`, version `1`.
Transport: existing VST3 controller, parameter queues, event input and native
state streams. No network service or Sonic AI connection is introduced.

Run `omega_control_probe.exe <absolute-module.vst3> <output.json>` to load the
actual DLL and discover its factory version, class identity, controller
parameters, defaults, units, ranges and flags. The probe verifies all fifteen
permanent sound parameters against the compiled registry. Preserve its JSON
beside the module checksum; discovery is not an orchestration acceptance test.

## Operations

| Operation | Existing mechanism | Contract |
|---|---|---|
| Parameter discovery | `IEditController::getParameterInfo` and plain/normalized conversion | IDs 100–114 retain existing meanings; 1000–1003 are MIDI control mappings; 1010–1013 are read-only meters |
| Instrument identity/version | DLL `GetPluginFactory`, `IPluginFactory2` | Existing processor/controller CIDs; report actual factory version rather than inferring V4 readiness from a filename |
| Safe macro edits | VST3 edit gestures and timestamped parameter queues | IDs 100 Morph, 101 Energy, 102 Motion, 103 Material, 104 Space, 105 Output; finite normalized values 0–1; honor step counts and automation flags |
| Preset selection | Existing validated JSON import or factory selection | A preset supplies all fifteen sound values; use the existing parser and normal edit gestures; never invent a new host parameter for preset indices |
| Project state | `IComponent::getState/setState` | Unchanged OSO1 schema 1, fifteen-value 140-byte current encoding; existing 6–15-value legacy reads remain supported |
| Offline render | Existing host MIDI events, tempo context and offline processing | No file/network work in the audio callback; the host writes the audio and its metadata |

The processor accepts a complete validated host state into a fixed-size
publication slot. The audio thread consumes a coherent snapshot at a callback
or lifecycle boundary. Host producers serialize outside `process`; callback
reads/stores are bounded lock-free atomics. Host capture uses at most eight
coherent-read attempts and returns `kResultFalse` under sustained contention
instead of serializing a torn state. Check the result before saving a project.
VST3 lifecycle operations such as reconfiguration and activation must retain
their host-prescribed sequencing relative to processing.

## Offline render provenance

Record `contractVersion`, `moduleSha256`, `nativeStateSha256`, `presetId`,
`sampleRate`, `frames`, `tempo`, `eventStreamSha256` and `audioSha256` in a
sidecar. Derive hashes from actual files/bytes and record the host and build
manifest. A matching parameter description does not prove matching audio.
Never store credentials, machine-specific preset paths or network operations
inside native state.

The experimental 16-step lane, modulation contour and coupled-chamber model
currently have no host-visible control/state extension. Do not send invented
IDs or claim those experiments are playable features. Integrating and
persisting them, and demonstrating Sonic AI/OS end-to-end control, remain
separate acceptance work.
