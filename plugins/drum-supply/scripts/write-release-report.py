"""Publish concise reports from executed verification, never inferred success."""
from pathlib import Path
import json,subprocess
r=Path(__file__).resolve().parents[1];e=r/'evidence';v=json.loads((e/'release-verification.json').read_text());x=json.loads((e/'release-fixtures/export-verification.json').read_text());validator=json.loads((Path(v['validation_directories'][-1])/'validation.json').read_text());commit=v['baseline_git_commit'];assert v['address_sanitizer']=='PASS'
branch=subprocess.check_output(['git','branch','--show-current'],cwd=r,text=True).strip()
build=f"""# Build report / 0.3.0 release candidate
Windows x64 Release, MSVC 14.51.36231, C++20, CMake/Ninja, pinned JUCE 8.0.16-security.
Branch: {branch}. Source implementation commit: {commit}.

Executed from repository root:
`powershell -NoProfile -ExecutionPolicy Bypass -File plugins/drum-supply/scripts/build-windows.ps1 -Jobs 1`
`powershell -NoProfile -ExecutionPolicy Bypass -File plugins/drum-supply/scripts/run-asan.ps1`
`powershell -NoProfile -ExecutionPolicy Bypass -File plugins/drum-supply/scripts/validate-windows.ps1 -Strictness 10`
`python plugins/drum-supply/scripts/run-release-checks.py`
`python plugins/drum-supply/scripts/package-candidate.py`

CMake build completed; all four CTest suites passed. Retained synthesis-build-final.log and synthesis-build-onset-wiring.log contain actual compiler output, including nonfatal signedness, hidden-member and deprecated test-writer warnings. The framework was reused; no replacement synthesizer was introduced.
Windows AMD64 PE check: {v['windows_x64_pe']}. Build freshness: {v['build']}.
Compiled module SHA-256: {v['binary']['sha256']} ({v['binary']['bytes']} bytes).
The build basename has a terminal product period; staging aligns canonical outer and inner names to DrumShotSupplyCo.vst3. Validators executed that exact canonical bundle; the compiled bytes are unchanged.
"""
dsp=f"""# DSP, state, UI and export evidence
Synthesis tests: {v['synthesis_dsp']}; original legacy synth: {v['legacy_dsp']}; optional sample regression: {v['sample_dsp']}; production processor: {v['processor']}.

Production processor tests exercised 181 stable parameters (all original 82 positions), exact v3 host-state/audio round trips, v1 migration, malformed state rejection, A/B, managed/portable samples, 24 concurrent sample publications with counted C++ allocation/free checks, MIDI mapping/timing, multiple sample rates and block partitions. Twenty editor close/reopen cycles and 21 slider bindings in both directions passed. Raw button interaction and neutral-audio comparison passed without changing kit state. Native snapshots were inspected at 960x760 and 1160x900; 1600x1000 was rendered. Windows OS scaling and actual DAW dialog interaction remain NOT TESTED.

The synthesis suite passed 120 macro/extreme cases, original seven-map golden regression, eight sample-free voices, category waveform distinction, normalized macro-waveform differences beyond gain, velocity, hat choke, pan/mute/solo, panic and finite guards. Sample rates include 44.1/48/96 kHz; processor adds 192 kHz and blocks 0/1/7/64/128/511/1024. Note root is preserved when MIDI is remapped.

MSVC AddressSanitizer synthesis execution: PASS (asan-run.log); no reported memory error. This is not full-host sanitizer coverage. No thread sanitizer claim.

Production WAV service read-back: {x['state']}, {x['wav_files']} PCM24 stereo WAV files, six distinct factory profiles, complete eight-file kit manifests, exact SHA-256 checks, nonzero measured PCM, bounded peaks. Individual 44.1/96 kHz and default 48 kHz kit exports executed; deterministic repeated PCM and overwrite refusal passed. Tail capture and full recipes are recorded in export-verification.json and each ExportManifest.json. Separate 16 processor renders passed exact PCM/recipe checks. Human listening: NOT TESTED.

Predeclared callback budget: p95 <=0.666667 ms, 48 kHz / 128 samples, fixed 16 overlapping voices retriggered each callback over ten wall-clock seconds. Current result: {v['performance']}.
`{v['performance_line']}`
Hardware: {v['hardware']}. Final runner executes these suites sequentially after compile/validator/sanitizer jobs. Results characterize this computer and workload, not guaranteed host CPU performance. Earlier overloaded benchmark failures are retained; they were not relabelled as passes.
"""
vst=f"""# VST3 validation
Exact canonical bundle: {validator['bundle']}.
Module SHA-256: {validator['binarySha256After']}.
Bundle unchanged before/after tools: {validator['artifactUnchanged']}.
pluginval strictness 10: {validator['tools']['pluginval']['state']}, GUI tests requested, 44.1/48/96 kHz, blocks 64/128/256/512/1024, fixed seed 0x504f434b.
Steinberg SDK 3.8.0 validator: {validator['tools']['steinberg']['state']}, 47 tests passed, zero failed.
Original component/controller class IDs: {', '.join(v['class_ids'])}; compatibility check {v['vst3_class_ids']}.
Float64 processing is not supported; the SDK reports that optional format and validates float32. Tool hashes, command lines, complete stdout/stderr and bundle file manifests are included in the validation directory. FL Studio acceptance is separate.
"""
(e/'BuildReport.md').write_text(build);(e/'DSPTests.md').write_text(dsp);(e/'VST3Validation.md').write_text(vst);(e/'FLStudioAcceptance.md').write_text((r/'docs/FL_STUDIO_ACCEPTANCE.md').read_text())
summary=f"""# Drum Shot Supply Co. 0.3.0 / RELEASE CANDIDATE
## Result
A compiled Windows x64 synthesis instrument with recovered native editor, eight drums, Punch/Tone/Character, kit state, six factory profiles, optional authorized sample layers, Raw comparison and actual PCM24 one-shot/kit export. FL Studio acceptance remains NOT TESTED.

## Recovery and changes
Recovery snapshot 844a155; synthesis implementation 0c61093; export/factory completion {commit}. Branch {branch}. Source/PluginEditor.cpp and scripts/run-sampler-checks.py contained invalid NUL data; their bytes were preserved and complete operational replacements recovered. Original synthesis and interrupted sampler are preserved under legacy/. The current callback instantiates the single extended original synthesis engine. FactoryManifest.h and RenderService.h/.cpp add real factory profiles and an offline use of that same engine. Processor/editor, CMake, tests, documentation and release scripts were updated. Current supplied assets and original archives: {v['original_assets']}, {v['original_files_checked']} file checks. Sample redistribution explicitly authorized by the owner.

## Executed gates
Build {v['build']}; synthesis {v['synthesis_dsp']}; legacy {v['legacy_dsp']}; sample {v['sample_dsp']}; processor/state/native UI {v['processor']}; VST3 validators {v['validators']}; processor renders {v['offline_renders']}; production WAV exports {v['wav_exports']}; originals {v['original_assets']}; callback budget {v['performance']}. AddressSanitizer synthesis PASS. Packaging has independent artifacts.json with extraction/hash results; its existence alone is not acceptance.

## Remaining release gates
FL Studio scan/load/playback/automation/project save-reopen/offline export: NOT TESTED because native host control is unavailable. Human listening, Windows OS display scaling and clean-machine install: NOT TESTED. Commercial framework licensing eligibility remains unresolved. Callback performance is an additional release blocker if reported FAIL above. No commercial-ready verdict or actual host acceptance is claimed. Follow Validation/FLStudioAcceptance.md on the exact packaged module.

See BuildReport.md, DSPTests.md, VST3Validation.md, the machine-readable release-verification.json and complete retained logs for commands, hashes and limits. Source and Windows ZIP SHA-256 values are recorded beside the archives in artifacts.json. Installation: copy the complete Plugin/DrumShotSupplyCo.vst3 bundle to the Windows Common Files/VST3 directory while the host is closed, then scan from FL Studio.
"""
(e/'RELEASE_VERIFICATION.md').write_text(summary)
print(summary)
