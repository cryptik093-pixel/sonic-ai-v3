# Omega House ADLIB-93

Offline human vocal ad-lib multi-effect for Windows x64 VST3. ADLIB-93 processes
an incoming performance using gate, high-band de-essing, character, doubling,
chorus, echo/diffusion, reverb, ducking and a short Freeze texture loop. It does
not generate voices or words. The approved specification and implementation
plan remain the source of product requirements under `docs/superpowers/`.

**Internal evaluation candidate.** Read `docs/PROGRESS.md` and `docs/VERIFICATION.md` for
actual results. FL Studio compatibility, subjective sound quality and commercial
release acceptance remain PENDING until the named checks are performed.

## Windows build

Required: x64 MSVC with C++17, Windows SDK, CMake >=3.24 and Ninja. The current
machine uses Visual Studio 2026 Build Tools; no Visual Studio 2022 installation
is assumed. JUCE 9.0.4 is pinned by full commit and archive hash in
`dependencies.lock.json` and `cmake/Dependencies.cmake`.

From PowerShell in this directory (the script changes only this process):

```powershell
. ./scripts/toolchain-windows.ps1 -EnvironmentOnly -Jobs 1
$env:CC = Join-Path $compilerDir cl.exe
$env:CXX = $env:CC
cmake --preset windows-release -DADLIB93_BUILD_PLUGIN=ON
cmake --build --preset windows-release --target ADLIB93_VST3 adlib93_processor_tests adlib93_tests adlib93_render adlib93_benchmark
ctest --preset windows-release --output-on-failure
```

The repository also provides process-local toolchain discovery at
`../../engineering/vst3/scripts/enter-windows.ps1`. An existing verified JUCE
source may be reused with `-DFETCHCONTENT_SOURCE_DIR_JUCE=<absolute-directory>`.
Default builds download the immutable archive and verify its SHA-256. No build
installs into a DAW or system plugin directory.

Build output: `build/windows-release/ADLIB93_artefacts/Release/VST3/ADLIB-93.vst3`.
The verified candidate is `dist/rc1/ADLIB93.vst3`. Its directory and inner binary
were renamed in a separate copy, preserving binary bytes, class IDs and the
established ADLIB-93 display name. Both validators passed on that exact copy.
Do not install the earlier `dist/ADLIB93.vst3`; its failed evidence is retained
for recovery history. See the verification ledger for hashes and test results.

## Routing and controls

Supported main buses: mono to mono, mono to stereo, stereo to stereo. Mono input
is duplicated at unity internally; mono output averages the stereo result. No
MIDI, external sidechain or network connection is required.

Insert uses a linear dry/wet blend. Send forces effective Mix=100% and mutes the
direct branch while preserving stored Insert settings. Insert bypass moves to
trimmed dry audio; Send bypass stops new wet excitation and lets tails decay.
Output gain and enabled sample-peak limiting remain active. This limiter is
not an intersample true-peak or transparent mastering guarantee.

JUCE supplies a persistent host Bypass separately from the 70 product parameters.
The plugin's own `bypass.internal` remains transient and resumes off on recall.
Host-bypass processing uses the same Insert/Send-aware tail behavior, while FL
Studio wrapper behavior still requires the host checklist.

Factory browsing and A/B honor Input, Gate and Output calibration locks; full
host project recall restores the complete saved state independently of locks.
Throw, Freeze, diagnostic Listen and internal bypass resume off on recall.
Presets contain parameter values, never captured vocal audio. Save As writes
validated user preset JSON beneath per-user application data.

Freeze holds a 250 ms texture window with overlap crossfades. Automate release
or set a deliberate render end: held Freeze is intentionally indefinite even
though normal tails report a conservative 180-second upper bound. Clear Tails
uses bounded clearing after a fade. Exact behavior requires the tests recorded
in the verification ledger.

## Engineering tools

```powershell
build/windows-release/adlib93_render --preset 1 --input dry.wav --output new-wet.wav --sample-rate 48000 --block-size 128 --tail-seconds 12
build/windows-release/adlib93_benchmark --sample-rate 48000 --block-size 128 --seconds 600 --report new-benchmark.json
```

The renderer accepts mono/stereo PCM 8/16/24/32-bit or IEEE float32 RIFF WAV,
requires a matching input sample rate, and writes stereo float32. Resampling is
explicitly outside this tool. It refuses an existing output. Tail duration is
explicit (default zero); choose enough duration for the preset and inspect it.
Generated engineering signals do not establish vocal quality or listening
acceptance. The benchmark defaults to ten wall-clock minutes per mode (steady
and transitions); shorter/unpaced runs are diagnostic and cannot pass the
reference CPU gate.

Use the reusable QA runner at
`../../engineering/vst3/skills/omega-vst-qa/scripts/validate_vst3.py` with actual
pluginval and Steinberg validator executables and a new evidence directory.
Retain exact bundle and log hashes. See `docs/FL_STUDIO_CHECKLIST.md` for manual
host acceptance and `docs/AUDITION.md` for owner listening requirements.

## Installation for evaluation

After reviewing a verified package, the standard Windows VST3 location is
`C:\Program Files\Common Files\VST3`. Copy the complete `ADLIB-93.vst3` directory
bundle from a fresh build, or the complete packaged `ADLIB93.vst3` candidate,
preserving `Contents/x86_64-win` and resources. Install only one copy of this
product identity; the two spellings are not separate plugins. Close affected hosts
before replacing a version. This project does not automatically install or
overwrite any plugin. In FL Studio open Options > Manage plugins, verify the
VST3 search location and scan. Use a disposable test project for the checklist;
do not modify an existing recording session to establish compatibility.

Dependency licensing and public distribution require owner review. See
`docs/THIRD_PARTY_NOTICES.md`; no paid license, signing, purchase or publication
is part of this build task.

## Internal evaluation packaging

From the repository workspace, the existing release helper verifies the exact
bundle, validator logs and ZIP contents before writing new archives. It refuses
to overwrite packages. From this product directory:

```powershell
./scripts/package.ps1 -BundlePath ./dist/rc1/ADLIB93.vst3 -ValidationReport ./evidence/validation-level10-final/validation.json
```

The binary evaluation archive includes the complete bundle, source, notices,
validation evidence and an internal-evaluation manifest. A separate source ZIP
and SHA-256 file are written alongside it. This does not install, sign or publish
the plugin, or complete the remaining commercial acceptance gates.
