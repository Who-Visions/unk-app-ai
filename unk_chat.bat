@echo off
REM Unk Agent CLI Launcher
title Unk Agent Chat

echo Starting Unk Agent...
echo.

REM Clear potential conflicting environment variables
set PYTHONHOME=
set PYTHONPATH=

REM Check python availability
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Python not found in PATH. Trying 'py' launcher...
    where py >nul 2>&1
    if %errorlevel% neq 0 (
        echo Error: Python is not installed or not in PATH.
        pause
        exit /b 1
    )
    set PYTHON_CMD=py
) else (
    set PYTHON_CMD=python
)

echo Using Python: %PYTHON_CMD%
%PYTHON_CMD% --version

REM 1. Handle incompatible venv
if exist venv (
    if not exist venv\Scripts\activate.bat (
        echo Detected incompatible venv. Cleaning up...
        rmdir /s /q venv
    )
)

REM 2. Create venv if missing
if not exist venv (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
    if errorlevel 1 (
        echo Failed to create venv. Your Python installation might be corrupt.
        pause
        exit /b 1
    )
)

REM 3. Activate venv
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate venv.
    pause
    exit /b 1
)

REM 4. Install dependencies if missing
pip show google-genai >nul 2>&1
if errorlevel 1 set INSTALL_REQ=1
pip show yt-dlp >nul 2>&1
if errorlevel 1 set INSTALL_REQ=1

if defined INSTALL_REQ (
    echo Installing dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo Dependency installation failed.
        pause
        exit /b 1
    )
)

REM 5. Set Env Var
if "%GOOGLE_CLOUD_PROJECT%"=="" (
    set "GOOGLE_CLOUD_PROJECT=unk-app-480102"
)

REM 6. Run CLI
echo Launching CLI...
python cli.py

if errorlevel 1 (
    echo.
    echo Application crashed with error code %errorlevel%
    pause
)
