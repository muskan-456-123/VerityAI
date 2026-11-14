from __future__ import annotations

from typing import Literal, cast

from app.models.schemas import FreshnessAssessment, TemporalSensitivity, Verdict

FreshnessLabel = Literal["Current", "Possibly outdated", "Not time-sensitive", "Unclear"]
VALID_LABELS = {"Current", "Possibly outdated", "Not time-sensitive", "Unclear"}


def assess_freshness(verdict: Verdict, sensitivity: TemporalSensitivity, model_label: str, explanation: str, temporal_change_evidence: bool) -> FreshnessAssessment:
    """Do not mark a fact stale merely because an available source is old."""
    if verdict == Verdict.STALE and not temporal_change_evidence:
        return FreshnessAssessment(label="Unclear", explanation="A newer change could not be established from the retrieved evidence.", temporal_change_evidence=False)
    if sensitivity == TemporalSensitivity.LOW and verdict == Verdict.STABLE:
        return FreshnessAssessment(label="Not time-sensitive", explanation=explanation, temporal_change_evidence=temporal_change_evidence)
    if verdict == Verdict.STALE:
        return FreshnessAssessment(label="Possibly outdated", explanation=explanation, temporal_change_evidence=True)
    normalized: FreshnessLabel = cast(FreshnessLabel, model_label if model_label in VALID_LABELS else "Unclear")
    return FreshnessAssessment(label=normalized, explanation=explanation, temporal_change_evidence=temporal_change_evidence)
