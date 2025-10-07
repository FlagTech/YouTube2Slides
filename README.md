# YouTube to Readable Slides

將 YouTube 影片轉換為靜態閱讀版本（投影片）的 Web 應用程式。

## 功能特色

### 核心功能
- ✅ **YouTube 影片處理**
  - 支援多種 YouTube URL 格式
  - 下載影片並提取資訊（標題、時長、頻道、縮圖等）
  - 可調整影片畫質（360p/480p/720p）

- ✅ **字幕處理**
  - 支援多語言字幕（繁體中文、簡體中文、英文、日文、韓文等）
  - 自動翻譯功能
  - 時間軸同步處理
  - SRT 格式解析與匯出

- ✅ **投影片生成**
  - 根據字幕變換自動截取關鍵幀
  - 可調整截圖間隔時間
  - 圖片壓縮與最佳化
  - 批次處理多個幀

- ✅ **互動式瀏覽**
  - 投影片檢視器
  - 鍵盤導航支援（方向鍵）
  - 縮圖預覽列表
  - 即時字幕顯示

## 技術架構

### 後端
- **框架**: FastAPI (Python)
- **影片處理**: yt-dlp, ffmpeg-python
- **字幕處理**: 自訂 SRT 解析器
- **翻譯**: deep-translator (Google Translate)
- **圖片處理**: Pillow
- **非同步任務**: Background Tasks

### 前端
- **框架**: React 18
- **HTTP 客戶端**: Axios
- **樣式**: CSS3 (漸層、動畫、響應式設計)

## 快速啟動

### 🚀 一鍵自動安裝與啟動（推薦新手）

#### Windows 用戶

**前置準備（必須）：**

1. **安裝 Python 3.9+**
   - 下載：https://www.python.org/downloads/
   - 安裝時請勾選「Add Python to PATH」

2. **安裝 Node.js 16+**
   - 下載：https://nodejs.org/
   - 建議下載 LTS（長期支援）版本

3. **安裝 ffmpeg（必須）**

   ffmpeg 是影片處理的核心工具，必須安裝才能正常使用本程式。

   **方法 1：使用 Chocolatey（推薦）**
   ```bash
   # 先安裝 Chocolatey（以管理員身份執行 PowerShell）
   # 安裝指令請參考：https://chocolatey.org/install

   # 安裝 ffmpeg
   choco install ffmpeg
   ```

   **方法 2：手動安裝**
   - 下載：https://www.gyan.dev/ffmpeg/builds/
   - 選擇「ffmpeg-release-essentials.zip」
   - 解壓縮到任意位置（例如：`C:\ffmpeg`）
   - 將 `bin` 資料夾路徑加入系統環境變數 PATH
     1. 右鍵點擊「本機」→「內容」
     2. 點擊「進階系統設定」
     3. 點擊「環境變數」
     4. 在「系統變數」中找到「Path」，點擊「編輯」
     5. 點擊「新增」，輸入 ffmpeg 的 bin 路徑（例如：`C:\ffmpeg\bin`）
     6. 點擊「確定」儲存
   - 重新開啟命令提示字元，輸入 `ffmpeg -version` 驗證安裝成功

**啟動步驟：**

1️⃣ 下載專案並解壓縮

2️⃣ 進入 `YouTube2Slides` 資料夾

3️⃣ 雙擊執行 **`setup_and_start.bat`**

腳本會自動：
- ✅ 檢查 Python、Node.js、ffmpeg 是否已安裝
- ✅ 自動安裝 uv 套件管理工具
- ✅ 建立 Python 虛擬環境
- ✅ 安裝所有後端依賴
- ✅ 安裝所有前端依賴
- ✅ 啟動後端服務器（port 8000）
- ✅ 啟動前端服務器（port 3000）
- ✅ 自動開啟瀏覽器

**注意事項：**
- 如果缺少 Python、Node.js 或 ffmpeg，腳本會顯示錯誤訊息並提供下載連結
- 首次執行會需要較長時間下載依賴（約 5-10 分鐘）
- 服務會在獨立視窗中運行，關閉視窗即可停止服務

#### macOS 用戶

1️⃣ 開啟終端機（Terminal）

2️⃣ 進入專案資料夾：
```bash
cd ~/Downloads/YouTube2Slides
```

3️⃣ 執行自動安裝腳本：
```bash
python3 setup_and_start.py
```

**注意事項：**
- 腳本會自動檢測是否已安裝 Homebrew
- 如果未安裝，會提示安裝指令
- 缺少的套件會透過 Homebrew 自動安裝
- 服務啟動後會在終端機中顯示輸出，按 Ctrl+C 停止

#### Linux 用戶

```bash
python3 setup_and_start.py
```

腳本會提示使用 apt 安裝依賴（適用於 Ubuntu/Debian）

### 一鍵啟動（已安裝依賴的用戶）

**Windows 用戶:**
```bash
# 方法 1: 雙擊批次檔
start.bat

# 方法 2: 使用 Python 腳本
python start.py
```

**Linux/macOS 用戶:**
```bash
# 方法 1: 使用 Shell 腳本
chmod +x start.sh  # 首次執行需要
./start.sh

# 方法 2: 使用 Python 腳本
python3 start.py
```

啟動腳本會自動：
- 檢查系統依賴
- 初始化虛擬環境（首次運行）
- 安裝前端依賴（首次運行）
- 同時啟動前端和後端服務

服務啟動後可訪問：
- **前端**: http://localhost:3000
- **後端**: http://localhost:8000
- **API 文檔**: http://localhost:8000/docs

詳細啟動說明請參考 [README_STARTUP.md](README_STARTUP.md)

---

## 手動安裝與設定

### 前置需求
- Python 3.9+
- Node.js 16+
- ffmpeg（**必須**，用於影片處理）
- uv (Python 套件管理工具) - 會自動安裝

### 安裝 ffmpeg（必須）

ffmpeg 是影片處理的核心工具，必須安裝。

**Windows:**
```bash
# 方法 1: 使用 Chocolatey（推薦）
choco install ffmpeg

# 方法 2: 手動下載安裝
# 1. 下載：https://www.gyan.dev/ffmpeg/builds/
# 2. 解壓縮到 C:\ffmpeg
# 3. 將 C:\ffmpeg\bin 加入系統 PATH
```

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install ffmpeg
```

**驗證安裝：**
```bash
ffmpeg -version
```
如果顯示版本資訊，表示安裝成功。

### 安裝 uv

**Windows/macOS/Linux:**
```bash
# 使用官方安裝腳本
curl -LsSf https://astral.sh/uv/install.sh | sh

# 或使用 pip
pip install uv
```

### 後端安裝

1. 進入後端目錄並同步依賴：
```bash
cd backend
uv sync
```

2. 啟動後端伺服器：
```bash
uv run python app.py
```

後端將在 `http://localhost:8000` 啟動

### 前端安裝

1. 進入前端目錄並安裝依賴：
```bash
cd frontend
npm install
```

2. 啟動開發伺服器：
```bash
npm start
```

前端將在 `http://localhost:3000` 啟動

## 使用方式

1. **開啟應用程式**
   - 瀏覽器訪問 `http://localhost:3000`

2. **輸入 YouTube URL**
   - 貼上 YouTube 影片連結
   - 選擇影片畫質（360p/480p/720p）

3. **設定字幕選項**
   - 選擇要下載的字幕語言
   - （可選）選擇翻譯目標語言
   - 調整截圖間隔時間（秒）

4. **處理影片**
   - 點擊「Process Video」開始處理
   - 等待處理完成（會顯示進度條）

5. **瀏覽投影片**
   - 使用左右箭頭鍵或按鈕導航
   - 點擊縮圖快速跳轉
   - 閱讀每張投影片的字幕

## API 端點

### 影片資訊
```http
POST /api/video/info
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID"
}
```

### 處理影片
```http
POST /api/video/process
Content-Type: application/json

{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "quality": "720",
  "subtitle_languages": ["zh-TW", "en"],
  "translate_to": "zh-TW",
  "frame_threshold": 2.0
}
```

### 查詢任務狀態
```http
GET /api/jobs/{job_id}
```

### 翻譯文字
```http
POST /api/translate
Content-Type: application/json

{
  "text": "Hello world",
  "source_lang": "en",
  "target_lang": "zh-TW"
}
```

### 獲取支援語言
```http
GET /api/languages
```

## 專案結構

```
VIDEO_TO_READABLE/
├── backend/
│   ├── app.py                 # FastAPI 主應用
│   ├── requirements.txt       # Python 依賴
│   ├── services/
│   │   ├── youtube.py         # YouTube 下載服務
│   │   ├── subtitle.py        # 字幕處理服務
│   │   ├── frame_extractor.py # 影格提取服務
│   │   └── translator.py      # 翻譯服務
│   ├── models/
│   │   └── schemas.py         # Pydantic 資料模型
│   └── utils/                 # 工具函數
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.js             # 主應用組件
│   │   ├── components/        # React 組件
│   │   │   ├── VideoInput.js  # 影片輸入表單
│   │   │   ├── ProcessingStatus.js  # 處理狀態
│   │   │   └── SlideViewer.js # 投影片檢視器
│   │   └── api/
│   │       └── api.js         # API 客戶端
│   └── package.json
├── storage/                   # 儲存目錄
│   ├── videos/                # 下載的影片
│   ├── frames/                # 擷取的影格
│   └── subtitles/             # 字幕檔案
└── README.md
```

## 環境變數

### 前端 (.env)
```env
REACT_APP_API_URL=http://localhost:8000
```

### 後端
無需額外環境變數設定（使用預設值）

## 效能最佳化

1. **影片畫質選擇**
   - 720p: 高畫質，檔案較大，處理時間較長
   - 480p: 平衡畫質與效能（推薦）
   - 360p: 快速處理，檔案較小

2. **截圖間隔**
   - 2 秒: 預設值，適合大多數影片
   - 3-5 秒: 減少投影片數量，加快處理
   - 1 秒: 更詳細的投影片，處理時間較長

3. **圖片壓縮**
   - 自動壓縮為 JPEG 格式
   - 預設品質: 85%
   - 自動調整尺寸至 1280px 寬度

## 疑難排解

### ffmpeg 未找到
```
Error: ffmpeg not found
```
**解決方案**:
1. 安裝 ffmpeg（參考上方安裝說明）
2. 確保 ffmpeg 已加入系統 PATH
3. 重新開啟命令提示字元或重啟電腦
4. 執行 `ffmpeg -version` 驗證安裝成功

### 字幕不可用
```
Error: No subtitles available
```
**解決方案**:
- 確認影片有字幕
- 嘗試不同的語言選項
- 檢查是否有自動生成字幕

### CORS 錯誤
```
Access to fetch has been blocked by CORS policy
```
**解決方案**: 確認後端 CORS 設定正確，或在生產環境中設定具體的 origin

## 未來改進

- [ ] OCR 文字辨識（從投影片提取額外文字）
- [ ] AI 自動摘要（整合 OpenAI/Claude API）
- [ ] 場景變化偵測（更智能的截圖時機）
- [ ] 匯出 PDF/PPT 格式
- [ ] 批次處理多個影片
- [ ] 使用者帳號系統與分享功能
- [ ] Redis 快取與 Celery 任務佇列
- [ ] Docker 容器化部署

## 授權

MIT License

## 貢獻

歡迎提交 Issue 和 Pull Request！

## 聯絡

如有問題或建議，請開啟 GitHub Issue。
