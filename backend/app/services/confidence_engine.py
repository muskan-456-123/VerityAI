from __future__ import annotations

from app.models.schemas import ConfidenceLevel, EvidenceSource


def assess_confidence(supporting: list[EvidenceSource], contradicting: list[EvidenceSource], all_sources: list[EvidenceSource]) -> tuple[ConfidenceLevel, float]:
    """Return an ordinal verdict-confidence label and a private sortable rank, not a probability."""
    if not all_sources or (not supporting and not contradicting):
        return ConfidenceLevel.LOW, 0.12
    verdict_evidence = supporting or contradicting
    average_relevance = sum(source.relevance for source in verdict_evidence) / len(verdict_evidence)
    independent_domains = len({source.domain.lower() for source in verdict_evidence})
    breadth = min(independent_domains, 3) / 3
    evidence_volume = min(len(verdict_evidence), 3) / 3
    agreement = len(verdict_evidence) / max(1, len(supporting) + len(contradicting))
    conflict_penalty = 0.22 if supporting and contradicting else 0.0
    score = max(0.0, min(1.0, average_relevance * 0.45 + breadth * 0.25 + evidence_volume * 0.20 + agreement * 0.10 - conflict_penalty))
    if score >= 0.76 and not (supporting and contradicting):
        return ConfidenceLevel.HIGH, score
    if score >= 0.43:
        return ConfidenceLevel.MODERATE, score
    return ConfidenceLevel.LOW, score
