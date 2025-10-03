@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul

:: 1) 鎖定工作目錄為腳本所在路徑
cd /d "%~dp0"

:: 2) 設定 log
set "LOG=%TEMP%\yt2slides_setup.log"
echo [%date% %time%] Start setup > "%LOG%"

echo ====================================
echo   YouTube 影片懶人觀看術
echo   自動安裝與啟動
echo ====================================
echo.

:: 3) 檢查是否以管理員權限運行（若否，帶參數提升、並等候）
whoami /groups | findstr /C:"S-1-16-12288" >nul 2>&1
if %errorlevel% neq 0 (
    echo [錯誤] 此批次檔需要系統管理員權限，正在嘗試重新啟動...
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process '%~f0' -Verb RunAs -WorkingDirectory '%CD%' -WindowStyle Normal"
    if !errorlevel! neq 0 (
        echo [取消] 尚未取得系統管理員權限，請手動以管理員身分執行。
        pause
    )
    exit /b
)

echo [檢查] 正在檢查系統環境...
echo.

:: ===== Python =====
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [安裝] 下載並安裝 Python 3.11.9...
    set "PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    set "PYTHON_INSTALLER=%TEMP%\python_installer.exe"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'" >>"%LOG%" 2>&1
    if not exist "%PYTHON_INSTALLER%" (
        echo [錯誤] Python 下載失敗，詳見 "%LOG%"
        pause & exit /b 1
    )
    "%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0 >>"%LOG%" 2>&1
    timeout /t 25 /nobreak >nul
    call :RefreshEnv
    del "%PYTHON_INSTALLER%" >nul 2>&1
    where python >nul 2>nul || (echo [錯誤] Python 未安裝成功 & pause & exit /b 1)
) else (
    echo ✓ Python 已安裝
)
echo.

:: ===== Node.js =====
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [安裝] 下載並安裝 Node.js 20.11.1 LTS...
    set "NODE_URL=https://nodejs.org/dist/v20.11.1/node-v20.11.1-x64.msi"
    set "NODE_INSTALLER=%TEMP%\node_installer.msi"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest '%NODE_URL%' -OutFile '%NODE_INSTALLER%'" >>"%LOG%" 2>&1
    if not exist "%NODE_INSTALLER%" (
        echo [錯誤] Node.js 下載失敗，詳見 "%LOG%"
        pause & exit /b 1
    )
    msiexec /i "%NODE_INSTALLER%" /quiet /norestart >>"%LOG%" 2>&1
    timeout /t 25 /nobreak >nul
    call :RefreshEnv
    del "%NODE_INSTALLER%" >nul 2>&1
    where node >nul 2>nul || (echo [錯誤] Node.js 未安裝成功 & pause & exit /b 1)
) else (
    echo ✓ Node.js 已安裝
)
echo.

:: ===== ffmpeg =====
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo [安裝] 下載並安裝 ffmpeg...
    set "FFMPEG_DIR=C:\ffmpeg"
    if not exist "%FFMPEG_DIR%" mkdir "%FFMPEG_DIR%"
    set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    set "FFMPEG_ZIP=%TEMP%\ffmpeg.zip"
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest '%FFMPEG_URL%' -OutFile '%FFMPEG_ZIP%'" >>"%LOG%" 2>&1
    if not exist "%FFMPEG_ZIP%" (
        echo [錯誤] ffmpeg 下載失敗，詳見 "%LOG%"
        pause & exit /b 1
    )
    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Path '%FFMPEG_ZIP%' -DestinationPath '%FFMPEG_DIR%' -Force" >>"%LOG%" 2>&1

    for /d %%i in ("%FFMPEG_DIR%\ffmpeg-*") do set "FFMPEG_BIN=%%i\bin"
    if not exist "!FFMPEG_BIN!\ffmpeg.exe" (
        echo [錯誤] ffmpeg 解壓後找不到 bin，詳見 "%LOG%"
        pause & exit /b 1
    )

    powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$p=[Environment]::GetEnvironmentVariable('Path','Machine'); if(!$p.Split(';') -contains '%FFMPEG_BIN%'){[Environment]::SetEnvironmentVariable('Path',$p+';%FFMPEG_BIN%','Machine')}" >>"%LOG%" 2>&1

    call :RefreshEnv
    where ffmpeg >nul 2>nul || (echo [警告] PATH 未更新成功，將在本次行程中臨時加入 & set "PATH=%PATH%;%FFMPEG_BIN%")
    del "%FFMPEG_ZIP%" >nul 2>&1
    echo ✓ ffmpeg 安裝完成
) else (
    echo ✓ ffmpeg 已安裝
)
echo.

:: ===== uv =====
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [安裝] 安裝 uv...
    python -m pip install --upgrade pip >>"%LOG%" 2>&1
    python -m pip install uv >>"%LOG%" 2>&1
    call :RefreshEnv
    where uv >nul 2>nul || (echo [錯誤] uv 安裝失敗，詳見 "%LOG%" & pause & exit /b 1)
) else (
    echo ✓ uv 已安裝
)
echo.

:: ===== 初始化專案環境 =====
echo [設定] 正在初始化專案環境...
echo.

if not exist "backend\.venv" (
    echo [提示] 首次運行：建立後端虛擬環境
    pushd backend
    python -m uv venv >>"%LOG%" 2>&1 || (echo [錯誤] uv venv 失敗，詳見 "%LOG%" & popd & pause & exit /b 1)
    echo ✓ 後端虛擬環境創建完成

    echo [提示] 正在安裝後端依賴套件...
    python -m uv sync >>"%LOG%" 2>&1 || (echo [錯誤] uv sync 失敗，詳見 "%LOG%" & popd & pause & exit /b 1)
    popd
    echo ✓ 後端依賴安裝完成
) else (
    echo ✓ 後端環境已存在
)

if not exist "frontend\node_modules" (
    echo [提示] 首次運行：安裝前端依賴
    pushd frontend
    call npm install >>"%LOG%" 2>&1 || (echo [錯誤] npm install 失敗，詳見 "%LOG%" & popd & pause & exit /b 1)
    popd
    echo ✓ 前端依賴安裝完成
) else (
    echo ✓ 前端依賴已存在
)

echo.
echo ====================================
echo   所有依賴已就緒！
echo ====================================
echo.
echo 正在啟動服務...
echo.

:: 啟動服務（隱藏監控器，只顯示前端視窗）
echo.
echo ====================================
echo   正在啟動服務（監控器隱藏）
echo ====================================
echo.

:: 1) 後端：隱藏視窗啟動 uvicorn（使用 python -m uv，避免 PATH 問題）
for /f %%i in ('powershell.exe -NoProfile -Command "Start-Process -FilePath cmd.exe -ArgumentList '/c','cd /d \"%~dp0backend\" && python -m uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000 >> \"%LOG%\" 2>&1' -WindowStyle Hidden -PassThru | Select-Object -ExpandProperty Id"') do set "BACKEND_PID=%%i"

if not defined BACKEND_PID (
  echo [錯誤] 後端啟動失敗，詳見 "%LOG%"
  pause
  exit /b 1
)

:: 2) 前端：一般視窗啟動（可見）
for /f %%i in ('powershell.exe -NoProfile -Command "Start-Process -FilePath cmd.exe -ArgumentList '/k','cd /d \"%~dp0frontend\" && npm start' -PassThru | Select-Object -ExpandProperty Id"') do set "FRONTEND_PID=%%i"

if not defined FRONTEND_PID (
  echo [錯誤] 前端啟動失敗
  powershell.exe -NoProfile -Command "if($env:BACKEND_PID){Stop-Process -Id $env:BACKEND_PID -ErrorAction SilentlyContinue}"
  pause
  exit /b 1
)

:: 3) 啟動隱藏監控器（獨立行程）：等前端關閉後自動關後端
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$f=%FRONTEND_PID%; $b=%BACKEND_PID%; Start-Process powershell -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-Command',\"try{Wait-Process -Id $f}catch{}; try{Stop-Process -Id $b -ErrorAction SilentlyContinue}catch{}\")"  >nul 2>&1

:: 4) 幫你打開前端頁
start "" "http://127.0.0.1:3000"
exit /b 0

:RefreshEnv
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYS_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%b"
set "PATH=%SYS_PATH%;%USER_PATH%"
goto :eof
