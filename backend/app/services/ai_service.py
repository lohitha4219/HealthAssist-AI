import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import json
import logging
from typing import AsyncGenerator, Dict, List, Optional

import httpx

from app.core.config import Settings, get_settings

logger = logging.getLogger("healthassist.ai")

GENERAL_SYSTEM_PROMPT = (
    "You are HealthAssist AI, an expert, empathetic, and trustworthy healthcare information "
    "and personal health assistant. "
    "Your primary mission is to support patients with clear, accessible healthcare education, "
    "symptom understanding, medical terminology and laboratory report explanations, preventive "
    "wellness, general treatment precautions, and guidance on finding verified hospitals and "
    "specialist doctors across Andhra Pradesh (including Tirupati, Visakhapatnam, Vijayawada, "
    "Guntur, Kurnool, Nellore, Kadapa, Anantapur, Chittoor, and Rajahmundry) to book appointments. "
    "\n\nCRITICAL MEDICAL SAFETY RULES:\n"
    "1. Never claim to make a definitive medical diagnosis.\n"
    "2. Never prescribe medications or suggest specific drug dosages.\n"
    "3. Never invent medical facts, lab values, or doctor contact numbers.\n"
    "4. If the user mentions urgent red-flag warning signs (e.g., severe or crushing chest pain, "
    "sudden difficulty breathing, sudden face drooping or speech difficulty, loss of consciousness, "
    "uncontrolled bleeding, severe trauma, or acute anaphylactic reaction), clearly and immediately "
    "urge them to seek emergency medical attention (such as calling 108 / 112 in India or going to "
    "the nearest emergency department immediately).\n"
    "5. Always recommend consulting a qualified, licensed healthcare professional for individual "
    "clinical evaluation, diagnosis, and treatment planning.\n"
    "6. Protect user privacy and maintain a compassionate, professional tone."
)

GEMINI_SETUP_HINT = (
    "To use Google Gemini Cloud AI: get a free API key at https://aistudio.google.com/ "
    "and set GEMINI_API_KEY in backend/.env. Alternatively, configure AI_PROVIDER=openai_compatible "
    "or run a local llama.cpp / Ollama server."
)

INTEL_MAC_SETUP_HINT = (
    "Recommended: configure Google Gemini cloud AI by setting GEMINI_API_KEY in backend/.env "
    "(free at https://aistudio.google.com/). On macOS 13 Intel (8 GB RAM), you can also run "
    "`llama-server -m ./models/qwen2.5-1.5b-instruct-q4_k_m.gguf --port 8080`, or configure "
    "`AI_PROVIDER=openai_compatible`."
)


class AIUnavailableError(Exception):
    def __init__(self, detail: str, status_code: int = 503):
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


@dataclass
class AIStatus:
    available: bool
    provider: str
    configured_provider: str
    model: Optional[str]
    base_url: Optional[str]
    status: str
    detail: str
    setup_hint: str
    checked_at: datetime


@dataclass
class AICompletionResult:
    content: str
    provider: str
    model: str


class LocalAIService:
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def check_gemini(self) -> AIStatus:
        now = datetime.now(timezone.utc)
        api_key = (self.settings.GEMINI_API_KEY or "").strip()
        model = (self.settings.GEMINI_MODEL or "").strip() or "gemini-2.5-flash"

        if not api_key:
            return AIStatus(
                available=False,
                provider="gemini",
                configured_provider=self.settings.AI_PROVIDER,
                model=model,
                base_url="https://generativelanguage.googleapis.com",
                status="unconfigured",
                detail=(
                    "GEMINI_API_KEY is not configured in backend/.env. "
                    "Get a free key from Google AI Studio (https://aistudio.google.com/) "
                    "and set GEMINI_API_KEY in backend/.env."
                ),
                setup_hint=GEMINI_SETUP_HINT,
                checked_at=now,
            )

        return AIStatus(
            available=True,
            provider="gemini",
            configured_provider=self.settings.AI_PROVIDER,
            model=model,
            base_url="https://generativelanguage.googleapis.com",
            status="online",
            detail=f"Google Gemini Cloud AI is configured and ready with model '{model}'.",
            setup_hint=GEMINI_SETUP_HINT,
            checked_at=now,
        )

    def check_openai_compatible(self) -> AIStatus:
        now = datetime.now(timezone.utc)
        base_url = (self.settings.AI_BASE_URL or "").strip().rstrip("/")
        model = (self.settings.AI_MODEL or "").strip() or None
        api_key = (self.settings.AI_API_KEY or "").strip()
        if not base_url or not api_key or not model:
            return AIStatus(
                available=False,
                provider="openai_compatible",
                configured_provider=self.settings.AI_PROVIDER,
                model=model,
                base_url=base_url or None,
                status="unconfigured",
                detail="AI_BASE_URL, AI_API_KEY, and AI_MODEL are required for openai_compatible mode.",
                setup_hint=INTEL_MAC_SETUP_HINT,
                checked_at=now,
            )
        return AIStatus(
            available=True,
            provider="openai_compatible",
            configured_provider=self.settings.AI_PROVIDER,
            model=model,
            base_url=base_url,
            status="configured",
            detail=f"Configured OpenAI-compatible provider with model '{model}'.",
            setup_hint=INTEL_MAC_SETUP_HINT,
            checked_at=now,
        )

    async def check_llamacpp(self) -> AIStatus:
        base_url = self.settings.LLAMACPP_BASE_URL.rstrip("/")
        now = datetime.now(timezone.utc)
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                health_resp = await client.get(f"{base_url}/health")
                if health_resp.status_code != 200:
                    return AIStatus(
                        available=False,
                        provider="llamacpp",
                        configured_provider=self.settings.AI_PROVIDER,
                        model=self.settings.LLAMACPP_MODEL,
                        base_url=base_url,
                        status="unhealthy",
                        detail=f"llama-server returned HTTP {health_resp.status_code}",
                        setup_hint=INTEL_MAC_SETUP_HINT,
                        checked_at=now,
                    )

                model_name = self.settings.LLAMACPP_MODEL
                try:
                    models_resp = await client.get(f"{base_url}/v1/models")
                    if models_resp.status_code == 200:
                        data = models_resp.json().get("data") or []
                        if data and isinstance(data[0], dict) and data[0].get("id"):
                            model_name = str(data[0]["id"])
                except Exception:
                    pass

                return AIStatus(
                    available=True,
                    provider="llamacpp",
                    configured_provider=self.settings.AI_PROVIDER,
                    model=model_name,
                    base_url=base_url,
                    status="online",
                    detail="llama.cpp local inference server is ready.",
                    setup_hint=INTEL_MAC_SETUP_HINT,
                    checked_at=now,
                )
        except httpx.RequestError:
            return AIStatus(
                available=False,
                provider="llamacpp",
                configured_provider=self.settings.AI_PROVIDER,
                model=self.settings.LLAMACPP_MODEL,
                base_url=base_url,
                status="offline",
                detail="Cannot connect to llama.cpp server on configured local port.",
                setup_hint=INTEL_MAC_SETUP_HINT,
                checked_at=now,
            )

    async def check_ollama(self) -> AIStatus:
        base_url = self.settings.OLLAMA_BASE_URL.rstrip("/")
        target_model = self.settings.OLLAMA_MODEL
        now = datetime.now(timezone.utc)
        try:
            async with httpx.AsyncClient(timeout=3.0) as client:
                resp = await client.get(f"{base_url}/api/tags")
                if resp.status_code != 200:
                    return AIStatus(
                        available=False,
                        provider="ollama",
                        configured_provider=self.settings.AI_PROVIDER,
                        model=target_model,
                        base_url=base_url,
                        status="unhealthy",
                        detail=f"Ollama returned HTTP {resp.status_code}",
                        setup_hint=INTEL_MAC_SETUP_HINT,
                        checked_at=now,
                    )
                models = [
                    m.get("name", "")
                    for m in (resp.json().get("models") or [])
                    if isinstance(m, dict)
                ]
                model_installed = any(
                    m == target_model or m.startswith(f"{target_model.split(':')[0]}")
                    for m in models
                )
                if not models or not model_installed:
                    return AIStatus(
                        available=False,
                        provider="ollama",
                        configured_provider=self.settings.AI_PROVIDER,
                        model=target_model,
                        base_url=base_url,
                        status="model_missing",
                        detail=(
                            f"Ollama is running, but model '{target_model}' is not installed. "
                            f"Run `ollama pull {target_model}`."
                        ),
                        setup_hint=INTEL_MAC_SETUP_HINT,
                        checked_at=now,
                    )

                return AIStatus(
                    available=True,
                    provider="ollama",
                    configured_provider=self.settings.AI_PROVIDER,
                    model=target_model,
                    base_url=base_url,
                    status="online",
                    detail=f"Ollama is online with model '{target_model}'.",
                    setup_hint=INTEL_MAC_SETUP_HINT,
                    checked_at=now,
                )
        except httpx.RequestError:
            return AIStatus(
                available=False,
                provider="ollama",
                configured_provider=self.settings.AI_PROVIDER,
                model=target_model,
                base_url=base_url,
                status="offline",
                detail="Cannot connect to Ollama local service.",
                setup_hint=INTEL_MAC_SETUP_HINT,
                checked_at=now,
            )

    async def get_health(self) -> AIStatus:
        mode = (self.settings.AI_PROVIDER or "auto").strip().lower()

        if mode == "gemini":
            return self.check_gemini()
        if mode == "openai_compatible":
            return self.check_openai_compatible()
        if mode == "llamacpp":
            return await self.check_llamacpp()
        if mode == "ollama":
            return await self.check_ollama()

        # "auto" resolution order:
        # 1. Google Gemini (Cloud AI preferred)
        gemini_status = self.check_gemini()
        if gemini_status.available:
            return gemini_status

        # 2. Generic OpenAI-compatible endpoint
        compat_status = self.check_openai_compatible()
        if compat_status.available:
            return compat_status

        # 3. Local llama.cpp
        llama_status = await self.check_llamacpp()
        if llama_status.available:
            return llama_status

        # 4. Local Ollama
        ollama_status = await self.check_ollama()
        if ollama_status.available or ollama_status.status == "model_missing":
            return ollama_status

        # None available
        return AIStatus(
            available=False,
            provider="auto",
            configured_provider=self.settings.AI_PROVIDER,
            model=self.settings.GEMINI_MODEL,
            base_url="https://generativelanguage.googleapis.com",
            status="offline",
            detail=(
                "No AI server is currently configured. To enable cloud AI instantly: "
                "get a free Gemini API key from https://aistudio.google.com/ and set "
                "GEMINI_API_KEY in backend/.env. Alternatively, start a local llama.cpp server "
                "on port 8080 or Ollama on port 11434."
            ),
            setup_hint=GEMINI_SETUP_HINT,
            checked_at=datetime.now(timezone.utc),
        )

    async def generate_chat_reply(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = GENERAL_SYSTEM_PROMPT,
    ) -> AICompletionResult:
        health = await self.get_health()
        if not health.available:
            raise AIUnavailableError(
                f"{health.detail} {health.setup_hint}", status_code=503
            )

        bounded = messages[-self.settings.AI_MAX_CONTEXT_MESSAGES :]

        if health.provider == "gemini":
            return await self._call_gemini(
                messages=bounded,
                system_prompt=system_prompt,
                model_name=health.model or self.settings.GEMINI_MODEL,
            )

        full_messages = [{"role": "system", "content": system_prompt}, *bounded]

        if health.provider == "llamacpp":
            return await self._call_openai_chat(
                base_url=self.settings.LLAMACPP_BASE_URL.rstrip("/"),
                model=health.model or self.settings.LLAMACPP_MODEL,
                messages=full_messages,
                provider_label="llamacpp",
                api_key=None,
            )
        if health.provider == "openai_compatible":
            return await self._call_openai_chat(
                base_url=(self.settings.AI_BASE_URL or "").rstrip("/"),
                model=health.model or (self.settings.AI_MODEL or ""),
                messages=full_messages,
                provider_label="openai_compatible",
                api_key=self.settings.AI_API_KEY,
            )
        return await self._call_ollama(full_messages, health.model or self.settings.OLLAMA_MODEL)

    async def generate_chat_stream(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = GENERAL_SYSTEM_PROMPT,
    ) -> AsyncGenerator[str, None]:
        health = await self.get_health()
        if not health.available:
            raise AIUnavailableError(
                f"{health.detail} {health.setup_hint}", status_code=503
            )

        bounded = messages[-self.settings.AI_MAX_CONTEXT_MESSAGES :]

        if health.provider == "gemini":
            async for chunk in self._stream_gemini(
                messages=bounded,
                system_prompt=system_prompt,
                model_name=health.model or self.settings.GEMINI_MODEL,
            ):
                yield chunk
            return

        full_messages = [{"role": "system", "content": system_prompt}, *bounded]
        if health.provider in ("llamacpp", "openai_compatible"):
            base_url = (
                self.settings.LLAMACPP_BASE_URL.rstrip("/")
                if health.provider == "llamacpp"
                else (self.settings.AI_BASE_URL or "").rstrip("/")
            )
            api_key = self.settings.AI_API_KEY if health.provider == "openai_compatible" else None
            model = health.model or (
                self.settings.LLAMACPP_MODEL
                if health.provider == "llamacpp"
                else (self.settings.AI_MODEL or "")
            )
            async for chunk in self._stream_openai_chat(
                base_url=base_url,
                model=model,
                messages=full_messages,
                api_key=api_key,
            ):
                yield chunk
            return

        # Fallback non-streaming for Ollama if streaming not implemented
        res = await self._call_ollama(full_messages, health.model or self.settings.OLLAMA_MODEL)
        yield res.content

    async def _call_gemini(
        self,
        *,
        messages: List[Dict[str, str]],
        system_prompt: str,
        model_name: str,
    ) -> AICompletionResult:
        from google import genai
        from google.genai import types
        from google.genai.errors import APIError

        api_key = (self.settings.GEMINI_API_KEY or "").strip()
        if not api_key:
            raise AIUnavailableError("GEMINI_API_KEY is not configured.", status_code=503)

        client = genai.Client(api_key=api_key)

        contents = []
        for msg in messages:
            role = "model" if msg.get("role") in ("assistant", "model") else "user"
            text_content = msg.get("content") or ""
            if text_content.strip():
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=text_content)],
                    )
                )

        if not contents:
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="Hello HealthAssist AI")],
                )
            )

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
            max_output_tokens=1000,
        )

        # Retry logic with backoff for transient errors
        last_exc: Optional[Exception] = None
        for attempt in range(2):
            try:
                response = await asyncio.wait_for(
                    client.aio.models.generate_content(
                        model=model_name,
                        contents=contents,
                        config=config,
                    ),
                    timeout=float(self.settings.AI_TIMEOUT_SECONDS),
                )
                text = (response.text or "").strip()
                if not text:
                    raise AIUnavailableError(
                        "Google Gemini returned an empty response. Please try again.",
                        status_code=502,
                    )
                return AICompletionResult(
                    content=text,
                    provider="gemini",
                    model=model_name,
                )
            except asyncio.TimeoutError as exc:
                last_exc = exc
                raise AIUnavailableError(
                    "Google Gemini API timed out while generating a response.",
                    status_code=504,
                ) from exc
            except APIError as exc:
                last_exc = exc
                if exc.code == 429 or "RESOURCE_EXHAUSTED" in str(exc):
                    raise AIUnavailableError(
                        "Google Gemini API rate limit reached. Please wait a moment and retry.",
                        status_code=429,
                    ) from exc
                if exc.code in (400, 401, 403) or "API_KEY_INVALID" in str(exc):
                    raise AIUnavailableError(
                        f"Google Gemini authentication error: {exc.message}. Please check GEMINI_API_KEY in backend/.env.",
                        status_code=502,
                    ) from exc
                if attempt == 0 and exc.code in (500, 502, 503):
                    await asyncio.sleep(1.0)
                    continue
                raise AIUnavailableError(
                    f"Google Gemini API error ({exc.code}): {exc.message}",
                    status_code=502,
                ) from exc
            except Exception as exc:
                last_exc = exc
                if attempt == 0:
                    await asyncio.sleep(1.0)
                    continue
                raise AIUnavailableError(
                    f"Gemini API request failed: {str(exc)}",
                    status_code=502,
                ) from exc

        raise AIUnavailableError(f"Gemini request failed: {str(last_exc)}", status_code=502)

    async def _stream_gemini(
        self,
        *,
        messages: List[Dict[str, str]],
        system_prompt: str,
        model_name: str,
    ) -> AsyncGenerator[str, None]:
        from google import genai
        from google.genai import types
        from google.genai.errors import APIError

        api_key = (self.settings.GEMINI_API_KEY or "").strip()
        client = genai.Client(api_key=api_key)

        contents = []
        for msg in messages:
            role = "model" if msg.get("role") in ("assistant", "model") else "user"
            text_content = msg.get("content") or ""
            if text_content.strip():
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part.from_text(text=text_content)],
                    )
                )

        if not contents:
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text="Hello HealthAssist AI")],
                )
            )

        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
            max_output_tokens=1000,
        )

        try:
            stream = await client.aio.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=config,
            )
            async for chunk in stream:
                chunk_text = getattr(chunk, "text", "") or ""
                if chunk_text:
                    yield chunk_text
        except asyncio.TimeoutError as exc:
            raise AIUnavailableError(
                "Google Gemini API timed out while streaming response.", status_code=504
            ) from exc
        except APIError as exc:
            if exc.code == 429 or "RESOURCE_EXHAUSTED" in str(exc):
                raise AIUnavailableError(
                    "Google Gemini API rate limit reached. Please wait a moment and retry.",
                    status_code=429,
                ) from exc
            if exc.code in (400, 401, 403) or "API_KEY_INVALID" in str(exc):
                raise AIUnavailableError(
                    f"Google Gemini authentication error: {exc.message}. Please check GEMINI_API_KEY in backend/.env.",
                    status_code=502,
                ) from exc
            raise AIUnavailableError(f"Gemini stream error ({exc.code}): {exc.message}", status_code=502) from exc
        except Exception as exc:
            raise AIUnavailableError(f"Gemini stream failed: {str(exc)}", status_code=502) from exc
        except Exception as exc:
            raise AIUnavailableError(f"Gemini stream failed: {str(exc)}", status_code=502) from exc

    async def _call_openai_chat(
        self,
        *,
        base_url: str,
        model: str,
        messages: List[Dict[str, str]],
        provider_label: str,
        api_key: Optional[str],
    ) -> AICompletionResult:
        endpoint = (
            f"{base_url}/chat/completions"
            if base_url.endswith("/v1")
            else f"{base_url}/v1/chat/completions"
        )
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000,
        }
        try:
            async with httpx.AsyncClient(
                timeout=float(self.settings.AI_TIMEOUT_SECONDS)
            ) as client:
                resp = await client.post(endpoint, json=payload, headers=headers)
        except httpx.TimeoutException as exc:
            raise AIUnavailableError(
                f"AI provider '{provider_label}' timed out while generating a response.",
                status_code=504,
            ) from exc
        except httpx.RequestError as exc:
            raise AIUnavailableError(
                f"Unable to reach AI provider '{provider_label}'.", status_code=503
            ) from exc

        if resp.status_code == 429:
            raise AIUnavailableError(
                "AI provider rate limit reached. Please retry in a moment.", status_code=429
            )
        if resp.status_code != 200:
            raise AIUnavailableError(
                f"AI provider '{provider_label}' returned HTTP {resp.status_code}.",
                status_code=502,
            )

        data = resp.json()
        choices = data.get("choices") or []
        content = ""
        if choices and isinstance(choices[0], dict):
            msg = choices[0].get("message") or {}
            content = (msg.get("content") or "").strip()
        if not content:
            raise AIUnavailableError(
                "AI provider returned an empty response. Please try again.", status_code=502
            )
        return AICompletionResult(
            content=content,
            provider=provider_label,
            model=str(data.get("model") or model),
        )

    async def _stream_openai_chat(
        self,
        *,
        base_url: str,
        model: str,
        messages: List[Dict[str, str]],
        api_key: Optional[str],
    ) -> AsyncGenerator[str, None]:
        endpoint = (
            f"{base_url}/chat/completions"
            if base_url.endswith("/v1")
            else f"{base_url}/v1/chat/completions"
        )
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 1000,
            "stream": True,
        }
        try:
            async with httpx.AsyncClient(
                timeout=float(self.settings.AI_TIMEOUT_SECONDS)
            ) as client:
                async with client.stream("POST", endpoint, json=payload, headers=headers) as resp:
                    if resp.status_code != 200:
                        raise AIUnavailableError(
                            f"AI stream returned HTTP {resp.status_code}", status_code=502
                        )
                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            item = json.loads(data_str)
                            delta = item.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if delta:
                                yield delta
                        except Exception:
                            continue
        except Exception as exc:
            raise AIUnavailableError(f"Stream error: {str(exc)}", status_code=502) from exc

    async def _call_ollama(
        self, messages: List[Dict[str, str]], model: str
    ) -> AICompletionResult:
        base_url = self.settings.OLLAMA_BASE_URL.rstrip("/")
        payload = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(
                timeout=float(self.settings.AI_TIMEOUT_SECONDS)
            ) as client:
                resp = await client.post(f"{base_url}/api/chat", json=payload)
        except httpx.TimeoutException as exc:
            raise AIUnavailableError(
                "Local Ollama server timed out while generating a response.",
                status_code=504,
            ) from exc
        except httpx.RequestError as exc:
            raise AIUnavailableError(
                "Lost connection to local Ollama server.", status_code=503
            ) from exc

        if resp.status_code == 404:
            raise AIUnavailableError(
                f"Ollama model '{model}' is not installed. Run `ollama pull {model}`.",
                status_code=503,
            )
        if resp.status_code != 200:
            raise AIUnavailableError(
                f"Ollama returned an unexpected status ({resp.status_code}).",
                status_code=502,
            )

        data = resp.json()
        content = ((data.get("message") or {}).get("content") or "").strip()
        if not content:
            raise AIUnavailableError(
                "Ollama returned an empty response. Please try again.", status_code=502
            )
        return AICompletionResult(
            content=content,
            provider="ollama",
            model=str(data.get("model") or model),
        )


def get_ai_service() -> LocalAIService:
    return LocalAIService()
