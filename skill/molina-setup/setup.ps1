# Installs Molina (https://github.com/DeyDom001/Molina) and starts her. Safe to run again.
#   powershell -ExecutionPolicy Bypass -File setup.ps1 [-Dir <folder>] [-NoStart]
# Kept ASCII-only: Windows PowerShell 5.1 reads scripts without a BOM as ANSI.
param(
    [string]$Dir = (Join-Path $env:USERPROFILE 'Molina'),
    [switch]$NoStart
)
$ErrorActionPreference = 'Stop'

function Step($text) { Write-Host "==> $text" -ForegroundColor Cyan }
function Fail($text) { Write-Host "Molina setup stopped: $text" -ForegroundColor Red; exit 1 }
function Run($exe, [string[]]$argv) {  # native commands don't throw on failure; check the exit code
    & $exe @argv
    if ($LASTEXITCODE -ne 0) { Fail "'$exe $($argv -join ' ')' failed (exit $LASTEXITCODE)." }
}

Step 'Checking requirements'
if ($env:OS -ne 'Windows_NT') { Fail 'Molina runs on Windows 10/11 only.' }
if (-not (Get-Command py -ErrorAction SilentlyContinue)) { Fail 'Python is not installed. Get Python 3.10+ from https://www.python.org/downloads/ and run this again.' }
& py -c "import sys; sys.exit(sys.version_info < (3, 10))"
if ($LASTEXITCODE -ne 0) { Fail "Python 3.10 or newer is needed (found $(& py --version)). Get it from https://www.python.org/downloads/." }
Write-Host "    $(& py --version)"

if (Test-Path (Join-Path $Dir 'setup\install.py')) {
    Step "Using the Molina folder already at $Dir"
} elseif (Get-Command git -ErrorAction SilentlyContinue) {
    if ((Test-Path $Dir) -and (Get-ChildItem $Dir -Force | Select-Object -First 1)) { Fail "$Dir exists and isn't a Molina folder. Pick another with -Dir." }
    Step "Downloading Molina to $Dir"
    Run git @('clone', '-q', 'https://github.com/DeyDom001/Molina.git', $Dir)
} else {
    Fail "Git isn't installed. Download the ZIP from https://github.com/DeyDom001/Molina (Code > Download ZIP), unzip it, and run this again with -Dir <that folder>."
}
Set-Location $Dir

$py = Join-Path $Dir '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) {
    Step 'Creating the Python environment (.venv)'
    Run py @('-m', 'venv', '.venv')
}
Step 'Installing PySide6 (about 700 MB the first time)'
Run $py @('-m', 'pip', 'install', '-q', '--disable-pip-version-check', 'PySide6')

Step 'Adding Molina hooks to Claude Code (settings.json is backed up first)'
Run $py @('setup\install.py')

if ($NoStart) {
    Step 'Done. Start her with: .venv\Scripts\pythonw.exe -m molina'
    exit 0
}
Step 'Starting Molina'
Start-Process (Join-Path $Dir '.venv\Scripts\pythonw.exe') -ArgumentList '-m', 'molina' -WorkingDirectory $Dir
Start-Sleep -Seconds 4
& $py -m molina status
Step 'Done. Open a NEW Claude Code session and watch her react. Right-click her > Start with Windows to keep her.'
