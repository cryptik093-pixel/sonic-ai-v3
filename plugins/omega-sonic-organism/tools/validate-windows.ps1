param([string]$Bundle,[string]$Validator,[string]$Pluginval)
$ErrorActionPreference='Stop'
$osoRoot=Split-Path -Parent $PSScriptRoot
if(-not $Bundle){$Bundle=Join-Path $osoRoot 'build/VST3/Release/OmegaSonicOrganism.vst3'}
if(-not $Validator){$Validator=Join-Path $osoRoot '../sonic-pocket/build/steinberg-validator/bin/validator.exe'}
if(-not $Pluginval){$Pluginval=Join-Path $osoRoot '../sonic-pocket/build/pluginval/pluginval.exe'}
foreach($required in @($Bundle,$Validator,$Pluginval)){if(-not(Test-Path -LiteralPath $required)){throw "Missing $required"}}
$evidence=Join-Path $osoRoot "test-results/validator-$([DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss'))"
New-Item -ItemType Directory $evidence | Out-Null
$binary=Get-ChildItem $Bundle -Recurse -File -Filter '*.vst3' | Select-Object -First 1
if(-not $binary){throw 'Bundle contains no VST3 binary'}
$beforeHash=(Get-FileHash $binary.FullName).Hash
& $Validator -help 2>&1 | Set-Content "$evidence/help.txt"
& $Validator $Bundle *> "$evidence/standard.txt"
$standardExit=$LASTEXITCODE
Write-Output "Standard validator finished: exit $standardExit; log $evidence/standard.txt"
& $Validator -e $Bundle *> "$evidence/extensive.txt"
$extensiveExit=$LASTEXITCODE
Write-Output "Extensive validator finished: exit $extensiveExit; log $evidence/extensive.txt"
$inherited=@{}
foreach($key in @('SKIP_GUI_TESTS','DISABLED_TESTS','RANDOMISE','DATA_FILE','VST3VALIDATOR')){
    $inherited[$key]=[Environment]::GetEnvironmentVariable($key,'Process')
    [Environment]::SetEnvironmentVariable($key,$null,'Process')
}
try {
    & $Pluginval --strictness-level 5 --random-seed 0x4f534f31 --sample-rates 44100,48000,96000 --block-sizes 64,128,256,512,1024 --repeat 1 --timeout-ms 120000 --validate $Bundle *> "$evidence/pluginval.txt"
    $pluginvalExit=$LASTEXITCODE
    Write-Output "Pluginval level 5 finished: exit $pluginvalExit; log $evidence/pluginval.txt"
} finally {
    foreach($key in $inherited.Keys){[Environment]::SetEnvironmentVariable($key,$inherited[$key],'Process')}
}
$afterHash=(Get-FileHash $binary.FullName).Hash
$versionMatch=[regex]::Match([IO.File]::ReadAllText("$evidence/standard.txt"),'(?m)^\s*version = ([^\r\n]+)')
if(-not $versionMatch.Success){throw 'Validator did not report the plugin version'}
$pluginVersion=$versionMatch.Groups[1].Value.Trim()
$report=[ordered]@{pluginVersion=$pluginVersion;bundle=(Resolve-Path $Bundle).Path;binarySha256=$afterHash;unchangedDuringValidation=($beforeHash -eq $afterHash);validatorSha256=(Get-FileHash $Validator).Hash;standardExit=$standardExit;extensiveExit=$extensiveExit;pluginvalExit=$pluginvalExit;pluginvalSha256=(Get-FileHash $Pluginval).Hash;pluginvalStrictness=5;guiTestsSkipped=$false;flStudio='NOT_TESTED';listening='NOT_TESTED'}
$report | ConvertTo-Json | Set-Content "$evidence/result.json"
if($standardExit -ne 0 -or $extensiveExit -ne 0 -or $pluginvalExit -ne 0 -or $beforeHash -ne $afterHash){throw "Validator failure; see $evidence"}
Write-Output "Validation evidence: $evidence"
