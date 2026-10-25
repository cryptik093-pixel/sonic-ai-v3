# ADLIB93 thread-cycle timing diagnostic

This Windows-only development tool links a retained, previously tested ADLIB93 core library. It changes no DSP, parameter/state contract, installed plugin, FL Studio session, power plan or thread priority. It is **not** a native VST3 host or a release CPU qualification.

It records per-block wall time, raw `QueryThreadCycleTime` deltas and pacing lag, with steady and preset-transition modes separated. It retains CSV observations and nearest-rank p50/p95/p99/max summaries. Wall outliers above twice the mode's p50, with cycles at most 1.5 times its cycle p50, are counted as diagnostic clues. This classification cannot establish scheduling causation. CPU frequency, transition/preset cost and instrumentation remain confounders.

Raw thread cycles must **not** be converted to elapsed time. Microsoft documents hardware-dependent cycle-counter behavior: https://learn.microsoft.com/en-us/windows/win32/api/realtimeapiset/nf-realtimeapiset-querythreadcycletime . Aggregate `GetThreadTimes` covers the whole measured loop, including input generation, output checking/fingerprinting, instrumentation and pacing overhead: https://learn.microsoft.com/en-us/windows/win32/api/processthreadsapi/nf-processthreadsapi-getthreadtimes . It is not presented as isolated DSP CPU time.

## Run

Enter the repository's existing process-local x64 environment, then invoke the runner. Choose a new output directory outside the baseline. It uses the existing compiler; no downloads, provider calls or package installations occur.

```powershell
. '<protected-repository>/engineering/vst3/scripts/enter-windows.ps1'
python -B run_profile.py --baseline '<sprint>/adlib-core-baseline-01' --output '<sprint>/adlib-thread-timing-NEW' --seconds 30
```

The runner verifies the frozen source against its passing baseline manifest, hashes the retained library, compiler and diagnostic source, compiles one small driver with Release `/O2 /MT` settings, runs a timing self-test, and compares deterministic synthetic output fingerprints with cycle capture off/on. It checks raw CSV counts, sequences, finite values, wall/cycle quantiles, lag, outlier counts and deadline miss counts; verifies existing-output refusal; and confirms inputs remain unchanged. Commands, PIDs, exit codes, logs and SHA-256 for generated reports, CSV, logs and executable are retained. Compilation/profile timeouts target only the runner's owned process tree; failures remain visible and are never promoted to a pass.

`warmup_audio_seconds` describes processed signal duration, not a guaranteed wall-time warm-up. The nominal block deadline is frames/sample-rate. Pacing uses ordinary sleep-until and may fall behind; this is recorded as start lag rather than hidden. There is no MMCSS registration, priority increase, affinity change or timer-resolution change. Before/after machine-load observations should accompany comparisons, and no benchmark should run during native compilation.

The audio fingerprint is FNV-1a over float bit patterns, a non-cryptographic regression clue. It is neither an approved audio golden nor a substitute for retained PCM/SHA-256 and listening acceptance. The `.lib` is a reused build input whose hash is recorded; this runner does not freshly rebuild or independently certify that library's provenance. Baseline product-source reconciliation remains a separate task.

Every output retains `diagnostic_only=true`, `cpu_budget=PENDING` and `release_qualified=false`, including successfully collected diagnostics. Actual FL Studio, sustained native CPU, approved golden, design/listening and release approvals remain separate.

## Evidence parser tests

```powershell
python -B -m unittest discover -s . -p test_profile.py -v
```

The tests reject falsified release claims, changed sources, unsafe manifest paths, undeclared source files, invalid deadlines/CSV data, altered quantiles, changed output fingerprints and incompatible comparison settings. Windows execution, native compile and actual diagnostic observations must be evidenced separately from these portable tests.
