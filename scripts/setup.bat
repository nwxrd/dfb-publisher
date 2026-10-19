@echo off
setlocal
cd /d "%~dp0.."
if not exist .venv (
  python -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
echo.
echo Listo. Copie .env.example a .env y config\settings.example.toml a config\settings.toml
endlocal
