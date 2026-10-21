param([ValidateSet(5,10)][int]$Strictness=10,[string]$Pluginval="",[string]$Steinberg="",[int]$Timeout=1200)
$ErrorActionPreference='Stop'
$drumRoot=Split-Path -Parent $PSScriptRoot
if(!$Pluginval){$Pluginval="$drumRoot/../sonic-pocket/build/pluginval/pluginval.exe"}
if(!$Steinberg){$Steinberg="$drumRoot/../sonic-pocket/build/steinberg-validator/bin/validator.exe"}
$drumBundle="$drumRoot/build/OmegaDrumSupply_artefacts/Release/VST3/Drum Shot Supply Co..vst3"
$drumEvidence="$drumRoot/evidence/validation-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
& python "$PSScriptRoot/validate-vst3.py" --bundle $drumBundle --pluginval $Pluginval --steinberg $Steinberg --output $drumEvidence --strictness $Strictness --timeout $Timeout
if($LASTEXITCODE){throw "VST3 validation failed or incomplete: $drumEvidence"}
