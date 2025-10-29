# balloon.ps1
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$VenvDir = Join-Path $ScriptDir ".venv"
$DevTool = Join-Path $ScriptDir "tools\dev.py"
$ProjectName = "WhiteBalloon"
$Version = "0.1.0"

function Log($msg) {
    Write-Host "[INFO] $msg" -ForegroundColor Blue
}

function Warn($msg) {
    Write-Host "[WARN] $msg" -ForegroundColor Yellow
}

function Fail($msg) {
    Write-Host "[ERROR] $msg" -ForegroundColor Red
    exit 1
}

function Get-PythonExec {
    $venvPython = Join-Path $VenvDir "Scripts\python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }
    $python3 = Get-Command python3 -ErrorAction SilentlyContinue
    if ($python3) {
        return $python3.Path
    }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return $python.Path
    }
    Fail "Python 3 is required. Please install it and re-run."
}

function Ensure-CliReady {
    $py = Get-PythonExec
    $code = @"
try:
    import fastapi
    import typer
except Exception:
    raise SystemExit(1)
"@
    $result = & $py -c $code
    if ($LASTEXITCODE -ne 0) {
        Fail "Dependencies missing. Run '.\balloon.ps1 setup' first."
    }
}

function Run-Dev {
    Ensure-CliReady
    $py = Get-PythonExec
    & $py $DevTool @args
}

function Create-EnvFile {
    $envFile = Join-Path $ScriptDir ".env"
    $envExample = Join-Path $ScriptDir ".env.example"
    if (!(Test-Path $envFile) -and (Test-Path $envExample)) {
        Copy-Item $envExample $envFile
        Log "Created .env from .env.example"
    }
}

function Setup-Cmd {
    $basePy = Get-PythonExec
    $venvPython = Join-Path $VenvDir "Scripts\python.exe"
    if (!(Test-Path $venvPython)) {
        Log "Creating virtual environment at .venv"
        & $basePy -m venv $VenvDir
    }
    Log "Installing project dependencies"
    & $venvPython -m pip install --upgrade pip | Out-Null
    & $venvPython -m pip install -e $ScriptDir | Out-Null
    Create-EnvFile
    Log "Setup complete"
}

function Print-Help {
    @"
WhiteBalloon CLI Wrapper
Usage: .\balloon.ps1 <command> [options]

Core commands:
  setup                 Create virtualenv and install dependencies
  runserver [--opts]    Start the development server
  init-db               Initialize the SQLite database
  create-admin USER     Promote a user to admin
  create-invite [opts]  Generate invite tokens
  version               Display CLI version info
  help                  Show this help message

Any other arguments are forwarded to the underlying Typer CLI in tools/dev.py.
"@ | Write-Host
}

# Main
if ($args.Count -eq 0) {
    Print-Help
    exit 0
}

$Command = $args[0]
$args = $args[1..($args.Count - 1)]

switch ($Command) {
    "help" { Print-Help }
    "-h" { Print-Help }
    "--help" { Print-Help }
    "version" { Write-Host "$ProjectName CLI $Version" }
    "-v" { Write-Host "$ProjectName CLI $Version" }
    "--version" { Write-Host "$ProjectName CLI $Version" }
    "setup" { Setup-Cmd }
    "runserver" { Run-Dev $Command @args }
    "init-db" { Run-Dev $Command @args }
    "create-admin" { Run-Dev $Command @args }
    "create-invite" { Run-Dev $Command @args }
    default { Run-Dev $Command @args }
}
