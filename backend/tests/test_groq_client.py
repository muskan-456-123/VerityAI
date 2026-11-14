from __future__ import annotations

import pytest

from app.services import groq_client


class FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, object]:
        return {"data": [
            {"id": "canopylabs/orpheus-arabic-saudi"},
            {"id": "whisper-large-v3"},
            {"id": "meta-llama/llama-prompt-guard-2-22m"},
            {"id": "qwen/qwen3.8-27b"},
        ]}


def test_model_discovery_ignores_non_chat_and_guard_models(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "fake-test-token")
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    monkeypatch.setattr(groq_client.httpx, "get", lambda *args, **kwargs: FakeResponse())
    groq_client._selected_model.cache_clear()
    try:
        assert groq_client._selected_model() == "qwen/qwen3.8-27b"
    finally:
        groq_client._selected_model.cache_clear()


def test_model_discovery_fails_closed_without_general_chat_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "fake-test-token")
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    class SpecializedResponse(FakeResponse):
        def json(self) -> dict[str, object]:
            return {"data": [{"id": "canopylabs/orpheus-v1-english"}, {"id": "whisper-large-v3"}]}
    monkeypatch.setattr(groq_client.httpx, "get", lambda *args, **kwargs: SpecializedResponse())
    groq_client._selected_model.cache_clear()
    try:
        with pytest.raises(groq_client.ProviderError, match="No general-purpose chat model"):
            groq_client._selected_model()
    finally:
        groq_client._selected_model.cache_clear()
