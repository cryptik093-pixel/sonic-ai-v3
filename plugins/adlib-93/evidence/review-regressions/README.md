# ADLIB-93 source regression probes

Date: 2026-10-15. These are small Windows native source probes, not a VST3,
FL Studio, listening, aliasing, or complete real-time verification result.

## Observed results

- RED: manual-tempo fallback with a valid host 3/4 or 6/8 signature returned
  1500 ms instead of the required manual 4/4 result of 2000 ms. Exit 1.
- RED: a captured sine texture, held for 5000 samples then released for one
  sample and re-triggered, jumped by 0.477298319 between adjacent samples.
- GREEN: both manual-tempo cases returned 2000 ms. Freeze re-trigger jumps
  were 0.001777828 after 5000 held samples and 0.002650097 after 20000 held
  samples. Both are below the declared 0.01 threshold for this fixture.
- GREEN: levelFromDb(-60) returned a normal positive 1.1920929e-07 value;
  levelToGain returned 0.0010000011, preserving exact mute separately. The
  endpoint gain tolerance in the probe is 1e-7 absolute. Exit 0.

The RED executable ran before the Freeze correction. The first timing GREEN
log still contains the old Freeze defect; use `green-final.txt` for the final
combined result. The endpoint defect was source-confirmed before correction;
there is no separate executable RED endpoint log.

## Toolchain and isolation

Repository root used:
`C:/Users/david someone/Desktop/SONIC AI V3/sonic-ai-v3`.

PowerShell dot-sourced `engineering/vst3/scripts/enter-windows.ps1`, setting
INCLUDE/LIB/PATH/CC/CXX only in that process. It discovered:

- MSVC: `C:/Program Files (x86)/Microsoft Visual Studio/18/BuildTools/VC/Tools/MSVC/14.51.36231`
- Compiler: the discovered MSVC directory's `bin/Hostx64/x64/cl.exe`.
- Windows SDK: `C:/Program Files (x86)/Windows Kits/10`, version `10.0.26100.0`.
- Compiler flags: `/nologo /std:c++17 /EHsc /O1`.

An earlier attempt via vcvars64.bat did not complete in the observation
window and was cancelled by its exact command match. That startup timeout
was not a DSP failure. The direct process-local environment completed the
native RED and GREEN runs. No heavy JUCE or VST3 build was used for this probe.

## Source provenance

`Echo-before-correction.cpp` is the copied source used by the actual RED
compile, with the pre-correction timing condition. `red-probe.cpp` preserves
the original small main used for that run. `Freeze-before-correction.cpp`
reconstructs the pre-correction rising-edge block from the observed original
source, for replay after the production fix; it was not copied at RED runtime.
The other Freeze code is unchanged. `green-probe.cpp` is the final probe main.

The GREEN probes link the actual production Parameters.cpp, Echo.cpp and
Freeze.cpp paths. The final incremental compile reused the Parameters.obj and
Echo.obj produced by the preceding GREEN compile, and recompiled the final
probe main plus corrected Freeze.cpp. `source-hashes.json` identifies the
source files preserved or used at evidence capture time.

## Reproduce from the repository root

Use fresh disposable build directories. Do not place compiler outputs in this
evidence directory. The following full tiny compiles reproduce the final
source cases, without relying on the previous incremental object cache:

```powershell
. ./engineering/vst3/scripts/enter-windows.ps1
$probeEvidence = 'plugins/adlib-93/evidence/review-regressions'
$probeBuild = 'plugins/adlib-93/build/review/reproduce'
New-Item -ItemType Directory -Force -Path "$probeBuild/red","$probeBuild/green" | Out-Null

& cl.exe /nologo /std:c++17 /EHsc /O1 /Iplugins/adlib-93/src /Iplugins/adlib-93/src/dsp "$probeEvidence/red-probe.cpp" plugins/adlib-93/src/core/Parameters.cpp "$probeEvidence/Echo-before-correction.cpp" "$probeEvidence/Freeze-before-correction.cpp" "/Fo$probeBuild/red/" "/Fe$probeBuild/red/probe.exe"
if ($LASTEXITCODE -ne 0) { throw 'RED compile failed' }
& "./$probeBuild/red/probe.exe"
# Expected exit 1: timing is 1500ms; the original Freeze jump is reported.

& cl.exe /nologo /std:c++17 /EHsc /O1 /Iplugins/adlib-93/src "$probeEvidence/green-probe.cpp" plugins/adlib-93/src/core/Parameters.cpp plugins/adlib-93/src/dsp/Echo.cpp plugins/adlib-93/src/dsp/Freeze.cpp "/Fo$probeBuild/green/" "/Fe$probeBuild/green/probe.exe"
if ($LASTEXITCODE -ne 0) { throw 'GREEN compile failed' }
& "./$probeBuild/green/probe.exe"
# Expected exit 0 for the captured corrected production source hashes.
```

Full repository unit tests, integrated engine processing, callback allocation
and timing checks, native editor interaction, validators, host recall and
listening are separate checks owned by the integrating engineer. No claim
about those outcomes follows from these probes.
