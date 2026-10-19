@echo off
setlocal EnableExtensions
cd /d "%~dp0.."

rem Preferir el launcher "py" (Python.org). Evita Inkscape u otros python del PATH.
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY (
  where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
  echo No se encontro Python. Instale Python 3.11+ desde python.org y marque "Add to PATH".
  exit /b 1
)

echo Usando: %PY%
%PY% -c "import sys; print(sys.executable); raise SystemExit(0 if sys.version_info >= (3,11) else 1)"
if errorlevel 1 (
  echo Se necesita Python 3.11 o superior.
  exit /b 1
)

if exist .venv\Scripts\python.exe goto :install
echo Creando .venv ...
%PY% -m venv .venv
if errorlevel 1 (
  echo Fallo al crear .venv
  exit /b 1
)
if not exist .venv\Scripts\python.exe (
  echo No se creo .venv\Scripts\python.exe
  exit /b 1
)

:install
echo Instalando dependencias en el venv ...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

echo.
echo OK. Siguiente:
echo   1. copy .env.example .env
echo   2. copy config\settings.example.toml config\settings.toml
echo   3. completar .env / settings / secrets
echo   4. scripts\run_publish.bat publish --month YYYY-MM
endlocal
