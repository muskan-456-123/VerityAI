from __future__ import annotations

import asyncio
import json
from typing import Any

from pydantic import HttpUrl, TypeAdapter

from app.models.schemas import Category, ConfidenceLevel, EvidenceSource, TemporalSensitivity, Verdict
from app.services import verification_pipeline as pipeline


_URL = TypeAdapter(HttpUrl)


def make_work_item(index: int, *, with_source: bool = True) -> pipeline.AssessmentWorkItem:
    claim_id = f"claim-{index:02d}"
    claim = pipeline.ExtractedClaim(
        statement=f"Test factual statement number {index}.",
        category=Category.TECHNICAL,
        temporal_sensitivity=TemporalSensitivity.LOW,
        search_query=f"test factual statement {index}",
    )
    sources = []
    if with_source:
        sources = [EvidenceSource(
            source_id=f"{claim_id}-S01",
            title=f"Evidence for claim {index}",
            url=_URL.validate_python(f"https://source{index}.example/evidence"),
            domain=f"source{index}.example",
            excerpt="A retrieved test excerpt.",
            relevance=0.9,
        )]
    return claim, sources, claim_id


def valid_batch(user_content: str) -> dict[str, Any]:
    context = json.loads(user_content)
    return {"assessments": [{
        "claim_id": item["claim_id"],
        "verdict": "STABLE",
        "explanation": "The retrieved evidence supports this claim.",
        "freshness_label": "Not time-sensitive",
        "freshness_explanation": "This claim is not time-sensitive.",
        "temporal_change_evidence": False,
        "supporting_source_ids": [source["id"] for source in item["sources"]],
        "contradicting_source_ids": [],
    } for item in context]}


def test_three_claims_are_assessed_in_one_call_and_no_source_claim_is_local(monkeypatch):
    calls: list[dict[str, Any]] = []

    async def fake_groq_json(_prompt: str, user_content: str, **_kwargs: Any) -> dict[str, Any]:
        calls.append(json.loads(user_content))
        return valid_batch(user_content)

    monkeypatch.setattr(pipeline, "groq_json", fake_groq_json)
    result = asyncio.run(pipeline.assess_claim_batch([
        make_work_item(1), make_work_item(2, with_source=False), make_work_item(3),
    ]))

    assert len(calls) == 1
    assert [claim.claim_id for claim in result] == ["claim-01", "claim-02", "claim-03"]
    assert result[1].verdict == Verdict.UNSUPPORTED
    assert result[1].confidence == ConfidenceLevel.LOW
    assert len(result[0].supporting_evidence) == 1
    assert len(result[2].supporting_evidence) == 1


def test_bad_batch_shape_falls_back_to_smaller_validated_batches(monkeypatch):
    calls: list[str] = []

    async def fake_groq_json(_prompt: str, user_content: str, **_kwargs: Any) -> dict[str, Any]:
        calls.append(user_content)
        if len(calls) == 1:
            return {"assessments": []}
        return valid_batch(user_content)

    monkeypatch.setattr(pipeline, "groq_json", fake_groq_json)
    result = asyncio.run(pipeline.assess_claim_batch([make_work_item(1), make_work_item(2)]))

    assert len(calls) == 3
    assert [claim.claim_id for claim in result] == ["claim-01", "claim-02"]
