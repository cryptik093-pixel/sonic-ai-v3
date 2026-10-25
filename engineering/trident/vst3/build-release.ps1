param(
 [ValidateSet('omega-house-eq','adlib-93-core','organism-v4-fx-core')][string]$Product='omega-house-eq',
 [Parameter(Mandatory=$true)][string]$Output,
 [string]$ReferenceModule,
 [string]$SourceRepo,
 [ValidateRange(1,2)][int]$Jobs=1,
 [string]$ResumeFrom
)
$ErrorActionPreference='Stop'
$repoRoot=[IO.Path]::GetFullPath((Join-Path $PSScriptRoot '../../..'))
if($SourceRepo){$repoRoot=[IO.Path]::GetFullPath($SourceRepo)}
. (Join-Path $repoRoot 'engineering/vst3/scripts/enter-windows.ps1')
$arguments=@((Join-Path $PSScriptRoot 'pipeline.py'),'--repo',$repoRoot,'--product',$Product,'--output',$Output,'--jobs',[string]$Jobs)
if($ReferenceModule){$arguments+=@('--reference-module',$ReferenceModule)}
if($ResumeFrom){$arguments+=@('--resume-from',$ResumeFrom)}
& python @arguments
if($LASTEXITCODE -ne 0){throw "TRIDENT baseline failed: exit $LASTEXITCODE; inspect $Output/report.json"}
