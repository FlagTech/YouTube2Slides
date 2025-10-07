"""
FastAPI main application
YouTube to Readable Slides Converter
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
import uvicorn
import time
import uuid
import zipfile
import io
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List

from models.schemas import (
    VideoInfoRequest,
    VideoInfoResponse,
    ProcessVideoRequest,
    ProcessVideoResponse,
    TranslateRequest,
    TranslateResponse,
    JobStatusResponse,
    JobStatus,
    Frame
)
from services.youtube import YouTubeService
from services.subtitle import SubtitleProcessor
from services.frame_extractor import FrameExtractor
from services.translator import TranslationService
from services.ai_outline import AIOutlineService
from services.ai_translator import AITranslationService
from services.audio_transcription import AudioTranscriptionService
from services.subtitle_optimizer import SubtitleOptimizer

# Initialize FastAPI app
app = FastAPI(
    title="YouTube 影片懶人觀看術",
    description="將 YouTube 影片轉換為靜態可讀投影片與字幕",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

# Initialize services
youtube_service = YouTubeService()
subtitle_processor = SubtitleProcessor()
frame_extractor = FrameExtractor()
translator = TranslationService()
ai_outline_service = AIOutlineService()
ai_translator = AITranslationService()
audio_transcription_service = AudioTranscriptionService()
subtitle_optimizer = SubtitleOptimizer()

# In-memory job storage (in production, use Redis or database)
jobs: Dict[str, Dict] = {}


HISTORY_MAX_ENTRIES = 200  # Increased to keep more history events
RESULTS_DIR = Path("storage/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def save_result_to_file(job_id: str, video_id: str, result_data: dict):
    """Save processing result to a JSON file for persistence"""
    try:
        result_file = RESULTS_DIR / f"{video_id}.json"
        result_with_metadata = {
            "job_id": job_id,
            "video_id": video_id,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "result": result_data
        }
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_with_metadata, f, ensure_ascii=False, indent=2)
        print(f"Result saved to {result_file}")
    except Exception as e:
        print(f"Failed to save result to file: {e}")


def load_all_results() -> List[dict]:
    """Load all saved results from files"""
    results = []
    try:
        for result_file in RESULTS_DIR.glob("*.json"):
            try:
                with open(result_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    results.append(data)
            except Exception as e:
                print(f"Failed to load {result_file}: {e}")
        # Sort by timestamp, newest first
        results.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    except Exception as e:
        print(f"Failed to load results: {e}")
    return results


def log_job_progress(job_id: str, *, step: str, status: JobStatus = None, progress: int = None, message: str = None):
    """Record progress updates for background jobs and keep a short history."""
    job = jobs[job_id]
    if status is not None:
        job["status"] = status
    if progress is not None:
        job["progress"] = int(progress)
    if message is not None:
        job["message"] = message
    job["current_step"] = step

    event = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "status": job.get("status"),
        "step": step,
        "message": job.get("message"),
        "progress": job.get("progress", 0),
    }

    history = job.setdefault("history", [])
    history.append(event)
    if len(history) > HISTORY_MAX_ENTRIES:
        del history[:-HISTORY_MAX_ENTRIES]


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "message": "YouTube 影片懶人觀看術 API",
        "version": "1.0.0",
        "endpoints": {
            "video_info": "/api/video/info",
            "process_video": "/api/video/process",
            "job_status": "/api/jobs/{job_id}",
            "translate": "/api/translate"
        }
    }


@app.post("/api/video/info", response_model=VideoInfoResponse)
async def get_video_info(request: VideoInfoRequest):
    """
    Get YouTube video information without downloading
    """
    try:
        info = youtube_service.get_video_info(request.url)
        return VideoInfoResponse(**info)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/video/process")
async def process_video(request: ProcessVideoRequest, background_tasks: BackgroundTasks):
    """
    Process YouTube video and extract frames with subtitles
    This creates a background job and returns job_id
    """
    job_id = str(uuid.uuid4())

    # Create job entry
    jobs[job_id] = {
        "job_id": job_id,
        "status": JobStatus.PENDING,
        "progress": 0,
        "message": "工作已建立",
        "result": None,
        "error": None,
        "history": [],
        "current_step": None
    }

    log_job_progress(
        job_id,
        step="queued",
        status=JobStatus.PENDING,
        progress=0,
        message="工作已加入佇列，準備開始處理..."
    )

    # Add background task
    background_tasks.add_task(process_video_task, job_id, request)

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "Video processing started"
    }


def process_video_task(job_id: str, request: ProcessVideoRequest):
    """
    Background task to process video
    Note: This is a sync function because all the processing is synchronous
    """
    try:
        log_job_progress(
            job_id,
            step="prepare",
            status=JobStatus.PROCESSING,
            progress=5,
            message="開始處理任務..."
        )

        start_time = time.time()

        log_job_progress(
            job_id,
            step="metadata",
            progress=10,
            message="擷取影片資訊..."
        )
        video_info = youtube_service.get_video_info(request.url)
        video_id = video_info['id']
        title = video_info['title']
        log_job_progress(
            job_id,
            step="metadata",
            progress=12,
            message="影片資訊擷取完成"
        )

        log_job_progress(
            job_id,
            step="download_video",
            progress=20,
            message="下載影片中..."
        )

        # Download with progress callback
        def video_download_progress(percent):
            # Map download progress (0-100%) to job progress (20-35%)
            job_progress = 20 + int(percent * 0.15)
            log_job_progress(
                job_id,
                step="download_video",
                progress=job_progress,
                message=f"下載影片中... {int(percent)}%"
            )

        video_data = youtube_service.download_video(
            request.url,
            request.quality.value,
            progress_callback=video_download_progress
        )
        video_path = video_data['video_path']
        log_job_progress(
            job_id,
            step="download_video",
            progress=35,
            message="影片下載完成"
        )
        subtitle_auto_flags = {}
        primary_subtitle_is_auto = False

        log_job_progress(
            job_id,
            step="fetch_subtitles",
            progress=38,
            message="取得字幕中..."
        )
        if request.use_ai_transcription and request.whisper_api_key:
            log_job_progress(
                job_id,
                step="ai_transcription",
                progress=40,
                message="使用 Whisper 產生字幕..."
            )
            try:
                transcription_result = audio_transcription_service.transcribe_video(
                    video_path=video_path,
                    video_id=video_id,
                    api_key=request.whisper_api_key,
                    language=None  # Auto-detect
                )

                subtitle_path = transcription_result['subtitle_path']
                primary_lang = transcription_result['language']
                subtitles = {primary_lang: subtitle_path}

                log_job_progress(
                    job_id,
                    step="ai_transcription",
                    progress=45,
                    message=f"Whisper 字幕產生完成 ({primary_lang})"
                )
            except Exception as e:
                log_job_progress(
                    job_id,
                    step="ai_transcription",
                    progress=38,
                    message=f"Whisper 失敗 ({str(e)}), 改用 YouTube 字幕..."
                )

                subtitle_data = youtube_service.download_subtitles(
                    request.url,
                    request.subtitle_languages,
                    video_info=video_info
                )
                subtitles = subtitle_data['subtitles']
                subtitle_auto_flags = subtitle_data.get('is_auto_generated', {})

                if not subtitles:
                    raise Exception(f"AI transcription failed and no YouTube subtitles available: {str(e)}")

                primary_lang = list(subtitles.keys())[0]
                subtitle_path = subtitles[primary_lang]
                primary_subtitle_is_auto = subtitle_auto_flags.get(primary_lang, False)

                log_job_progress(
                    job_id,
                    step="fetch_subtitles",
                    progress=47,
                    message="已改用 YouTube 字幕"
                )
        else:
            log_job_progress(
                job_id,
                step="fetch_subtitles",
                progress=40,
                message="下載 YouTube 字幕中..."
            )
            subtitle_data = youtube_service.download_subtitles(
                request.url,
                request.subtitle_languages,
                video_info=video_info
            )
            subtitles = subtitle_data['subtitles']
            subtitle_auto_flags = subtitle_data.get('is_auto_generated', {})

            if not subtitles:
                raise Exception("No subtitles available for this video. Try enabling 'AI字幕生成' option.")

            primary_lang = list(subtitles.keys())[0]
            subtitle_path = subtitles[primary_lang]
            primary_subtitle_is_auto = subtitle_auto_flags.get(primary_lang, False)

            log_job_progress(
                job_id,
                step="fetch_subtitles",
                progress=47,
                message="字幕下載完成"
            )
        log_job_progress(
            job_id,
            step="subtitle_selection",
            progress=50,
            message=f"使用 {primary_lang} 字幕"
        )
        if primary_subtitle_is_auto:
            log_job_progress(
                job_id,
                step="subtitle_optimize",
                progress=52,
                message="優化自動字幕..."
            )
            try:
                # Pass language code to optimizer for language-specific handling
                optimized_path = subtitle_optimizer.optimize_srt_file(subtitle_path, language=primary_lang)
                stats = subtitle_optimizer.get_optimization_stats(subtitle_path)

                if stats['reduction_percentage'] > 30:
                    subtitle_path = optimized_path
                    # Update the subtitles dictionary with optimized path
                    subtitles[primary_lang] = optimized_path
                    log_job_progress(
                        job_id,
                        step="subtitle_optimize",
                        progress=55,
                        message=f"字幕優化完成，段落減少 {stats['reduction_percentage']:.1f}%"
                    )
                else:
                    log_job_progress(
                        job_id,
                        step="subtitle_optimize",
                        progress=53,
                        message="字幕優化變化不大，保留原始字幕"
                    )
            except Exception as e:
                print(f"Subtitle optimization failed: {str(e)}")
                log_job_progress(
                    job_id,
                    step="subtitle_optimize",
                    progress=52,
                    message="字幕優化失敗，改用原始字幕"
                )
        else:
            log_job_progress(
                job_id,
                step="subtitle_optimize",
                progress=50,
                message="偵測為手動字幕，略過優化"
            )

        log_job_progress(
            job_id,
            step="subtitle_parse",
            progress=58,
            message="解析字幕片段..."
        )
        segments = subtitle_processor.parse_srt(subtitle_path)
        log_job_progress(
            job_id,
            step="subtitle_parse",
            progress=62,
            message=f"字幕解析完成，共 {len(segments)} 段"
        )

        keyframe_timestamps = subtitle_processor.get_keyframe_timestamps(
            offset=request.screenshot_offset,
            position=request.screenshot_position.value
        )
        log_job_progress(
            job_id,
            step="keyframe_selection",
            progress=65,
            message=f"產生 {len(keyframe_timestamps)} 個截圖時間點"
        )

        original_subtitle_texts = [
            subtitle_processor.get_subtitle_at_time(ts)
            for ts in keyframe_timestamps
        ]

        translated_subtitle_texts = None
        translated_subtitle_path = None
        if request.translate_to:
            log_job_progress(
                job_id,
                step="translate",
                progress=68,
                message=f"翻譯字幕成 {request.translate_to}..."
            )

            def translation_progress(percent):
                # Map translation progress (0-100%) to job progress (68-72%)
                job_progress = 68 + int(percent * 0.04)
                log_job_progress(
                    job_id,
                    step="translate",
                    progress=job_progress,
                    message=f"翻譯字幕中... {int(percent)}%"
                )

            if request.generate_outline and request.ai_provider:
                try:
                    log_job_progress(
                        job_id,
                        step="translate",
                        progress=69,
                        message=f"使用 {request.ai_provider.value} 翻譯字幕..."
                    )
                    translated_subtitle_texts = ai_translator.translate_batch(
                        original_subtitle_texts,
                        source_lang=primary_lang,
                        target_lang=request.translate_to,
                        provider=request.ai_provider,
                        model=request.ai_model,
                        api_key=request.api_key,
                        batch_size=20
                    )
                except Exception as e:
                    print(f"AI translation failed, falling back to Google Translate: {str(e)}")
                    translated_subtitle_texts = translator.batch_translate(
                        original_subtitle_texts,
                        source_lang=primary_lang,
                        target_lang=request.translate_to,
                        progress_callback=translation_progress
                    )
            else:
                translated_subtitle_texts = translator.batch_translate(
                    original_subtitle_texts,
                    source_lang=primary_lang,
                    target_lang=request.translate_to,
                    progress_callback=translation_progress
                )

            from pathlib import Path
            translated_subtitle_dir = Path("./storage/subtitles")
            translated_subtitle_path = str(translated_subtitle_dir / f"{video_id}.{request.translate_to}.translated.srt")

            with open(translated_subtitle_path, 'w', encoding='utf-8') as f:
                for i, (seg, text) in enumerate(zip(segments, translated_subtitle_texts)):
                    f.write(f"{i + 1}\n")
                    f.write(f"{subtitle_processor._format_timestamp(seg.start_time)} --> {subtitle_processor._format_timestamp(seg.end_time)}\n")
                    f.write(f"{text}\n\n")

            log_job_progress(
                job_id,
                step="translate",
                progress=72,
                message="字幕翻譯完成"
            )
        else:
            log_job_progress(
                job_id,
                step="translate",
                progress=72,
                message="未啟用字幕翻譯，略過此步驟"
            )

        log_job_progress(
            job_id,
            step="frame_capture",
            progress=75,
            message="擷取影格中..."
        )

        # Frame extraction with progress callback
        def frame_extraction_progress(percent):
            # Map extraction progress (0-100%) to job progress (75-85%)
            job_progress = 75 + int(percent * 0.10)
            log_job_progress(
                job_id,
                step="frame_capture",
                progress=job_progress,
                message=f"擷取影格中... {int(percent)}%"
            )
        frames_data = frame_extractor.extract_frames_with_subtitles(
            video_path=video_path,
            timestamps=keyframe_timestamps,
            subtitles=original_subtitle_texts,
            video_id=video_id,
            quality=2,
            resolution=request.quality.value,
            progress_callback=frame_extraction_progress
        )
        log_job_progress(
            job_id,
            step="frame_capture",
            progress=85,
            message=f"影格擷取完成，共 {len(frames_data)} 張"
        )
        log_job_progress(
            job_id,
            step="frame_optimize",
            progress=86,
            message="壓縮影格與整理字幕..."
        )
        total_frames = len(frames_data)
        for i, frame in enumerate(frames_data):
            frame_extractor.compress_frame(frame['path'], quality=85)
            if translated_subtitle_texts and i < len(translated_subtitle_texts):
                frame['subtitle_translated'] = translated_subtitle_texts[i]

            # Report progress every 5 frames or on last frame for more granular updates
            if (i + 1) % 5 == 0 or (i + 1) == total_frames:
                percent = ((i + 1) / total_frames) * 100
                job_progress = 86 + int(percent * 0.04)  # 86-90%
                log_job_progress(
                    job_id,
                    step="frame_optimize",
                    progress=job_progress,
                    message=f"壓縮影格... {i+1}/{total_frames}"
                )
        log_job_progress(
            job_id,
            step="frame_optimize",
            progress=90,
            message="影格最佳化完成"
        )
        ai_outline = None
        ai_provider_used = None
        if request.generate_outline and request.ai_provider:
            log_job_progress(
                job_id,
                step="ai_outline",
                progress=92,
                message=f"使用 {request.ai_provider.value} 產生大綱..."
            )
            try:
                subtitle_texts = [seg.text for seg in segments]

                outline_result = ai_outline_service.generate_outline(
                    video_title=title,
                    video_description=video_info.get('description', ''),
                    subtitles=subtitle_texts,
                    provider=request.ai_provider.value,
                    model=request.ai_model,
                    api_key=request.api_key
                )
                ai_outline = outline_result.get('outline')
                ai_provider_used = outline_result.get('provider')
                log_job_progress(
                    job_id,
                    step="ai_outline",
                    progress=95,
                    message="AI 大綱產生完成"
                )
            except Exception as e:
                print(f"AI outline generation failed: {str(e)}")
                log_job_progress(
                    job_id,
                    step="ai_outline",
                    progress=95,
                    message="AI 大綱產生失敗，略過"
                )
        else:
            log_job_progress(
                job_id,
                step="ai_outline",
                progress=92,
                message="未啟用 AI 大綱，略過此步驟"
            )
        processing_time = time.time() - start_time
        log_job_progress(
            job_id,
            step="finalize",
            progress=98,
            message="整理處理結果..."
        )
        result = ProcessVideoResponse(
            video_id=video_id,
            title=title,
            total_frames=len(frames_data),
            frames=[Frame(**frame) for frame in frames_data],
            subtitles=subtitles,
            processing_time=processing_time,
            ai_outline=ai_outline,
            ai_provider=ai_provider_used,
            translated_subtitle=translated_subtitle_path
        )

        result_dict = result.dict()
        jobs[job_id]["result"] = result_dict

        # Save result to file for persistence
        save_result_to_file(job_id, video_id, result_dict)

        log_job_progress(
            job_id,
            step="complete",
            status=JobStatus.COMPLETED,
            progress=100,
            message="處理完成"
        )

    except Exception as e:
        print(f"[ERROR] Background task failed for job_id {job_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        jobs[job_id]["error"] = str(e)
        log_job_progress(
            job_id,
            step="failed",
            status=JobStatus.FAILED,
            message=f"處理失敗: {str(e)}"
        )



@app.get("/api/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get status of a processing job
    """
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    return JobStatusResponse(**jobs[job_id])


@app.get("/api/videos/history")
async def get_video_history():
    """
    Get all processed video history from saved results
    """
    try:
        results = load_all_results()
        # Return in format compatible with frontend history
        history = []
        for item in results:
            result_data = item.get('result', {})
            history.append({
                "jobId": item.get('job_id'),
                "videoId": item.get('video_id'),
                "title": result_data.get('title', '未命名影片'),
                "totalFrames": result_data.get('total_frames', 0),
                "timestamp": item.get('timestamp'),
                "result": result_data
            })
        return {"history": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load history: {str(e)}")


@app.post("/api/translate", response_model=TranslateResponse)
async def translate_text(request: TranslateRequest):
    """
    Translate text to target language
    """
    try:
        translated = translator.translate_text(
            request.text,
            request.source_lang,
            request.target_lang
        )

        return TranslateResponse(
            original_text=request.text,
            translated_text=translated,
            source_lang=request.source_lang,
            target_lang=request.target_lang
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/ollama/models")
async def get_ollama_models():
    """
    Get list of available Ollama models from local installation
    """
    try:
        models = ai_outline_service.get_ollama_models()
        return {"models": models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/languages")
async def get_supported_languages():
    """
    Get list of supported languages
    """
    return translator.get_supported_languages()


@app.get("/api/ai-providers")
async def get_ai_providers():
    """
    Get list of available AI providers for outline generation
    """
    available_providers = ai_outline_service.get_available_providers()
    return {
        "providers": available_providers,
        "configured": len(available_providers) > 0
    }


@app.get("/api/video/{video_id}/download-frames")
async def download_all_frames(video_id: str):
    """
    Download all frames for a video as a ZIP file
    """
    try:
        # 檢查兩種可能的目錄結構
        frames_dir_nested = Path(f"./storage/frames/{video_id}")
        frames_dir_flat = Path("./storage/frames")

        frame_files = []

        # 優先檢查巢狀結構
        if frames_dir_nested.exists() and frames_dir_nested.is_dir():
            frame_files = list(frames_dir_nested.glob("*.jpg")) + list(frames_dir_nested.glob("*.png"))

        # 如果沒有找到，檢查扁平結構（檔名包含 video_id）
        if not frame_files and frames_dir_flat.exists():
            frame_files = list(frames_dir_flat.glob(f"{video_id}_*.jpg")) + list(frames_dir_flat.glob(f"{video_id}_*.png"))

        if not frame_files:
            raise HTTPException(status_code=404, detail=f"No frames found for video {video_id}")

        # 建立記憶體中的 ZIP 檔案
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for frame_file in sorted(frame_files):
                # 將檔案加入 ZIP，使用相對路徑作為 ZIP 內的檔名
                zip_file.write(frame_file, frame_file.name)

        # 將指標移到開頭
        zip_buffer.seek(0)

        # 回傳 ZIP 檔案
        return StreamingResponse(
            zip_buffer,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={video_id}_frames.zip"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create ZIP: {str(e)}")


@app.delete("/api/video/{video_id}")
async def delete_video(video_id: str):
    """
    Delete video and associated frames
    """
    try:
        # Delete frames
        deleted_frames = frame_extractor.cleanup_frames(video_id)

        # Delete video file
        video_path = Path(f"./storage/videos/{video_id}.mp4")
        if video_path.exists():
            video_path.unlink()

        return {
            "message": "Video deleted successfully",
            "deleted_frames": deleted_frames
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    # Create storage directories
    Path("./storage/videos").mkdir(parents=True, exist_ok=True)
    Path("./storage/frames").mkdir(parents=True, exist_ok=True)
    Path("./storage/subtitles").mkdir(parents=True, exist_ok=True)

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
