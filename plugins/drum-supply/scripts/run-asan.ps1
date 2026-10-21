$ErrorActionPreference='Stop'
$drumRoot=Split-Path -Parent $PSScriptRoot
. "$PSScriptRoot/toolchain-windows.ps1" -Jobs 1
Push-Location $drumRoot
try {
 New-Item -ItemType Directory -Force evidence/asan | Out-Null
 & "$compilerDir/cl.exe" /nologo /std:c++20 /EHsc /MD /O1 /Zi /fsanitize=address /I Source Tests/SynthesisTests.cpp /Fe:evidence/asan/DrumSynthesisAsan.exe /Fo:evidence/asan/DrumSynthesisAsan.obj /Fd:evidence/asan/DrumSynthesisAsan.pdb
 if($LASTEXITCODE){throw 'AddressSanitizer compile failed'}
 & ./evidence/asan/DrumSynthesisAsan.exe
 if($LASTEXITCODE){throw 'AddressSanitizer execution failed'}
} finally {Pop-Location}
