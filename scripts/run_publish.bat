@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

if not exist .venv\Scripts\python.exe (
  echo No existe .venv. Ejecute: scripts\setup.bat
  exit /b 1
)

set "PYTHONPATH=src"
".venv\Scripts\python.exe" -m dfb_publisher %*
set "ERR=%ERRORLEVEL%"
endlocal & exit /b %ERR%
