from __future__ import annotations

import asyncio
from types import SimpleNamespace

import httpx
import pytest
from groq import APIStatusError

from app.services import groq_client


class FakeCompletions:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0

    async def create(self, **_kwargs):
        self.calls += 1
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=outcome))])


class FakeClient:
    def __init__(self, outcomes):
        self.completions = FakeCompletions(outcomes)
        self.chat = SimpleNamespace(completions=self.completions)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return None


def rate_limited(retry_after: str | None) -> APIStatusError:
    headers = {"retry-after": retry_after} if retry_after else {}
    request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    response = httpx.Response(429, headers=headers, request=request)
    return APIStatusError("rate limited", response=response, body={"error": "test only"})


def test_groq_retries_once_after_short_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-only-key")
    monkeypatch.setattr(groq_client, "_selected_model", lambda: "test/chat-model")
    client = FakeClient([rate_limited("0.25"), '{"claims":[]}'])
    monkeypatch.setattr(groq_client, "AsyncGroq", lambda **_kwargs: client)
    delays: list[float] = []

    async def fake_sleep(delay: float) -> None:
        delays.append(delay)

    monkeypatch.setattr(groq_client.asyncio, "sleep", fake_sleep)
    result = asyncio.run(groq_client.groq_json("extract", "sample text", collection_key="claims"))

    assert result == {"claims": []}
    assert client.completions.calls == 2
    assert delays == [0.25]


def test_groq_does_not_retry_429_without_safe_retry_after(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test-only-key")
    monkeypatch.setattr(groq_client, "_selected_model", lambda: "test/chat-model")
    client = FakeClient([rate_limited(None)])
    monkeypatch.setattr(groq_client, "AsyncGroq", lambda **_kwargs: client)

    with pytest.raises(groq_client.RateLimitError, match="HTTP 429"):
        asyncio.run(groq_client.groq_json("extract", "sample text"))

    assert client.completions.calls == 1


def test_long_or_malformed_retry_after_is_not_retried() -> None:
    assert groq_client._retry_after_seconds("31") is None
    assert groq_client._retry_after_seconds("tomorrow") is None
    assert groq_client._retry_after_seconds("3") == 3.0
