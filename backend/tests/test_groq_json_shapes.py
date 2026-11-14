from __future__ import annotations

import asyncio
import json
from types import SimpleNamespace
from typing import Any

import pytest

from app.services import groq_client


class FakeGroqClient:
    def __init__(self, content: str) -> None:
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.content = content

    async def __aenter__(self) -> FakeGroqClient:
        return self

    async def __aexit__(self, *_: Any) -> None:
        return None

    async def create(self, **_: Any) -> Any:
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))])


def fake_groq(monkeypatch: pytest.MonkeyPatch, content: str) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "offline-test-token")
    monkeypatch.setattr(groq_client, "_selected_model", lambda: "offline/test-chat-model")
    monkeypatch.setattr(groq_client, "AsyncGroq", lambda **_: FakeGroqClient(content))


def test_claim_extraction_wraps_top_level_array(monkeypatch: pytest.MonkeyPatch) -> None:
    claims = [{"statement": "The Moon orbits Earth.", "category": "Technical", "temporal_sensitivity": "Low", "search_query": "Moon orbit Earth"}]
    fake_groq(monkeypatch, json.dumps(claims))

    result = asyncio.run(groq_client.groq_json("extract claims", "text", collection_key="claims"))

    assert result == {"claims": claims}


def test_singleton_assessment_array_is_unwrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    assessment = {"verdict": "STABLE", "explanation": "Evidence supports this historical claim."}
    fake_groq(monkeypatch, json.dumps([assessment]))

    result = asyncio.run(groq_client.groq_json("assess claim", "text"))

    assert result == assessment


def test_double_encoded_object_is_decoded(monkeypatch: pytest.MonkeyPatch) -> None:
    expected = {"answer": "A careful answer."}
    fake_groq(monkeypatch, json.dumps(json.dumps(expected)))

    result = asyncio.run(groq_client.groq_json("correct answer", "text"))

    assert result == expected


def test_malformed_array_for_single_object_is_still_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_groq(monkeypatch, '["not a claim object"]')

    with pytest.raises(groq_client.ProviderError, match="JSON array; expected an object"):
        asyncio.run(groq_client.groq_json("assess claim", "text"))
