param([Parameter(Mandatory=$true)][string]$Evidence,[string]$Makensis)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
if(-not $Makensis){$Makensis=Join-Path $root 'build-tools/nsis-3.11/makensis.exe'}
$qualification=Get-Content -LiteralPath "$Evidence/result.json" -Raw | ConvertFrom-Json
$bundle=Join-Path $qualification.buildDirectory 'VST3/Release/OmegaSonicOrganism.vst3'
$binary=Join-Path $bundle 'Contents/x86_64-win/OmegaSonicOrganism.vst3'
$sha=(Get-FileHash -LiteralPath $binary).Hash
if($qualification.version -ne '1.0.0-rc.2' -or $qualification.binarySha256 -ne $sha -or $qualification.validators -ne 'PASSED' -or $qualification.binaryRenderCases -ne 174){throw 'Qualification does not match this binary'}
$validator=Get-Content -LiteralPath "$Evidence/validator/result.json" -Raw | ConvertFrom-Json
if($validator.binarySha256 -ne $sha -or $validator.standardExit -ne 0 -or $validator.extensiveExit -ne 0 -or $validator.pluginvalExit -ne 0){throw 'Exact binary validator check failed'}
[xml]$tests=Get-Content -LiteralPath "$Evidence/ctest-plugin.xml" -Raw
if($tests.testsuite.failures -ne '0' -or $tests.testsuite.tests -ne '5'){throw 'Five passing plugin test suites are required'}
$sdkProofPath=if(Test-Path -LiteralPath "$Evidence/sdk-provenance.json"){"$Evidence/sdk-provenance.json"}else{"$root/test-results/sdk-provenance.json"}
$sdkProof=Get-Content -LiteralPath $sdkProofPath -Raw | ConvertFrom-Json
if(-not $sdkProof.compiledSdkInputsMatchArchive -or $sdkProof.buildDirectory -ne $qualification.buildDirectory -or $sdkProof.ninjaIncludeCount -le 0){throw 'Compiler SDK dependency provenance is missing or stale'}
& python "$PSScriptRoot/binary_dependencies.py" $Evidence
if($LASTEXITCODE){throw 'Native binary dependency check failed'}
& python "$PSScriptRoot/release_report.py" $Evidence
if($LASTEXITCODE){throw 'Evidence-bound release report failed'}
$stage=Join-Path $root "dist/windows-1.0.0-rc.2-$([DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss'))"
New-Item -ItemType Directory -Path "$stage/tools","$stage/presets","$stage/evidence" | Out-Null
Copy-Item -LiteralPath $bundle -Destination $stage -Recurse
Copy-Item -LiteralPath "$root/presets/factory-v1" -Destination "$stage/presets" -Recurse
New-Item -ItemType Directory -Path "$stage/OmegaSonicOrganism.vst3/Contents/Resources/FactoryPresets" -Force | Out-Null
Copy-Item -LiteralPath "$root/presets/factory-v1" -Destination "$stage/OmegaSonicOrganism.vst3/Contents/Resources/FactoryPresets" -Recurse
Copy-Item -LiteralPath "$PSScriptRoot/install-user.ps1","$PSScriptRoot/uninstall-user.ps1" -Destination "$stage/tools"
Copy-Item -LiteralPath "$root/docs/USER_GUIDE.md" -Destination "$stage/README.md"
Copy-Item -LiteralPath "$root/docs/COMPLETION_REPORT.md" -Destination $stage
Copy-Item -LiteralPath "$root/docs/STEINBERG-LICENSE.txt","$root/docs/VSTGUI-LICENSE.txt","$root/docs/THIRD_PARTY_NOTICES.md","$root/docs/NSIS-LICENSE.txt" -Destination $stage
Copy-Item -LiteralPath "$stage/README.md","$root/docs/STEINBERG-LICENSE.txt","$root/docs/VSTGUI-LICENSE.txt","$root/docs/THIRD_PARTY_NOTICES.md","$root/docs/NSIS-LICENSE.txt" -Destination "$stage/OmegaSonicOrganism.vst3"
foreach($name in @('result.json','ctest-plugin.xml','factory-calibration.json','metrics.log','editor.log','binary-eco.log','binary-hq.log','binary-bank.log')){Copy-Item -LiteralPath "$Evidence/$name" -Destination "$stage/evidence"}
Copy-Item -LiteralPath "$Evidence/validator" -Destination "$stage/evidence" -Recurse
Copy-Item -LiteralPath "$Evidence/metrics/benchmark.json","$Evidence/metrics/analysis.json" -Destination "$stage/evidence"
Copy-Item -LiteralPath "$Evidence/metrics" -Destination "$stage/evidence" -Recurse
foreach($name in @('core-build.log','plugin-build.log','ctest-core.xml','auditions.log','validation.log','factory-calibration.log','legacy-v02.log','legacy-restoration.log','legacy-state-result.json','binary-dependencies.txt','binary-dependencies.json')){Copy-Item -LiteralPath "$Evidence/$name" -Destination "$stage/evidence"}
foreach($name in @('renders-eco','renders-hq','renders-bank','editor','legacy-v02','legacy-restored-candidate')){Copy-Item -LiteralPath "$Evidence/$name" -Destination "$stage/evidence" -Recurse}
Copy-Item -LiteralPath $sdkProofPath -Destination "$stage/evidence"
if(Test-Path -LiteralPath "$Evidence/cpu-comparison"){Copy-Item -LiteralPath "$Evidence/cpu-comparison","$Evidence/cpu-held-before","$Evidence/cpu-held-after" -Destination "$stage/evidence" -Recurse;Copy-Item -Path "$Evidence/cpu-equivalence-*.json","$Evidence/cpu-held-*.log" -Destination "$stage/evidence"}
Copy-Item -LiteralPath "$root/test-results/denormal-reproduction.log","$root/test-results/denormal-reproduction.xml" -Destination "$stage/evidence"
Copy-Item -LiteralPath "$Evidence/audio-previews" -Destination "$stage/audio_previews" -Recurse
Copy-Item -LiteralPath "$root/docs" -Destination "$stage/documentation" -Recurse
New-Item -ItemType Directory -Path "$stage/source/dependencies" | Out-Null
& python "$PSScriptRoot/source_snapshot.py" "$stage/source"
if($LASTEXITCODE){throw 'Source snapshot failed'}
$sdkArchive=Join-Path $root 'dependencies/steinberg-sdk.zip'
if(-not(Test-Path -LiteralPath $sdkArchive)){$sdkArchive=Join-Path $root '../sonic-pocket/build/steinberg-sdk.zip'}
if((Get-FileHash -LiteralPath $sdkArchive).Hash -ne '64965F1B74E08A6D4087A35AF7A716F4DCFF5852C66AD7EE13F1C47E79C1AB77'){throw 'Pinned SDK archive mismatch'}
Copy-Item -LiteralPath $sdkArchive -Destination "$stage/source/dependencies/steinberg-sdk.zip"
New-Item -ItemType Directory -Path "$stage/source/history" | Out-Null
Copy-Item -LiteralPath "$root/test-results/source-before-completion-20261019.zip" -Destination "$stage/source/history/pre-completion-workspace-source.zip"
Copy-Item -LiteralPath "$root/test-results/m2-before-lookup-optimization.vst3/Contents/x86_64-win/OmegaSonicOrganism.vst3" -Destination "$stage/source/history/v0.2-alpha-reference.vst3"
[ordered]@{sourceSnapshot='pre-completion workspace backup, not a Git revision';sourceSha256=(Get-FileHash -LiteralPath "$stage/source/history/pre-completion-workspace-source.zip").Hash;legacyVersion='0.2.0-alpha';legacySha256=(Get-FileHash -LiteralPath "$stage/source/history/v0.2-alpha-reference.vst3").Hash;note='Historical artifacts are not installed. Original historical render evidence remains preserved in the originating workspace.'} | ConvertTo-Json | Set-Content "$stage/source/history/HISTORY.json"
# Setup contains the installable product only, not the much larger source/test kit.
$payload=Join-Path $root ('build-tools/installer-payload-'+[Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path "$payload/tools" | Out-Null
Copy-Item -LiteralPath "$stage/OmegaSonicOrganism.vst3" -Destination $payload -Recurse
Copy-Item -LiteralPath "$stage/tools/install-user.ps1","$stage/tools/uninstall-user.ps1" -Destination "$payload/tools"
$setup=Join-Path $root 'dist/Omega-Sonic-Organism-1.0.0-rc.2-Windows-x64-Setup.exe'
$fixtureSetup=Join-Path $root 'build-tools/Omega-Organism-Installer-Fixture.exe'
if(Test-Path -LiteralPath $setup){throw 'A setup artifact already exists; preserve it and select a new version before rebuilding.'}
Push-Location $PSScriptRoot
try {
    & $Makensis /V2 "/DPAYLOAD=$payload" "/DOUTFILE=$fixtureSetup" /DUSERTEST windows-installer.nsi *> "$Evidence/installer-test-build.log"
    if($LASTEXITCODE){throw 'Installer fixture build failed'}
    & $Makensis /V2 "/DPAYLOAD=$payload" "/DOUTFILE=$setup" windows-installer.nsi *> "$Evidence/installer-build.log"
    if($LASTEXITCODE){throw 'Windows installer build failed'}
} finally {Pop-Location}
$fixture=Join-Path $root "test-results/installer-fixture-$([Guid]::NewGuid().ToString('N'))"
$install=Start-Process -FilePath $fixtureSetup -ArgumentList @('/S',('/D='+$fixture)) -WindowStyle Hidden -Wait -PassThru
if($install.ExitCode -ne 0){throw 'Installer payload fixture failed'}
$installed=Join-Path $fixture 'OmegaSonicOrganism.vst3'
if((Get-FileHash -LiteralPath "$installed/Contents/x86_64-win/OmegaSonicOrganism.vst3").Hash -ne $sha){throw 'Installer changed binary content'}
$again=Start-Process -FilePath $fixtureSetup -ArgumentList @('/S',('/D='+$fixture)) -WindowStyle Hidden -Wait -PassThru
if($again.ExitCode -eq 0){throw 'Installer did not preserve an existing installation'}
$unfamiliar=Join-Path $installed 'fixture-unfamiliar-empty-directory'
New-Item -ItemType Directory -Path $unfamiliar | Out-Null
$null=Start-Process -FilePath "$installed/Uninstall.exe" -ArgumentList '/S' -WindowStyle Hidden -Wait -PassThru
$childResult=Join-Path $fixture 'fixture-uninstall-result.log'
if(-not(Test-Path -LiteralPath $childResult) -or (Get-Content -LiteralPath $childResult -Raw) -notmatch 'Unfamiliar directory preserved' -or -not(Test-Path -LiteralPath $unfamiliar)){throw 'Uninstaller did not preserve an unfamiliar directory'}
Copy-Item -LiteralPath $childResult -Destination "$Evidence/installer-unfamiliar-refusal.log"
Remove-Item -LiteralPath $unfamiliar
$guide=Join-Path $installed 'README.md'
$guideBytes=[IO.File]::ReadAllBytes($guide)
[IO.File]::AppendAllText($guide,"`nInstaller preservation fixture.`n")
$refused=Start-Process -FilePath "$installed/Uninstall.exe" -ArgumentList '/S' -WindowStyle Hidden -Wait -PassThru
$childResult=Join-Path $fixture 'fixture-uninstall-result.log'
if(-not(Test-Path -LiteralPath $childResult) -or (Get-Content -LiteralPath $childResult -First 1) -eq '0' -or -not(Test-Path -LiteralPath $guide)){throw 'Uninstaller did not preserve a modified installation'}
if((Get-Content -LiteralPath $childResult -Raw) -notmatch 'Modified installation preserved'){throw 'Uninstall refusal did not reach the content-preservation guard'}
Copy-Item -LiteralPath $childResult -Destination "$Evidence/installer-modified-refusal.log"
[IO.File]::WriteAllBytes($guide,$guideBytes)
$removed=Start-Process -FilePath "$installed/Uninstall.exe" -ArgumentList '/S' -WindowStyle Hidden -Wait -PassThru
if(-not(Test-Path -LiteralPath $childResult) -or (Get-Content -LiteralPath $childResult -First 1) -ne '0' -or (Test-Path -LiteralPath $installed)){throw 'Verified fixture uninstall failed'}
Copy-Item -LiteralPath $childResult -Destination "$Evidence/installer-clean-removal.log"
[ordered]@{installerSha256=(Get-FileHash -LiteralPath $setup).Hash;binarySha256=$sha;payloadInstall='PASSED';existingInstallPreserved='PASSED';unfamiliarDirectoryPreserved='PASSED';modifiedInstallPreserved='PASSED';fixtureUninstall='PASSED';adminUacInstall='NOT_TESTED';flStudio='NOT_TESTED';fixtureVariant='same NSIS source with USERTEST: user manifest and no registry writes';fixture=$fixture} | ConvertTo-Json | Set-Content "$Evidence/installer-result.json"
Copy-Item -LiteralPath "$Evidence/installer-result.json" -Destination "$stage/evidence"
Copy-Item -LiteralPath "$Evidence/installer-unfamiliar-refusal.log","$Evidence/installer-modified-refusal.log","$Evidence/installer-clean-removal.log" -Destination "$stage/evidence"
& python "$PSScriptRoot/release_report.py" $Evidence --package-verified
if($LASTEXITCODE){throw 'Final release report failed'}
foreach($name in @('TEST_REPORT.md','COMPLETION_REPORT.md','RELEASE_STATUS.md','RELEASE_GATES.json')){
    Copy-Item -LiteralPath "$root/docs/$name" -Destination "$stage/documentation/$name" -Force
    Copy-Item -LiteralPath "$root/docs/$name" -Destination "$stage/source/docs/$name" -Force
}
Copy-Item -LiteralPath "$root/docs/COMPLETION_REPORT.md" -Destination "$stage/COMPLETION_REPORT.md" -Force
Copy-Item -LiteralPath $setup -Destination $stage
$gateReport=Get-Content -LiteralPath "$root/docs/RELEASE_GATES.json" -Raw | ConvertFrom-Json
$files=@(Get-ChildItem -LiteralPath $stage -File -Recurse -Force | Sort-Object FullName | ForEach-Object {[ordered]@{path=$_.FullName.Substring($stage.Length+1);sha256=(Get-FileHash -LiteralPath $_.FullName).Hash;bytes=$_.Length}})
[ordered]@{product='OMEGA SONIC ORGANISM';version='1.0.0-rc.2';binarySha256=$sha;commercialReady=$false;gitBaseRevision=$gateReport.gitBaseRevision;sourceFingerprintSha256=$gateReport.sourceFingerprintSha256;manifestExcludesItself=$true;qualification=$qualification;gates=$gateReport.gates;files=$files} | ConvertTo-Json -Depth 10 | Set-Content "$stage/BUILD_MANIFEST.json"
& python "$PSScriptRoot/archive_delivery.py" $stage *> "$Evidence/archive-verification.log"
if($LASTEXITCODE){throw 'ZIP creation/readback/hash validation failed'}
$setupHash=(Get-FileHash -LiteralPath $setup).Hash
$zipHash=(Get-FileHash -LiteralPath "$stage.zip").Hash
$downloads=Join-Path ([Environment]::GetFolderPath('UserProfile')) 'Downloads'
$downloadFolder=Join-Path $downloads ('OMEGA_SONIC_ORGANISM_RC2-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss'))
if(Test-Path -LiteralPath $downloadFolder){throw 'Preserve the existing download directory and choose a new timestamp.'}
New-Item -ItemType Directory -Path $downloadFolder | Out-Null
Copy-Item -LiteralPath $setup,"$stage.zip" -Destination $downloadFolder
$downloadSetup=Join-Path $downloadFolder ([IO.Path]::GetFileName($setup))
$downloadZip=Join-Path $downloadFolder ([IO.Path]::GetFileName("$stage.zip"))
if((Get-FileHash -LiteralPath $downloadSetup).Hash -ne $setupHash -or (Get-FileHash -LiteralPath $downloadZip).Hash -ne $zipHash){throw 'Downloads copy hash mismatch'}
Copy-Item -LiteralPath "$root/docs/RELEASE_STATUS.md" -Destination $downloadFolder
$setupLeaf=[IO.Path]::GetFileName($setup)
$zipLeaf=[IO.Path]::GetFileName("$stage.zip")
@("$setupHash  $setupLeaf","$zipHash  $zipLeaf") | Set-Content "$downloadFolder/SHA256SUMS.txt"
[ordered]@{installer=$setup;installerSha256=$setupHash;portableZip="$stage.zip";portableZipSha256=$zipHash;downloadFolder=$downloadFolder;downloadInstaller=$downloadSetup;downloadZip=$downloadZip;stage=$stage;evidence=$Evidence} | ConvertTo-Json | Set-Content "$root/test-results/delivery.json"
Get-Content -LiteralPath "$root/test-results/delivery.json" -Raw
