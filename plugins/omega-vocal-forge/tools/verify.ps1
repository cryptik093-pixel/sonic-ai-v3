param([string]$BuildDir='build',[switch]$SkipPluginval)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
if(-not [IO.Path]::IsPathRooted($BuildDir)){$BuildDir=Join-Path $projectRoot $BuildDir}
$bundle=Join-Path $BuildDir 'VST3/Release/OmegaVocalForge.vst3'
$binary=Join-Path $bundle 'Contents/x86_64-win/OmegaVocalForge.vst3'
$run=Join-Path $projectRoot 'evidence'
New-Item -ItemType Directory -Force $run | Out-Null
$validator=Join-Path $BuildDir 'bin/Release/validator.exe'
if(-not(Test-Path -LiteralPath $validator)){$validator=Join-Path $BuildDir 'bin/validator.exe'}
if(-not(Test-Path -LiteralPath $validator)){$validator=Join-Path $projectRoot '../sonic-pocket/build/steinberg-validator/bin/validator.exe'}
foreach($path in @($binary,$validator)){if(-not(Test-Path -LiteralPath $path)){throw "Missing artifact: $path"}}
$hash=(Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash
& $validator $bundle *> "$run/steinberg-standard.log"
$standard=$LASTEXITCODE
& $validator -e $bundle *> "$run/steinberg-extensive.log"
$extensive=$LASTEXITCODE
$audioProbe=Join-Path $BuildDir 'bin/ovf_artifact_probe.exe'
if(-not(Test-Path -LiteralPath $audioProbe)){$audioProbe=Join-Path $BuildDir 'ovf_artifact_probe.exe'}
if(-not(Test-Path -LiteralPath $audioProbe)){throw 'Missing exact-DLL audio probe'}
& $audioProbe $binary $run *> "$run/artifact-probe.log"
$probe=$LASTEXITCODE
$pluginval=[ordered]@{status='NOT_TESTED';exitCode=$null}
if(-not $SkipPluginval){
 $pv=Join-Path $projectRoot '../sonic-pocket/build/pluginval/pluginval.exe'
 if(Test-Path -LiteralPath $pv){
  $pluginval=& "$PSScriptRoot/pluginval.ps1" -Bundle $bundle -EvidenceDirectory $run -Executable $pv
 }
}
$result=[ordered]@{timestampUtc=[DateTime]::UtcNow.ToString('o');binary=$binary;sha256=$hash;binaryUnchanged=$hash -eq (Get-FileHash -LiteralPath $binary -Algorithm SHA256).Hash;validator=$validator;validatorSha256=(Get-FileHash -LiteralPath $validator -Algorithm SHA256).Hash;steinbergStandardExit=$standard;steinbergExtensiveExit=$extensive;artifactProbeExit=$probe;pluginval=$pluginval;flStudio='BLOCKED: Windows helper initialization/discovery timed out in three attempts; final error: computer-use request timed out: list_apps';ci='DEFINED_NOT_RUN';gate2='NOT_STARTED'}
$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath "$run/validation.json" -Encoding utf8
$result | ConvertTo-Json -Depth 5
if($standard -ne 0 -or $extensive -ne 0 -or $probe -ne 0 -or -not $result.binaryUnchanged -or $pluginval.status -eq 'FAIL'){throw 'Validation failed; inspect evidence logs'}
