@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: Lock working directory to script location
cd /d "%~dp0"

echo ====================================
echo   YouTube to Slides Converter
echo   Auto Setup and Start
echo ====================================
echo.
echo Current directory: %CD%
echo.

:: Check Python
echo [CHECK] Checking Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found in PATH
    echo.
    echo Please install Python 3.9+ from: https://www.python.org
    echo Or run this script as Administrator for automatic installation
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('where python') do echo [OK] Python found: %%i
    for /f "tokens=*" %%i in ('python --version') do echo [OK] Version: %%i
)
echo.

:: Check Node.js
echo [CHECK] Checking Node.js...
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js not found in PATH
    echo.
    echo Please install Node.js from: https://nodejs.org
    echo Or run this script as Administrator for automatic installation
    echo.
    pause
    exit /b 1
) else (
    for /f "tokens=*" %%i in ('where node') do echo [OK] Node.js found: %%i
    for /f "tokens=*" %%i in ('node --version') do echo [OK] Version: %%i
)
echo.

:: Check ffmpeg
echo [CHECK] Checking ffmpeg...
where ffmpeg >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] ffmpeg not found - optional for video processing
    echo [INFO] You can install it from: https://ffmpeg.org
) else (
    for /f "tokens=*" %%i in ('where ffmpeg') do echo [OK] ffmpeg found: %%i
)
echo.

:: Check uv
echo [CHECK] Checking uv...
where uv >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing uv package manager...
    python -m pip install --user uv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install uv
        pause
        exit /b 1
    )

    :: Add Python user Scripts to PATH for current session
    for /f "tokens=*" %%i in ('python -c "import sysconfig; print(sysconfig.get_path('scripts', 'nt_user'))"') do set USER_SCRIPTS=%%i
    set "PATH=%USER_SCRIPTS%;%PATH%"
    echo [OK] uv installed and added to PATH for this session
)

for /f "tokens=*" %%i in ('uv --version') do echo [OK] uv Version: %%i
echo.

:: Check backend environment
echo [SETUP] Setting up backend...
if not exist "backend\.venv" (
    echo [INFO] Creating backend virtual environment...
    pushd backend
    uv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create venv
        popd
        pause
        exit /b 1
    )
    echo [OK] Virtual environment created

    echo [INFO] Installing dependencies...
    uv sync
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install dependencies
        popd
        pause
        exit /b 1
    )
    popd
    echo [OK] Backend dependencies installed
) else (
    echo [OK] Backend environment exists
)
echo.

:: Check frontend dependencies
echo [SETUP] Setting up frontend...
if not exist "frontend\node_modules" (
    echo [INFO] Installing frontend dependencies...
    echo [INFO] This may take a few minutes...
    pushd frontend
    call npm install
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to install npm packages
        popd
        pause
        exit /b 1
    )
    popd
    echo [OK] Frontend dependencies installed
) else (
    echo [OK] Frontend dependencies exist
)
echo.

echo ====================================
echo   All dependencies ready!
echo ====================================
echo.
echo [INFO] Starting backend server...
pushd backend
start "Backend Server" cmd /k "uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000"
popd
timeout /t 3 /nobreak >nul

echo [INFO] Starting frontend server...
echo [INFO] Browser will open automatically when ready...
pushd frontend
start "Frontend Server" cmd /k "npm start"
popd

echo.
echo ====================================
echo   Services Started Successfully!
echo ====================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo [INFO] Servers are running in separate windows.
echo [INFO] Close the server windows to stop the services.
echo.
echo This setup window will close automatically in 3 seconds...
timeout /t 3 /nobreak >nul
