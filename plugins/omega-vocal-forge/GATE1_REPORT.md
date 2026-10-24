# Gate 1 result — 2026-10-23

**State: PARTIALLY VALIDATED.** Actual Windows x64 VST3 built and automated
checks passed. FL Studio acceptance is BLOCKED. Gate 2 has not started.

## Completed

- Separate Omega Vocal Forge 0.1.0 native effect; original minimal Win32 GUI.
- Mono-to-stereo and stereo-to-stereo audio, input/output gain, 10 ms smoothing
  and full unity-dry bypass. Stable parameter IDs 100/101/102 and OVF1 schema 1.
- Repeatable CMake/MSVC build, offline engine/adapter tests, actual-DLL audio
  probe, pinned SDK provenance, validator runner and manual Windows CI job.
- Supplied skill extracted to `.agents/skills/omega-vocal-vst3-forge`;
  seven files match the original ZIP byte for byte. Packaged preflight ran;
  its two unit tests passed. Its PATH/depth/time-limit caveats remain recorded.
- All 93 original ADLIB93 source/configuration/documentation/test files checked
  by the preservation manifest remain byte-identical. Existing dirty DSP edits
  are preserved. No installed plugin, FL session, source vocal or routing changed.

## Artifact

Bundle: `build/VST3/Release/OmegaVocalForge.vst3/`

Inner Windows binary: `Contents/x86_64-win/OmegaVocalForge.vst3`, 1,272,320 bytes.

SHA256:
`DEB64666C5D4744E5146964DB0E48356636CB6258C3C7F2F45236DA90474EC2E`

The binary remained unchanged through validation. This is a development
artifact, not a distribution or FL Studio compatibility certification.

## Verified

| Check | Actual result | Evidence |
| --- | --- | --- |
| Toolchain | MSVC 19.51.36256.0, CMake 4.3.1-msvc1, Windows SDK 10.0.26100.0, x64 Release | `evidence/build.log`, `build/CMakeCache.txt` |
| Build | Native plugin, engine tests, adapter tests and DLL probe compiled/linked; exit 0 | `evidence/compile.log`, `evidence/probe-build.log` |
| CTest | 2/2 suites passed, zero failures | `evidence/ctest.log` |
| Engine | 44.1/48/96 kHz; unity, gain, finite extremes, silence, bounded bypass step and partition independence | `evidence/engine-direct.log`, `tests/EngineTests.cpp` |
| Native adapter | 3 rates; blocks 0/1/7/64/128/512/1031/2048; routing, automation offsets, in-place/null/silence, state corruption and fresh-instance recall | `tests/AdapterTests.cpp`, CTest log |
| Audio callback allocations | Zero intercepted C++ new/new[] allocations in measured adapter callbacks | Adapter suite; does not instrument every C/aligned allocation or arbitrary host behavior |
| SDK provenance | 299 SDK compiler/configuration inputs match pinned official archive | `evidence/sdk-provenance.json` |
| Steinberg standard | 47 passed, 0 failed; exit 0 | `evidence/steinberg-standard.log` |
| Steinberg extensive | 537 passed, 0 failed; exit 0 | `evidence/steinberg-extensive.log` |
| Pluginval | Strictness 5, completed SUCCESS; editor, editor while processing, and editor automation executed; GUI tests not skipped | `evidence/pluginval.txt`, `evidence/pluginval-result.json` |
| Exact DLL audio | Three 96,000-frame stereo cases at 48 kHz; finite output; +18 dB gain error 0; unity bypass error 0; settled fresh-instance recall error 0 | `evidence/artifact-audio.json`, `evidence/artifact-probe.log` |
| Preservation | 93/93 original files unchanged; seven supplied skill files identical to ZIP | `evidence/adlib93-preservation-after.json`, `evidence/supplied-skill-integrity.json` |

The audio probe produced `evidence/actual-dll-bypass.wav` (synthetic tones,
48 kHz stereo float32, 2 seconds), peak 0.15 and RMS 0.0960469. No vocal recording
or listening assessment was substituted. The initial simultaneously automated
gain/bypass ramp differs from immediate recalled bypass by up to 0.20835;
fresh-instance equality is asserted after that finite transition, not across
the initialization transient. Full gain/bypass parameter-state bytes round-trip
exactly in the adapter suite.

Commands executed from repository root:

```powershell
python .agents/skills/omega-vocal-vst3-forge/scripts/preflight.py --repo . --output plugins/omega-vocal-forge/evidence/preflight.json
python -m unittest discover -s .agents/skills/omega-vocal-vst3-forge/tests -v
./plugins/omega-vocal-forge/tools/build.ps1 -Jobs 2
. ./plugins/adlib-93/scripts/toolchain-windows.ps1 -EnvironmentOnly -Jobs 2
cmake --build plugins/omega-vocal-forge/build --target ovf_artifact_probe --parallel 2
./plugins/omega-vocal-forge/tools/verify.ps1
python plugins/omega-vocal-forge/tools/preservation.py
```

Pluginval was additionally rerun using `tools/pluginval.ps1` with explicit
bundle/evidence/executable paths, process-tree waiting, cleared inherited skip
options and a fresh result log. Its detailed arguments and tool hash are in
`evidence/pluginval-result.json`. The final report does not rely solely on a
Windows GUI launcher's early return code.

The initial build was stopped to reuse the installed SDK validator. A missing
COM header in the test probe was repaired. Both attempts are retained as history
in `evidence/build-initial-cancelled.log` and
`evidence/build-probe-include-failure.log`; the later successful build supersedes
them. Python syntax, PowerShell parsing and focused diff whitespace checks ran.

## Blocked / not tested

- FL Studio 2025 executable version **25.1.6.4997** is present and FL64.exe is
  running. The Windows helper initialization/discovery timed out in three
  attempts, ending with `computer-use request timed out: list_apps`. No
  targetable FL window was established. Scan, load, actual vocal routing,
  project save/reopen, and FL automation are **NOT_TESTED / BLOCKED**.
- The Windows CI workflow is **DEFINED, NOT_RUN**. No cloud execution, paid
  service, purchase, deployment, signing, publication or distribution occurred.
- Subjective listening and real singing-take evaluation are **NOT_TESTED**.
  Automated editor tests do not establish FL Studio compatibility or visual QA.

## Changes

New scope: `plugins/omega-vocal-forge/`, the supplied repo-local skill, and
`.github/workflows/omega-vocal-gate1.yml`. The architecture and license decision
are in `BUILD_DECISION.md`; full MIT notice is in `STEINBERG_LICENSE.txt`.
No JUCE entitlement is assumed. The selected SDK route requires no paid tools
under [Steinberg's published MIT terms](https://steinbergmedia.github.io/vst3_dev_portal/pages/VST+3+Licensing/VST3+License.html).

Feature branch: `dev/omega-vocal-gate1-20261023`. Only this new scope and its
evidence are staged; unrelated working-tree changes remain untouched. No commit,
push or production action. Raw tool logs retain their original whitespace;
the focused source/documentation diff passes the whitespace check.

## Next

Restore Windows UI access and perform the FL Studio scan/load/vocal-routing/
parameter-save/reopen acceptance in a new isolated test project. Gate 1 remains
open until that evidence exists; do not start Gate 2.
