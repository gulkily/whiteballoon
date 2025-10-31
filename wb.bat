@echo off
setlocal ENABLEDELAYEDEXPANSION
set SCRIPT_DIR=%~dp0

REM Find Python (prefer Windows launcher)
where py >NUL 2>NUL
if %ERRORLEVEL%==0 (
  set "PY=py -3"
) else (
  where python >NUL 2>NUL
  if %ERRORLEVEL%==0 (
    set "PY=python"
  ) else (
    echo [ERROR] Python 3.10+ not found. Install from https://www.python.org/downloads/ or run: winget install Python.Python.3 1>&2
    exit /b 1
  )
)

REM Delegate to the unified Python launcher
call %PY% "%SCRIPT_DIR%wb.py" %*
exit /b %ERRORLEVEL%
