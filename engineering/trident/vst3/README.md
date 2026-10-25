# TRIDENT isolated Windows Release baseline

This additive runner uses existing product CMake targets and the existing
`engineering/vst3/scripts/enter-windows.ps1` environment. It never installs a
plugin. One build/test worker is used by default; `-Jobs 2` is the maximum build
concurrency. The output directory must be new and
outside the checkout and installed-program trees. No downloads or paid services
are required by these three configurations.
Requires Python 3.12 or newer. When using the isolated tooling review branch,
pass `-SourceRepo 'C:\path\to\protected\source\checkout'` explicitly: plugin
source and the existing toolchain/validators have not been reconciled into main.

```powershell
./engineering/trident/vst3/build-release.ps1 -Product omega-house-eq -Output 'C:\scratch\trident-eq-001' -ReferenceModule 'C:\path\to\existing\OmegaHouseEQ.vst3'
./engineering/trident/vst3/build-release.ps1 -Product adlib-93-core -Output 'C:\scratch\trident-adlib-001'
./engineering/trident/vst3/build-release.ps1 -Product organism-v4-fx-core -Output 'C:\scratch\trident-v4-core-001'
python -B -m unittest discover -s engineering/trident/vst3 -p test_pipeline.py -v
```

The EQ reference argument is the inner Windows module, not the bundle folder.
The SDK archive must match SHA256 in `pipeline.py`; actual compiler dependencies
are verified with the existing Vocal Forge SDK verifier. Its lock and verifier
are existing recovery-checkout dependencies; they must accompany integration.
Product inputs are copied before CMake execution and hashed before/after. EQ's
extra renderer target is appended only to the copied CMake file. Compiler,
Python, CMake and Ninja paths/hashes, exact commands, return codes, logs, CTest
JUnit, copied source and bundle-content manifests are retained in each run.

EQ coverage includes existing engine, adapter/state and exact-DLL frequency
response/recall probes, plus new synthetic full-audio DLL captures across three
rates and three block sizes. Repeated captures must be bit identical. Optional
comparison against an existing DLL is a continuity check; it does not constitute
approval of that reference. No approved golden is created automatically.
The existing QA helper runs Steinberg and pluginval level 5 against the fresh EQ
bundle in its own new evidence directory; missing validators fail this baseline.
ADLIB core includes existing CTest cases and deterministic two-preset stereo
render/tail captures at 48k in two callback partitions. It does not qualify the
JUCE processor or a VST3 bundle. V4 FX core tests the separate effect; it does
not qualify the Organism instrument or implement Creator DNA.

Bundle content hash = SHA256 of UTF-8 canonical JSON (`sort_keys=True`, compact
separators) containing sorted relative path, byte count and per-file SHA256
records. This covers resources as well as the DLL. Empty and linked inputs fail.

`report.json.status=PASS` means executed baseline checks passed. Host, CPU,
listening/design and approved golden gates remain separate. Every report has
`release_qualified=false`. A changed reference render or source fails the run;
review the evidence and start a new directory after diagnosis. Do not overwrite
failed evidence or automatically accept changed audio.
`-ResumeFrom 'C:\scratch\previous-run'` reuses a completed run's isolated build
cache only if its recorded source, current frozen source and newly captured
inputs match exactly. Supply a new `-Output` directory for the retry logs/report.
The previous report and logs remain immutable; generated cache/artifacts may
advance. Do not resume a cache while another build is using it.
An exclusive cache lock rejects concurrent runner access. A hard process kill
can leave a stale lock; investigate the recorded process before removing it.
Commands have bounded timeouts (one hour for compilation). A timed-out command
has its own process tree terminated before the runner exits; unrelated jobs are
not stopped. Failed runs retain their logs and must not be silently overwritten.

See [recovery plan](RECOVERY_PLAN.md) and [host procedure](FL_STUDIO_ACCEPTANCE.md).
Source-only work is not a reproducible final integrated revision until reviewed
dependencies and product source are committed together on the designated branch.
