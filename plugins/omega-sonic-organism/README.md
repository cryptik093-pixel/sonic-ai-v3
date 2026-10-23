# OMEGA SONIC ORGANISM development

Current source identifies itself as **1.0.0-dev.v4**. It is an engineering
build, not a qualified V4 release candidate. CPU recovery, experimental V4
feature integration, FL Studio acceptance and listening remain open. Current
work and reproducible evidence are recorded in
[V4_RECOVERY_2026-10-22.md](docs/V4_RECOVERY_2026-10-22.md).
The existing CIDs, sound parameter IDs, OSO1 encoding and 30 factory patches
remain unchanged. See [host control contract v1](docs/CONTROL_CONTRACT_V1.md).

## Historical RC2 delivery

Windows x64 VST3 instrument for evaluation in FL Studio Producer Edition. This is an **unqualified release candidate**. CPU, interactive editor, FL Studio and listening gates remain open; see documentation/RELEASE_STATUS.md in the delivery or docs/RELEASE_STATUS.md in source.

The actual instrument uses one shared structural morph voice across Bass, Bells, Lead, Synth and Percussion. It includes five expressive macros, native VSTGUI editor, 30 embedded factory configurations and JSON patch exchange. It runs offline without samples, login or a server.

Run the included Windows Setup to install the complete bundle in C:\Program Files\Common Files\VST3. Follow INSTALLATION.md and USER_MANUAL.md. The installer preserves an existing bundle. Installation, generic validation and FL Studio acceptance are separate states.

The delivery includes the VST3 bundle, Setup, source with pinned SDK archive, presets, 48 PCM24 audition demonstrations, actual-DLL regression renders, validator/CTest/performance reports, a release-gate matrix and BUILD_MANIFEST.json. Hashes and source snapshot identity describe the delivered revision; a dirty workspace Git base alone does not.

Build source with tools/reproduce-build.ps1 after installing free MSVC Build Tools, Windows SDK, CMake and Python. Existing historical M1/M2 evidence is retained in the original workspace and described by docs/IMPLEMENTATION_REPORT.md and docs/M2_TEST_REPORT.md. Those reports are historical, not current candidate certification.
