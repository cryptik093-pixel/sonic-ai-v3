param([int]$Strictness=5)
$ErrorActionPreference='Stop'
$drumRoot=Split-Path -Parent $PSScriptRoot
$drumBundle="$drumRoot/build/OmegaDrumSupply_artefacts/Release/VST3/Omega Drum Supply.vst3"
$drumBinary="$drumBundle/Contents/x86_64-win/Omega Drum Supply.vst3"
$pluginval="$drumRoot/../sonic-pocket/build/pluginval/pluginval.exe"
$validator="$drumRoot/../sonic-pocket/build/steinberg-validator/bin/validator.exe"
foreach($required in @($drumBinary,$pluginval,$validator)){if(!(Test-Path -LiteralPath $required)){throw "Missing artifact or local validator: $required"}}
$drumRun="$drumRoot/evidence/validation-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
New-Item -ItemType Directory -Path $drumRun | Out-Null
$drumHash=(Get-FileHash -LiteralPath $drumBinary).Hash.ToLowerInvariant()
$saved=@{}
foreach($name in @('SKIP_GUI_TESTS','DISABLED_TESTS','RANDOMISE','DATA_FILE','VST3VALIDATOR')){
  $saved[$name]=[Environment]::GetEnvironmentVariable($name,'Process')
  [Environment]::SetEnvironmentVariable($name,$null,'Process')
}
try{
  $pvArgs='--strictness-level '+$Strictness+' --random-seed 0x4F484453 --sample-rates 44100,48000,96000 --block-sizes 64,128,256,512,1024 --repeat 1 --timeout-ms 120000 --output-dir "'+$drumRun+'" --output-filename pluginval.txt --validate "'+$drumBundle+'"'
  $pv=Start-Process -FilePath $pluginval -ArgumentList $pvArgs -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput "$drumRun/pluginval.out.txt" -RedirectStandardError "$drumRun/pluginval.err.txt"
}finally{foreach($name in $saved.Keys){[Environment]::SetEnvironmentVariable($name,$saved[$name],'Process')}}
$sv=Start-Process -FilePath $validator -ArgumentList ('"'+$drumBundle+'"') -WindowStyle Hidden -Wait -PassThru -RedirectStandardOutput "$drumRun/steinberg.out.txt" -RedirectStandardError "$drumRun/steinberg.err.txt"
$unchanged=$drumHash -eq (Get-FileHash -LiteralPath $drumBinary).Hash.ToLowerInvariant()
[ordered]@{version='0.1.0';binary=$drumBinary;sha256=$drumHash;timestamp=(Get-Date).ToUniversalTime().ToString('o');pluginvalStrictness=$Strictness;pluginvalArguments=$pvArgs;pluginvalToolSha256=(Get-FileHash -LiteralPath $pluginval).Hash.ToLowerInvariant();pluginvalExit=$pv.ExitCode;steinbergToolSha256=(Get-FileHash -LiteralPath $validator).Hash.ToLowerInvariant();steinbergExit=$sv.ExitCode;artifactUnchanged=$unchanged;FLStudio='NOT_TESTED';listening='NOT_TESTED'} | ConvertTo-Json | Set-Content -LiteralPath "$drumRun/result.json"
Write-Output "Evidence: $drumRun; pluginval=$($pv.ExitCode), Steinberg=$($sv.ExitCode), artifact unchanged=$unchanged"
if($pv.ExitCode -or $sv.ExitCode -or !$unchanged){throw 'Artifact validation failed; inspect retained evidence'}
