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


def _rate_limit_message(retry_after: str | None = None) -> str:
    wait_message = "Wait for the provider's rate-limit window to reset before retrying."
    try:
        seconds = float(retry_after) if retry_after else 0
        if 0 < seconds <= 86400:
            wait_message = f"Wait about {max(1, int(seconds + 0.5))} seconds before retrying."
    except (TypeError, ValueError):
        pass
    return (
        "Groq rejected the request with HTTP 429 (rate limit or available quota). "
        f"{wait_message} If it persists, check the Groq Console for model limits and usage/quota. "
        "Settings only confirms that an API key is present; it cannot confirm remaining quota."
    )


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
        if exc.response.status_code == 429:
            raise ProviderError(_rate_limit_message(exc.response.headers.get("retry-after"))) from exc
        raise ProviderError(f"Could not retrieve the current Groq model catalog (HTTP {exc.response.status_code}).") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise ProviderError(f"Could not retrieve the current Groq model catalog: {type(exc).__name__}.") from exc


def _decode_structured_json(content: str, collection_key: str | None = None) -> dict[str, Any]:
    parsed = json.loads(content)
    if isinstance(parsed, str):
        try:
            parsed = json.loads(parsed)
        except json.JSONDecodeError:
            pass
    if isinstance(parsed, list):
        if collection_key is not None and all(isinstance(item, dict) for item in parsed):
            return {collection_key: parsed}
        if len(parsed) == 1 and isinstance(parsed[0], dict):
            parsed = parsed[0]
    if isinstance(parsed, dict):
        return parsed
    root_type = (
        "null" if parsed is None else "boolean" if isinstance(parsed, bool)
        else "array" if isinstance(parsed, list) else "string" if isinstance(parsed, str)
        else "number" if isinstance(parsed, (int, float)) else "unknown"
    )
    raise ProviderError(f"Groq returned JSON {root_type}; expected an object.")


async def groq_json(
    system_prompt: str,
    user_content: str,
    *,
    collection_key: str | None = None,
) -> dict[str, Any]:
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
        return _decode_structured_json(content, collection_key)
    except APIStatusError as exc:
        if exc.status_code == 429:
            raise ProviderError(_rate_limit_message(exc.response.headers.get("retry-after"))) from exc
        raise ProviderError(f"Groq returned HTTP {exc.status_code}; check model access and project settings.") from exc
    except APIConnectionError as exc:
        raise ProviderError(f"Groq request failed: {type(exc).__name__}.") from exc
    except (IndexError, json.JSONDecodeError) as exc:
        raise ProviderError("Groq returned a response that could not be parsed as structured JSON.") from exc
