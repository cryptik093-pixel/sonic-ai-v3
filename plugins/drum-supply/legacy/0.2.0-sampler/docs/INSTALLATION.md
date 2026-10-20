# Installation, removal and recovery

This is a local evaluation build, not a commercially cleared installer. Public distribution, framework eligibility, native host acceptance and clean-machine testing remain separate gates. No installed release is overwritten by the build/package scripts.

## Windows x64 VST3

Unzip the candidate into a staging folder. Keep the complete `Omega Drum Supply.vst3` directory and its `Contents` tree together. Have the host scan that staging location if it supports a custom VST3 path. Otherwise, after backing up any previous installed version, the conventional per-user VST3 folder is `%LOCALAPPDATA%/Programs/Common/VST3` and the shared folder is `C:/Program Files/Common Files/VST3`. Changing those installed locations is a user action; this engineering task does not install there automatically.

The package uses the original Omega Drum Supply identity. Do not keep two versions with that identity in host scan paths and assume the host selected the intended one. Record the loaded binary hash/version. Move the previous release outside scan paths under your own backup procedure before an upgrade. Never replace the synthesis-era plugin while expecting unchanged synthesis-session sound: the v2 migration preserves the four old controls, then uses the sample starter kit.

## Recall and backups

Back up DAW sessions, `.dhpreset` files and `%APPDATA%/OmegaHouse/DrumSupply/Samples`. Local kit files and DAW state contain hashes, not PCM. For a movable kit, use `.dhkit` portable export. Unavailable assets remain explicitly missing rather than falling back to an unrelated sound. LOAD / RELINK SAMPLE recovers a missing slot with the file you choose; save the session again after relinking.

The preserved 0.1.0 source wrapper is under `legacy/0.1.0`; its synthesis engine remains available there and in `Source/DrumEngine.h`. An original local bundle is retained under `evidence/baseline-0.1.0` when present. Recover old synthesized sessions with that version, in a separate disposable evaluation setup.

## Removal

Close the host and remove only the bundle you installed. Leave your sample cache, kits and DAW projects intact. No activation service, installer service, telemetry, registry registration or network daemon is added by this plugin. Cache deletion is deliberately not automated because old projects may still reference those samples.

## Rebuild

Run `./scripts/build-windows.ps1 -Jobs 2` from an appropriate PowerShell session. It discovers installed MSVC x64, Windows SDK, CMake and Ninja using the scoped local toolchain helper. It can reuse the repository's pinned JUCE cache when present; otherwise CMake downloads the SHA-256-pinned JUCE archive. No sibling plugin script is required for environment discovery. The VST3 and processor tests require JUCE; `-CoreOnly` runs the preserved synthesis and new standalone sampler numerical tests without JUCE.

Local staging tests do not establish a clean Windows-user-profile or VM installation pass. Refer to the verification report for executed checks and exact hashes.
