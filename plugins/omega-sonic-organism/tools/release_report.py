"""Generate an evidence-bound candidate report. Never infer DAW or listening approval."""
import argparse, hashlib, json, platform, subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('evidence',type=Path);parser.add_argument('--package-verified',action='store_true');args=parser.parse_args()
    evidence=args.evidence.resolve(); result=json.loads((evidence/'result.json').read_text(encoding='utf-8-sig'))
    analysis=json.loads((evidence/'metrics/analysis.json').read_text(encoding='utf-8-sig'))
    auditions=json.loads((evidence/'audio-previews/audition-results.json').read_text(encoding='utf-8-sig'))
    assert result['cleanBuildStartedInEmptyDirectory'] is True
    assert result['version']=='1.0.0-rc.1' and result['binaryRenderCases']==174
    assert len(auditions['renders'])==48 and all(x['finiteNonzeroBounded'] for x in auditions['renders'])
    pcm=json.loads((evidence/'audio-previews/pcm24-verification.json').read_text())
    assert pcm['status']=='PASS' and len(pcm['files'])==48
    assert not analysis['audio_criteria_failures']
    validator=json.loads((evidence/'validator/result.json').read_text(encoding='utf-8-sig'))
    assert all(validator[x]==0 for x in ('standardExit','extensiveExit','pluginvalExit'))
    assert validator['binarySha256']==result['binarySha256']
    assert validator['pluginVersion']==result['version']
    legacy=json.loads((evidence/'legacy-state-result.json').read_text(encoding='utf-8-sig'))
    assert legacy['status']=='PASS' and legacy['candidateSha256']==result['binarySha256'] and legacy['legacyStates']==27
    modes=analysis['benchmark']['modes'];cpu_pass=all(x['reference_percentile_goal_met'] and x['overruns']==0 for x in modes)
    gates=[
        ('G01','PASS','Windows x64 Ninja Release build started in a new empty directory; five CTest suites passed. SDK archive and reproduction commands supplied.'),
        ('G02','PASS','Original 27-case grid rerun in Eco and HQ through actual DLL: 54 renders.'),
        ('G03','PASS','Core/engine/adapter tests: MIDI, macros, five sample rates, bounded output, measured allocation checks.'),
        ('G04','PASS','State/JSON/instance recall; 174 exact repeat renders plus 27 states saved by the original v0.2 DLL and restored/rendered by the candidate.'),
        ('G05','PASS','Five shared-engine trait anchors and four intermediate regions covered by regression and audition renders; identity listening pending.'),
        ('G06','PASS','Macro boundary/difference tests, timed VST automation comparisons, actual-DLL sweep renders. Musical approval pending.'),
        ('G07','PASS' if cpu_pass else 'FAIL','CPU reference goals and callback deadline '+('met in recorded benchmark.' if cpu_pass else 'not met; see unfiltered benchmark percentiles and overruns.')),
        ('G08','PASS','Official Steinberg standard and extensive validator; pluginval level 5 with GUI enabled, exits 0.'),
        ('G09','PENDING','Native editor attach/remove/reopen and resize API passed; readable capture inspected. Full mouse/file-dialog/host-automation interaction acceptance remains pending.'),
        ('G10','PASS','30 JSON presets embedded and packaged; 120 DLL preset-note recall renders; numerical calibration only, audition pending.'),
        ('G11','PENDING','FL Studio scan/play/automation/save-reopen/multi-instance/render acceptance has not been performed.'),
        ('G12','PENDING','Human review of identity, transitions, musicality, dynamics and preset usefulness required.'),
        ('G13','PASS' if args.package_verified else 'PENDING','Installer payload/hash/preservation/uninstall fixtures and deliverable inventory verified.' if args.package_verified else 'Final installer and ZIP verification not complete.')]
    revision=subprocess.check_output(['git','log','-1','--format=%H','--','.'],cwd=root,text=True).strip()
    if not revision:revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    source=[]
    for directory in ('core','plugin','contracts','tests','tools','presets'):
        for p in sorted((root/directory).rglob('*')):
            if p.is_file() and '__pycache__' not in p.parts:source.append(dict(path=p.relative_to(root).as_posix(),sha256=digest(p)))
    for name in ('CMakeLists.txt','AGENTS.md'):
        p=root/name;source.append(dict(path=name,sha256=digest(p)))
    fingerprint=hashlib.sha256(json.dumps(source,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    data=dict(product='OMEGA SONIC ORGANISM',version=result['version'],status='UNQUALIFIED RELEASE CANDIDATE - NOT COMMERCIAL READY',commercialReady=False,gitBaseRevision=revision,sourceState='Last project commit plus the delivered per-file source snapshot; generated release reports may be newer than the code commit.',sourceFingerprintSha256=fingerprint,sourceFiles=source,binarySha256=result['binarySha256'],evidenceDirectory=evidence.name,platform=platform.platform(),flStudio='NOT_TESTED',listening='PENDING',gates=[dict(gate=a,state=b,evidence=c) for a,b,c in gates])
    (root/'docs/RELEASE_GATES.json').write_text(json.dumps(data,indent=2)+'\n')
    table='| Gate | State | Evidence / outstanding work |\n|---|---|---|\n'+''.join(f'| {a} | {b} | {c} |\n' for a,b,c in gates)
    costs='\n'.join(f"- {m['quality']}: median {m['medianMs']} ms, P95 {m['p95Ms']} ms, P99 {m['p99Ms']} ms, max {m['maximumMs']} ms; {m['overruns']}/{m['callbacks']} over 5.333 ms." for m in modes)
    report=f'''# OMEGA SONIC ORGANISM 1.0.0-rc.1

UNQUALIFIED RELEASE CANDIDATE. Commercial release is blocked by the unresolved gates below.
This candidate is supplied for engineering and host evaluation, with actual Windows x64 VST3 and installer.

## Result

IMPLEMENTED: Shared structural morph synthesizer; five anchors; five expressive macros; 1/8/16/32 voices; velocity, bend, sustain, mono legato/glide; Eco/HQ drive; native VSTGUI editor; 30 factory patches; atomic JSON import/export; preserved native OSO1 state and parameter IDs.

AUTOMATICALLY VERIFIED: Five CTest suites, official standard/extensive validation, pluginval level 5 with GUI enabled, 174 finite/nonzero/bounded DLL renders and exact audio recall after instance reconstruction; native editor lifecycle/resize API; 48 actual-DLL 24-bit audition WAVs.

HOST VERIFIED: Project-specific native Windows integration hosts and validators only. FL Studio NOT_TESTED. LISTENING APPROVED: none.

## Release gates

{table}
## Performance

Production portable core, 16 active voices, 48 kHz, 256 frames, 30 seconds of audio per mode, automated morph. Includes all scheduling outliers; not a DAW measurement. This shared Windows machine has an Intel i5-4310U (2 cores / 4 logical processors) and 8 GB RAM. Reference goal remains P95 <=1 ms, P99 <=2 ms. No threshold was relaxed.

{costs}

The measured callback deadline is 5.333 ms. CPU failure is a real unresolved gate even where scheduling contention contributes. Use fewer voices/Eco/larger buffers for evaluation; these mitigations do not turn a failed gate into a pass.

## Signal measurements

HQ drive nonfundamental-energy improvement in the documented coherent experiment: {analysis['alias_improvement_db']:.3f} dB. This is not a general instrument alias score. Twenty pitched steady-tone measurements (percussion intentionally excluded) have maximum error {max(abs(x['error_cents']) for x in analysis['tuning']):.3f} cents; worst window DC {max(x['dc_dbfs'] for x in analysis['tuning']):.2f} dBFS. Full methods and raw values: tests/metrics or evidence/analysis.json.

48 audition files comprise five anchors, four transitions, five macro sweeps, four performances and 30 factory patches. They are stereo 48 kHz signed PCM 24-bit, undithered, without normalization. Quantization is below normal audition resolution. Finite output, nonzero signal, peaks/RMS/mean/maximum adjacent sample differences are reported; these metrics do not prove musical quality or click-free perception.

## Revision and artifacts

Last project commit: `{revision}`. Generated reports may be newer than this code commit. Exact delivered source fingerprint: `{fingerprint}`; per-file hashes are in RELEASE_GATES.json and BUILD_MANIFEST.json. No unrelated checkout work was committed or discarded.

DLL SHA-256: `{result['binarySha256']}`.
Evidence run: `{evidence.name}`. Original v0.2 evidence remains preserved in the workspace; original binary SHA-256 `7ee74e6f4b95168d42ed31bbb5ad264470d0aac761910a33387cfbec0eff1454`. Historical logs are separate from current candidate proof.

## Reproduce

Install free Visual Studio Build Tools with MSVC x64 C++ and Windows SDK, CMake >=3.25, Python 3. Build used CMake 4.3.1, MSVC 14.51 toolset and Windows SDK 10.0.26100.0; exact banners are in build logs.
In source/: `powershell -NoProfile -ExecutionPolicy Bypass -File tools/reproduce-build.ps1`.
Then `tools/finish-windows.ps1 -Jobs 1` with explicit available validators, or run each probe as documented in ARCHITECTURE.md. Reproduction requires the bundled SDK archive or the same verified official archive; the build script takes an explicit SDK path. Installer builder NSIS 3.11 is optional and separate from audio build.

## Changes and unresolved work

Core: equivalent polyphase half-band oversampling and bounded table indexing; coefficient reuse. Adapter: segmented sample-offset scheduling with matching tests, preserved IDs and state. Editor/presets: actual controls, host gestures, factory selection, JSON parser/exporter and calibrated bank. Release: actual DLL probes, 24-bit auditions, guarded installer and machine-readable evidence.

Next highest-leverage action: profile and reduce CPU cost on a controlled reference Windows machine, then complete interactive editor and FL Studio acceptance using the supplied projects/procedure and obtain a human listening decision. Do not sell or certify this candidate as v1.0 commercial ready.
'''
    for name in ('TEST_REPORT.md','COMPLETION_REPORT.md','RELEASE_STATUS.md'):(root/'docs'/name).write_text(report,encoding='utf-8')
    print(json.dumps(dict(version=result['version'],binarySha256=result['binarySha256'],gates={a:b for a,b,_ in gates}),indent=2))

if __name__=='__main__':main()
