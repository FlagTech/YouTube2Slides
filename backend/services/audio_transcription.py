"""
OpenAI Whisper audio transcription service
Extracts audio from video and transcribes using Whisper API
"""
import os
import subprocess
from pathlib import Path
from typing import Dict, Optional
from openai import OpenAI


class AudioTranscriptionService:
    """Service for transcribing audio using OpenAI Whisper"""

    def __init__(self):
        self.audio_dir = Path("../storage/audio")
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        self.subtitle_dir = Path("../storage/subtitles")
        self.subtitle_dir.mkdir(parents=True, exist_ok=True)

    def extract_audio_from_video(self, video_path: str, video_id: str) -> str:
        """
        Extract audio from video file using ffmpeg

        Args:
            video_path: Path to video file
            video_id: Video ID for naming

        Returns:
            Path to extracted audio file
        """
        audio_path = self.audio_dir / f"{video_id}.mp3"

        # Use ffmpeg to extract audio
        # -vn: no video
        # -acodec libmp3lame: use MP3 codec
        # -ar 16000: 16kHz sample rate (optimal for Whisper)
        # -ac 1: mono channel
        # -b:a 64k: 64kbps bitrate
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-vn',  # No video
            '-acodec', 'libmp3lame',
            '-ar', '16000',  # 16kHz for Whisper
            '-ac', '1',  # Mono
            '-b:a', '64k',
            '-y',  # Overwrite output file
            str(audio_path)
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return str(audio_path)
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to extract audio: {e.stderr.decode()}")
        except FileNotFoundError:
            raise Exception("ffmpeg not found. Please install ffmpeg to use audio transcription.")

    def transcribe_audio(
        self,
        audio_path: str,
        api_key: str,
        language: Optional[str] = None
    ) -> Dict:
        """
        Transcribe audio using OpenAI Whisper API

        Args:
            audio_path: Path to audio file
            api_key: OpenAI API key
            language: Language code (e.g., 'en', 'zh', 'ja'). Auto-detect if None.

        Returns:
            Dict with transcription text and segments
        """
        try:
            client = OpenAI(api_key=api_key)

            with open(audio_path, 'rb') as audio_file:
                # Use Whisper API for transcription
                # response_format='verbose_json' gives us timestamps
                # timestamp_granularities=['segment'] provides better sentence-level segmentation
                transcription = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],  # Sentence-level timestamps
                    language=language  # None for auto-detection
                )

            return {
                'text': transcription.text,
                'language': transcription.language,
                'duration': transcription.duration,
                'segments': transcription.segments
            }

        except Exception as e:
            raise Exception(f"Whisper transcription failed: {str(e)}")

    def save_transcription_as_srt(
        self,
        transcription: Dict,
        video_id: str,
        language: str = 'ai'
    ) -> str:
        """
        Convert Whisper transcription to SRT subtitle format

        Args:
            transcription: Whisper transcription result
            video_id: Video ID
            language: Language code for filename

        Returns:
            Path to SRT file
        """
        srt_path = self.subtitle_dir / f"{video_id}.{language}.srt"

        segments = transcription['segments']

        with open(srt_path, 'w', encoding='utf-8') as f:
            for i, segment in enumerate(segments, 1):
                # SRT format:
                # 1
                # 00:00:00,000 --> 00:00:05,000
                # Subtitle text

                # Whisper segments are objects, use attribute access
                start_time = self._format_timestamp_srt(segment.start)
                end_time = self._format_timestamp_srt(segment.end)
                text = segment.text.strip()

                f.write(f"{i}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")

        return str(srt_path)

    def _format_timestamp_srt(self, seconds: float) -> str:
        """
        Format timestamp for SRT format (HH:MM:SS,mmm)

        Args:
            seconds: Time in seconds

        Returns:
            Formatted timestamp string
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def transcribe_video(
        self,
        video_path: str,
        video_id: str,
        api_key: str,
        language: Optional[str] = None
    ) -> Dict:
        """
        Complete workflow: Extract audio, transcribe, and save as SRT

        Args:
            video_path: Path to video file
            video_id: Video ID
            api_key: OpenAI API key
            language: Target language (None for auto-detect)

        Returns:
            Dict with subtitle path and transcription info
        """
        # Step 1: Extract audio
        audio_path = self.extract_audio_from_video(video_path, video_id)

        # Step 2: Transcribe audio
        transcription = self.transcribe_audio(audio_path, api_key, language)

        # Step 3: Save as SRT
        detected_lang = transcription['language']
        srt_path = self.save_transcription_as_srt(
            transcription,
            video_id,
            detected_lang
        )

        # Clean up audio file
        try:
            os.remove(audio_path)
        except:
            pass

        return {
            'subtitle_path': srt_path,
            'language': detected_lang,
            'duration': transcription['duration'],
            'segments_count': len(transcription['segments'])
        }

    def cleanup_audio(self, video_id: str):
        """Clean up audio files"""
        audio_file = self.audio_dir / f"{video_id}.mp3"
        if audio_file.exists():
            audio_file.unlink()
