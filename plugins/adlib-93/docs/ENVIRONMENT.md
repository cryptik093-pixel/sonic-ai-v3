# ADLIB-93 development environment

2026-10-15. Isolated project: `plugins/adlib-93` within the existing Sonic AI V3
checkout. Every plan-relative path maps directly beneath this directory.
Historical specification approval-pending wording is superseded by the owner's
explicit approval in this task. Original handoff documents remain unchanged.

Baseline branch `recovery/actual-project-state`, commit
`c51a0012e13b9b9b8359ca269db5f292fb5fed24`. Existing modified application files,
private configuration, database and untracked Sonic Pocket are preserved.
Only ADLIB-93 paths may enter task commits. No project coordination marker was
found under `.codex`; no new task board/server is introduced.

Windows 10 Pro x64 10.0.19045; Intel Core i5-4310U, 2 cores/4 logical CPUs,
8 GB RAM. MSVC compiler execution reported 19.51.36256 for x64. Toolset directory
14.51.36231, Visual Studio 2026 Build Tools (18), SDK 10.0.26100.0. CMake execution
reported 4.3.1-msvc1. Native Ninja presets replace unavailable VS 2022 generator.
`scripts/toolchain-windows.ps1 -EnvironmentOnly` discovers tools and sets only
the current process environment. No installation or system changes occur.

JUCE official tag 9.0.4 resolved via `git ls-remote` to immutable commit
`3fb5cbc0340758596dac39f7c8de47d562b4896e`. The exact archive SHA256 is recorded
in `dependencies.lock.json` and checked by CMake. This project does not alter
Sonic Pocket's JUCE 8.0.16-security pin. JUCE's pinned LICENSE.md permits
AGPLv3 or commercial licensing; use the open-source development route here.
No proprietary licensing eligibility is claimed, purchase made or paid terms
accepted. Distribution obligations remain an owner release gate.

FL Studio executable version 25.1.6.4997 is PRESENT. Edition/license, native
scan/load, routing, listening and device monitoring latency are PENDING.
No FL project or recording is changed. Source-signal numerical tests are not
listening evidence. Temporal was reviewed and is unnecessary for local DSP.

Build commands (PowerShell from this directory):
```powershell
. ./scripts/toolchain-windows.ps1 -EnvironmentOnly -Jobs 1
$env:CC = Join-Path $compilerDir cl.exe
$env:CXX = $env:CC
cmake --preset windows-release
cmake --build --preset windows-release --target adlib93_tests
ctest --preset windows-release --output-on-failure
```

Dependency selection sources: https://github.com/juce-framework/JUCE/releases/tag/9.0.4
and the pinned source's LICENSE.md. Tool execution/build logs are in `evidence/`.
See PROGRESS.md for actual task status rather than interpreting this inventory
as a successful full plugin build.

Approved specification SHA256: 1af09fabee685af6afee6106f0b42308c88a664d83fa5d754b728943d28a91b3.
