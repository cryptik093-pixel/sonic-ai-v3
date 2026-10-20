param([string]$Bundle)
$ErrorActionPreference='Stop'
$osoRoot=Split-Path -Parent $PSScriptRoot
if(-not $Bundle){$Bundle=Join-Path $osoRoot 'build/VST3/Release/OmegaSonicOrganism.vst3'}
if(-not(Test-Path -LiteralPath $Bundle)){throw "Missing bundle: $Bundle"}
$stage=Join-Path $osoRoot "dist/alpha-$([DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss'))"
New-Item -ItemType Directory $stage | Out-Null
Copy-Item -LiteralPath $Bundle -Destination $stage -Recurse -Force
Copy-Item -LiteralPath "$osoRoot/docs/STEINBERG-LICENSE.txt" -Destination $stage
Copy-Item -LiteralPath "$osoRoot/docs/THIRD_PARTY_NOTICES.md" -Destination $stage
Copy-Item -LiteralPath "$osoRoot/docs/PRODUCT_BRIEF.md" -Destination $stage
Copy-Item -LiteralPath "$osoRoot/docs/FL_STUDIO_ACCEPTANCE.md" -Destination $stage
Copy-Item -LiteralPath "$osoRoot/docs/IMPLEMENTATION_REPORT.md" -Destination $stage
$packEvidence=Join-Path $stage 'evidence'
New-Item -ItemType Directory $packEvidence | Out-Null
Copy-Item -LiteralPath "$osoRoot/test-results/ctest.xml","$osoRoot/test-results/binary-probe.log","$osoRoot/test-results/renders/analysis.json" -Destination $packEvidence
$validation=Get-ChildItem "$osoRoot/test-results" -Directory -Filter 'validator-*' | Sort-Object Name -Descending | Select-Object -First 1
if(-not $validation){throw 'Validator evidence is missing'}
$validationResult=Get-Content -LiteralPath "$($validation.FullName)/result.json" -Raw | ConvertFrom-Json
if($validationResult.pluginVersion -and $validationResult.pluginVersion -ne '0.1.0-alpha'){throw 'This historical M1 packager cannot stage M2 evidence. M2 packaging remains gated by its own report and measurements.'}
$checkedBinary=Get-ChildItem $Bundle -Recurse -File -Filter '*.vst3' | Select-Object -First 1
if($validationResult.standardExit -ne 0 -or $validationResult.extensiveExit -ne 0 -or $validationResult.pluginvalExit -ne 0 -or $validationResult.unchangedDuringValidation -ne $true -or $validationResult.binarySha256 -ne (Get-FileHash $checkedBinary.FullName).Hash){throw 'Latest validation is missing, failed or belongs to another binary'}
if(-not ([IO.File]::ReadAllText("$osoRoot/test-results/binary-probe.log").Contains('PASS actual VST3 binary:'))){throw 'Binary rendering/state recall did not pass'}
$renderAnalysis=Get-Content -LiteralPath "$osoRoot/test-results/renders/analysis.json" -Raw | ConvertFrom-Json
if($renderAnalysis.records.Count -ne 27){throw 'Expected 27 analyzed binary renders'}
Copy-Item -LiteralPath $validation.FullName -Destination $packEvidence -Recurse
$files=Get-ChildItem $stage -File -Recurse -Force | Sort-Object FullName | ForEach-Object { [ordered]@{path=$_.FullName.Substring($stage.Length+1).Replace('\','/');sha256=(Get-FileHash $_.FullName).Hash.ToLowerInvariant();bytes=$_.Length} }
[ordered]@{product='OMEGA SONIC ORGANISM';version='0.1.0-alpha';commercialReady=$false;files=@($files)} | ConvertTo-Json -Depth 5 | Set-Content "$stage/manifest.json"
$archive="$stage.zip"
Compress-Archive -LiteralPath $stage -DestinationPath $archive
Get-FileHash -LiteralPath $archive -Algorithm SHA256
Write-Output "Staged alpha only, no installation or publishing: $stage"
