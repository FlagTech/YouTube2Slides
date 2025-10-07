@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: Lock working directory to script location
cd /d "%~dp0"

:: Set log file
set "LOG=%TEMP%\yt2slides_setup.log"
echo [%date% %time%] Start setup > "%LOG%"

echo ====================================
echo   YouTube to Slides Converter
echo   Auto Setup and Start
echo ====================================
echo.

:: Check for admin rights (if not, try to elevate)
whoami /groups | findstr /C:"S-1-16-12288" >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Administrator rights required. Attempting to restart...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process '%~f0' -Verb RunAs -WorkingDirectory '%CD%' -WindowStyle Normal"
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to get admin rights. Please run as Administrator.
        echo.
        echo Press any key to exit...
        pause >nul
    )
    exit /b
)

echo [CHECK] Checking system environment...
echo.

:: ===== Python =====
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [INSTALL] Downloading and installing Python 3.11.9...
    set "PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    set "PYTHON_INSTALLER=%TEMP%\python_installer.exe"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'" >>"%LOG%" 2>&1
    if not exist "%PYTHON_INSTALLER%" (
        echo [ERROR] Python download failed. See "%LOG%"
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    "%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 >>"%LOG%" 2>&1
    timeout /t 25 /nobreak >nul
    call :RefreshEnv
    del "%PYTHON_INSTALLER%" >nul 2>&1
    where python >nul 2>nul || (echo [ERROR] Python installation failed & echo. & echo Press any key to exit... & pause >nul & exit /b 1)
    echo [OK] Python installed successfully
) else (
    echo [OK] Python already installed
)
echo.

:: ===== Node.js =====
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [INSTALL] Downloading and installing Node.js 20.11.1 LTS...
    set "NODE_URL=https://nodejs.org/dist/v20.11.1/node-v20.11.1-x64.msi"
    set "NODE_INSTALLER=%TEMP%\node_installer.msi"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest '%NODE_URL%' -OutFile '%NODE_INSTALLER%'" >>"%LOG%" 2>&1
    if not exist "%NODE_INSTALLER%" (
        echo [ERROR] Node.js download failed. See "%LOG%"
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )
    msiexec /i "%NODE_INSTALLER%" /quiet /norestart >>"%LOG%" 2>&1
    timeout /t 25 /nobreak >nul
    call :RefreshEnv
    del "%NODE_INSTALLER%" >nul 2>&1
    where node >nul 2>nul || (echo [ERROR] Node.js installation failed & echo. & echo Press any key to exit... & pause >nul & exit /b 1)
    echo [OK] Node.js installed successfully
) else (
    echo [OK] Node.js already installed
)
echo.

:: ===== ffmpeg =====
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo [INSTALL] Downloading and installing ffmpeg...
    set "FFMPEG_DIR=C:\ffmpeg"
    if not exist "%FFMPEG_DIR%" mkdir "%FFMPEG_DIR%"
    set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    set "FFMPEG_ZIP=%TEMP%\ffmpeg.zip"

    echo [INFO] This may take a few minutes (downloading ~100MB)...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest '%FFMPEG_URL%' -OutFile '%FFMPEG_ZIP%'" >>"%LOG%" 2>&1
    if not exist "%FFMPEG_ZIP%" (
        echo [ERROR] ffmpeg download failed. See "%LOG%"
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )

    echo [INFO] Extracting ffmpeg...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%FFMPEG_ZIP%' -DestinationPath '%FFMPEG_DIR%' -Force" >>"%LOG%" 2>&1

    for /d %%i in ("%FFMPEG_DIR%\ffmpeg-*") do set "FFMPEG_BIN=%%i\bin"
    if not exist "!FFMPEG_BIN!\ffmpeg.exe" (
        echo [ERROR] ffmpeg extraction failed. See "%LOG%"
        echo.
        echo Press any key to exit...
        pause >nul
        exit /b 1
    )

    echo [INFO] Adding ffmpeg to system PATH...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$p=[Environment]::GetEnvironmentVariable('Path','Machine'); $paths=$p.Split(';'); if($paths -notcontains '!FFMPEG_BIN!'){[Environment]::SetEnvironmentVariable('Path',($p+';!FFMPEG_BIN!'),'Machine')}" >>"%LOG%" 2>&1

    call :RefreshEnv
    where ffmpeg >nul 2>nul || (echo [WARNING] PATH not updated, adding to current session & set "PATH=%PATH%;!FFMPEG_BIN!")
    del "%FFMPEG_ZIP%" >nul 2>&1
    echo [OK] ffmpeg installed successfully
) else (
    echo [OK] ffmpeg already installed
)
echo.

:: ===== uv =====
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [INSTALL] Installing uv package manager...
    python -m pip install --upgrade pip >>"%LOG%" 2>&1
    python -m pip install uv >>"%LOG%" 2>&1
    call :RefreshEnv
    where uv >nul 2>nul || (echo [ERROR] uv installation failed. See "%LOG%" & echo. & echo Press any key to exit... & pause >nul & exit /b 1)
    echo [OK] uv installed successfully
) else (
    echo [OK] uv already installed
)
echo.

:: ===== Initialize project environment =====
echo [SETUP] Initializing project environment...
echo.

if not exist "backend\.venv" (
    echo [INFO] First run: Creating backend virtual environment
    pushd backend
    python -m uv venv >>"%LOG%" 2>&1 || (echo [ERROR] uv venv failed. See "%LOG%" & popd & echo. & echo Press any key to exit... & pause >nul & exit /b 1)
    echo [OK] Backend virtual environment created

    echo [INFO] Installing backend dependencies...
    python -m uv sync >>"%LOG%" 2>&1 || (echo [ERROR] uv sync failed. See "%LOG%" & popd & echo. & echo Press any key to exit... & pause >nul & exit /b 1)
    popd
    echo [OK] Backend dependencies installed
) else (
    echo [OK] Backend environment exists
)

if not exist "frontend\node_modules" (
    echo [INFO] First run: Installing frontend dependencies
    echo [INFO] This may take a few minutes...
    pushd frontend
    call npm install >>"%LOG%" 2>&1 || (echo [ERROR] npm install failed. See "%LOG%" & popd & echo. & echo Press any key to exit... & pause >nul & exit /b 1)
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
echo Starting services...
echo.

:: Start services (backend hidden, frontend visible)
echo ====================================
echo   Starting Backend and Frontend
echo ====================================
echo.

:: 1) Backend: Start in hidden window
echo [INFO] Starting backend server (port 8000)...
for /f %%i in ('powershell.exe -NoProfile -Command "Start-Process -FilePath cmd.exe -ArgumentList '/c','cd /d \"%~dp0backend\" && python -m uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000 >> \"%LOG%\" 2>&1' -WindowStyle Hidden -PassThru | Select-Object -ExpandProperty Id"') do set "BACKEND_PID=%%i"

if not defined BACKEND_PID (
  echo [ERROR] Backend failed to start. See "%LOG%"
  echo.
  echo Press any key to exit...
  pause >nul
  exit /b 1
)
echo [OK] Backend started (PID: %BACKEND_PID%)

:: Wait for backend to initialize
echo [INFO] Waiting for backend to initialize...
timeout /t 3 /nobreak >nul

:: 2) Frontend: Start in visible window
echo [INFO] Starting frontend server (port 3000)...
for /f %%i in ('powershell.exe -NoProfile -Command "Start-Process -FilePath cmd.exe -ArgumentList '/k','cd /d \"%~dp0frontend\" && npm start' -PassThru | Select-Object -ExpandProperty Id"') do set "FRONTEND_PID=%%i"

if not defined FRONTEND_PID (
  echo [ERROR] Frontend failed to start
  powershell.exe -NoProfile -Command "if($env:BACKEND_PID){Stop-Process -Id $env:BACKEND_PID -ErrorAction SilentlyContinue}"
  echo.
  echo Press any key to exit...
  pause >nul
  exit /b 1
)
echo [OK] Frontend started (PID: %FRONTEND_PID%)

:: 3) Open browser
echo [INFO] Opening browser...
start "" "http://127.0.0.1:3000"

echo.
echo ====================================
echo   Services Started Successfully!
echo ====================================
echo.
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Log file: %LOG%
echo.
echo ====================================
echo   CONTROL PANEL
echo ====================================
echo.
echo [INFO] Services are now running.
echo [INFO] Press Ctrl+C or close this window to stop all services.
echo.

:: Monitor processes and wait for user to close window
:MonitorLoop
timeout /t 5 /nobreak >nul

:: Check if backend is still running
tasklist /FI "PID eq %BACKEND_PID%" 2>nul | find /I /N "cmd.exe">nul
if %errorlevel% neq 0 (
    echo [WARNING] Backend process stopped unexpectedly
    goto Cleanup
)

:: Check if frontend is still running
tasklist /FI "PID eq %FRONTEND_PID%" 2>nul | find /I /N "cmd.exe">nul
if %errorlevel% neq 0 (
    echo [WARNING] Frontend process stopped unexpectedly
    goto Cleanup
)

goto MonitorLoop

:Cleanup
echo.
echo [INFO] Stopping all services...
powershell.exe -NoProfile -Command "Stop-Process -Id %BACKEND_PID% -ErrorAction SilentlyContinue" >nul 2>&1
powershell.exe -NoProfile -Command "Stop-Process -Id %FRONTEND_PID% -ErrorAction SilentlyContinue" >nul 2>&1
echo [OK] All services stopped
echo.
echo Press any key to exit...
pause >nul
exit /b 0

:RefreshEnv
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYS_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%b"
set "PATH=%SYS_PATH%;%USER_PATH%"
goto :eof
