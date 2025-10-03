"""
Subtitle translation service
"""
from deep_translator import GoogleTranslator
from typing import List, Dict
import time


class TranslationService:
    """Translate subtitles to different languages"""

    def __init__(self):
        self.supported_languages = {
            'zh-TW': 'zh-TW',
            'zh-CN': 'zh-CN',
            'en': 'en',
            'ja': 'ja',
            'ko': 'ko',
            'es': 'es',
            'fr': 'fr',
            'de': 'de',
            'ru': 'ru',
            'ar': 'ar'
        }

    def translate_text(
        self,
        text: str,
        source_lang: str = 'auto',
        target_lang: str = 'en'
    ) -> str:
        """
        Translate a single text string
        Args:
            text: Text to translate
            source_lang: Source language code (use 'auto' for auto-detection)
            target_lang: Target language code
        Returns:
            Translated text
        """
        if not text.strip():
            return text

        try:
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            translated = translator.translate(text)
            return translated
        except Exception as e:
            print(f"Translation error: {str(e)}")
            return text  # Return original text if translation fails

    def translate_subtitle_segments(
        self,
        segments: List[Dict],
        source_lang: str = 'auto',
        target_lang: str = 'en',
        delay: float = 0.1
    ) -> List[Dict]:
        """
        Translate multiple subtitle segments
        Args:
            segments: List of subtitle segment dicts with 'text' field
            source_lang: Source language code
            target_lang: Target language code
            delay: Delay between translation requests (to avoid rate limiting)
        Returns:
            List of segments with translated text
        """
        translated_segments = []

        for segment in segments:
            text = segment.get('text', '')

            if text.strip():
                try:
                    translated_text = self.translate_text(text, source_lang, target_lang)
                    time.sleep(delay)  # Avoid rate limiting
                except Exception as e:
                    print(f"Failed to translate segment: {str(e)}")
                    translated_text = text
            else:
                translated_text = text

            translated_segment = segment.copy()
            translated_segment['text'] = translated_text
            translated_segment['original_text'] = text
            translated_segments.append(translated_segment)

        return translated_segments

    def batch_translate(
        self,
        texts: List[str],
        source_lang: str = 'auto',
        target_lang: str = 'en',
        batch_size: int = 10,
        delay: float = 0.1,
        progress_callback=None
    ) -> List[str]:
        """
        Translate multiple texts with batching
        Args:
            texts: List of text strings
            source_lang: Source language code
            target_lang: Target language code
            batch_size: Number of texts to translate before delay
            delay: Delay between batches
            progress_callback: Callback function(percent) for progress updates
        Returns:
            List of translated texts
        """
        translated = []
        total = len(texts)

        for i, text in enumerate(texts):
            if not text.strip():
                translated.append(text)
                continue

            try:
                translated_text = self.translate_text(text, source_lang, target_lang)
                translated.append(translated_text)

                # Report progress
                if progress_callback:
                    percent = ((i + 1) / total) * 100
                    progress_callback(percent)

                # Add delay after every batch_size translations
                if (i + 1) % batch_size == 0:
                    time.sleep(delay)
            except Exception as e:
                print(f"Translation failed for text {i}: {str(e)}")
                translated.append(text)

        return translated

    def detect_language(self, text: str) -> str:
        """
        Detect language of text
        Args:
            text: Text to analyze
        Returns:
            Language code
        """
        try:
            from deep_translator import GoogleTranslator
            # Google Translator doesn't have built-in detection,
            # but we can use langdetect as fallback
            try:
                from langdetect import detect
                return detect(text)
            except ImportError:
                # If langdetect not available, return 'auto'
                return 'auto'
        except Exception as e:
            print(f"Language detection failed: {str(e)}")
            return 'auto'

    def translate_srt_file(
        self,
        input_path: str,
        output_path: str,
        source_lang: str = 'auto',
        target_lang: str = 'en'
    ) -> str:
        """
        Translate an entire SRT file
        Args:
            input_path: Path to input SRT file
            output_path: Path to output SRT file
            source_lang: Source language
            target_lang: Target language
        Returns:
            Path to translated SRT file
        """
        from .subtitle import SubtitleProcessor

        processor = SubtitleProcessor()
        segments = processor.parse_srt(input_path)

        # Prepare segments for translation
        segment_dicts = [
            {
                'index': seg.index,
                'start_time': seg.start_time,
                'end_time': seg.end_time,
                'text': seg.text
            }
            for seg in segments
        ]

        # Translate
        translated_segments = self.translate_subtitle_segments(
            segment_dicts,
            source_lang,
            target_lang
        )

        # Write to output file
        with open(output_path, 'w', encoding='utf-8') as f:
            for seg in translated_segments:
                f.write(f"{seg['index']}\n")
                f.write(f"{processor._format_timestamp(seg['start_time'])} --> ")
                f.write(f"{processor._format_timestamp(seg['end_time'])}\n")
                f.write(f"{seg['text']}\n\n")

        return output_path

    def get_supported_languages(self) -> Dict[str, str]:
        """
        Get list of supported language codes and names
        """
        return {
            'zh-TW': 'Chinese (Traditional)',
            'zh-CN': 'Chinese (Simplified)',
            'en': 'English',
            'ja': 'Japanese',
            'ko': 'Korean',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'ru': 'Russian',
            'ar': 'Arabic',
            'pt': 'Portuguese',
            'it': 'Italian',
            'nl': 'Dutch',
            'pl': 'Polish',
            'tr': 'Turkish',
            'vi': 'Vietnamese',
            'th': 'Thai',
            'id': 'Indonesian',
            'hi': 'Hindi'
        }
