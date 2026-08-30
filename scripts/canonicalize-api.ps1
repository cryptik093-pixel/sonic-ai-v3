$ErrorActionPreference = "Stop"

Write-Host "Sonic AI V3 - Phase 3.2 API Canonicalization" -ForegroundColor Cyan

$root = git rev-parse --show-toplevel
Set-Location $root

$branch = git branch --show-current
if ($branch -ne "recovery/actual-project-state") {
    throw "Refusing to run on '$branch'. Switch to recovery/actual-project-state first."
}

$status = git status --porcelain
if ($status) {
    throw "Working tree is not clean. Commit or stash local changes before canonicalization."
}

$source = Join-Path $root "apps/api_backup_before_import_fix"
$target = Join-Path $root "apps/api"
$legacy = Join-Path $root "apps/api_legacy_event_layer"

if (-not (Test-Path $source)) {
    throw "Recovery API source not found: $source"
}

Write-Host "Preserving current event implementation..." -ForegroundColor Yellow
if (Test-Path $legacy) {
    throw "Legacy preservation directory already exists. Review before rerunning."
}

New-Item -ItemType Directory -Path $legacy | Out-Null

git mv "$target/event_store.py" "$legacy/event_store.py"
git mv "$target/events_router.py" "$legacy/events_router.py"
git mv "$target/test_event_store.py" "$legacy/test_event_store.py"

# The existing TypeScript package manifest is not the Python API contract.
# Remove it from the canonical API; Python dependencies are declared in requirements.txt.
if (Test-Path "$target/package.json") {
    git rm "$target/package.json"
}

Write-Host "Promoting recovered FastAPI implementation into apps/api..." -ForegroundColor Yellow

$exclude = @(
    ".env",
    ".env.example",
    "data/sonic_ai.db"
)

Get-ChildItem -LiteralPath $source -Force | ForEach-Object {
    $relative = $_.Name
    $destination = Join-Path $target $relative

    if ($exclude -contains $relative) {
        return
    }

    if ($_.PSIsContainer) {
        if ($relative -eq "data") {
            return
        }
        Copy-Item -LiteralPath $_.FullName -Destination $destination -Recurse -Force
    } else {
        Copy-Item -LiteralPath $_.FullName -Destination $destination -Force
    }
}

# Remove any copied Python cache artifacts if they exist.
Get-ChildItem -Path $target -Recurse -Force -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq "__pycache__" } |
    Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

# Ensure the canonical API is explicitly a Python package.
if (-not (Test-Path "$target/__init__.py")) {
    New-Item -ItemType File -Path "$target/__init__.py" | Out-Null
}

git add apps/api scripts/canonicalize-api.ps1

git status --short

Write-Host "`nCanonicalization staged but NOT committed." -ForegroundColor Green
Write-Host "Review the staged diff before committing:" -ForegroundColor Green
Write-Host "  git diff --cached --stat"
Write-Host "  git diff --cached -- apps/api"
Write-Host "`nIf the review is correct, commit with:" -ForegroundColor Green
Write-Host "  git commit -m \"refactor(api): promote recovered FastAPI implementation to canonical API\""
Write-Host "  git push"
