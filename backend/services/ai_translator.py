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

        prompt = f"""Translate ALL {len(texts)} subtitles from {source_name} to {target_name}.

IMPORTANT: You MUST translate ALL {len(texts)} items below.

Rules:
1. Keep the [0], [1], [2] numbering format
2. Translate naturally - do not add notes or explanations
3. Output ONLY translations, nothing else
4. Make sure to translate ALL items

Input ({len(texts)} items):
{text_block}

Output ({len(texts)} translations):"""

        return prompt

    def _get_target_char_count(self, provider: Optional[AIProvider] = None) -> int:
        """
        Get target character count per batch based on provider

        Returns:
            Target total character count for each batch
        """
        if provider == AIProvider.OLLAMA:
            # Conservative for Ollama local models
            # Target: 300 chars = ~1-5 subtitles (typically 3-5, dynamic based on length)
            return 300
        else:
            # More generous for cloud APIs
            return 1000  # ~1000 chars = ~15-25 subtitles

    def _calculate_batch_by_char_count(self, texts: List[str], provider: Optional[AIProvider] = None, max_batch_size: int = 5) -> int:
        """
        Calculate batch size based on accumulated character count

        Strategy:
        - Accumulate characters until reaching target count
        - Ensures consistent processing load per batch
        - Better handles mixed-length subtitles
        - Limits maximum batch size for safety

        Args:
            texts: List of text strings to analyze
            provider: AI provider (affects target char count)
            max_batch_size: Maximum number of items per batch (default: 5)

        Returns:
            Number of texts to include in this batch
        """
        if not texts:
            return 0

        target_chars = self._get_target_char_count(provider)
        accumulated_chars = 0
        batch_count = 0

        for text in texts:
            text_length = len(text)

            # If adding this text would exceed target, decide whether to include it
            if accumulated_chars + text_length > target_chars:
                # If we haven't added any texts yet, include at least one
                if batch_count == 0:
                    batch_count = 1
                break

            # Add this text to the batch
            accumulated_chars += text_length
            batch_count += 1

            # Enforce maximum batch size limit
            if batch_count >= max_batch_size:
                break

        # Ensure at least 1 text per batch, but not more than max_batch_size
        return max(1, min(batch_count, max_batch_size))

    def _calculate_optimal_batch_size(self, texts: List[str], provider: Optional[AIProvider] = None) -> int:
        """
        Calculate optimal batch size based on text length and provider
        (Legacy method - kept for backward compatibility)

        Rationale:
        - Longer texts consume more tokens
        - Smaller batches for long texts prevent context window overflow
        - Larger batches for short texts improve efficiency
        - Ollama local models have stricter output token limits
        """
        if not texts:
            return 20

        # Calculate average text length
        avg_length = sum(len(text) for text in texts) / len(texts)

        # Ollama models need much smaller batches due to output token limits
        if provider == AIProvider.OLLAMA:
            # Very conservative batch sizes for Ollama to ensure complete translations
            if avg_length < 20:
                return 3  # Very short texts
            elif avg_length < 40:
                return 3  # Short texts
            elif avg_length < 60:
                return 2  # Medium texts
            else:
                return 2  # Long texts

        # For cloud providers (OpenAI, Claude, Gemini) - more generous
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
        batch_size: int = None,
        use_dynamic_batching: bool = True
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
            use_dynamic_batching: If True, recalculate batch size for each batch based on remaining texts

        Returns:
            List of translated texts
        """
        if not texts:
            return []

        all_translations = []
        remaining_texts = texts[:]
        batch_num = 0

        # Calculate initial batch size if not provided
        if batch_size is None and not use_dynamic_batching:
            batch_size = self._calculate_optimal_batch_size(texts, provider)
            avg_len = sum(len(t) for t in texts) / len(texts)
            print(f"[AI Translator] Initial batch size: {batch_size} (provider: {provider.value}, avg text length: {avg_len:.1f})")

        # Process in batches to avoid token limits
        while remaining_texts:
            batch_num += 1

            # Dynamic batching: recalculate batch size for remaining texts based on character count
            if use_dynamic_batching:
                current_batch_size = self._calculate_batch_by_char_count(remaining_texts, provider)
                batch_chars = sum(len(t) for t in remaining_texts[:current_batch_size])
                target_chars = self._get_target_char_count(provider)
                print(f"[AI Translator] Batch {batch_num}: {current_batch_size} items ({batch_chars}/{target_chars} chars, {len(remaining_texts)} remaining)")
            else:
                current_batch_size = batch_size

            # Get current batch
            batch = remaining_texts[:current_batch_size]
            remaining_texts = remaining_texts[current_batch_size:]

            # Calculate total batches estimate (for display)
            if use_dynamic_batching:
                estimated_remaining_batches = (len(remaining_texts) + current_batch_size - 1) // current_batch_size if current_batch_size > 0 else 0
                total_estimate = batch_num + estimated_remaining_batches
                print(f"[AI Translator] Processing batch {batch_num}/~{total_estimate} ({len(batch)} items, {len(remaining_texts)} remaining)")
            else:
                total_batches = batch_num + ((len(remaining_texts) + current_batch_size - 1) // current_batch_size)
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
                print(f"[AI Translator] Batch {batch_num} completed: {len(translated_batch)} translations")

            except Exception as e:
                print(f"[ERROR] Translation batch {batch_num} failed: {str(e)}")
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

        # Calculate required output tokens (estimate: 3x input for Chinese)
        estimated_output_chars = sum(len(text) for text in texts) * 3
        estimated_output_tokens = estimated_output_chars // 2  # Rough estimate
        # Use larger buffer and higher minimum for Ollama
        num_predict = max(3000, min(8000, estimated_output_tokens + 1000))  # Add generous buffer

        url = f"{self.ollama_base_url}/api/generate"
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3,
                "num_predict": num_predict
            }
        }

        print(f"[Ollama] Batch size: {len(texts)}, num_predict: {num_predict}")

        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()

        result = response.json()
        response_text = result.get("response", "")
        translations = self._parse_translation_response(response_text, len(texts))

        if len(translations) != len(texts):
            print(f"Warning: Expected {len(texts)} translations, got {len(translations)}")
            translations = texts

        return translations
