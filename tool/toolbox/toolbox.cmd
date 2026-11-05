@echo off
setlocal
set "SCRIPT_DIR=%~dp0"
set "PY_CMD=py -3.11"
where py >nul 2>nul
if errorlevel 1 (
  set "PY_CMD=python"
)
%PY_CMD% "%SCRIPT_DIR%toolbox_cli\cli.py" %*
