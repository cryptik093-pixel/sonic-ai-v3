<#
Hardened dev helper for Windows PowerShell.
Behavior:
- Kill any existing Next dev process (commandline contains "next dev") and any process listening on port 3000.
- Start backend and frontend each in a new PowerShell window.
#>

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "HARDENED DEV: Ensuring no existing Next dev or port 3000 processes are running..."

# Stop processes that have 'next dev' in command line
Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -and $_.CommandLine -like '*next dev*' } | ForEach-Object {
	try { Stop-Process -Id $_.ProcessId -Force -ErrorAction Stop; Write-Host "Stopped existing Next process PID:$($_.ProcessId)" } catch { }
}

# Stop processes listening on port 3000
$net = netstat -ano | Select-String ":3000"
if ($net) {
	$pids = ($net -split "\r?\n" | ForEach-Object { ($_ -split '\\s+')[-1] } | Where-Object { $_ -match '^[0-9]+$' }) | Select-Object -Unique
	foreach ($p in $pids) {
		try { Stop-Process -Id ([int]$p) -Force -ErrorAction Stop; Write-Host "Stopped process on port 3000 PID:$p" } catch { }
	}
}

Write-Host "Starting backend and frontend..."

# Start backend in new PowerShell window
$apiPath = Join-Path $repoRoot 'apps\api'
$apiCmd = "& { Set-Location -LiteralPath '$apiPath'; python -m uvicorn main:app --reload --port 8000 }"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $apiCmd

# Start frontend in new PowerShell window
$webPath = Join-Path $repoRoot 'apps\web'
$webCmd = "& { Set-Location -LiteralPath '$webPath'; pnpm dev }"
Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", $webCmd

Write-Host "Started backend and frontend in new PowerShell windows. Backend: http://127.0.0.1:8000  Frontend: http://localhost:3000"