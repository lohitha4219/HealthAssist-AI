from collections import Counter, defaultdict
from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.chat import Conversation
from app.models.medical_report import MedicalReport
from app.models.symptom_assessment import SymptomAssessment
from app.models.user import User
from app.schemas.analytics import (
    BreakdownItem,
    InsightsSummaryResponse,
    InsightsTrendsResponse,
    TrendPoint,
)

router = APIRouter(prefix="/insights", tags=["Health Insights"])


@router.get("/summary", response_model=InsightsSummaryResponse)
def get_insights_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    assessments = db.scalars(
        select(SymptomAssessment).where(SymptomAssessment.user_id == current_user.id)
    ).all()
    reports = db.scalars(
        select(MedicalReport).where(MedicalReport.user_id == current_user.id)
    ).all()
    conversations = db.scalars(
        select(Conversation).where(Conversation.user_id == current_user.id)
    ).all()

    severity_counts = Counter(a.severity for a in assessments)
    urgency_counts = Counter(a.urgency_level for a in assessments)
    report_cat_counts = Counter(r.category for r in reports)
    symptom_counts: Counter[str] = Counter()
    for a in assessments:
        for s in a.symptoms or []:
            symptom_counts[s] += 1

    educational_guidance = [
        "Keep a consistent record of symptom duration and severity to help clinicians identify patterns.",
        "Upload lab results and imaging summaries in PDF or image format so important details stay organized in one vault.",
        "Educational insights reflect only your logged records and do not replace clinical diagnosis or preventive screenings.",
    ]

    has_data = bool(assessments or reports or conversations)

    return InsightsSummaryResponse(
        total_assessments=len(assessments),
        total_reports=len(reports),
        total_conversations=len(conversations),
        severity_breakdown=[
            BreakdownItem(label=k.title(), count=v)
            for k, v in severity_counts.most_common()
        ],
        urgency_breakdown=[
            BreakdownItem(label=k.replace("_", " ").title(), count=v)
            for k, v in urgency_counts.most_common()
        ],
        report_categories=[
            BreakdownItem(label=k, count=v)
            for k, v in report_cat_counts.most_common()
        ],
        top_symptoms=[
            BreakdownItem(label=k, count=v)
            for k, v in symptom_counts.most_common(6)
        ],
        educational_guidance=educational_guidance,
        has_data=has_data,
    )


@router.get("/trends", response_model=InsightsTrendsResponse)
def get_insights_trends(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    buckets: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"assessments": 0, "reports": 0, "chats": 0}
    )

    assessments = db.scalars(
        select(SymptomAssessment).where(SymptomAssessment.user_id == current_user.id)
    ).all()
    reports = db.scalars(
        select(MedicalReport).where(MedicalReport.user_id == current_user.id)
    ).all()
    conversations = db.scalars(
        select(Conversation).where(Conversation.user_id == current_user.id)
    ).all()

    for a in assessments:
        buckets[a.created_at.strftime("%Y-%m-%d")]["assessments"] += 1
    for r in reports:
        buckets[r.created_at.strftime("%Y-%m-%d")]["reports"] += 1
    for c in conversations:
        buckets[c.created_at.strftime("%Y-%m-%d")]["chats"] += 1

    timeline = [
        TrendPoint(
            date=day,
            assessments=vals["assessments"],
            reports=vals["reports"],
            chats=vals["chats"],
        )
        for day, vals in sorted(buckets.items())
    ][-30:]

    return InsightsTrendsResponse(
        timeline=timeline,
        has_sufficient_data=len(timeline) > 0,
    )
