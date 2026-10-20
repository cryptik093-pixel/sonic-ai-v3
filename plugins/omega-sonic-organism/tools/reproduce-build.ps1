param([string]$SdkRoot,[int]$Jobs=1)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
if(-not $SdkRoot){
    $archive=Join-Path $root 'dependencies/steinberg-sdk.zip'
    if(-not(Test-Path -LiteralPath $archive)){throw 'Supply -SdkRoot or the pinned dependencies/steinberg-sdk.zip archive.'}
    if((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash -ne '64965F1B74E08A6D4087A35AF7A716F4DCFF5852C66AD7EE13F1C47E79C1AB77'){throw 'SDK archive hash mismatch'}
    $extracted=Join-Path $root 'build-tools/reproduction-sdk'
    if(-not(Test-Path -LiteralPath $extracted)){Expand-Archive -LiteralPath $archive -DestinationPath $extracted}
    $SdkRoot=Join-Path $extracted 'VST_SDK/vst3sdk'
}
$fresh=Join-Path $root ('build-reproduction-'+[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss'))
& "$PSScriptRoot/build-windows.ps1" -SdkRoot $SdkRoot -BuildDirectory $fresh -Jobs $Jobs
if($LASTEXITCODE){throw 'Fresh reproduction failed'}
Write-Output "Fresh build and tests completed: $fresh"
Write-Output 'Run validators on this new bundle before treating it as a separately qualified artifact.'
