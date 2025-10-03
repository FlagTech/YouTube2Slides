@echo off
chcp 65001 >nul
echo ====================================
echo   YouTube 影片懶人觀看術
echo ====================================
echo.
echo 正在啟動後端服務器...
echo.

:: 檢查是否已安裝 uv
where uv >nul 2>nul
if %errorlevel% neq 0 (
    echo [錯誤] 找不到 uv，請先安裝 uv
    echo 安裝方式: pip install uv
    pause
    exit /b 1
)

:: 檢查是否已安裝 Node.js
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [錯誤] 找不到 Node.js，請先安裝 Node.js
    echo 下載地址: https://nodejs.org/
    pause
    exit /b 1
)

:: 檢查後端虛擬環境
if not exist "backend\.venv" (
    echo [提示] 首次運行，正在初始化後端環境...
    cd backend
    uv venv
    cd ..
)

:: 檢查前端依賴
if not exist "frontend\node_modules" (
    echo [提示] 首次運行，正在安裝前端依賴...
    cd frontend
    call npm install
    cd ..
)

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
