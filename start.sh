#!/bin/bash

# YouTube 影片懶人觀看術 - 啟動腳本 (Linux/macOS)

echo "===================================="
echo "  YouTube 影片懶人觀看術"
echo "===================================="
echo ""

# 檢查 uv
if ! command -v uv &> /dev/null; then
    echo "[錯誤] 找不到 uv，請先安裝 uv"
    echo "安裝方式: pip install uv"
    exit 1
fi

# 檢查 Node.js
if ! command -v node &> /dev/null; then
    echo "[錯誤] 找不到 Node.js，請先安裝 Node.js"
    echo "下載地址: https://nodejs.org/"
    exit 1
fi

# 檢查後端虛擬環境
if [ ! -d "backend/.venv" ]; then
    echo "[提示] 首次運行，正在初始化後端環境..."
    cd backend
    uv venv
    cd ..
fi

# 檢查前端依賴
if [ ! -d "frontend/node_modules" ]; then
    echo "[提示] 首次運行，正在安裝前端依賴..."
    cd frontend
    npm install
    cd ..
fi

echo ""
echo "===================================="
echo "  啟動服務中..."
echo "===================================="
echo ""

# 啟動後端 (背景執行)
echo "[啟動] 後端服務器 (Port 8000)"
cd backend
uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000 > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# 等待後端啟動
sleep 3

# 啟動前端 (背景執行)
echo "[啟動] 前端服務器 (Port 3000)"
cd frontend
npm start > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

echo ""
echo "===================================="
echo "  所有服務已啟動！"
echo "===================================="
echo ""
echo "後端服務: http://localhost:8000"
echo "前端服務: http://localhost:3000"
echo ""
echo "後端日誌: backend.log"
echo "前端日誌: frontend.log"
echo ""
echo "按 Ctrl+C 停止所有服務"
echo ""

# 捕捉中斷信號
trap "echo ''; echo '正在停止服務...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; echo '服務已停止'; exit 0" INT TERM

# 等待進程
wait
