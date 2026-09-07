@echo off
setlocal
cd /d "%~dp0"
set "PYTHON="
py --version >nul 2>&1 && set "PYTHON=py"
if not defined PYTHON python --version >nul 2>&1 && set "PYTHON=python"
if not defined PYTHON if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PYTHON=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PYTHON (
    echo Python is not installed or is not available on PATH.
    echo Install Python 3.11+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
if not exist ".venv\Scripts\python.exe" (
    %PYTHON% -m venv .venv
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
start "EcoPulse server" cmd /k "cd /d "%~dp0" && .venv\Scripts\python.exe app.py"
timeout /t 2 /nobreak >nul
start "EcoPulse browser" http://127.0.0.1:5000
