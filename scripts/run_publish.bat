@echo off
setlocal
cd /d "%~dp0.."
if not exist .venv\Scripts\activate.bat (
  echo Ejecute scripts\setup.bat primero.
  exit /b 1
)
call .venv\Scripts\activate.bat
set PYTHONPATH=src
python -m dfb_publisher %*
endlocal
