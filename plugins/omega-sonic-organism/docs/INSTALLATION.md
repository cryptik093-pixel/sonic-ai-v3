# Windows x64 installation

This is an unqualified engineering candidate, not an approved commercial release. Read RELEASE_STATUS.md before evaluating it.

Run Omega-Sonic-Organism-1.0.0-rc.2-Windows-x64-Setup.exe and keep C:\Program Files\Common Files\VST3. The complete bundle is installed as OmegaSonicOrganism.vst3 with Contents/x86_64-win/OmegaSonicOrganism.vst3 and required resources. Administrator access is required for that system folder. Setup is unsigned. It refuses to replace an existing installation. Preserve the older version before removing it; do not discard user patches or original binaries.

Open FL Studio > Options > Manage plugins. Enable Verify plugins, click Find installed plugins and add OMEGA SONIC ORGANISM as a Generator. Actual acceptance must follow DAW_ACCEPTANCE.md. A successful generic validator or installer fixture is not proof of this FL Studio workflow.

The ZIP contains the whole VST3 bundle for manual installation. Keep Contents intact. It also contains source, factory patches, audio demonstrations and evidence. Do not copy the native binary alone. The portable install-user.ps1 script accepts -Directory; its per-user default is not the recommended FL Studio scan location. Select the documented system folder when using FL Studio.

Uninstall through Windows Installed Apps or the bundle Uninstall.exe. Hash receipts protect modified/unfamiliar files: removal is refused if content changes. Export patches outside the installed bundle. Installation never migrates or removes FL Studio projects.

Actual administrator/UAC and Windows Installed Apps behavior is pending unless recorded in installer-result.json. Automated fixture testing uses the same NSIS source with a non-admin manifest and registry writes disabled. Only its demonstrated scope may be called passed.

Official host guidance: https://www.image-line.com/fl-studio-learning/fl-studio-online-manual/html/basics_externalplugins.htm
