param(
    [ValidateSet('Release')][string]$Configuration = 'Release',
    [string]$ValidationReport = '',
    [string]$JuceSource = '',
    [string]$BundlePath = ''
)
$ErrorActionPreference = 'Stop'
$pluginRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$repoRoot = (Resolve-Path (Join-Path $pluginRoot '../..')).Path
$buildRoot = Join-Path $pluginRoot 'build/windows-release'
$bundle = Join-Path $buildRoot "ADLIB93_artefacts/$Configuration/VST3/ADLIB-93.vst3"
if ($BundlePath) { $bundle = (Resolve-Path -LiteralPath $BundlePath).Path }
if (-not $ValidationReport) { $ValidationReport = Join-Path $pluginRoot 'evidence/validation-level10/validation.json' }
$reportPath = (Resolve-Path -LiteralPath $ValidationReport).Path
$report = Get-Content -LiteralPath $reportPath -Raw | ConvertFrom-Json
if ($report.state -ne 'PASS' -or $report.schemaVersion -ne 2 -or $report.strictness -ne 10) {
    throw 'Release-candidate staging requires the exact bundle with a successful schema-v2 level10 validation report.'
}
if (-not $JuceSource) {
    $cachePath = Join-Path $buildRoot 'CMakeCache.txt'
    if (Test-Path -LiteralPath $cachePath) {
        $cache = Get-Content -LiteralPath $cachePath -Raw
        $match = [regex]::Match($cache, '(?m)^FETCHCONTENT_SOURCE_DIR_JUCE:[^=]*=([^\r\n]+)')
        if ($match.Success) { $JuceSource = $match.Groups[1].Value }
    }
    if (-not $JuceSource) { $JuceSource = Join-Path $buildRoot '_deps/juce-src' }
}
$juceRoot = (Resolve-Path -LiteralPath $JuceSource).Path
$notices = @((Join-Path $pluginRoot 'docs/THIRD_PARTY_NOTICES.md'),
             (Join-Path $juceRoot 'LICENSE.md'), (Join-Path $juceRoot 'JUCE.spdx.json'))
# Preserve separate files even when their basenames match. The staging helper
# assigns each a distinct notice directory and hashes the copied bytes.
$notices += @(Get-ChildItem -LiteralPath (Join-Path $juceRoot 'modules') -Recurse -File |
    Where-Object { $_.Name -match '(?i)(^|[._-])(licen[cs]e|copying|copyright|notices?)($|[._-])' } |
    ForEach-Object { $_.FullName })
foreach ($notice in $notices) { if (-not (Test-Path -LiteralPath $notice -PathType Leaf)) { throw "Required notice missing: $notice" } }
$cmakeText = Get-Content -LiteralPath (Join-Path $pluginRoot 'CMakeLists.txt') -Raw
$versionMatch = [regex]::Match($cmakeText, 'project\(ADLIB93\s+VERSION\s+([0-9.]+)')
if (-not $versionMatch.Success) { throw 'Cannot determine actual ADLIB93 project version.' }
$version = $versionMatch.Groups[1].Value
$dist = Join-Path $pluginRoot 'dist'
$binaryZip = Join-Path $dist "ADLIB-93_${version}_Windows_x64.zip"
$sourceZip = Join-Path $dist "ADLIB-93_${version}_Source.zip"
$sums = Join-Path $dist "ADLIB-93_${version}_SHA256SUMS.json"
foreach ($target in @($binaryZip,$sourceZip,$sums)) {
    if (Test-Path -LiteralPath $target) { throw "Preserving existing package: $target" }
}
$python = Join-Path $repoRoot '.venv/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { $python = (Get-Command python -ErrorAction Stop).Source }
$stager = Join-Path $repoRoot 'engineering/vst3/skills/omega-vst-release/scripts/stage_release.py'
if (-not (Test-Path -LiteralPath $stager -PathType Leaf)) { throw 'Reusable release helper is missing from this source checkout.' }
$stageRoot = Join-Path $repoRoot ('engineering/vst3/dist/adlib93-' + [guid]::NewGuid().ToString('N'))
& $python $stager --bundle $bundle --validation-report $reportPath --source $pluginRoot --notices $notices --output $stageRoot
if ($LASTEXITCODE -ne 0) { throw 'Validation-bound internal staging failed; no release ZIP copied.' }
New-Item -ItemType Directory -Path $dist -Force | Out-Null
[IO.File]::Copy((Join-Path $stageRoot 'internal-evaluation.zip'),$binaryZip,$false)
[IO.File]::Copy((Join-Path $stageRoot 'source.zip'),$sourceZip,$false)
$hashes = [ordered]@{}
foreach ($pair in @(@($binaryZip,'internal-evaluation.zip'),@($sourceZip,'source.zip'))) {
    $hash = (Get-FileHash -LiteralPath $pair[0] -Algorithm SHA256).Hash.ToLowerInvariant()
    $expected = (Get-FileHash -LiteralPath (Join-Path $stageRoot $pair[1]) -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($hash -ne $expected) { throw 'Copied archive differs from verified stage.' }
    $hashes[[IO.Path]::GetFileName($pair[0])] = $hash
}
$sumStream = [IO.File]::Open($sums,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write)
try {
    $sumBytes = [Text.Encoding]::UTF8.GetBytes(($hashes | ConvertTo-Json))
    $sumStream.Write($sumBytes,0,$sumBytes.Length)
} finally { $sumStream.Dispose() }
Write-Output "Staged INTERNAL EVALUATION artifacts: $binaryZip and $sourceZip"
Write-Output 'FL Studio, listening, licensing eligibility and commercial distribution remain subject to the verification report. No installation/signing/publication performed.'
