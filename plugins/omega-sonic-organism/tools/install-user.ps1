param([string]$PackageRoot=(Split-Path -Parent $PSScriptRoot),[string]$Directory=(Join-Path $env:LOCALAPPDATA 'Programs/Common/VST3'))
$ErrorActionPreference='Stop'
# NSIS is a 32-bit process; inherited module search paths may point at another
# PowerShell edition. Resolve the built-in modules from the executing runtime.
Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Utility/Microsoft.PowerShell.Utility.psd1') -ErrorAction Stop
Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Management/Microsoft.PowerShell.Management.psd1') -ErrorAction Stop
$source=Join-Path $PackageRoot 'OmegaSonicOrganism.vst3'
if(-not(Test-Path -LiteralPath "$source/Contents/x86_64-win/OmegaSonicOrganism.vst3")){throw 'Run this from the extracted delivery package.'}
$destination=Join-Path ([IO.Path]::GetFullPath($Directory)) 'OmegaSonicOrganism.vst3'
if(Test-Path -LiteralPath $destination){throw "Existing installation preserved: $destination. Remove it explicitly before installing an update."}
New-Item -ItemType Directory -Path $Directory -Force | Out-Null
Copy-Item -LiteralPath $source -Destination $destination -Recurse
$entries=@(Get-ChildItem -LiteralPath $destination -Recurse -File -Force | ForEach-Object { [ordered]@{path=$_.FullName.Substring($destination.Length+1);sha256=(Get-FileHash -LiteralPath $_.FullName).Hash} })
foreach($entry in $entries){if((Get-FileHash -LiteralPath (Join-Path $source $entry.path)).Hash -ne $entry.sha256){throw 'Installed copy differs from package; inspect installation before using.'}}
[ordered]@{product='omega-sonic-organism';directory=$destination;files=$entries} | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath "$destination/.oso-install-receipt.json" -Encoding utf8
Write-Output "Installed and verified $destination. Add the parent folder to your host's VST3 search paths if needed."
