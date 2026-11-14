from pydantic import HttpUrl, TypeAdapter

from app.models.schemas import EvidenceSource, TemporalSensitivity, Verdict
from app.services.confidence_engine import assess_confidence
from app.services.freshness_engine import assess_freshness

_URL = TypeAdapter(HttpUrl)


def source(source_id: str, domain: str, relevance: float = 0.9) -> EvidenceSource:
    return EvidenceSource(source_id=source_id, title="Test source", url=_URL.validate_python(f"https://{domain}/page"), domain=domain, relevance=relevance)


def test_freshness_does_not_mark_old_context_stale_without_change_evidence():
    result = assess_freshness(Verdict.STALE, TemporalSensitivity.HIGH, "Possibly outdated", "A dated page was found.", False)
    assert result.label == "Unclear"
    assert result.temporal_change_evidence is False


def test_stale_requires_temporal_change_evidence():
    result = assess_freshness(Verdict.STALE, TemporalSensitivity.HIGH, "Possibly outdated", "Newer terms supersede the old terms.", True)
    assert result.label == "Possibly outdated"


def test_confidence_rank_rewards_independent_support_without_percentage():
    one, rank_one = assess_confidence([source("a", "one.example")], [], [source("a", "one.example")])
    two, rank_two = assess_confidence([source("b", "one.example"), source("c", "two.example")], [], [source("b", "one.example"), source("c", "two.example")])
    assert rank_two > rank_one
    assert one.value in {"Low", "Moderate", "High"}
    assert two.value in {"Low", "Moderate", "High"}


def test_no_sources_means_low_confidence():
    label, rank = assess_confidence([], [], [])
    assert label.value == "Low"
    assert rank < 0.2
