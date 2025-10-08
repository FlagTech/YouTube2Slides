# YouTube2Slides

> 將 YouTube 影片轉換為靜態閱讀版本（投影片）的 Web 應用程式。

- 一鍵輸入 YouTube 連結，下載影片與字幕（手動或自動產生）。
- 智慧斷句與字幕最佳化（支援中/日/韓等 CJK 字元）。
- 擷取關鍵畫面，生成「逐頁幻燈片」觀看流程。
- 可選擇翻譯與 AI 產生影片大綱（支援 OpenAI / Claude / Gemini / 本機 Ollama）。

## 功能特色

- ✅ 將 YouTube 影片轉換為好閱讀的投影片

![screen_1](./images/1.png)

- ✅ 一鍵下載各種檔案

![screen_2](./images/2.png)

- ✅ AI 產生影片大綱

![screen_3](./images/3.png)

- ✅ 輸入 YouTube 連結 → 自動處理

![screen_4](./images/4.png)

- ✅ 支援多國語言翻譯及截圖設定

![screen_5](./images/5.png)

- ✅ 可選擇使用本機 Ollama 模型或 OpenAI、Gemini、Calude 等 API 

![screen_6](./images/6.png)

## 快速啟動說明

### Windows 用戶

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
   1. 以系統管理員身份執行「PowerShell」，並一次貼上整段以下指令：
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; `
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; `
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```
   2. 驗證安裝是否成功
   ```powershell
   choco -v
   ```
   3. 自動下載 ffmpeg、解壓縮、配置 PATH
   ```powershell
   choco install ffmpeg
   ```
   4. 重新開啟命令提示字元，輸入 `ffmpeg -version` 驗證安裝成功
   5. 注意！安裝完後請重新開機

   **方法 2：手動安裝**
   1. 下載：https://www.gyan.dev/ffmpeg/builds/
   2. 選擇「ffmpeg-release-essentials.zip」
   3. 解壓縮到任意位置（例如：`C:\ffmpeg`）
   4. 將 `bin` 資料夾路徑加入系統環境變數 PATH
     - 點擊「開始」→「設定」
     - 進入「系統」→「系統資訊」→「進階系統設定」
     - 點擊「環境變數」
     - 在「系統變數」中找到「Path」，點擊「編輯」
     - 點擊「新增」，輸入 ffmpeg 的 bin 路徑（例如：`C:\ffmpeg\bin`）
     - 點擊「確定」儲存
   5. 重新開啟命令提示字元，輸入 `ffmpeg -version` 驗證安裝成功
   6. 注意！安裝完後請重新開機

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
- 首次執行會需要較長時間下載依賴套件
- 應用程式會在 cmd 視窗中運行，關閉即可停止服務

### macOS / Linux
- 以終端機進入專案根目錄後執行：
```bash
python3 setup_and_start.py
```

## 使用方式

1. **開啟應用程式**
   - 瀏覽器訪問 `http://localhost:3000`

2. **輸入 YouTube URL**
   - 貼上 YouTube 影片連結
   - 選擇影片畫質（360p/480p/720p）

3. **設定選項**
   - （可選）選擇翻譯目標語言
   - 調整截圖間隔時間（秒）
   - 選擇是否生成 AI 大綱 & 翻譯

4. **處理影片**
   - 點擊「處理影片」
   - 等待處理完成（會顯示進度條）

5. **瀏覽投影片**
   - 使用左右箭頭鍵或按鈕導航
   - 點擊縮圖快速跳轉

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
- 使用 OpenAI Whisper 模型辨識音頻 (需申請 API Key)

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
