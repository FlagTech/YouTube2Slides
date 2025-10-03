# YouTube 影片懶人觀看術 - 啟動指南

本專案提供多種啟動方式，可以一次啟動前後端服務。

## 🚀 一鍵安裝與啟動（最簡單，推薦新手）

這個方式會自動檢查並安裝所有需要的工具（Node.js、ffmpeg、uv），完全不需要手動安裝任何東西！

### Windows 用戶

**方法 1: 使用自動安裝批次檔（推薦）**
```batch
setup_and_start.bat
```
雙擊 `setup_and_start.bat`，腳本會：
- 自動檢查是否已安裝 Python、Node.js、ffmpeg、uv
- 若缺少任何工具，會自動下載並安裝
- 初始化專案環境
- 啟動前後端服務

**方法 2: 使用 Python 自動安裝腳本**
```bash
python setup_and_start.py
```

### Linux/macOS 用戶

```bash
python3 setup_and_start.py
```

腳本會引導您使用套件管理器（Homebrew 或 apt）安裝缺少的工具。

---

## 快速啟動（已安裝所有依賴）

### Windows 用戶

**方法 1: 使用批次檔 (推薦)**
```batch
start.bat
```
雙擊 `start.bat` 或在命令提示字元中執行，會自動在新視窗開啟前後端服務。

**方法 2: 使用 Python 腳本**
```bash
python start.py
```

### Linux/macOS 用戶

**方法 1: 使用 Shell 腳本**
```bash
chmod +x start.sh  # 首次執行需要添加執行權限
./start.sh
```

**方法 2: 使用 Python 腳本**
```bash
python3 start.py
```

## 系統需求

### 必要依賴
- **Python 3.8+**
- **Node.js 14+**
- **uv** - Python 環境管理工具
  ```bash
  pip install uv
  ```

### 首次運行
啟動腳本會自動檢查並安裝必要的依賴：
- 後端：自動創建虛擬環境 (backend/.venv)
- 前端：自動安裝 npm 依賴 (frontend/node_modules)

## 服務地址

啟動成功後，可以訪問：
- **前端界面**: http://localhost:3000
- **後端 API**: http://localhost:8000
- **API 文檔**: http://localhost:8000/docs

## 停止服務

### Windows (使用 start.bat)
- 關閉啟動的命令提示字元視窗

### Linux/macOS (使用 start.sh)
- 在終端機按 `Ctrl+C`

### Python 腳本 (start.py)
- Windows: 按任意鍵或關閉視窗
- Linux/macOS: 按 `Ctrl+C`

## 手動啟動 (進階用戶)

如果您需要分別控制前後端：

### 啟動後端
```bash
cd backend
uv run uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### 啟動前端
```bash
cd frontend
npm start
```

## 疑難排解

### 問題 1: 找不到 uv 命令
```bash
pip install uv
# 或
pip3 install uv
```

### 問題 2: 找不到 Node.js
請至 https://nodejs.org/ 下載並安裝最新的 LTS 版本

### 問題 3: 端口被占用
如果 3000 或 8000 端口被占用：

**Windows:**
```bash
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

**Linux/macOS:**
```bash
lsof -i :3000
kill -9 <PID>
```

### 問題 4: 權限錯誤 (Linux/macOS)
```bash
chmod +x start.sh
```

## 日誌文件

使用 `start.sh` 時，日誌會保存在：
- `backend.log` - 後端日誌
- `frontend.log` - 前端日誌

## 環境變數設定

在運行前，您可能需要設定以下環境變數 (在 `backend/.env` 檔案中)：

```env
# AI 服務 API 金鑰 (可選)
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_claude_key
GEMINI_API_KEY=your_gemini_key

# Ollama 設定 (可選)
OLLAMA_BASE_URL=http://localhost:11434
```

詳細的環境變數設定請參考主要的 README.md 文件。
