from __future__ import annotations

import asyncio

from pydantic import HttpUrl, TypeAdapter

from app.models.schemas import Claim, Category, ConfidenceLevel, EvidenceSource, FreshnessAssessment, TemporalSensitivity, Verdict
from app.services import verification_pipeline

_URL = TypeAdapter(HttpUrl)


def test_corrected_answer_adds_only_real_source_links_when_model_omits_citations(monkeypatch):
    source = EvidenceSource(
        source_id="claim-01-S01",
        title="Verified page",
        url=_URL.validate_python("https://example.com/source"),
        domain="example.com",
        excerpt="Supporting excerpt.",
        relevance=0.95,
        classification="supporting",
    )
    claim = Claim(
        claim_id="claim-01",
        statement="A short supported factual statement.",
        category=Category.HISTORICAL,
        temporal_sensitivity=TemporalSensitivity.LOW,
        search_query="short supported factual statement",
        verdict=Verdict.STABLE,
        confidence=ConfidenceLevel.HIGH,
        confidence_rank=0.9,
        freshness=FreshnessAssessment(label="Not time-sensitive", explanation="Historical fact."),
        explanation="The retrieved source supports it.",
        supporting_evidence=[source],
        evidence=[source],
    )

    async def fake_groq_json(system_prompt: str, user_content: str) -> dict[str, str]:
        return {"answer": "The claim is supported. [invented-source] https://fake.example/unretrieved"}

    monkeypatch.setattr(verification_pipeline, "groq_json", fake_groq_json)
    answer = asyncio.run(verification_pipeline.corrected_answer("Original answer.", [claim]))
    assert "[Verified page](https://example.com/source)" in answer
    assert "invented-source" not in answer
    assert "fake.example" not in answer
