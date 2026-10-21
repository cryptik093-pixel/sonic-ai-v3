param([string]$SdkRoot,[switch]$CoreOnly,[int]$Jobs=2,[switch]$EditorSyntaxOnly,[string]$BuildDirectory)
$ErrorActionPreference='Stop'
$osoRoot=Split-Path -Parent $PSScriptRoot
$vsLocator="${env:ProgramFiles(x86)}/Microsoft Visual Studio/Installer/vswhere.exe"
$vsRoot=& $vsLocator -latest -products '*' -property installationPath
$compilerRoot=Get-ChildItem "$vsRoot/VC/Tools/MSVC" -Directory | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName
$winSdk="${env:ProgramFiles(x86)}/Windows Kits/10"
$sdkVersion=Get-ChildItem "$winSdk/Lib" -Directory | Where-Object { Test-Path "$($_.FullName)/um/x64/kernel32.lib" } | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty Name
$env:INCLUDE="$compilerRoot/include;$winSdk/Include/$sdkVersion/ucrt;$winSdk/Include/$sdkVersion/shared;$winSdk/Include/$sdkVersion/um;$winSdk/Include/$sdkVersion/winrt"
$env:LIB="$compilerRoot/lib/x64;$winSdk/Lib/$sdkVersion/ucrt/x64;$winSdk/Lib/$sdkVersion/um/x64"
$env:PATH="$compilerRoot/bin/Hostx64/x64;$vsRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin;$vsRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja;$winSdk/bin/$sdkVersion/x64;$env:PATH"
if(-not $SdkRoot){$SdkRoot=Join-Path $osoRoot 'build-tools/reproduction-sdk/VST_SDK/vst3sdk';if(-not(Test-Path -LiteralPath $SdkRoot)){$SdkRoot=Join-Path $osoRoot '../sonic-pocket/build/steinberg/VST_SDK/vst3sdk'}}
if($EditorSyntaxOnly){
    & cl /nologo /Zs /EHsc /std:c++17 /utf-8 /DRELEASE=1 /DOSO_WITH_EDITOR=1 "/I$SdkRoot" "/I$SdkRoot/vstgui4" "/I$osoRoot/core/include" "$osoRoot/plugin/Editor.cpp"
    if($LASTEXITCODE){throw 'Editor syntax check failed'}
    return
}
New-Item -ItemType Directory "$osoRoot/test-results" -Force | Out-Null
& cmake --version
& cl
Write-Output "Windows SDK $sdkVersion; compiler $compilerRoot; SDK $SdkRoot"
& python "$PSScriptRoot/validate_contracts.py"
if($LASTEXITCODE){throw 'Contract validation failed'}
& python "$PSScriptRoot/generate_parameters.py" --check
if($LASTEXITCODE){throw 'Generated parameter registry mismatch'}
$build=if($CoreOnly){"$osoRoot/build-core"}else{"$osoRoot/build"}
if($BuildDirectory){$build=[IO.Path]::GetFullPath($BuildDirectory)}
$enabled=if($CoreOnly){'OFF'}else{'ON'}
& cmake -S $osoRoot -B $build -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON "-DOSO_BUILD_PLUGIN=$enabled" "-DOSO_SDK_ROOT=$SdkRoot"
if($LASTEXITCODE){throw 'Configure failed'}
$targets=if($CoreOnly){@('omega_core_tests','omega_state_tests','omega_engine_tests','omega_engine_metrics','omega_cpu_profile','omega_preset_tests','omega_calibrate_bank')}else{@('OmegaSonicOrganism','omega_core_tests','omega_state_tests','omega_engine_tests','omega_engine_metrics','omega_cpu_profile','omega_preset_tests','omega_calibrate_bank','omega_adapter_tests','omega_binary_probe','omega_editor_probe','omega_audition_probe')}
& cmake --build $build --target @targets --parallel $Jobs
if($LASTEXITCODE){throw 'Build failed'}
& ctest --test-dir $build --output-on-failure --output-junit "$osoRoot/test-results/ctest.xml"
if($LASTEXITCODE){throw 'CTest failed'}
