"""
YouTube video download and metadata extraction service
"""
import os
import yt_dlp
from typing import Dict, List, Optional
from pathlib import Path


class YouTubeService:
    def __init__(self, download_path: str = "./storage/videos"):
        self.download_path = Path(download_path)
        self.download_path.mkdir(parents=True, exist_ok=True)

    def get_video_info(self, url: str) -> Dict:
        """
        Extract video metadata without downloading
        """
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'channel': info.get('channel'),
                    'channel_id': info.get('channel_id'),
                    'thumbnail': info.get('thumbnail'),
                    'description': info.get('description'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'like_count': info.get('like_count'),
                    'available_subtitles': list(info.get('subtitles', {}).keys()),
                    'automatic_captions': list(info.get('automatic_captions', {}).keys()),
                }
        except Exception as e:
            raise Exception(f"Failed to get video info: {str(e)}")

    def download_video(self, url: str, quality: str = "720", progress_callback=None) -> Dict:
        """
        Download YouTube video with specified quality
        Args:
            url: YouTube video URL
            quality: Video quality (360, 480, 720)
            progress_callback: Callback function(progress_percent) for download progress
        Returns:
            Dict with video_path and video_id
        """
        video_id = self._extract_video_id(url)
        output_path = self.download_path / f"{video_id}.mp4"

        # Quality format mapping
        format_map = {
            "360": "best[height<=360]",
            "480": "best[height<=480]",
            "720": "best[height<=720]",
            "1080": "best[height<=1080]",
        }

        def progress_hook(d):
            if progress_callback and d['status'] == 'downloading':
                # Extract download percentage
                if 'total_bytes' in d:
                    percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                elif 'total_bytes_estimate' in d:
                    percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
                else:
                    percent = 0
                progress_callback(percent)

        ydl_opts = {
            'format': format_map.get(quality, "best[height<=720]"),
            'outtmpl': str(output_path),
            'quiet': False,
            'no_warnings': True,
            'progress_hooks': [progress_hook],
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            return {
                'video_id': video_id,
                'video_path': str(output_path),
                'quality': quality
            }
        except Exception as e:
            raise Exception(f"Failed to download video: {str(e)}")

    def get_best_subtitle_language(self, url: str) -> str:
        """
        Automatically detect and return the best subtitle language
        Priority: zh-TW > zh-CN > en > ja > ko > other languages

        Strategy:
        1. Check manual subtitles first (more reliable)
        2. Look for original language markers (e.g., 'en-orig', 'ja-orig')
        3. Fall back to auto-captions if no manual subs
        """
        info = self.get_video_info(url)
        available_subs = info.get('available_subtitles', [])
        auto_captions = info.get('automatic_captions', [])

        # Priority order for checking (prioritize Chinese and English)
        priority_langs = ['zh-TW', 'zh-Hant', 'zh-CN', 'zh-Hans', 'zh', 'en-orig', 'en', 'ja-orig', 'ja', 'ko-orig', 'ko']

        # Step 1: Check manual subtitles first (these are uploaded by creators)
        manual_subs_set = set(available_subs)
        for lang in priority_langs:
            if lang in manual_subs_set:
                # Map back to our standard format
                if lang in ['zh-TW', 'zh-Hant', 'zh']:
                    return 'zh-TW'
                elif lang in ['zh-CN', 'zh-Hans']:
                    return 'zh-CN'
                elif lang in ['en', 'en-orig']:
                    return 'en'
                elif lang in ['ja', 'ja-orig']:
                    return 'ja'
                elif lang in ['ko', 'ko-orig']:
                    return 'ko'

        # Step 2: Check auto-captions for original language markers (-orig suffix)
        # These markers indicate the source language of the video
        auto_captions_set = set(auto_captions)

        # Common language original markers
        orig_markers = {
            'en-orig': 'en',
            'ja-orig': 'ja',
            'ko-orig': 'ko',
            'es-orig': 'es',
            'fr-orig': 'fr',
            'de-orig': 'de',
            'it-orig': 'it',
            'pt-orig': 'pt',
            'ru-orig': 'ru',
            'ar-orig': 'ar',
            'hi-orig': 'hi',
            'th-orig': 'th',
            'vi-orig': 'vi',
            'id-orig': 'id',
        }

        # Check for priority languages first
        for orig_lang in ['en-orig', 'ja-orig', 'ko-orig']:
            if orig_lang in auto_captions_set:
                return orig_markers[orig_lang]

        # Check for other language originals
        for orig_lang, base_lang in orig_markers.items():
            if orig_lang in auto_captions_set:
                return base_lang

        # Step 3: Check if video has Chinese auto-captions as source
        for lang in ['zh-TW', 'zh-Hant', 'zh-CN', 'zh-Hans', 'zh']:
            if lang in auto_captions_set:
                # Verify it's likely the source language by checking if 'en' is also available
                # If both Chinese and English auto-captions exist, prefer the one that appears first in our priority
                if 'en' in auto_captions_set or 'en-orig' in auto_captions_set:
                    # If English is available, assume it's the source for most videos
                    # unless we have Chinese manual subtitles
                    continue
                # Map to standard format
                if lang in ['zh-TW', 'zh-Hant', 'zh']:
                    return 'zh-TW'
                elif lang in ['zh-CN', 'zh-Hans']:
                    return 'zh-CN'

        # Step 4: If only auto-captions available, check priority languages
        for lang in ['en', 'ja', 'ko']:
            if lang in auto_captions_set:
                return lang

        # Step 5: Fall back to first available subtitle or auto-caption
        if available_subs:
            return available_subs[0]
        if auto_captions:
            # Remove -orig suffix if present
            first_caption = auto_captions[0]
            if first_caption.endswith('-orig'):
                return first_caption[:-5]  # Remove '-orig'
            return first_caption

        # Default to English if nothing available
        return 'en'

    def download_subtitles(
        self,
        url: str,
        languages: List[str] = None,
        video_info: Optional[Dict] = None,
    ) -> Dict:
        """
        Download subtitles for specified languages
        Args:
            url: YouTube video URL
            languages: List of language codes. If None, auto-detect best language.
            video_info: Optional pre-fetched video metadata to avoid duplicate lookups.
        Returns:
            Dict with subtitle paths for each language and auto-generated flags
        """
        if languages is None:
            # Auto-detect best language
            best_lang = self.get_best_subtitle_language(url)
            languages = [best_lang]

        if video_info is None:
            video_info = self.get_video_info(url)

        lang_variations = {
            'zh-TW': ['zh-TW', 'zh-Hant', 'zh'],
            'zh-CN': ['zh-CN', 'zh-Hans', 'zh'],
            'en': ['en-orig', 'en'],
            'ja': ['ja-orig', 'ja'],
            'ko': ['ko-orig', 'ko'],
            'es': ['es-orig', 'es'],
            'fr': ['fr-orig', 'fr'],
            'de': ['de-orig', 'de'],
            'it': ['it-orig', 'it'],
            'pt': ['pt-orig', 'pt'],
            'ru': ['ru-orig', 'ru'],
            'ar': ['ar-orig', 'ar'],
            'hi': ['hi-orig', 'hi'],
            'th': ['th-orig', 'th'],
            'vi': ['vi-orig', 'vi'],
            'id': ['id-orig', 'id'],
        }

        def normalize_codes(*codes: str) -> set:
            normalized = set()
            for code in codes:
                if not code:
                    continue
                normalized.add(code)
                if code.endswith('-orig'):
                    normalized.add(code[:-5])
                cleaned = code.replace('-orig', '')
                if cleaned:
                    normalized.add(cleaned)
                if code in lang_variations:
                    normalized.update(lang_variations[code])
                for canonical, variants in lang_variations.items():
                    if code in variants:
                        normalized.add(canonical)
                        normalized.update(variants)
            normalized.discard('')
            return normalized

        auto_caption_keys = set()
        for code in video_info.get('automatic_captions', []):
            auto_caption_keys.update(normalize_codes(code))

        manual_subtitle_keys = set()
        for code in video_info.get('available_subtitles', []):
            manual_subtitle_keys.update(normalize_codes(code))

        video_id = self._extract_video_id(url)
        subtitle_dir = Path("./storage/subtitles")
        subtitle_dir.mkdir(parents=True, exist_ok=True)

        def is_auto_caption(lang_code: str, variant_code: str) -> bool:
            normalized = normalize_codes(lang_code, variant_code)
            if normalized & manual_subtitle_keys:
                return False
            if normalized & auto_caption_keys:
                return True
            variant_only = normalize_codes(variant_code)
            return any(code.endswith('-orig') for code in variant_only)

        # Build a comprehensive list of language codes to try
        all_lang_codes = []
        for lang in languages:
            all_lang_codes.extend(lang_variations.get(lang, [lang]))

        ydl_opts = {
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
            'subtitleslangs': all_lang_codes,
            'subtitlesformat': 'srt',
            'outtmpl': str(subtitle_dir / f"{video_id}"),
            'quiet': False,
            'sleep_interval': 1,  # Add delay between requests
            'max_sleep_interval': 5,
            'retries': 3,  # Retry on errors
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            # Find downloaded subtitle files (check all possible variations)
            subtitle_files = {}
            is_auto_generated = {}  # Track whether subtitle is auto-generated
            for lang in languages:
                found = False
                # Try all variations for this language
                for variant in lang_variations.get(lang, [lang]):
                    srt_file = subtitle_dir / f"{video_id}.{variant}.srt"
                    if srt_file.exists():
                        subtitle_files[lang] = str(srt_file)
                        is_auto_generated[lang] = is_auto_caption(lang, variant)
                        found = True
                        break

                # If not found, also check the original language code
                if not found:
                    srt_file = subtitle_dir / f"{video_id}.{lang}.srt"
                    if srt_file.exists():
                        subtitle_files[lang] = str(srt_file)
                        is_auto_generated[lang] = is_auto_caption(lang, lang)

            return {
                'video_id': video_id,
                'subtitles': subtitle_files,
                'is_auto_generated': is_auto_generated
            }
        except Exception as e:
            raise Exception(f"Failed to download subtitles: {str(e)}")

    def _extract_video_id(self, url: str) -> str:
        """
        Extract video ID from YouTube URL
        """
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return info['id']
        except Exception as e:
            raise Exception(f"Failed to extract video ID: {str(e)}")

    def get_available_subtitles(self, url: str) -> Dict:
        """
        Get list of available subtitle languages for a video
        """
        try:
            info = self.get_video_info(url)
            return {
                'manual_subtitles': info.get('available_subtitles', []),
                'auto_captions': info.get('automatic_captions', [])
            }
        except Exception as e:
            raise Exception(f"Failed to get available subtitles: {str(e)}")
