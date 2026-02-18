@echo off
setlocal enabledelayedexpansion

REM Resolve project root relative to this script's location
set "PROJECT_ROOT=%~dp0"

REM Strip trailing backslash if present
if "%PROJECT_ROOT:~-1%"=="\" set "PROJECT_ROOT=%PROJECT_ROOT:~0,-1%"

set "VENV_DIR=%PROJECT_ROOT%\.venv"
set "REQUIREMENTS=%PROJECT_ROOT%\requirements.txt"
set "HASH_FILE=%VENV_DIR%\.requirements_hash"

REM ---------------------------------------------------------------------------
REM 1. Find Python 3
REM ---------------------------------------------------------------------------
set "PYTHON_CMD="

REM Try "python" first
python --version >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PY_VER=%%v"
    if "!PY_VER:~0,1!"=="3" set "PYTHON_CMD=python"
)

REM Try "python3" if not found yet
if not defined PYTHON_CMD (
    python3 --version >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=2" %%v in ('python3 --version 2^>^&1') do set "PY_VER=%%v"
        if "!PY_VER:~0,1!"=="3" set "PYTHON_CMD=python3"
    )
)

REM Try "py -3" (Windows py launcher) if still not found
if not defined PYTHON_CMD (
    py -3 --version >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_CMD=py -3"
    )
)

REM Bail out if no Python 3 was found
if not defined PYTHON_CMD (
    echo ERROR: Python 3 could not be found.
    echo Please install Python 3 from https://www.python.org/ and ensure it is on your PATH.
    pause
    exit /b 1
)

echo Found Python 3: %PYTHON_CMD%

REM ---------------------------------------------------------------------------
REM 2. Create virtual environment if it does not exist
REM ---------------------------------------------------------------------------
if not exist "%VENV_DIR%\" (
    echo Creating virtual environment in %VENV_DIR% ...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo Virtual environment created.
)

REM ---------------------------------------------------------------------------
REM 3. Install / update dependencies only when requirements.txt has changed
REM ---------------------------------------------------------------------------
set "NEEDS_INSTALL=0"

REM Compute the current MD5 hash of requirements.txt
set "CURRENT_HASH="
for /f "skip=1 tokens=*" %%h in ('certutil -hashfile "%REQUIREMENTS%" MD5 2^>nul') do (
    if not defined CURRENT_HASH set "CURRENT_HASH=%%h"
)

if not defined CURRENT_HASH (
    echo WARNING: Could not hash requirements.txt - will attempt install anyway.
    set "NEEDS_INSTALL=1"
) else (
    REM Trim any trailing spaces from the hash
    set "CURRENT_HASH=!CURRENT_HASH: =!"
)

if "%NEEDS_INSTALL%"=="0" (
    REM Check whether the stored hash matches the current hash
    if not exist "%HASH_FILE%" (
        set "NEEDS_INSTALL=1"
    ) else (
        set "STORED_HASH="
        for /f "usebackq tokens=*" %%s in ("%HASH_FILE%") do set "STORED_HASH=%%s"
        set "STORED_HASH=!STORED_HASH: =!"
        if not "!CURRENT_HASH!"=="!STORED_HASH!" set "NEEDS_INSTALL=1"
    )
)

if "%NEEDS_INSTALL%"=="1" (
    echo Installing / updating dependencies ...
    "%VENV_DIR%\Scripts\pip.exe" install -r "%REQUIREMENTS%"
    if errorlevel 1 (
        echo ERROR: pip install failed.
        pause
        exit /b 1
    )
    REM Save the new hash so we skip install on the next run
    echo !CURRENT_HASH!> "%HASH_FILE%"
    echo Dependencies installed successfully.
) else (
    echo Dependencies are up to date - skipping install.
)

REM ---------------------------------------------------------------------------
REM 4. Activate the venv and launch the application
REM ---------------------------------------------------------------------------
echo Launching AutoWriter ...
call "%VENV_DIR%\Scripts\activate.bat"
python "%PROJECT_ROOT%\src\main.py"
