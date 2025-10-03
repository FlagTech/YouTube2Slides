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

        prompt = f"""You are a professional translator. Translate the following subtitle segments from {source_name} to {target_name}.

IMPORTANT INSTRUCTIONS:
1. Translate each line accurately while maintaining natural language flow
2. Keep the subtitle format - each line should remain on its own line
3. Preserve the numbering format [0], [1], [2], etc.
4. Do NOT add any explanations, notes, or extra text
5. Output ONLY the translated text with the same numbering
6. Maintain appropriate subtitle length (typically under 42 characters per line for readability)
7. Use natural, conversational language suitable for video subtitles

Source text ({source_name}):
{text_block}

Translated text ({target_name}):"""

        return prompt

    def translate_batch(
        self,
        texts: List[str],
        source_lang: str,
        target_lang: str,
        provider: AIProvider,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        batch_size: int = 20
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
            batch_size: Number of texts per batch

        Returns:
            List of translated texts
        """
        if not texts:
            return []

        all_translations = []

        # Process in batches to avoid token limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

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

                all_translations.extend(translated_batch)

            except Exception as e:
                print(f"Translation batch {i//batch_size + 1} failed: {str(e)}")
                # Fallback: return original text if translation fails
                all_translations.extend(batch)

        return all_translations

    def _parse_translation_response(self, response_text: str, expected_count: int) -> List[str]:
        """Parse AI response and extract translated texts"""
        lines = response_text.strip().split('\n')
        translations = []

        for line in lines:
            line = line.strip()
            # Look for numbered format [0], [1], etc.
            if line.startswith('[') and ']' in line:
                # Extract text after the bracket
                try:
                    bracket_end = line.index(']')
                    text = line[bracket_end + 1:].strip()
                    translations.append(text)
                except:
                    pass

        # If parsing failed, try splitting by newlines
        if len(translations) != expected_count:
            translations = [line.strip() for line in lines if line.strip() and not line.startswith('[')]

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
