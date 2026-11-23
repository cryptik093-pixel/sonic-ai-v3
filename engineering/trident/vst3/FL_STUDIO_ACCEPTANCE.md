# FL Studio acceptance record

Status: NOT_TESTED. An installed executable or existing open session is not proof.
Use a new disposable project and explicitly authorized test plugin location. Do
not replace the installed production VST3 or change an existing user's project.

Record run ID, source manifest content hash, complete bundle content hash, module
SHA256, FL Studio executable/version/edition, Windows version, driver, sample
rate and buffer. Preserve scan logs and screenshots alongside the run report.

1. Scan/load the exact staged bundle; verify product and stable parameter IDs.
2. Route known synthetic stereo and mono fixtures. For ADLIB test the actual
   send bus wet-only contract independently from the insert/bypass path. Record
   gain, dry leakage, latency and tail behavior against documented expectations.
3. Automate continuous and discrete parameters at recorded timeline positions.
   Exercise bypass, presets, editor reopen and output gain. Capture the result.
4. Save, close and reopen the disposable project. Verify every stored parameter,
   automation lane, route and preset. Render before/after; retain both hashes
   and the declared comparison/tolerance results.
5. Offline render the same source and compare with the deterministic harness;
   account explicitly for host sample rate, transport, latency and tail settings.
6. Measure callback/host CPU at declared buffers and instance counts with other
   builds stopped. Record p95/p99/maximum, underruns and measurement limitations.
   Acceptance needs the product's approved CPU budget, not a guessed threshold.
7. Record listener, source, level matching, listening observations and design
   acceptance. Never infer listening from finite-output or numerical tests.

Every step needs PASS/FAIL/NOT_TESTED and a path to evidence. Any missing required
gate keeps release_qualified=false. Bind this record to the final integrated
revision and rebuild/retest when source or binary changes.
