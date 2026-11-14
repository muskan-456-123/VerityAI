from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query, Response

from app.database import repository
from app.models.schemas import CorrectRequest, ExtractRequest, HistoryItem, VerifyAccepted, VerificationReport, VerifyRequest
from app.services.verification_pipeline import corrected_answer, extract_claims, run_verification

router = APIRouter(prefix="/api")


@router.post("/extract-claims")
async def extract_endpoint(request: ExtractRequest):
    try:
        claims = await extract_claims(request.text)
        return {"claims": [claim.model_dump(mode="json") for claim in claims]}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/verify", response_model=VerifyAccepted, status_code=202)
async def verify_endpoint(request: VerifyRequest, background_tasks: BackgroundTasks):
    report_id = uuid.uuid4().hex[:12].upper()
    report = {
        "report_id": report_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": "processing",
        "source_text": request.text,
        "stages": [
            {"key": "extract", "label": "Extracting claims", "status": "pending", "detail": ""},
            {"key": "search", "label": "Searching live sources", "status": "pending", "detail": ""},
            {"key": "collect", "label": "Collecting evidence", "status": "pending", "detail": ""},
            {"key": "evaluate", "label": "Evaluating claims", "status": "pending", "detail": ""},
            {"key": "report", "label": "Generating report", "status": "pending", "detail": ""},
        ],
        "claims": [],
        "corrected_answer": None,
        "error": None,
    }
    repository.create(report)
    background_tasks.add_task(run_verification, report_id)
    return VerifyAccepted(report_id=report_id, status="processing")


@router.post("/correct")
async def correct_endpoint(request: CorrectRequest):
    if request.report_id:
        report = repository.get(request.report_id)
        if not report:
            raise HTTPException(status_code=404, detail="Report not found")
        if report["status"] != "complete":
            raise HTTPException(status_code=409, detail="The report is not complete yet")
        from app.models.schemas import Claim
        claims = [Claim.model_validate(item) for item in report.get("claims", [])]
        return {"corrected_answer": await corrected_answer(report["source_text"], claims)}
    if request.text is not None and request.claims is not None:
        return {"corrected_answer": await corrected_answer(request.text, request.claims)}
    raise HTTPException(status_code=422, detail="Provide report_id, or both text and claims")


@router.get("/history", response_model=list[HistoryItem])
def history_endpoint(limit: int = Query(default=100, ge=1, le=250)):
    items = []
    for report in repository.list_reports(limit):
        claims = report.get("claims", [])
        counts = {verdict: sum(item.get("verdict") == verdict for item in claims) for verdict in ("CURRENT", "STALE", "CONTRADICTED", "UNSUPPORTED", "CONFLICTING", "STABLE")}
        result_summary = " · ".join(f"{count} {verdict.lower()}" for verdict, count in counts.items() if count) or ("No factual claims" if report["status"] == "complete" else report["status"].capitalize())
        items.append(HistoryItem(
            report_id=report["report_id"],
            created_at=report["created_at"],
            status=report["status"],
            preview=report["source_text"][:180],
            claim_count=len(claims),
            stale_count=counts["STALE"],
            current_count=counts["CURRENT"],
            result_summary=result_summary,
        ))
    return items


@router.get("/report/{report_id}")
def report_endpoint(report_id: str):
    report = repository.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/report/{report_id}", status_code=204)
def delete_endpoint(report_id: str):
    if not repository.delete(report_id):
        raise HTTPException(status_code=404, detail="Report not found")
    return Response(status_code=204)
