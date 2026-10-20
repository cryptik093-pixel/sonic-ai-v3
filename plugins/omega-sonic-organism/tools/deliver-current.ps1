param([Parameter(Mandatory=$true)][string]$Evidence,[int]$WaitForProcess=0)
$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
function Record([string]$Step,[string]$State){[ordered]@{step=$Step;state=$State;evidence=$Evidence;utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json | Set-Content "$root/test-results/delivery-job.json"}
try {
    Record 'waiting for candidate qualification' 'RUNNING'
    while($WaitForProcess -and (Get-Process -Id $WaitForProcess -ErrorAction SilentlyContinue)){Start-Sleep -Seconds 5}
    if(-not(Test-Path -LiteralPath "$Evidence/result.json")){throw 'Candidate qualification did not produce a final result; inspect completion-job.json and its failure log.'}
    $workflow=Get-Content -LiteralPath "$root/test-results/completion-job.json" -Raw | ConvertFrom-Json
    if($workflow.state -ne 'PASSED' -or $workflow.evidence -ne $Evidence){throw 'Candidate workflow did not finish successfully'}
    Record 'original v0.2 to candidate native-state compatibility' 'RUNNING'
    if(-not(Test-Path -LiteralPath "$Evidence/legacy-state-result.json")){& "$PSScriptRoot/verify-legacy-state.ps1" -Evidence $Evidence}
    Record 'readback of 48 exported PCM24 demonstrations' 'RUNNING'
    if(-not(Test-Path -LiteralPath "$Evidence/audio-previews/pcm24-verification.json")){
        & python "$PSScriptRoot/verify_auditions.py" "$Evidence/audio-previews" *> "$Evidence/pcm24-verification.log"
        if($LASTEXITCODE){throw 'PCM24 readback failed'}
    }
    Record 'waiting for pinned SDK provenance comparison' 'RUNNING'
    $deadline=[DateTime]::UtcNow.AddMinutes(45)
    while(-not(Test-Path -LiteralPath "$root/test-results/sdk-provenance.json")){
        if([DateTime]::UtcNow -gt $deadline){throw 'Pinned SDK comparison did not finish; inspect its command output.'}
        Start-Sleep -Seconds 5
    }
    Record 'Windows Setup, preservation fixtures and complete ZIP' 'RUNNING'
    & "$PSScriptRoot/package-windows.ps1" -Evidence $Evidence
    Record 'delivery artifacts created and verified' 'PASSED'
} catch {
    Record $_.Exception.Message 'FAILED'
    $_ | Out-String | Set-Content "$root/test-results/delivery-failure.txt"
    exit 1
}
