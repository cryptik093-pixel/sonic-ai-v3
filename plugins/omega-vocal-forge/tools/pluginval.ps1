param([Parameter(Mandatory)][string]$Bundle,[Parameter(Mandatory)][string]$EvidenceDirectory,[Parameter(Mandatory)][string]$Executable)
$ErrorActionPreference='Stop'
foreach($path in @($Bundle,$EvidenceDirectory,$Executable)){if(-not(Test-Path -LiteralPath $path)){throw "Missing pluginval input: $path"}}
$Bundle=(Resolve-Path -LiteralPath $Bundle).Path
$EvidenceDirectory=(Resolve-Path -LiteralPath $EvidenceDirectory).Path
$Executable=(Resolve-Path -LiteralPath $Executable).Path
$saved=@{}
foreach($name in @('SKIP_GUI_TESTS','DISABLED_TESTS','RANDOMISE','DATA_FILE','VST3VALIDATOR')){$saved[$name]=[Environment]::GetEnvironmentVariable($name,'Process');[Environment]::SetEnvironmentVariable($name,$null,'Process')}
try {
 $logPath=Join-Path $EvidenceDirectory 'pluginval.txt'
 if(Test-Path -LiteralPath $logPath){Copy-Item -LiteralPath $logPath -Destination "$EvidenceDirectory/pluginval-previous.txt" -Force}
 [IO.File]::WriteAllText($logPath,'')
 $arguments='--strictness-level 5 --random-seed 0x564f4341 --sample-rates 44100,48000,96000 --block-sizes 64,128,512,1024 --repeat 1 --timeout-ms 120000 --output-dir "'+$EvidenceDirectory+'" --output-filename pluginval.txt --validate "'+$Bundle+'"'
 # Native GUI executables can return early under PowerShell's call operator.
 # Wait for the process tree and require a complete semantic result as well.
 $process=Start-Process -FilePath $Executable -ArgumentList $arguments -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput "$EvidenceDirectory/pluginval-console.log" -RedirectStandardError "$EvidenceDirectory/pluginval-stderr.log"
 $log=Get-Content -LiteralPath $logPath -Raw
 $pass=$process.ExitCode -eq 0 -and $log -match '(?m)^SUCCESS\s*\z'
 $result=[ordered]@{status=$(if($pass){'PASS'}else{'FAIL'});exitCode=$process.ExitCode;strictness=5;guiTestsSkipped=$false;completedSuccessMarker=($log -match '(?m)^SUCCESS\s*\z');executableSha256=(Get-FileHash -LiteralPath $Executable -Algorithm SHA256).Hash;arguments=$arguments;timestampUtc=[DateTime]::UtcNow.ToString('o')}
 $result | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath "$EvidenceDirectory/pluginval-result.json" -Encoding utf8
 if(-not $pass){throw 'Pluginval failed or did not finish; inspect pluginval.txt'}
 [pscustomobject]$result
} finally {foreach($name in $saved.Keys){[Environment]::SetEnvironmentVariable($name,$saved[$name],'Process')}}
