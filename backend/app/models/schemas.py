from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class Verdict(str, Enum):
    CURRENT = "CURRENT"
    STALE = "STALE"
    CONTRADICTED = "CONTRADICTED"
    UNSUPPORTED = "UNSUPPORTED"
    CONFLICTING = "CONFLICTING"
    STABLE = "STABLE"


class Category(str, Enum):
    HISTORICAL = "Historical"
    TECHNICAL = "Technical"
    PRICING = "Pricing"
    LEGAL = "Legal"
    COMPANY = "Company"
    CURRENT_EVENTS = "Current events"
    GENERAL = "General"


class TemporalSensitivity(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"


class ConfidenceLevel(str, Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"


class FreshnessAssessment(BaseModel):
    label: Literal["Current", "Possibly outdated", "Not time-sensitive", "Unclear"]
    explanation: str = Field(max_length=1200)
    temporal_change_evidence: bool = False


class EvidenceSource(BaseModel):
    source_id: str
    title: str
    url: HttpUrl
    domain: str
    excerpt: str = ""
    relevance: float = Field(default=0, ge=0, le=1)
    published_date: str | None = None
    updated_date: str | None = None
    classification: Literal["supporting", "contradicting", "context"] = "context"


class Claim(BaseModel):
    claim_id: str
    statement: str
    category: Category
    temporal_sensitivity: TemporalSensitivity
    search_query: str
    verdict: Verdict
    confidence: ConfidenceLevel
    confidence_rank: float = Field(ge=0, le=1)
    freshness: FreshnessAssessment
    explanation: str
    supporting_evidence: list[EvidenceSource] = Field(default_factory=list)
    contradicting_evidence: list[EvidenceSource] = Field(default_factory=list)
    evidence: list[EvidenceSource] = Field(default_factory=list)


class StageState(BaseModel):
    key: Literal["extract", "search", "collect", "evaluate", "report"]
    label: str
    status: Literal["pending", "active", "complete", "error"] = "pending"
    detail: str = ""


class VerificationReport(BaseModel):
    report_id: str
    created_at: datetime
    status: Literal["processing", "complete", "error"]
    source_text: str
    stages: list[StageState]
    claims: list[Claim] = Field(default_factory=list)
    corrected_answer: str | None = None
    error: str | None = None

    @property
    def summary(self) -> dict[str, int]:
        return {verdict.value.lower(): sum(c.verdict == verdict for c in self.claims) for verdict in Verdict}


class VerifyRequest(BaseModel):
    text: str = Field(min_length=20, max_length=12_000)


class ExtractRequest(BaseModel):
    text: str = Field(min_length=20, max_length=12_000)


class CorrectRequest(BaseModel):
    report_id: str | None = None
    text: str | None = Field(default=None, max_length=12_000)
    claims: list[Claim] | None = None


class VerifyAccepted(BaseModel):
    report_id: str
    status: Literal["processing"]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    groq_configured: bool
    tavily_configured: bool


class HistoryItem(BaseModel):
    report_id: str
    created_at: datetime
    status: Literal["processing", "complete", "error"]
    preview: str
    claim_count: int
    stale_count: int
    current_count: int
    result_summary: str
