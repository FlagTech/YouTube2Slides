"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional, Dict
from enum import Enum


class VideoQuality(str, Enum):
    """Video quality options"""
    Q360 = "360"
    Q480 = "480"
    Q720 = "720"


class Language(str, Enum):
    """Supported languages"""
    ZH_TW = "zh-TW"
    ZH_CN = "zh-CN"
    EN = "en"
    JA = "ja"
    KO = "ko"
    ES = "es"
    FR = "fr"
    DE = "de"


class VideoInfoRequest(BaseModel):
    """Request model for getting video info"""
    url: str = Field(..., description="YouTube video URL")


class VideoInfoResponse(BaseModel):
    """Response model for video information"""
    id: str
    title: str
    duration: float
    channel: str
    thumbnail: str
    description: Optional[str] = None
    available_subtitles: List[str] = []
    automatic_captions: List[str] = []


class AIProvider(str, Enum):
    """AI providers for outline generation"""
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    OLLAMA = "ollama"


class ScreenshotPosition(str, Enum):
    """Screenshot position within subtitle segment"""
    START = "start"
    MIDDLE = "middle"
    END = "end"


class ProcessVideoRequest(BaseModel):
    """Request model for processing video"""
    url: str = Field(..., description="YouTube video URL")
    quality: VideoQuality = Field(default=VideoQuality.Q720, description="Video quality")
    subtitle_languages: Optional[List[str]] = Field(default=None, description="Subtitle languages to download (auto-detect if None)")
    translate_to: Optional[str] = Field(default=None, description="Translate subtitles to this language")
    screenshot_position: ScreenshotPosition = Field(default=ScreenshotPosition.MIDDLE, description="Screenshot position in subtitle segment")
    screenshot_offset: float = Field(default=0.0, description="Screenshot time offset in seconds")
    generate_outline: bool = Field(default=False, description="Generate AI outline")
    ai_provider: Optional[AIProvider] = Field(default=None, description="AI provider for outline generation")
    ai_model: Optional[str] = Field(default=None, description="AI model to use")
    api_key: Optional[str] = Field(default=None, description="API key for AI provider")
    use_ai_transcription: bool = Field(default=False, description="Use OpenAI Whisper for audio transcription")
    whisper_api_key: Optional[str] = Field(default=None, description="OpenAI API key for Whisper transcription")


class SubtitleSegment(BaseModel):
    """Subtitle segment model"""
    index: int
    start_time: float
    end_time: float
    text: str


class Frame(BaseModel):
    """Frame information model"""
    index: int
    timestamp: float
    path: str
    filename: str
    subtitle: Optional[str] = None
    subtitle_translated: Optional[str] = None
    size_bytes: int


class ProcessVideoResponse(BaseModel):
    """Response model for video processing"""
    video_id: str
    title: str
    total_frames: int
    frames: List[Frame]
    subtitles: Dict[str, str]
    processing_time: float
    ai_outline: Optional[str] = None
    translated_subtitle: Optional[str] = None
    ai_provider: Optional[str] = None


class TranslateRequest(BaseModel):
    """Request model for translation"""
    text: str
    source_lang: str = "auto"
    target_lang: str = "en"


class TranslateResponse(BaseModel):
    """Response model for translation"""
    original_text: str
    translated_text: str
    source_lang: str
    target_lang: str


class JobStatus(str, Enum):
    """Job processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class JobProgressEvent(BaseModel):
    """Timeline entry for background job progress."""
    timestamp: str
    status: JobStatus
    progress: int = Field(ge=0, le=100)
    step: Optional[str] = None
    message: Optional[str] = None


class JobStatusResponse(BaseModel):
    """Response model for job status"""
    job_id: str
    status: JobStatus
    progress: int = Field(default=0, ge=0, le=100)
    message: Optional[str] = None
    current_step: Optional[str] = None
    history: List[JobProgressEvent] = Field(default_factory=list)
    result: Optional[ProcessVideoResponse] = None
    error: Optional[str] = None

