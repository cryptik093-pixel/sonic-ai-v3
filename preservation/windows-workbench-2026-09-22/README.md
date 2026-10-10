# Sonic Windows build preservation

Preserved 2026-10-10 UTC from cryptik093-pixel/sonic-ai-v3.

## Preserved build

- File: Sonic-Windows-x64.zip
- GitHub artifact ID: 10692450374
- Size: 43,814,804 bytes
- SHA-256: d8f2cc2865c9f6fb2546d8d74b6e6ca5a9db0622125a6c1eebfab3f29e70a778
- Source commit: c390daa0f14d307d79d46dc8508fca76622d806b
- Workflow run: https://github.com/cryptik093-pixel/sonic-ai-v3/actions/runs/35721229933
- Original artifact expiry: 2026-12-21T11:24:01Z

The downloaded build matches the GitHub-recorded SHA-256 and byte count. ZIP CRC checks pass. Sonic.exe is present alongside its bundled runtime files. Extract the entire build ZIP and keep _internal beside Sonic.exe.

## Preserved evidence

- Original Windows verification ZIP: packaged HTTP/output smoke and native window smoke JSON.
- Original Linux verification ZIP: browser proof, desktop smoke JSON and screenshots.
- Complete fetched Windows and Linux job logs: 80 passed, 15 warnings on each runner.
- Workflow run, jobs, artifact metadata and source commit metadata JSON.
- Source snapshot ZIP pinned to the exact build commit, including build workflows and verification code. This is a source snapshot, not a complete Git history backup.
- preservation-manifest.json: provenance, local hashes, byte counts and checks.
- SHA256SUMS.txt: checksums for every preserved file other than the checksum list itself.
- verify_preservation.py: local checksum and ZIP validation command.

All three downloaded workflow artifacts match their respective GitHub-recorded digests and sizes. Every preserved ZIP passes integrity validation. Verification JSON records report passed=true. Screenshots are preserved without a new visual assessment. No executable was run here; no new Windows or physical FL Studio validation is claimed. This snapshot preserves the September 22 build and does not include the later MIDI upgrade.

Run python verify_preservation.py from this directory to verify the saved files. Keep the preservation bundle in a durable backup independent of GitHub Actions artifact retention.
