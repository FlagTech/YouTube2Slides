"""
AI-powered video outline generation service
Supports OpenAI, Claude (Anthropic), Gemini, and Ollama
"""
import os
import requests
from typing import List, Dict, Optional
from enum import Enum


class AIProvider(str, Enum):
    """Supported AI providers"""
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    OLLAMA = "ollama"


class AIOutlineService:
    """Generate video outlines using various AI providers"""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def generate_outline(
        self,
        video_title: str,
        video_description: str,
        subtitles: List[str],
        provider: AIProvider = AIProvider.OPENAI,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Generate video outline using AI

        Args:
            video_title: Video title
            video_description: Video description
            subtitles: List of subtitle texts
            provider: AI provider to use
            model: Specific model to use (optional)

        Returns:
            Dict with outline, summary, and key points
        """
        if provider == AIProvider.OPENAI:
            return self._generate_with_openai(video_title, video_description, subtitles, model, api_key)
        elif provider == AIProvider.CLAUDE:
            return self._generate_with_claude(video_title, video_description, subtitles, model, api_key)
        elif provider == AIProvider.GEMINI:
            return self._generate_with_gemini(video_title, video_description, subtitles, model, api_key)
        elif provider == AIProvider.OLLAMA:
            return self._generate_with_ollama(video_title, video_description, subtitles, model, api_key)
        else:
            raise ValueError(f"Unsupported AI provider: {provider}")

    def _prepare_prompt(self, video_title: str, video_description: str, subtitles: List[str]) -> str:
        """Prepare the prompt for AI"""
        # Intelligently sample subtitles to stay within token limits while covering the entire video
        total_segments = len(subtitles)

        # Strategy: Use all subtitles if <= 300, otherwise sample evenly across the video
        if total_segments <= 300:
            # Use all subtitles
            selected_subtitles = subtitles
            subtitle_note = f"完整字幕（共 {total_segments} 段）"
        else:
            # Sample evenly across the video to maintain context
            # Take first 100, middle 100, and last 100 segments
            first_part = subtitles[:100]
            middle_start = (total_segments - 100) // 2
            middle_part = subtitles[middle_start:middle_start + 100]
            last_part = subtitles[-100:]

            selected_subtitles = first_part + ["...[中間省略部分內容]..."] + middle_part + ["...[中間省略部分內容]..."] + last_part
            subtitle_note = f"字幕摘要（從總共 {total_segments} 段中均勻採樣 300 段：開頭、中段、結尾）"

        subtitle_text = "\n".join(selected_subtitles)

        prompt = f"""請分析以下 YouTube 影片的內容，並生成詳細的大綱。

影片標題：{video_title}

影片描述：
{video_description[:500]}

{subtitle_note}：
{subtitle_text}

請提供：
1. **影片摘要**（2-3句話概述影片主要內容）
2. **關鍵重點**（列出3-5個主要重點，每個用一句話說明）
3. **詳細大綱**（按時間順序列出主要章節，包含主題和簡短說明）

請以繁體中文回覆，使用清晰的結構化格式。"""

        return prompt

    def _generate_with_openai(
        self,
        video_title: str,
        video_description: str,
        subtitles: List[str],
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Dict:
        """Generate outline using OpenAI API"""
        # Use provided API key or fallback to environment variable
        used_api_key = api_key or self.openai_api_key
        if not used_api_key:
            raise ValueError("OPENAI_API_KEY not configured")

        try:
            from openai import OpenAI

            client = OpenAI(api_key=used_api_key)
            model_name = model or "gpt-4o-mini"

            prompt = self._prepare_prompt(video_title, video_description, subtitles)

            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "你是一個專業的影片內容分析助手，擅長從字幕和描述中提取關鍵資訊並生成結構化大綱。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )

            outline_text = response.choices[0].message.content

            return {
                "provider": "openai",
                "model": model_name,
                "outline": outline_text,
                "tokens_used": response.usage.total_tokens
            }

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    def _generate_with_claude(
        self,
        video_title: str,
        video_description: str,
        subtitles: List[str],
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Dict:
        """Generate outline using Claude API"""
        # Use provided API key or fallback to environment variable
        used_api_key = api_key or self.claude_api_key
        if not used_api_key:
            raise ValueError("ANTHROPIC_API_KEY not configured")

        try:
            from anthropic import Anthropic

            client = Anthropic(api_key=used_api_key)
            model_name = model or "claude-sonnet-4-5-20250929"

            prompt = self._prepare_prompt(video_title, video_description, subtitles)

            message = client.messages.create(
                model=model_name,
                max_tokens=2000,
                temperature=0.7,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            outline_text = message.content[0].text

            return {
                "provider": "claude",
                "model": model_name,
                "outline": outline_text,
                "tokens_used": message.usage.input_tokens + message.usage.output_tokens
            }

        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")

    def _generate_with_gemini(
        self,
        video_title: str,
        video_description: str,
        subtitles: List[str],
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Dict:
        """Generate outline using Gemini API"""
        # Use provided API key or fallback to environment variable
        used_api_key = api_key or self.gemini_api_key
        if not used_api_key:
            raise ValueError("GEMINI_API_KEY not configured")

        try:
            import google.generativeai as genai

            genai.configure(api_key=used_api_key)
            model_name = model or "models/gemini-2.5-flash"

            model_instance = genai.GenerativeModel(model_name)

            prompt = self._prepare_prompt(video_title, video_description, subtitles)

            response = model_instance.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2000,
                )
            )

            outline_text = response.text

            return {
                "provider": "gemini",
                "model": model_name,
                "outline": outline_text,
                "tokens_used": response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else None
            }

        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

    def _generate_with_ollama(
        self,
        video_title: str,
        video_description: str,
        subtitles: List[str],
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ) -> Dict:
        """Generate outline using Ollama (local LLM)"""
        try:
            model_name = model or "llama3.2"

            prompt = self._prepare_prompt(video_title, video_description, subtitles)

            # Ollama API endpoint
            url = f"{self.ollama_base_url}/api/generate"

            payload = {
                "model": model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 2000
                }
            }

            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()

            result = response.json()
            outline_text = result.get("response", "")

            return {
                "provider": "ollama",
                "model": model_name,
                "outline": outline_text,
                "tokens_used": result.get("eval_count", 0)
            }

        except requests.exceptions.ConnectionError:
            raise Exception("無法連線到 Ollama。請確認 Ollama 服務已啟動（http://localhost:11434）")
        except requests.exceptions.Timeout:
            raise Exception("Ollama 請求逾時。模型可能需要更長時間來生成回應。")
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")

    def get_ollama_models(self) -> List[Dict[str, str]]:
        """Get list of available Ollama models"""
        try:
            url = f"{self.ollama_base_url}/api/tags"
            response = requests.get(url, timeout=5)
            response.raise_for_status()

            result = response.json()
            models = []

            if "models" in result:
                for model_info in result["models"]:
                    models.append({
                        "name": model_info.get("name", ""),
                        "size": model_info.get("size", 0),
                        "modified_at": model_info.get("modified_at", "")
                    })

            return models

        except requests.exceptions.ConnectionError:
            return []
        except Exception as e:
            print(f"Failed to get Ollama models: {str(e)}")
            return []

    def get_available_providers(self) -> List[str]:
        """Get list of configured AI providers"""
        providers = []
        if self.openai_api_key:
            providers.append("openai")
        if self.claude_api_key:
            providers.append("claude")
        if self.gemini_api_key:
            providers.append("gemini")

        # Check if Ollama is available
        try:
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                providers.append("ollama")
        except:
            pass

        return providers
