# Omega Vocal Forge — Gate 1

Separate Windows x64 vocal effect shell for Omega House Studio LLC, version
0.1.0. Gate 2 DSP has not started. ADLIB93 remains a separate product: its class
IDs, parameter IDs, state, GUI, presets, source and existing binaries are not
replaced. This shell cannot load ADLIB93 presets or sessions.

Signal contract: mono or stereo input, stereo output. Input gain and output
gain each range from -24 to +24 dB, default 0 dB. Bypass crossfades the entire
gain path to untrimmed unity dry audio. Gains and bypass use finite 10 ms ramps.
No MIDI, sidechain, effects rack, pitch correction, AI service or network access.
Float32 processing; no reported algorithmic latency or tail. Audio sanitizes
nonfinite inputs and bounds overflow to finite float range; it is not a limiter.

| Persistent identity | Value |
| --- | --- |
| Processor CID | A423BE19-C7104CA6-8F1C546E-D45D9321 |
| Controller CID | 2D772BC5-E3B04ED7-A827B35A-6F6F27A9 |
| Input gain ID | 100 |
| Output gain ID | 101 |
| Host bypass ID | 102, marked kIsBypass |
| State | OVF1 magic, schema 1; little-endian normalized input/output doubles and int32 bypass |

State rejects wrong magic/version, truncation, nonfinite and out-of-range values
before changing stored targets. Audio targets use lock-free atomics. DSP is
separate from the VST3 adapter and original native Win32 GUI.

## Reproduce locally

From repository root, in PowerShell:

```powershell
./plugins/omega-vocal-forge/tools/build.ps1 -Jobs 2
./plugins/omega-vocal-forge/tools/verify.ps1
python ./plugins/omega-vocal-forge/tools/preservation.py
```

The build script discovers installed MSVC, Windows SDK, CMake and Ninja. The
default SDK is the existing local official 3.8.1 distribution used by Sonic
Pocket. On another Windows machine supply `-SdkRoot` and `-SdkArchive`; the
archive must match `dependencies.lock.json`. Acquire it from Steinberg's SDK
download page, retain the original ZIP, and extract `VST_SDK/vst3sdk` intact.
Nothing installs into system plugin folders or modifies FL Studio settings.

The manual workflow `.github/workflows/omega-vocal-gate1.yml` accepts an official
archive URL and verifies the exact same SHA256 before extraction. It is defined,
not evidence of a completed CI run. No cloud job has been started.

Build artifact: `build/VST3/Release/OmegaVocalForge.vst3/`.
Evidence: `evidence/build.log`, CTest logs under `build/Testing/Temporary`,
`evidence/sdk-provenance.json`, `evidence/validation.json` and validator logs.
The artifact probe loads the exact built DLL, renders synthetic audio, and
checks state in a new factory-created instance. The generated WAV is a test
signal; no singing take or subjective listening approval is implied.

## Gate status and host acceptance

See `GATE1_REPORT.md` for observed results. FL Studio acceptance requires a real
scan/load/audio/parameter/project-save/reopen test. The current app discovery
helper timed out; a running FL64 process alone does not establish accessibility.
Keep Gate 1 partially validated until host evidence exists. Do not proceed to
Gate 2 from automated test results alone.

## Licensing

Direct Steinberg VST3 SDK 3.8.1 under MIT; full notice is preserved in
`STEINBERG_LICENSE.txt`. Only SDK and Windows platform components are linked.
JUCE, VSTGUI and iPlug2 are not dependencies of this shell. Original Omega House
source and artwork are used; the attached hardware study is a behavioral
reference only. There is no distribution, signing or publication in this task.
