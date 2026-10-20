# M2 DSP validation record

Status: partially validated; CPU gate FAILED. This is not a commercial release.
The M1 archive and its historical report remain separate. Playback has no
Temporal, network, Sonic service or cloud dependency.

## Captured baseline

The 0.2.0-alpha baseline binary SHA-256 is
`7ee74e6f4b95168d42ed31bbb5ad264470d0aac761910a33387cfbec0eff1454`.
Its bundle is retained in `test-results/m2-before-lookup-optimization.vst3`.
The permanent component IDs and original fifteen parameter IDs are unchanged.
Native schema 1 remains 140 bytes. Hidden performance MIDI IDs are documented
in `contracts/midi-mapping.json`; they are not patch fields.

`tools/build-windows.ps1 -Jobs 1` completed successfully after fixing a missing
`<string>` include in the measurement executable. The four CTest suites passed:
core, state, expanded engine and native adapter. The complete build/test log is
`test-results/m2-vst-build-retry.log`. The clean earlier attempt and initial
failure logs are retained. The expanded matrix covers five rates, both quality
modes, all MIDI pitches, parameter extremes, mono glide, sustain, note IDs,
voice stealing, state validation and sample-offset MIDI mapping. C++ allocation
probes cover the measured operations; this is not a universal allocator audit.

`tools/validate-windows.ps1` completed with standard, extensive and pluginval
level 5 exit codes zero. Evidence is in
`test-results/validator-20261019-001013/`; the before/after binary hash matched.
The GUI skip flag was false, but there is no custom editor to validate.

The actual binary probe passed 27 cases in each quality mode. Each render was
bit-identical after destroying/recreating the component and restoring native
state. Logs: `test-results/m2-binary-probe-{eco,hq}.log`; WAVs:
`test-results/m2-renders-{eco,hq}/`. This is not FL Studio or listening proof.

## Audio measurements

Reproduce the recorded baseline with `omega_engine_metrics.exe <folder> 30`
and `python tools/analyze_engine_metrics.py <folder>`. Complete inputs, raw
float captures, benchmark results and analysis are in `test-results/m2-metrics/`.
The coherent 10.047 kHz drive fixture measured 29.02 dB lower nonfundamental
energy in HQ, with 0.001 dB fundamental gain difference. This specific component
experiment is not a general instrument aliasing score or an audibility claim.

Twenty steady pitched cases across four anchors and five notes measured a
maximum 0.310-cent root error and worst finite-window DC of −86.92 dBFS.
The estimator was calibrated against synthetic tones; percussion was excluded
because it is intentionally noisy and inharmonic. Proposed 10 dB alias and
5-cent tuning criteria passed; the blueprint −60 dBFS DC criterion passed.

## Failed CPU gate

Machine: Intel Core i5-4310U, 2 physical / 4 logical cores. OS evidence is in
`test-results/m2-hardware-os.json`. This is a laptop, not the unspecified
reference desktop. The actual processing missed both the reference goals and
the 5.333 ms callback deadline on this machine; neither criterion is waived.

The exact run used 16 voices, 48 kHz, 256 frames, 5,625 callbacks per mode,
30 nominal seconds per mode, two Morph sweeps, Energy .65, Motion .7,
Material .65 and Space .3. All slow callbacks remained included.

| Mode | Median ms | P95 ms | P99 ms | Maximum ms | Deadline overruns |
|---|---:|---:|---:|---:|---:|
| Eco | 8.3631 | 14.1700 | 26.3899 | 90.1361 | 5,619 |
| HQ | 30.7848 | 196.1320 | 427.9870 | 1,236.7700 | 5,625 |

Both modes recorded zero nonfinite faults. Wall-clock callback costs include
scheduling delays. These are production-core measurements outside a DAW.
They cannot establish host CPU usage or identify a hotspot by themselves.

A bounded sine-phase wrapping optimization is under validation. It replaces
general floor with exact integer truncation only in the nonnegative [0,8)
oscillator domain and preserves the general path elsewhere. No CPU improvement
is claimed until the same benchmark is repeated. The baseline remains intact.

## Remaining gates

CPU optimization and repeat evidence, listening review, custom VSTGUI editor,
thirty reviewed/gain-matched presets, JSON patch workflows, FL Studio playback,
automation, save/reopen and offline export, installation/uninstallation,
reproducible SDK bootstrap and final licensing/distribution review remain open.
Native UI automation initialization failed twice; FL Studio was not tested.
