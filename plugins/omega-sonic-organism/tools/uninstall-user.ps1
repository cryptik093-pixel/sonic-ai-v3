param([string]$Directory=(Join-Path $env:LOCALAPPDATA 'Programs/Common/VST3'))
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Utility/Microsoft.PowerShell.Utility.psd1') -ErrorAction Stop
Import-Module (Join-Path $PSHOME 'Modules/Microsoft.PowerShell.Management/Microsoft.PowerShell.Management.psd1') -ErrorAction Stop
$destination=[IO.Path]::GetFullPath((Join-Path $Directory 'OmegaSonicOrganism.vst3'))
$receiptPath=Join-Path $destination '.oso-install-receipt.json'
if(-not(Test-Path -LiteralPath $receiptPath)){throw 'No owned installation receipt. Nothing removed.'}
$receipt=Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
if($receipt.product -ne 'omega-sonic-organism' -or $receipt.directory -ne $destination){throw 'Receipt does not identify this installation.'}
$items=@(Get-ChildItem -LiteralPath $destination -Recurse -Force)
if((Get-Item -LiteralPath $destination).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Refusing a reparse-point installation.'}
foreach($item in $items){if($item.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Refusing a reparse point inside the installation.'}}
$files=@($items | Where-Object { -not $_.PSIsContainer -and $_.FullName -ne $receiptPath })
if($files.Count -ne $receipt.files.Count){throw 'Installation contains changed or additional files. Nothing removed.'}
$ownedFiles=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
$ownedDirectories=[Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
foreach($entry in $receipt.files){
    $path=[IO.Path]::GetFullPath((Join-Path $destination $entry.path))
    if(-not $path.StartsWith($destination+[IO.Path]::DirectorySeparatorChar,[StringComparison]::OrdinalIgnoreCase)){throw 'Unsafe receipt path. Nothing removed.'}
    if(-not $ownedFiles.Add($path)){throw 'Duplicate receipt path. Nothing removed.'}
    if(-not(Test-Path -LiteralPath $path -PathType Leaf) -or (Get-FileHash -LiteralPath $path).Hash -ne $entry.sha256){throw 'Modified installation preserved. Nothing removed.'}
    $parent=[IO.Path]::GetDirectoryName($path)
    while($parent -and $parent -ne $destination){$null=$ownedDirectories.Add($parent);$parent=[IO.Path]::GetDirectoryName($parent)}
}
foreach($file in $files){if(-not $ownedFiles.Contains($file.FullName)){throw 'Unfamiliar file preserved. Nothing removed.'}}
foreach($directory in ($items | Where-Object PSIsContainer)){if(-not $ownedDirectories.Contains($directory.FullName)){throw 'Unfamiliar directory preserved. Nothing removed.'}}
# The exact absolute directory and all owned file hashes have been checked.
Remove-Item -LiteralPath $destination -Recurse -Force
Write-Output "Removed verified owned installation: $destination. User patches and projects are outside this bundle."
