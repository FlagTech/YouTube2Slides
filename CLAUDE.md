# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

YouTube2Slides 是一個將 YouTube 影片轉換為靜態可讀投影片的 Web 應用程式。使用者可以輸入 YouTube URL，系統會：
1. 下載影片並提取字幕
2. 根據字幕時間軸自動截取關鍵幀
3. 使用 AI 翻譯字幕（可選）
4. 生成 AI 影片大綱（可選）
5. 在前端瀏覽器中展示投影片與字幕

## Python 環境管理

本專案使用 **uv** 作為 Python 套件管理工具：

- **初始化環境**: `uv init`
- **安裝套件**: `uv add <package-name>`
- **執行 Python 程式**: `uv run python <script.py>`
- **同步依賴**: `cd backend && uv sync`

**IMPORTANT**: 所有 Python 命令都必須使用 `uv run` 前綴執行。

## 啟動服務

### 自動啟動（推薦）
- **Windows**: 雙擊 `setup_and_start.bat`
- **macOS/Linux**: `python3 setup_and_start.py` 或 `./start.sh`

### 手動啟動

**後端** (FastAPI, port 8000):
```bash
cd backend
uv run python app.py
```

**前端** (React, port 3000):
```bash
cd frontend
npm install   # 首次執行
npm start
```

**API 文檔**: http://localhost:8000/docs

## 核心架構

### 後端架構 (FastAPI)

**主要服務** (`backend/services/`):

1. **youtube.py**: 使用 `yt-dlp` 下載 YouTube 影片與字幕
2. **subtitle.py**: SRT 字幕解析、合併、時間軸處理
3. **frame_extractor.py**: 使用 `ffmpeg` 根據字幕時間截取影格
4. **translator.py**: Google Translate 批次翻譯（備用）
5. **ai_translator.py**: AI 翻譯服務（OpenAI/Claude/Gemini/Ollama）
   - 使用動態批次大小優化（根據字幕長度自動調整 10-30 項/批次）
   - 三種解析方法防止翻譯遺漏
   - 詳細日誌記錄
6. **ai_outline.py**: AI 大綱生成服務
7. **audio_transcription.py**: Whisper API 音訊轉字幕（使用 `timestamp_granularities=["segment"]`）
8. **subtitle_optimizer.py**: 字幕斷行與格式優化

**資料模型** (`backend/models/schemas.py`):
- 使用 Pydantic 定義 API request/response schemas
- `ProcessVideoRequest`: 包含 `generate_outline`, `ai_provider`, `translate_to` 等欄位
- `JobStatusResponse`: 包含處理進度、狀態、結果

**主要 API 端點** (`backend/app.py`):
- `POST /api/video/info`: 取得影片資訊
- `POST /api/video/process`: 處理影片（主要端點）
- `GET /api/jobs/{job_id}`: 查詢任務狀態
- `GET /api/video/history`: 取得處理歷史記錄
- `DELETE /api/video/history/{video_id}`: 刪除歷史記錄與檔案
- `GET /api/download/{job_id}`: 下載打包檔案（frames + subtitles）

**重要邏輯**:
- **AI 翻譯觸發條件** (`app.py:456`): 需要 `request.generate_outline and request.ai_provider`
  - 如果勾選「AI 翻譯 & 生成 AI 影片大綱」且選擇 AI 提供商，使用 AI 翻譯
  - 否則使用 Google Translate
- **批次翻譯優化**: `ai_translator.py` 會根據字幕平均長度自動計算最佳批次大小

### 前端架構 (React)

**主要組件** (`frontend/src/components/`):

1. **VideoInput.js**: 影片 URL 輸入表單
   - 包含畫質選擇、字幕語言、翻譯選項
   - AI 設定區塊（提供商、模型、API Key）
   - 勾選框：「AI 翻譯 & 生成 AI 影片大綱」

2. **ProcessingStatus.js**: 處理進度顯示
   - 即時輪詢後端任務狀態
   - 顯示當前步驟與進度條

3. **SlideViewer.js**: 投影片檢視器
   - 左右鍵盤導航
   - 縮圖預覽
   - 字幕同步顯示
   - AI 大綱顯示（如有）

4. **Sidebar.js**: 歷史記錄側邊欄
   - **資料夾管理**: 新增、重新命名、刪除資料夾
   - **拖放功能**: 拖曳項目至資料夾或調整順序
   - 未分類區塊顯示未歸類項目
   - 刪除按鈕可清除本地與後端資料

**工具函數** (`frontend/src/utils/`):

1. **historyManager.js**: localStorage 管理
   - `HISTORY_KEY`: 儲存歷史記錄（含 `folderId` 欄位）
   - `FOLDERS_KEY`: 儲存資料夾結構
   - `syncHistoryFromBackend()`: 合併後端資料，保留本地 `folderId`
   - `moveHistoryToFolder()`: 移動項目至資料夾
   - `reorderHistory()`: 拖放排序（僅限同資料夾）

2. **settingsManager.js**: 使用者設定管理（AI provider、model、API keys）

**資料流**:
1. `App.js` 呼叫 `processVideo()` → 後端建立 job
2. `pollJobStatus()` 每 2 秒輪詢 `/api/jobs/{job_id}`
3. 完成後儲存至 `historyManager` → localStorage + 呼叫後端 `/api/video/history`
4. `Sidebar.js` 讀取歷史並支援資料夾分類

### 儲存結構

**storage/** 目錄（由後端管理）:
```
storage/
├── {job_id}/
│   ├── video.mp4                  # 下載的影片
│   ├── original_subtitle.srt      # 原始字幕
│   ├── translated_subtitle.srt    # 翻譯後字幕
│   ├── ai_outline.txt             # AI 生成的大綱
│   └── frames/                    # 截取的影格
│       ├── frame_0001.jpg
│       ├── frame_0002.jpg
│       └── ...
```

**前端 localStorage**:
- `videoHistory`: 儲存歷史項目（含 `folderId`）
- `historyFolders`: 儲存資料夾結構（id, name, expanded）
- `lastHistorySync`: 最後同步時間戳
- `userSettings`: AI 設定

## 關鍵功能實作細節

### 1. 資料夾管理與拖放排序

**資料結構**:
```javascript
// historyItem
{
  jobId: "uuid",
  videoId: "youtube_id",
  title: "影片標題",
  folderId: "folder_uuid" | null,  // null = uncategorized
  timestamp: "2025-10-07T...",
  result: { ... }
}

// folder
{
  id: "uuid",
  name: "資料夾名稱",
  expanded: true,
  createdAt: "2025-10-07T..."
}
```

**拖放邏輯** (`Sidebar.js`):
- 拖曳至資料夾 → `moveHistoryToFolder()`
- 拖曳至另一項目 → 檢查 `folderId` 是否相同
  - 相同 → `reorderHistory()` 調整順序
  - 不同 → 忽略（不允許跨資料夾排序）

**同步邏輯** (`historyManager.js:syncHistoryFromBackend`):
```javascript
const localItemsMap = new Map();
for (const localItem of localHistory) {
  localItemsMap.set(localItem.jobId, localItem);
}

const mergedHistory = backendHistory.map(backendItem => {
  const localItem = localItemsMap.get(backendItem.jobId);
  if (localItem) {
    return { ...backendItem, folderId: localItem.folderId || null };
  }
  return { ...backendItem, folderId: null };
});
```

### 2. AI 翻譯批次優化

**動態批次大小** (`ai_translator.py:_calculate_optimal_batch_size`):
```python
avg_length = sum(len(text) for text in texts) / len(texts)

if avg_length < 30:    return 30  # 短字幕
elif avg_length < 60:  return 20  # 中等
elif avg_length < 100: return 15  # 長字幕
else:                  return 10  # 極長字幕
```

**三種解析方法** (`ai_translator.py:_parse_translation_response`):
1. 標準編號格式: `[0] 翻譯文字`
2. Regex 模式匹配（DOTALL 模式）
3. 逐行過濾（移除前綴）

**錯誤處理**:
- 翻譯數量不匹配 → 自動補齊原始文字
- 詳細日誌記錄每個批次狀態

### 3. Whisper 字幕生成

**音訊轉字幕** (`audio_transcription.py`):
```python
transcription = client.audio.transcriptions.create(
    model="whisper-1",
    file=audio_file,
    response_format="verbose_json",
    timestamp_granularities=["segment"],  # 句子級別斷點
    language=language
)
```

使用 `segment` granularity 可獲得更自然的句子斷點。

## 常見開發任務

### 新增 AI 提供商

1. 在 `backend/models/schemas.py` 新增 enum 值：
   ```python
   class AIProvider(str, Enum):
       openai = "openai"
       claude = "claude"
       your_provider = "your_provider"
   ```

2. 在 `ai_translator.py` 和 `ai_outline.py` 新增實作：
   ```python
   elif provider == AIProvider.your_provider:
       # API 呼叫邏輯
   ```

3. 在 `VideoInput.js` 新增選項：
   ```javascript
   <option value="your_provider">Your Provider</option>
   ```

### 修改 AI 翻譯提示詞

編輯 `backend/services/ai_translator.py:_get_translation_prompt()`：
```python
prompt = f"""..."""
```

當前提示詞包含 7 條規則，強調自然翻譯、保留格式、42 字符長度限制。

### 調整批次大小策略

修改 `backend/services/ai_translator.py:_calculate_optimal_batch_size()`。

### 新增前端組件

1. 建立檔案於 `frontend/src/components/`
2. 在 `App.js` 匯入並使用
3. 在 `App.css` 或獨立 CSS 檔案中定義樣式

## 疑難排解

### ffmpeg 找不到
```bash
# Windows (使用 Chocolatey)
choco install ffmpeg

# macOS
brew install ffmpeg

# Linux
sudo apt install ffmpeg
```

### 虛擬環境問題
```bash
cd backend
uv sync  # 重新同步依賴
```

### 前端無法連接後端
檢查 `frontend/src/api/api.js` 中的 `API_BASE_URL` 是否正確（預設 `http://localhost:8000`）。

### AI 翻譯不觸發
確認勾選「AI 翻譯 & 生成 AI 影片大綱」且選擇 AI 提供商。目前邏輯：只有當 `generate_outline=true` 且 `ai_provider` 非空時才使用 AI 翻譯。

### 資料夾分類遺失
確認 `syncHistoryFromBackend()` 邏輯正確執行，保留本地 `folderId`。後端不儲存 `folderId`，僅在前端 localStorage 管理。

## 重要檔案位置

- **主要後端邏輯**: `backend/app.py`
- **AI 翻譯服務**: `backend/services/ai_translator.py`
- **字幕處理**: `backend/services/subtitle.py`
- **影格擷取**: `backend/services/frame_extractor.py`
- **前端主應用**: `frontend/src/App.js`
- **歷史管理**: `frontend/src/utils/historyManager.js`
- **側邊欄UI**: `frontend/src/components/Sidebar.js`
- **影片輸入表單**: `frontend/src/components/VideoInput.js`

## 依賴套件

**後端主要依賴**:
- `fastapi`: Web 框架
- `yt-dlp`: YouTube 影片下載
- `ffmpeg-python`: 影片處理
- `deep-translator`: Google 翻譯備用
- `openai`: OpenAI API (含 Whisper)
- `anthropic`: Claude API
- `google-generativeai`: Gemini API
- `pillow`: 圖片處理

**前端主要依賴**:
- `react`: UI 框架
- `axios`: HTTP 客戶端
- `react-router-dom`: 路由管理
