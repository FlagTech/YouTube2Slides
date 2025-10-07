"""
AI-powered translation service
Supports OpenAI, Claude, Gemini, and Ollama for high-quality translations
"""
import os
import requests
from typing import List, Dict, Optional
from services.ai_outline import AIProvider


class AITranslationService:
    """Translate text using AI models for better quality"""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def _get_translation_prompt(
        self,
        source_lang: str,
        target_lang: str,
        texts: List[str]
    ) -> str:
        """Generate translation prompt for AI"""

        # Language name mapping
        lang_names = {
            'en': 'English',
            'zh-TW': 'Traditional Chinese (繁體中文)',
            'zh-CN': 'Simplified Chinese (简体中文)',
            'ja': 'Japanese (日本語)',
            'ko': 'Korean (한국어)',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'ru': 'Russian',
            'pt': 'Portuguese',
            'it': 'Italian'
        }

        source_name = lang_names.get(source_lang, source_lang)
        target_name = lang_names.get(target_lang, target_lang)

        # Join all texts with markers
        text_block = ""
        for i, text in enumerate(texts):
            text_block += f"[{i}] {text}\n"

        prompt = f"""Translate these subtitles from {source_name} to {target_name}.

Rules:
1. Keep the [0], [1], [2] format
2. Translate naturally - do not add notes or explanations
3. Output only translations

{text_block}

Translations:"""

        return prompt

    def _calculate_optimal_batch_size(self, texts: List[str]) -> int:
        """
        Calculate optimal batch size based on text length

        Rationale:
        - Longer texts consume more tokens
        - Smaller batches for long texts prevent context window overflow
        - Larger batches for short texts improve efficiency
        """
        if not texts:
            return 20

        # Calculate average text length
        avg_length = sum(len(text) for text in texts) / len(texts)

        # Adaptive batch sizing - more conservative for long texts
        if avg_length < 30:
            # Short subtitles (e.g., "Yes", "Hello")
            return 25
        elif avg_length < 60:
            # Medium subtitles (typical)
            return 15
        elif avg_length < 100:
            # Long subtitles
            return 10
        elif avg_length < 150:
            # Very long subtitles
            return 5
        else:
            # Extremely long subtitles (200+ chars)
            return 3

    def translate_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
        provider: AIProvider,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        batch_size: int = None
    ) -> List[str]:
        """
        Translate a batch of texts using AI

        Args:
            texts: List of text strings to translate
            source_lang: Source language code
            target_lang: Target language code
            provider: AI provider to use
            model: Specific model name
            api_key: API key (optional, will use env var if not provided)
            batch_size: Number of texts per batch (auto-calculated if None)

        Returns:
            List of translated texts
        """
        if not texts:
            return []

        # Auto-calculate optimal batch size if not provided
        if batch_size is None:
            batch_size = self._calculate_optimal_batch_size(texts)
            print(f"[AI Translator] Auto-calculated batch size: {batch_size} (avg text length: {sum(len(t) for t in texts) / len(texts):.1f})")

        all_translations = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        # Process in batches to avoid token limits
        for batch_num, i in enumerate(range(0, len(texts), batch_size), 1):
            batch = texts[i:i + batch_size]
            print(f"[AI Translator] Processing batch {batch_num}/{total_batches} ({len(batch)} items)")

            try:
                if provider == AIProvider.OPENAI:
                    translated_batch = self._translate_with_openai(
                        batch, source_lang, target_lang, model, api_key
                    )
                elif provider == AIProvider.CLAUDE:
                    translated_batch = self._translate_with_claude(
                        batch, source_lang, target_lang, model, api_key
                    )
                elif provider == AIProvider.GEMINI:
                    translated_batch = self._translate_with_gemini(
                        batch, source_lang, target_lang, model, api_key
                    )
                elif provider == AIProvider.OLLAMA:
                    translated_batch = self._translate_with_ollama(
                        batch, source_lang, target_lang, model, api_key
                    )
                else:
                    raise ValueError(f"Unsupported provider: {provider}")

                # Verify translation count matches
                if len(translated_batch) != len(batch):
                    print(f"[WARNING] Batch {batch_num}: Expected {len(batch)} translations, got {len(translated_batch)}")
                    print(f"[WARNING] Original batch: {batch[:3]}...")
                    print(f"[WARNING] Translated batch: {translated_batch[:3] if translated_batch else 'EMPTY'}...")

                    # Pad with original text if missing translations
                    while len(translated_batch) < len(batch):
                        missing_index = len(translated_batch)
                        print(f"[WARNING] Missing translation at index {missing_index}, using original: '{batch[missing_index]}'")
                        translated_batch.append(batch[missing_index])

                all_translations.extend(translated_batch)
                print(f"[AI Translator] Batch {batch_num}/{total_batches} completed: {len(translated_batch)} translations")

            except Exception as e:
                print(f"[ERROR] Translation batch {batch_num}/{total_batches} failed: {str(e)}")
                import traceback
                traceback.print_exc()
                # Fallback: return original text if translation fails
                all_translations.extend(batch)

        print(f"[AI Translator] Translation complete: {len(all_translations)}/{len(texts)} items")
        return all_translations

    def _parse_translation_response(self, response_text: str, expected_count: int) -> List[str]:
        """Parse AI response and extract translated texts"""
        lines = response_text.strip().split('\n')
        translations = []

        print(f"[Parser] Raw response length: {len(response_text)} chars, {len(lines)} lines")
        print(f"[Parser] Expected {expected_count} translations")

        # Method 1: Try to extract numbered format [0], [1], etc.
        for line in lines:
            line = line.strip()
            # Look for numbered format [0], [1], etc.
            if line.startswith('[') and ']' in line:
                # Extract text after the bracket
                try:
                    bracket_end = line.index(']')
                    text = line[bracket_end + 1:].strip()
                    if text:  # Only add non-empty translations
                        translations.append(text)
                except:
                    pass

        print(f"[Parser] Method 1 (numbered): Found {len(translations)} translations")

        # Method 2: If parsing failed or count mismatch, try alternative parsing
        if len(translations) != expected_count:
            print(f"[Parser] Count mismatch, trying alternative parsing...")

            # Try to match by pattern more flexibly
            import re
            pattern = r'\[\s*(\d+)\s*\]\s*(.+?)(?=\n\[|$)'
            matches = re.findall(pattern, response_text, re.DOTALL)

            if matches:
                # Sort by index to ensure order
                matches.sort(key=lambda x: int(x[0]))
                alternative_translations = [match[1].strip() for match in matches]
                print(f"[Parser] Method 2 (regex): Found {len(alternative_translations)} translations")

                if len(alternative_translations) == expected_count:
                    translations = alternative_translations
                elif len(alternative_translations) > len(translations):
                    # Use regex result if it's better
                    translations = alternative_translations

        # Method 3: Last resort - split by lines and filter
        if len(translations) != expected_count:
            print(f"[Parser] Still mismatch, trying line-by-line parsing...")
            line_translations = []
            for line in lines:
                line = line.strip()
                # Skip empty lines and common AI response prefixes
                if not line or line.startswith(('Translation', 'Translated', 'Here', 'Sure', 'Note:')):
                    continue
                # Remove numbering if present
                line = re.sub(r'^\[\d+\]\s*', '', line)
                if line:
                    line_translations.append(line)

            print(f"[Parser] Method 3 (lines): Found {len(line_translations)} translations")

            if len(line_translations) == expected_count:
                translations = line_translations

        # Final verification
        if len(translations) != expected_count:
            print(f"[WARNING] Final count mismatch: expected {expected_count}, got {len(translations)}")
            print(f"[WARNING] First 5 lines of response:\n{chr(10).join(lines[:5])}")

        return translations

    def _translate_with_openai(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> List[str]:
        """Translate using OpenAI"""
        from openai import OpenAI

        used_api_key = api_key or self.openai_api_key
        if not used_api_key:
            raise ValueError("OPENAI_API_KEY not configured")

        client = OpenAI(api_key=used_api_key)
        model_name = model or "gpt-4o-mini"

        prompt = self._get_translation_prompt(source_lang, target_lang, texts)

        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a professional translator specializing in subtitle translation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=4000
        )

        response_text = response.choices[0].message.content
        translations = self._parse_translation_response(response_text, len(texts))

        # Fallback if parsing failed
        if len(translations) != len(texts):
            print(f"Warning: Expected {len(texts)} translations, got {len(translations)}")
            translations = texts

        return translations

    def _translate_with_claude(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> List[str]:
        """Translate using Claude"""
        from anthropic import Anthropic

        used_api_key = api_key or self.claude_api_key
        if not used_api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        client = Anthropic(api_key=used_api_key)
        model_name = model or "claude-sonnet-4-5-20250929"

        prompt = self._get_translation_prompt(source_lang, target_lang, texts)

        message = client.messages.create(
            model=model_name,
            max_tokens=4000,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text
        translations = self._parse_translation_response(response_text, len(texts))

        if len(translations) != len(texts):
            print(f"Warning: Expected {len(texts)} translations, got {len(translations)}")
            translations = texts

        return translations

    def _translate_with_gemini(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> List[str]:
        """Translate using Gemini"""
        import google.generativeai as genai

        used_api_key = api_key or self.gemini_api_key
        if not used_api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        genai.configure(api_key=used_api_key)
        model_name = model or "models/gemini-2.5-flash"

        model_instance = genai.GenerativeModel(model_name)
        prompt = self._get_translation_prompt(source_lang, target_lang, texts)

        response = model_instance.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.3,
                max_output_tokens=4000,
            )
        )

        response_text = response.text
        translations = self._parse_translation_response(response_text, len(texts))

        if len(translations) != len(texts):
            print(f"Warning: Expected {len(texts)} translations, got {len(translations)}")
            translations = texts

        return translations

    def _translate_with_ollama(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> List[str]:
        """Translate using Ollama"""
        model_name = model or "llama3.2"
        prompt = self._get_translation_prompt(source_lang, target_lang, texts)

        url = f"{self.ollama_base_url}/api/generate"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": 4000
            }
        }

        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()

        result = response.json()
        response_text = result.get("response", "")
        translations = self._parse_translation_response(response_text, len(texts))

        if len(translations) != len(texts):
            print(f"Warning: Expected {len(texts)} translations, got {len(translations)}")
            translations = texts

        return translations
