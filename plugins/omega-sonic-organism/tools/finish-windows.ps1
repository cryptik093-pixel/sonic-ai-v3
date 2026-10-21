param([int]$Jobs=1,[string]$SdkRoot,[string]$Validator,[string]$Pluginval,[string]$EvidenceDirectory,[string]$PreviousEvidence,[string]$CpuEvidence,[switch]$CalibrateFactory)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
if(-not $SdkRoot){$SdkRoot=Join-Path $root 'build-tools/reproduction-sdk/VST_SDK/vst3sdk';if(-not(Test-Path -LiteralPath $SdkRoot)){$SdkRoot=Join-Path $root '../sonic-pocket/build/steinberg/VST_SDK/vst3sdk'}}
$stamp=[DateTime]::UtcNow.ToString('yyyyMMdd-HHmmss')
$evidence=if($EvidenceDirectory){[IO.Path]::GetFullPath($EvidenceDirectory)}else{Join-Path $root "test-results/completion-$stamp"}
if(Test-Path -LiteralPath $evidence){throw 'Preserve the existing evidence directory and choose a new one.'}
$pluginBuild=Join-Path $root "build-rc2-$stamp"
if(Test-Path -LiteralPath $pluginBuild){throw 'A clean candidate build requires a new directory.'}
New-Item -ItemType Directory -Path $evidence | Out-Null
function Record([string]$Step,[string]$State){[ordered]@{step=$Step;state=$State;utc=[DateTime]::UtcNow.ToString('o');evidence=$evidence} | ConvertTo-Json | Set-Content -LiteralPath "$root/test-results/completion-job.json"}
try {
    Record 'portable build and tests' 'RUNNING'
    $coreBuild=Join-Path $root "build-core-$stamp"
    & "$PSScriptRoot/build-windows.ps1" -CoreOnly -Jobs $Jobs -SdkRoot $SdkRoot -BuildDirectory $coreBuild *> "$evidence/core-build.log"
    Copy-Item -LiteralPath "$root/test-results/ctest.xml" -Destination "$evidence/ctest-core.xml"
    Record 'factory calibration' 'RUNNING'
    $calibrationArguments=@("$root/presets/factory-v1","$evidence/factory-calibration.json")
    if($CalibrateFactory){$calibrationArguments+='--apply'}
    & "$coreBuild/omega_calibrate_bank.exe" @calibrationArguments *> "$evidence/factory-calibration.log"
    if($LASTEXITCODE){throw 'Factory calibration failed'}
    & python "$PSScriptRoot/generate_factory.py" *> "$evidence/factory-generation.log"
    if($LASTEXITCODE){throw 'Factory embedding failed'}
    Record 'VST3 build and tests' 'RUNNING'
    & "$PSScriptRoot/build-windows.ps1" -Jobs $Jobs -SdkRoot $SdkRoot -BuildDirectory $pluginBuild *> "$evidence/plugin-build.log"
    Copy-Item -LiteralPath "$root/test-results/ctest.xml" -Destination "$evidence/ctest-plugin.xml"
    $bundle=Join-Path $pluginBuild 'VST3/Release/OmegaSonicOrganism.vst3'
    $binary=Join-Path $bundle 'Contents/x86_64-win/OmegaSonicOrganism.vst3'
    $beforeHash=(Get-FileHash -LiteralPath $binary).Hash
    Record 'VST3 validators' 'RUNNING'
    & "$PSScriptRoot/validate-windows.ps1" -Bundle $bundle -Validator $Validator -Pluginval $Pluginval *> "$evidence/validation.log"
    $validation=Get-ChildItem "$root/test-results" -Directory -Filter 'validator-*' | Sort-Object Name -Descending | Select-Object -First 1
    Copy-Item -LiteralPath $validation.FullName -Destination "$evidence/validator" -Recurse
    foreach($mode in @('0','1','--bank')){
        $name=if($mode -eq '--bank'){'bank'}elseif($mode -eq '1'){'hq'}else{'eco'}
        Record "binary renders $name" 'RUNNING'
        & "$pluginBuild/bin/omega_binary_probe.exe" $binary "$evidence/renders-$name" $mode *> "$evidence/binary-$name.log"
        if($LASTEXITCODE){throw "Actual binary probe failed: $name"}
    }
    Record '24-bit audition demonstrations' 'RUNNING'
    & "$pluginBuild/bin/omega_audition_probe.exe" $binary "$evidence/audio-previews" *> "$evidence/auditions.log"
    if($LASTEXITCODE){throw 'Audition probe failed'}
    & python "$PSScriptRoot/verify_auditions.py" "$evidence/audio-previews" *> "$evidence/pcm24-verification.log"
    if($LASTEXITCODE){throw 'PCM24 readback failed'}
    Record 'native editor API probe' 'RUNNING'
    & "$pluginBuild/bin/omega_editor_probe.exe" $binary "$evidence/editor" *> "$evidence/editor.log"
    if($LASTEXITCODE){throw 'Editor probe failed'}
    Record 'engine measurement' 'RUNNING'
    & "$pluginBuild/omega_engine_metrics.exe" "$evidence/metrics" 30 *> "$evidence/metrics.log"
    if($LASTEXITCODE){throw 'Engine measurement failed'}
    & python "$PSScriptRoot/analyze_engine_metrics.py" "$evidence/metrics" *> "$evidence/metrics-analysis.log"
    if($LASTEXITCODE){throw 'Engine measurement analysis failed'}
    if($PreviousEvidence){
        Record 'CPU optimization audio equivalence against preserved candidate' 'RUNNING'
        foreach($name in @('renders-eco','renders-hq','renders-bank','audio-previews')){
            & python "$PSScriptRoot/compare_cpu_audio.py" "$PreviousEvidence/$name" "$evidence/$name" "$evidence/cpu-equivalence-$name.json" *> "$evidence/cpu-equivalence-$name.log"
            if($LASTEXITCODE){throw "CPU audio equivalence failed: $name"}
        }
        $previous=Get-Content -LiteralPath "$PreviousEvidence/result.json" -Raw | ConvertFrom-Json
        $previousBinary=Join-Path $previous.buildDirectory 'VST3/Release/OmegaSonicOrganism.vst3/Contents/x86_64-win/OmegaSonicOrganism.vst3'
        if((Get-FileHash -LiteralPath $previousBinary).Hash -ne $previous.binarySha256){throw 'Preserved baseline binary differs from its qualification'}
        foreach($item in @(@{name='before';binary=$previousBinary},@{name='after';binary=$binary})){
            & "$pluginBuild/bin/omega_audition_probe.exe" $item.binary "$evidence/cpu-held-$($item.name)" --cpu-regression *> "$evidence/cpu-held-$($item.name).log"
            if($LASTEXITCODE){throw 'Long-held CPU regression capture failed'}
        }
        & python "$PSScriptRoot/compare_cpu_audio.py" "$evidence/cpu-held-before" "$evidence/cpu-held-after" "$evidence/cpu-equivalence-held.json" *> "$evidence/cpu-equivalence-held.log"
        if($LASTEXITCODE){throw 'Long-held CPU regression equivalence failed'}
    }
    if($CpuEvidence){Copy-Item -LiteralPath $CpuEvidence -Destination "$evidence/cpu-comparison" -Recurse}
    Record 'pinned SDK compiler dependency verification' 'RUNNING'
    $sdkArchive=Join-Path $root 'dependencies/steinberg-sdk.zip';if(-not(Test-Path -LiteralPath $sdkArchive)){$sdkArchive=Join-Path $root '../sonic-pocket/build/steinberg-sdk.zip'}
    & python "$PSScriptRoot/verify_sdk.py" $sdkArchive $SdkRoot "$evidence/sdk-provenance.json" $pluginBuild *> "$evidence/sdk-provenance.log"
    if($LASTEXITCODE){throw 'SDK compiler dependency verification failed'}
    $afterHash=(Get-FileHash -LiteralPath $binary).Hash
    if($beforeHash -ne $afterHash){throw 'Binary changed during qualification'}
    [ordered]@{version='1.0.0-rc.2';buildDirectory=$pluginBuild;cleanBuildStartedInEmptyDirectory=$true;binarySha256=$afterHash;validators='PASSED';binaryRenderCases=174;editorApi='PASSED';flStudio='NOT_TESTED';listening='NOT_TESTED';performance='See metrics/benchmark.json; no automatic release approval';utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content "$evidence/result.json"
    Record 'legacy state compatibility' 'RUNNING'
    if(Test-Path -LiteralPath "$root/test-results/m2-before-lookup-optimization.vst3"){& "$PSScriptRoot/verify-legacy-state.ps1" -Evidence $evidence}
    Record 'available automated qualification' 'PASSED'
} catch {
    Record $_.Exception.Message 'FAILED'
    $_ | Out-String | Set-Content "$evidence/failure.txt"
    exit 1
}
