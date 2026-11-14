from __future__ import annotations

import json
import os
from functools import lru_cache
from typing import Any

import httpx
from groq import APIConnectionError, APIStatusError, AsyncGroq

GROQ_BASE = "https://api.groq.com/openai/v1"
CHAT_FAMILY_PREFIXES = (
    "meta-llama/llama-",
    "llama-",
    "qwen/",
    "deepseek/",
    "mistral/",
    "openai/gpt-oss-",
)
NON_CHAT_MARKERS = ("guard", "safeguard", "whisper", "audio", "speech", "orpheus", "embed", "transcribe")


class ProviderError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def _selected_model() -> str:
    configured = os.getenv("GROQ_MODEL")
    if configured:
        return configured
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ProviderError("Groq is not configured. Add GROQ_API_KEY in project settings.")
    try:
        response = httpx.get(f"{GROQ_BASE}/models", headers={"Authorization": f"Bearer {key}"}, timeout=15)
        response.raise_for_status()
        models = response.json().get("data", [])
        candidates: list[str] = []
        for model in models:
            if isinstance(model, dict) and isinstance(model.get("id"), str):
                candidates.append(model["id"])
        # The account catalog can include audio, guard and other specialized models. Select only
        # recognized general-purpose chat families, never the first arbitrary catalog entry.
        for prefix in CHAT_FAMILY_PREFIXES:
            for candidate in candidates:
                normalized = candidate.lower()
                if normalized.startswith(prefix) and not any(marker in normalized for marker in NON_CHAT_MARKERS):
                    return candidate
        raise ProviderError("No general-purpose chat model is available in the Groq catalog. Set GROQ_MODEL to a supported chat model.")
    except httpx.HTTPStatusError as exc:
        raise ProviderError(f"Could not retrieve the current Groq model catalog (HTTP {exc.response.status_code}).") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise ProviderError(f"Could not retrieve the current Groq model catalog: {type(exc).__name__}.") from exc


async def groq_json(system_prompt: str, user_content: str) -> dict[str, Any]:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise ProviderError("Groq is not configured. Add GROQ_API_KEY in project settings.")
    try:
        async with AsyncGroq(api_key=key, timeout=50, max_retries=1) as client:
            response = await client.chat.completions.create(
                model=_selected_model(),
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )
        content = response.choices[0].message.content
        if not isinstance(content, str):
            raise ProviderError("Groq returned a response without structured JSON content.")
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            raise ProviderError("Groq returned JSON in an unexpected format.")
        return parsed
    except APIStatusError as exc:
        raise ProviderError(f"Groq returned HTTP {exc.status_code}; check model access, limits and project settings.") from exc
    except APIConnectionError as exc:
        raise ProviderError(f"Groq request failed: {type(exc).__name__}.") from exc
    except (IndexError, json.JSONDecodeError) as exc:
        raise ProviderError("Groq returned a response that could not be parsed as structured JSON.") from exc
