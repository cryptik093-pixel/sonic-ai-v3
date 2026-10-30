param([string]$SdkRoot,[string]$SdkArchive,[string]$BuildDir='build',[int]$Jobs=2)
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$vsLocator="${env:ProgramFiles(x86)}/Microsoft Visual Studio/Installer/vswhere.exe"
$vsRoot=& $vsLocator -latest -products '*' -property installationPath
if(-not $vsRoot){throw 'MSVC Build Tools unavailable'}
$compilerRoot=Get-ChildItem "$vsRoot/VC/Tools/MSVC" -Directory | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName
$winSdk="${env:ProgramFiles(x86)}/Windows Kits/10"
$sdkVersion=Get-ChildItem "$winSdk/Lib" -Directory | Where-Object {Test-Path "$($_.FullName)/um/x64/kernel32.lib"} | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty Name
$env:INCLUDE="$compilerRoot/include;$winSdk/Include/$sdkVersion/ucrt;$winSdk/Include/$sdkVersion/shared;$winSdk/Include/$sdkVersion/um;$winSdk/Include/$sdkVersion/winrt"
$env:LIB="$compilerRoot/lib/x64;$winSdk/Lib/$sdkVersion/ucrt/x64;$winSdk/Lib/$sdkVersion/um/x64"
$env:PATH="$compilerRoot/bin/Hostx64/x64;$vsRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/CMake/bin;$vsRoot/Common7/IDE/CommonExtensions/Microsoft/CMake/Ninja;$winSdk/bin/$sdkVersion/x64;$env:PATH"
if(-not $SdkRoot){$SdkRoot=[IO.Path]::GetFullPath("$projectRoot/../sonic-pocket/build/steinberg/VST_SDK/vst3sdk")}
if(-not $SdkArchive){$SdkArchive=[IO.Path]::GetFullPath("$projectRoot/../sonic-pocket/build/steinberg-sdk.zip")}
if((Get-FileHash -LiteralPath $SdkArchive -Algorithm SHA256).Hash -ne '64965F1B74E08A6D4087A35AF7A716F4DCFF5852C66AD7EE13F1C47E79C1AB77'){throw 'SDK archive pin mismatch'}
if(-not [IO.Path]::IsPathRooted($BuildDir)){$BuildDir=Join-Path $projectRoot $BuildDir}
New-Item -ItemType Directory -Force "$projectRoot/evidence" | Out-Null
Start-Transcript -Path "$projectRoot/evidence/build.log" -Force
try {
 Write-Output "Compiler $compilerRoot; Windows SDK $sdkVersion; VST SDK $SdkRoot"
 & cmake --version
 & cmake -S $projectRoot -B $BuildDir -G Ninja -DCMAKE_BUILD_TYPE=Release -DCMAKE_EXPORT_COMPILE_COMMANDS=ON "-DOVF_SDK_ROOT=$SdkRoot" -DBUILD_TESTING=ON 2>&1 | Tee-Object -FilePath "$projectRoot/evidence/configure.log"
 if($LASTEXITCODE){throw 'Configure failed'}
 $targets=@('OmegaVocalForge','ovf_engine_tests','ovf_adapter_tests','ovf_artifact_probe')
 $existingValidator=Join-Path $projectRoot '../sonic-pocket/build/steinberg-validator/bin/validator.exe'
 if(-not(Test-Path -LiteralPath $existingValidator)){$targets+='validator'}
 & cmake --build $BuildDir --target @targets --parallel $Jobs 2>&1 | Tee-Object -FilePath "$projectRoot/evidence/compile.log"
 if($LASTEXITCODE){throw 'Build failed'}
 & ctest --test-dir $BuildDir --output-on-failure 2>&1 | Tee-Object -FilePath "$projectRoot/evidence/ctest.log"
 if($LASTEXITCODE){throw 'CTest failed'}
 & python "$PSScriptRoot/verify-sdk.py" $SdkArchive $SdkRoot $BuildDir "$projectRoot/evidence/sdk-provenance.json"
 if($LASTEXITCODE){throw 'SDK provenance failed'}
} finally {Stop-Transcript}
