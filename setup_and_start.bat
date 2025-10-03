@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo ====================================
echo   YouTube 影片懶人觀看術
echo   自動安裝與啟動
echo ====================================
echo.

:: 檢查是否以管理員權限運行
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [提示] 正在請求管理員權限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo [檢查] 正在檢查系統環境...
echo.

:: ========================================
:: 檢查並安裝 Python
:: ========================================
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [安裝] 找不到 Python，正在下載並安裝...
    echo.

    :: 下載 Python 安裝器
    set "PYTHON_URL=https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    set "PYTHON_INSTALLER=%TEMP%\python_installer.exe"

    echo 下載 Python 3.11.9...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%PYTHON_URL%' -OutFile '%PYTHON_INSTALLER%'}"

    if exist "%PYTHON_INSTALLER%" (
        echo 正在安裝 Python（這可能需要幾分鐘）...
        "%PYTHON_INSTALLER%" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

        :: 等待安裝完成
        timeout /t 30 /nobreak >nul

        :: 刷新環境變數
        call :RefreshEnv

        echo ✓ Python 安裝完成
        del "%PYTHON_INSTALLER%"
    ) else (
        echo [錯誤] Python 下載失敗
        pause
        exit /b 1
    )
) else (
    echo ✓ Python 已安裝
)
echo.

:: ========================================
:: 檢查並安裝 Node.js
:: ========================================
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [安裝] 找不到 Node.js，正在下載並安裝...
    echo.

    :: 下載 Node.js 安裝器
    set "NODE_URL=https://nodejs.org/dist/v20.11.1/node-v20.11.1-x64.msi"
    set "NODE_INSTALLER=%TEMP%\node_installer.msi"

    echo 下載 Node.js 20.11.1 LTS...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%NODE_URL%' -OutFile '%NODE_INSTALLER%'}"

    if exist "%NODE_INSTALLER%" (
        echo 正在安裝 Node.js（這可能需要幾分鐘）...
        msiexec /i "%NODE_INSTALLER%" /quiet /norestart

        :: 等待安裝完成
        timeout /t 30 /nobreak >nul

        :: 刷新環境變數
        call :RefreshEnv

        echo ✓ Node.js 安裝完成
        del "%NODE_INSTALLER%"
    ) else (
        echo [錯誤] Node.js 下載失敗
        pause
        exit /b 1
    )
) else (
    echo ✓ Node.js 已安裝
)
echo.

:: ========================================
:: 檢查並安裝 ffmpeg
:: ========================================
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo [安裝] 找不到 ffmpeg，正在下載並安裝...
    echo.

    :: 創建 ffmpeg 目錄
    set "FFMPEG_DIR=C:\ffmpeg"
    if not exist "%FFMPEG_DIR%" mkdir "%FFMPEG_DIR%"

    :: 下載 ffmpeg
    set "FFMPEG_URL=https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    set "FFMPEG_ZIP=%TEMP%\ffmpeg.zip"

    echo 下載 ffmpeg...
    powershell -Command "& {[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri '%FFMPEG_URL%' -OutFile '%FFMPEG_ZIP%'}"

    if exist "%FFMPEG_ZIP%" (
        echo 正在解壓縮 ffmpeg...
        powershell -Command "Expand-Archive -Path '%FFMPEG_ZIP%' -DestinationPath '%FFMPEG_DIR%' -Force"

        :: 找到 bin 目錄並加入 PATH
        for /d %%i in ("%FFMPEG_DIR%\ffmpeg-*") do (
            set "FFMPEG_BIN=%%i\bin"
        )

        :: 永久加入系統 PATH
        echo 正在設定環境變數...
        setx /M PATH "%PATH%;!FFMPEG_BIN!" >nul 2>&1

        :: 刷新環境變數
        call :RefreshEnv

        echo ✓ ffmpeg 安裝完成
        del "%FFMPEG_ZIP%"
    ) else (
        echo [錯誤] ffmpeg 下載失敗
        pause
        exit /b 1
    )
) else (
    echo ✓ ffmpeg 已安裝
)
echo.

:: ========================================
:: 檢查並安裝 uv
:: ========================================
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [安裝] 找不到 uv，正在安裝...
    echo.

    python -m pip install --upgrade pip
    python -m pip install uv

    if %errorlevel% equ 0 (
        echo ✓ uv 安裝完成
    ) else (
        echo [錯誤] uv 安裝失敗
        pause
        exit /b 1
    )
) else (
    echo ✓ uv 已安裝
)
echo.

:: ========================================
:: 初始化專案環境
:: ========================================
echo [設定] 正在初始化專案環境...
echo.

:: 檢查後端虛擬環境
if not exist "backend\.venv" (
    echo [提示] 首次運行，正在初始化後端環境...
    cd backend
    uv venv
    cd ..
    echo ✓ 後端環境初始化完成
)

:: 檢查前端依賴
if not exist "frontend\node_modules" (
    echo [提示] 首次運行，正在安裝前端依賴...
    cd frontend
    call npm install
    cd ..
    echo ✓ 前端依賴安裝完成
)

echo.
echo ====================================
echo   所有依賴已就緒！
echo ====================================
echo.
echo 正在啟動服務...
echo.

:: 啟動後端 (在新視窗)
echo [啟動] 後端服務器 (Port 8000)
start "後端服務器" cmd /k "cd backend && uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000"

:: 等待後端啟動
timeout /t 3 /nobreak >nul

:: 啟動前端 (在新視窗)
echo [啟動] 前端服務器 (Port 3000)
start "前端服務器" cmd /k "cd frontend && npm start"

echo.
echo ====================================
echo   所有服務已啟動！
echo ====================================
echo.
echo 後端服務: http://localhost:8000
echo 前端服務: http://localhost:3000
echo.
echo 關閉此視窗不會停止服務
echo 若要停止服務，請關閉對應的視窗
echo.
pause
exit /b 0

:: ========================================
:: 刷新環境變數函數
:: ========================================
:RefreshEnv
:: 從註冊表讀取最新的 PATH
for /f "tokens=2*" %%a in ('reg query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v PATH 2^>nul') do set "SYS_PATH=%%b"
for /f "tokens=2*" %%a in ('reg query "HKCU\Environment" /v PATH 2^>nul') do set "USER_PATH=%%b"
set "PATH=%SYS_PATH%;%USER_PATH%"
goto :eof
