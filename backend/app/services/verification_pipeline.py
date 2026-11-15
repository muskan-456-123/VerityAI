from __future__ import annotations

import json
import re
from typing import Any, Callable

from pydantic import BaseModel, Field, ValidationError
from pydantic import TypeAdapter

from app.database import repository
from app.models.schemas import Claim, Category, ConfidenceLevel, EvidenceSource, FreshnessAssessment, TemporalSensitivity, Verdict
from app.services.confidence_engine import assess_confidence
from app.services.freshness_engine import assess_freshness
from app.services.groq_client import ProviderError, StructuredOutputError, groq_json
from app.services.tavily_search import search_claim


class ExtractedClaim(BaseModel):
    statement: str = Field(min_length=5, max_length=1000)
    category: Category
    temporal_sensitivity: TemporalSensitivity
    search_query: str = Field(min_length=3, max_length=400)


class ExtractionPayload(BaseModel):
    claims: list[ExtractedClaim] = Field(max_length=12)


class AssessmentItem(BaseModel):
    claim_id: str = Field(min_length=1, max_length=32)
    verdict: Verdict
    explanation: str = Field(max_length=1400)
    freshness_label: str = "Unclear"
    freshness_explanation: str = Field(max_length=1000)
    temporal_change_evidence: bool = False
    supporting_source_ids: list[str] = Field(default_factory=list)
    contradicting_source_ids: list[str] = Field(default_factory=list)


class AssessmentBatchPayload(BaseModel):
    assessments: list[AssessmentItem] = Field(min_length=1, max_length=3)


STAGES = [
    {"key": "extract", "label": "Extracting claims", "status": "pending", "detail": ""},
    {"key": "search", "label": "Searching live sources", "status": "pending", "detail": ""},
    {"key": "collect", "label": "Collecting evidence", "status": "pending", "detail": ""},
    {"key": "evaluate", "label": "Evaluating claims", "status": "pending", "detail": ""},
    {"key": "report", "label": "Generating report", "status": "pending", "detail": ""},
]


def _stage(report: dict[str, Any], key: str, status: str, detail: str = "") -> None:
    for item in report["stages"]:
        if item["key"] == key:
            item.update(status=status, detail=detail)
            break
    repository.update(report)


def _evidence_context(sources: list[EvidenceSource]) -> str:
    return json.dumps([
        {"id": s.source_id, "title": s.title, "domain": s.domain, "excerpt": s.excerpt[:850],
         "relevance": s.relevance, "published_date": s.published_date, "updated_date": s.updated_date}
        for s in sources
    ], ensure_ascii=False)


async def extract_claims(text: str) -> list[ExtractedClaim]:
    payload = await groq_json(
        "Extract only independently verifiable factual claims from the supplied text. Split compound factual statements. Preserve meaning and add no facts. Do not extract opinions or instructions. For each claim choose exactly one category from Historical, Technical, Pricing, Legal, Company, Current events, General; one temporal_sensitivity Low, Medium, High; and a concise targeted web search query. Return JSON {\"claims\":[{\"statement\":...,\"category\":...,\"temporal_sensitivity\":...,\"search_query\":...}] }.",
        text,
        collection_key="claims",
    )
    try:
        return ExtractionPayload.model_validate(payload).claims[:12]
    except ValidationError as exc:
        raise ProviderError(f"Groq returned claims outside the required schema: {exc.errors()[0]['msg']}") from exc


def _build_claim(claim: ExtractedClaim, assessment: AssessmentItem, sources: list[EvidenceSource], claim_id: str) -> Claim:
    allowed = {source.source_id for source in sources}
    supporting_ids = [sid for sid in assessment.supporting_source_ids if sid in allowed]
    contradicting_ids = [sid for sid in assessment.contradicting_source_ids if sid in allowed]
    support = [source.model_copy(update={"classification": "supporting"}) for source in sources if source.source_id in supporting_ids]
    oppose = [source.model_copy(update={"classification": "contradicting"}) for source in sources if source.source_id in contradicting_ids]
    used_ids = set(supporting_ids + contradicting_ids)
    other = [source.model_copy(update={"classification": "context"}) for source in sources if source.source_id not in used_ids]
    confidence, rank = assess_confidence(support, oppose, sources)
    freshness = assess_freshness(assessment.verdict, claim.temporal_sensitivity, assessment.freshness_label, assessment.freshness_explanation, assessment.temporal_change_evidence)
    if not sources:
        confidence, rank = ConfidenceLevel.LOW, 0.0
    return Claim(
        claim_id=claim_id,
        statement=claim.statement,
        category=claim.category,
        temporal_sensitivity=claim.temporal_sensitivity,
        search_query=claim.search_query,
        verdict=assessment.verdict,
        confidence=confidence,
        confidence_rank=rank,
        freshness=freshness,
        explanation=assessment.explanation,
        supporting_evidence=support,
        contradicting_evidence=oppose,
        evidence=support + oppose + other,
    )


AssessmentWorkItem = tuple[ExtractedClaim, list[EvidenceSource], str]


async def _assess_claim_batch_once(items: list[AssessmentWorkItem]) -> list[Claim]:
    if not items:
        return []
    model_items = [item for item in items if item[1]]
    assessments_by_id: dict[str, AssessmentItem] = {}
    for claim, sources, claim_id in items:
        if not sources:
            assessments_by_id[claim_id] = AssessmentItem(
                claim_id=claim_id,
                verdict=Verdict.UNSUPPORTED,
                explanation="No retrieved evidence was available to assess this claim.",
                freshness_label="Unclear",
                freshness_explanation="Freshness could not be established because no source evidence was retrieved.",
            )
    if model_items:
        context = [{
            "claim_id": claim_id,
            "claim": claim.model_dump(mode="json"),
            "sources": json.loads(_evidence_context(sources)),
        } for claim, sources, claim_id in model_items]
        payload = await groq_json(
            "For every supplied claim, compare it only with that claim's retrieved sources. Return JSON {\"assessments\":[{\"claim_id\":...,\"verdict\":...,\"explanation\":...,\"freshness_label\":...,\"freshness_explanation\":...,\"temporal_change_evidence\":false,\"supporting_source_ids\":[],\"contradicting_source_ids\":[]}]}. Use verdict CURRENT, STALE, CONTRADICTED, UNSUPPORTED, CONFLICTING, or STABLE; freshness_label Current, Possibly outdated, Not time-sensitive, or Unclear. Copy every claim_id exactly and return exactly one assessment per claim. Reference sources only by IDs listed for that claim. Never invent facts, dates, IDs, or URLs. STALE requires evidence of a newer factual change, not merely an old source. Use UNSUPPORTED when evidence is insufficient and CONFLICTING when credible sources disagree. Be explicit about limitations.",
            json.dumps(context, ensure_ascii=False),
            collection_key="assessments",
        )
        if "assessments" not in payload and len(model_items) == 1 and "verdict" in payload:
            payload = {"assessments": [{**payload, "claim_id": model_items[0][2]}]}
        try:
            validated = AssessmentBatchPayload.model_validate(payload).assessments
        except ValidationError as exc:
            raise StructuredOutputError(f"Groq returned an invalid evidence assessment batch: {exc.errors()[0]['msg']}") from exc
        expected_ids = {claim_id for _, _, claim_id in model_items}
        returned_ids = [item.claim_id for item in validated]
        if len(returned_ids) != len(set(returned_ids)) or set(returned_ids) != expected_ids:
            raise StructuredOutputError("Groq did not return exactly one assessment for every requested claim.")
        assessments_by_id.update({item.claim_id: item for item in validated})
    return [_build_claim(claim, assessments_by_id[claim_id], sources, claim_id) for claim, sources, claim_id in items]


async def assess_claim_batch(items: list[AssessmentWorkItem]) -> list[Claim]:
    try:
        return await _assess_claim_batch_once(items)
    except StructuredOutputError:
        if len(items) <= 1:
            raise
        midpoint = len(items) // 2
        return await assess_claim_batch(items[:midpoint]) + await assess_claim_batch(items[midpoint:])


async def assess_claim(claim: ExtractedClaim, sources: list[EvidenceSource], claim_id: str) -> Claim:
    return (await assess_claim_batch([(claim, sources, claim_id)]))[0]


async def corrected_answer(source_text: str, claims: list[Claim]) -> str:
    source_pool: dict[str, EvidenceSource] = {}
    for claim in claims:
        for evidence in claim.supporting_evidence:
            source_pool[evidence.source_id] = evidence
    context = {
        "original_answer": source_text,
        "findings": [
            {"claim": c.statement, "verdict": c.verdict.value, "explanation": c.explanation,
             "supported_evidence_ids": [e.source_id for e in c.supporting_evidence]}
            for c in claims
        ],
        "allowed_sources": [{"id": s.source_id, "title": s.title, "url": str(s.url)} for s in source_pool.values()],
    }
    payload = await groq_json(
        "Produce a concise corrected answer grounded only in the findings and allowed sources. Preserve useful original content, remove or qualify unsupported/contradicted/outdated statements, and do not add unverified facts. Do not write URLs. Cite sources only using their exact bracketed ids, e.g. [claim-01-S01]. Return JSON {\"answer\":\"...\"}. If no claims have usable support, state that a reliable correction cannot be established from the available evidence.",
        json.dumps(context, ensure_ascii=False),
    )
    answer = str(payload.get("answer", "")).strip()
    if not answer:
        raise ProviderError("Groq did not provide a corrected answer.")
    # Make citations clickable only when they resolve to a Tavily-returned source.
    def replace_citation(match: re.Match[str]) -> str:
        source_id = match.group(1)
        source = source_pool.get(source_id)
        if not source:
            return ""
        return f"[{source.title}]({source.url})"
    answer = re.sub(r"\[([A-Za-z0-9_-]+)\]", replace_citation, answer)
    # Prevent a model-generated URL from being mistaken for retrieved evidence.
    known_urls = {str(source.url) for source in source_pool.values()}
    answer = re.sub(r"https?://\S+", lambda m: m.group(0) if m.group(0).rstrip(".,)") in known_urls else "", answer)
    if source_pool and not any(url in answer for url in known_urls):
        links = []
        for source in list(source_pool.values())[:3]:
            label = re.sub(r"[\[\]()\\]", " ", source.title).strip()[:180] or source.domain
            links.append(f"[{label}]({source.url})")
        answer = f"{answer.rstrip()}\n\nSources: {' '.join(links)}"
    return answer


async def run_verification(report_id: str) -> None:
    report = repository.get(report_id)
    if not report:
        return
    try:
        _stage(report, "extract", "active", "Asking Groq to isolate factual claims")
        extracted = await extract_claims(report["source_text"])
        if not extracted:
            for key in ("extract", "search", "collect", "evaluate", "report"):
                _stage(report, key, "complete", "No independently verifiable factual claims were identified." if key == "extract" else "Not needed")
            report["status"] = "complete"
            report["claims"] = []
            repository.update(report)
            return
        _stage(report, "extract", "complete", f"{len(extracted)} factual claims extracted")

        _stage(report, "search", "active", "Searching Tavily for source evidence")
        sources_by_claim: dict[str, list[EvidenceSource]] = {}
        for index, item in enumerate(extracted, start=1):
            claim_id = f"claim-{index:02d}"
            sources_by_claim[claim_id] = await search_claim(item.search_query, claim_id)
        _stage(report, "search", "complete", f"Search complete for {len(extracted)} claims")

        _stage(report, "collect", "active", "Using search results and available extracted page content")
        total_sources = sum(len(items) for items in sources_by_claim.values())
        _stage(report, "collect", "complete", f"Retrieved {total_sources} source records; publication dates are shown only when supplied")

        _stage(report, "evaluate", "active", "Comparing evidence in small provider-call batches")
        work_items: list[AssessmentWorkItem] = [
            (item, sources_by_claim[f"claim-{index:02d}"], f"claim-{index:02d}")
            for index, item in enumerate(extracted, start=1)
        ]
        claims: list[Claim] = []
        for start in range(0, len(work_items), 3):
            batch = work_items[start:start + 3]
            _stage(report, "evaluate", "active", f"Assessing {len(batch)} claims in one evidence-analysis request")
            claims.extend(await assess_claim_batch(batch))
        report["claims"] = [claim.model_dump(mode="json") for claim in claims]
        _stage(report, "evaluate", "complete", f"Evidence assessed for {len(claims)} claims")

        _stage(report, "report", "active", "Building an evidence-linked correction")
        report["corrected_answer"] = await corrected_answer(report["source_text"], claims)
        report["status"] = "complete"
        _stage(report, "report", "complete", "Report is ready")
    except Exception as exc:  # error is persisted for the polling client; credentials are never echoed
        report["status"] = "error"
        report["error"] = str(exc)[:600]
        for stage in report["stages"]:
            if stage["status"] == "active":
                stage.update(status="error", detail="The provider request could not be completed.")
        repository.update(report)
