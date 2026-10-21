$ErrorActionPreference='Stop'
$drumRoot=Split-Path -Parent $PSScriptRoot
. "$PSScriptRoot/toolchain-windows.ps1" -Jobs 1
Push-Location $drumRoot
try {
 New-Item -ItemType Directory -Force evidence/asan | Out-Null
 [IO.File]::WriteAllText("$drumRoot/evidence/asan-verification.json",'{"state":"RUNNING"}')
 & "$compilerDir/cl.exe" /nologo /std:c++20 /EHsc /MD /O1 /Zi /fsanitize=address /I Source Tests/SynthesisTests.cpp /Fe:evidence/asan/DrumSynthesisAsan.exe /Fo:evidence/asan/DrumSynthesisAsan.obj /Fd:evidence/asan/DrumSynthesisAsan.pdb
 if($LASTEXITCODE){throw 'AddressSanitizer compile failed'}
 & ./evidence/asan/DrumSynthesisAsan.exe
 if($LASTEXITCODE){throw 'AddressSanitizer execution failed'}
 $asanRecord=@{state='PASS';command='scripts/run-asan.ps1';engine_sha256=(Get-FileHash Source/DrumEngine.h).Hash.ToLower();test_sha256=(Get-FileHash Tests/SynthesisTests.cpp).Hash.ToLower();executable_sha256=(Get-FileHash evidence/asan/DrumSynthesisAsan.exe).Hash.ToLower();scope='Framework-independent production synthesis, not full-host instrumentation'}
 [IO.File]::WriteAllText("$drumRoot/evidence/asan-verification.json",($asanRecord | ConvertTo-Json),[Text.UTF8Encoding]::new($false))
} finally {Pop-Location}
