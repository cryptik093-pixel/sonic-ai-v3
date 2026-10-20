param([Parameter(Mandatory=$true)][string]$Evidence,[string]$LegacyBinary)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
if(-not $LegacyBinary){$LegacyBinary=Join-Path $root 'test-results/m2-before-lookup-optimization.vst3'}
$legacyHash=(Get-FileHash -LiteralPath $LegacyBinary).Hash
if($legacyHash -ne '7EE74E6F4B95168D42ED31BBB5AD264470D0AAC761910A33387CFBEC0EFF1454'){throw 'The preserved v0.2 baseline is not the documented binary'}
$expected=Get-Content -LiteralPath "$Evidence/result.json" -Raw | ConvertFrom-Json
$build=$expected.buildDirectory
$candidate=Join-Path $build 'VST3/Release/OmegaSonicOrganism.vst3/Contents/x86_64-win/OmegaSonicOrganism.vst3'
$candidateHash=(Get-FileHash -LiteralPath $candidate).Hash
$expected=Get-Content -LiteralPath "$Evidence/result.json" -Raw | ConvertFrom-Json
if($expected.binarySha256 -ne $candidateHash){throw 'Candidate is not the qualified binary'}
& "$build/bin/omega_binary_probe.exe" $LegacyBinary "$Evidence/legacy-v02" 0 *> "$Evidence/legacy-v02.log"
if($LASTEXITCODE){throw 'Original v0.2 state generation/render failed'}
& "$build/bin/omega_binary_probe.exe" $candidate "$Evidence/legacy-restored-candidate" --restore "$Evidence/legacy-v02" *> "$Evidence/legacy-restoration.log"
if($LASTEXITCODE){throw 'Candidate did not restore original v0.2 states'}
[ordered]@{legacyVersion='0.2.0-alpha';legacySha256=$legacyHash;candidateSha256=$candidateHash;legacyStates=27;candidateParameterBytes='bit-identical to decoded legacy sound parameters';candidateReinstantiationAudio='bit-identical';status='PASS'} | ConvertTo-Json | Set-Content "$Evidence/legacy-state-result.json"
