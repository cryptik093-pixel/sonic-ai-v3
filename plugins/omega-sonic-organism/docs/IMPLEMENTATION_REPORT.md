# OMEGA SONIC ORGANISM — first-stage engineering report

Date: 2026-10-18. Version: 0.1.0-alpha. Status: M1 TESTED; commercially NOT READY.

This is an alpha integration milestone, not commercial release approval.
The supplied CODEX_FIRST_TASK.md defines a stop after the first audible VST3
stage, followed by a gap report. Full commercial acceptance remains G0–G5.

## Repository and tooling

Canonical root: `C:/Users/david someone/Desktop/SONIC AI V3/sonic-ai-v3`.
Branch inspected: `recovery/actual-project-state`. The checkout was already dirty.
Task changes are confined to `plugins/omega-sonic-organism`; unrelated plugin,
API, web, database and studio sources are preserved.

Compiler: MSVC 19.51.36256 x64, CMake 4.3.1-msvc1, Ninja, Windows SDK
10.0.26100.0. The existing official Steinberg SDK distribution reports VST 3.8.1.
Archive provenance and license limitations are recorded in THIRD_PARTY_NOTICES.md.

The two supplied attachments were found under `.codex-remote-attachments/`
and the ZIP extracted to a previously absent directory. Future timestamps on
the extracted files caused repeated Ninja regeneration; only new extracted
file timestamps were normalized. The initial default build also selected a
redundant validator compilation; it was stopped and the build script now names
the required plugin and test targets. The initial log is retained.

## Changes

- `plugin/Plugin.h`, `plugin/Plugin.cpp`: stable supplied processor/controller
  identities, instrument buses, sample-offset note/parameter scheduling,
  generic host parameters and native state callbacks.
- `core/include/omega/State.h`: versioned little-endian state, validation,
  checksum and backward defaults; `Parameters.h` is generated from the contract.
- `core/OrganismCore`: bounded voice-limit/reset methods and note-ID-aware
  release, retaining the supplied provisional synthesis design.
- `tests/state_tests.cpp`, `tests/adapter_tests.cpp`: malformed state, migration,
  production callback timing, reset, repeatability and C++ allocation probes.
- `tools/binary_probe.cpp`: independent host loads the actual Windows DLL for
  deterministic WAV render tests; build/validation/staging scripts added.
- Product brief, third-party notices, FL acceptance guide, and this report.

## Executed checks so far

- Portable Windows Release core/state CTest: 2/2 passed.
- Supplied contract consistency check passed; generated 15-ID registry matched.
- MSVC syntax-only compilation of plugin, adapter tests and binary probe passed.
- Windows Computer Use initialization timed out twice and reset its kernel.
  FL Studio was not opened or exercised through that connection. Installed
  FL64.exe version metadata is 25.1.6.4997; this is not host-test evidence.

## Final executed evidence

The actual Windows x64 bundle is
`build/VST3/Release/OmegaSonicOrganism.vst3`.
Its binary is `Contents/x86_64-win/OmegaSonicOrganism.vst3`, SHA-256:

`0532aaecc40fa8918dd229b819bb2611171d342a131e15381f2f30ad6f6db182`

| Check | Actual outcome | Evidence |
|---|---|---|
| MSVC Release build and CTest | 3/3 suites passed, 0 failed | `test-results/build.log`, `test-results/ctest.xml` |
| Core | Finite/bounded five anchors and midpoints, block splitting, note-off, voice count | Core suite |
| State | Round-trip, all truncated lengths, corruption, NaN/discrete rejection, earlier six-field state | State suite |
| Adapter | 44.1/48/96 kHz × 1/7/64/128/257/1024 frames; exact note/automation collision timing against core | Adapter suite, `build/Testing/Temporary/LastTest.log` |
| C++ allocation probe | 0 ordinary/array C++ `new` calls in the measured process calls | Adapter suite; does not instrument every possible OS/C allocation |
| Steinberg 3.8.1 standard | 47 passed, 0 failed; exit 0 | `test-results/validator-20261018-212244/standard.txt` |
| Steinberg extensive | 537 passed, 0 failed; exit 0 | Same directory, `extensive.txt` |
| Pluginval level 5 | SUCCESS; exit 0; no GUI-skip option | Same directory, `pluginval.txt`, `result.json` |
| Actual binary render/state recall | 27 nonzero finite bounded stereo WAVs; all bit-identical after instance destruction/recreation and native state restore | `test-results/binary-probe.log`, `test-results/renders/` |
| FL Studio | NOT_TESTED | Desktop connection timed out twice |
| Listening / custom UI / commercial QA | NOT_TESTED / NOT_IMPLEMENTED | Remaining milestones below |

The final validator record confirms the binary hash did not change during the
checks. Unsupported 64-bit processing is explicitly declined; validator entries
that report unsupported precision are not evidence for a working double path.
The SDK format test logs rejected rates 1234.568 and 1234567.8 Hz, outside the
adapter's declared 8–384 kHz range; the suite reports zero failures. Passing
pluginval without skipping GUI tests does not prove a custom editor: this alpha
does not implement one.

Binary renders use 48 kHz, 256-frame blocks, note-on at sample 0, note-off at
sample 36000, velocity 0.85, MIDI notes 36/48/60, Morph 0/0.125/…/1 and otherwise
contract defaults. Each file is two seconds; long releases can extend beyond
the demonstration file. All DSP noise is seeded deterministically per voice.
No playback/listening judgment, full-tail test or production sound quality is
implied by nonzero WAV data. The independent render analysis records Hann
window, FFT convention, sample window, RMS/peak/mean and power centroid.

## Reproduction

Run from the canonical repository root in PowerShell:

```powershell
./plugins/omega-sonic-organism/tools/build-windows.ps1
./plugins/omega-sonic-organism/tools/validate-windows.ps1
$binary = (Resolve-Path 'plugins/omega-sonic-organism/build/VST3/Release/OmegaSonicOrganism.vst3/Contents/x86_64-win/OmegaSonicOrganism.vst3').Path
& ./plugins/omega-sonic-organism/build/bin/omega_binary_probe.exe $binary plugins/omega-sonic-organism/test-results/renders
python plugins/omega-sonic-organism/tools/analyze_renders.py plugins/omega-sonic-organism/test-results/renders
./plugins/omega-sonic-organism/tools/stage-alpha.ps1
```

The final validator commands were `validator.exe <bundle>`,
`validator.exe -e <bundle>`, and
`pluginval.exe --strictness-level 5 --random-seed 0x4f534f31 --sample-rates 44100,48000,96000 --block-sizes 64,128,256,512,1024 --repeat 1 --timeout-ms 120000 --validate <bundle>`.
Executable hashes and exit codes are retained in `result.json`. No inherited
GUI-skip, disabled-test, randomization, data-file or external-validator settings
were allowed to silently alter the pluginval run.

## Defects found and repaired

The first bundle attempt lacked the parent-directory SDK generator configuration
and entry-point source path. Initial generated bundles were not usable; the
build now initializes both through the installed SDK helpers. A later strict
adapter test caught `setProcessing` forwarding the SDK base class's
`kNotImplemented`; the processor now handles the reset and returns success.
The exact adapter test, whole CTest run, actual binary probe and both validators
were rerun after the fix. Earlier failed/interrupted logs remain in test-results
and are not the final acceptance evidence.

## Release state

G0: partial; official archive identified, recursive Git revision/bootstrap pending.
G1: partial; portable core and measured callback allocation/timing tests passed;
production synthesis, continuous-morph fidelity and full audio matrix remain.
G2: partial; VST3 standard/extensive and pluginval checks passed for the stated
binary; all 15 IDs retained but deferred controls are read-only in alpha.
G3: NOT_TESTED; desktop interaction unavailable after two initialization timeouts.
G4: NOT_TESTED; alias/DC/tuning/CPU/listening qualification remains M2 work.
G5: partial alpha staging only; custom editor, 30 reviewed patches, portable
dependency bootstrap, installation/uninstallation and commercial review remain.

No 1.0 label, signing, publishing, store changes or installed plugin replacement.
Next highest-leverage action after M1 evidence is the M2 production synthesis
engine and controlled five-anchor audio review described in EXECUTION_BACKLOG.md.

The supplied first-task instruction says: “Stop the first stage after a
functioning audible VST3 and report known gaps vs full specification.” This
report is that stage boundary. The user's requested full commercial outcome
has not been achieved; this package is an evaluation alpha, not a sellable 1.0.
