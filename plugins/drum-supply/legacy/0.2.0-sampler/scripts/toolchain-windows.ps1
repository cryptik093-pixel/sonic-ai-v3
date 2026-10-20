# Local environment discovery adapted from the existing Sonic Pocket helper.
param([ValidateRange(1,8)][int]$Jobs=1)
$ErrorActionPreference = 'Stop'
$vswherePath = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\Installer\vswhere.exe"
$vsDir = @("${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\BuildTools", "${env:ProgramFiles}\Microsoft Visual Studio\2022\BuildTools") | Where-Object { Test-Path "$_\VC\Tools\MSVC" } | Select-Object -First 1
if (-not $vsDir -and (Test-Path $vswherePath)) {
    $vsDir = & $vswherePath -latest -products '*' -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
}
# Some BuildTools installs are usable but absent from vswhere's component registry.
if (-not $vsDir) {
    $candidates = @("${env:ProgramFiles(x86)}\Microsoft Visual Studio\18\BuildTools", "${env:ProgramFiles}\Microsoft Visual Studio\2022\BuildTools")
    $vsDir = $candidates | Where-Object { Test-Path "$_\VC\Tools\MSVC" } | Select-Object -First 1
}
if (-not $vsDir) { throw 'Install Microsoft C++ Build Tools with Windows SDK and CMake tools.' }
$msvcDir = Get-ChildItem "$vsDir\VC\Tools\MSVC" -Directory | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty FullName
$sdkDir = "${env:ProgramFiles(x86)}\Windows Kits\10"
$sdkVersion = Get-ChildItem "$sdkDir\Lib" -Directory | Where-Object { Test-Path "$($_.FullName)\um\x64\kernel32.lib" } | Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty Name
if (-not $sdkVersion) { throw 'Windows x64 SDK libraries are missing.' }
$compilerDir = "$msvcDir\bin\Hostx64\x64"
$env:INCLUDE = "$msvcDir\include;$sdkDir\Include\$sdkVersion\ucrt;$sdkDir\Include\$sdkVersion\shared;$sdkDir\Include\$sdkVersion\um;$sdkDir\Include\$sdkVersion\winrt"
$env:LIB = "$msvcDir\lib\x64;$sdkDir\Lib\$sdkVersion\ucrt\x64;$sdkDir\Lib\$sdkVersion\um\x64"
$cmakeDir = "$vsDir\Common7\IDE\CommonExtensions\Microsoft\CMake"
$env:PATH = "$compilerDir;$cmakeDir\CMake\bin;$cmakeDir\Ninja;$sdkDir\bin\$sdkVersion\x64;$env:PATH"
$env:CMAKE_BUILD_PARALLEL_LEVEL = [string]$Jobs # Also bounds JUCE's configure-time helper build.
