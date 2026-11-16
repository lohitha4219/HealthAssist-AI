from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.chat import Conversation
from app.models.health_activity import HealthActivity
from app.models.medical_report import MedicalReport
from app.models.symptom_assessment import SymptomAssessment
from app.models.user import User
from app.schemas.analytics import (
    DashboardNotification,
    DashboardStats,
    DashboardSummaryResponse,
    HealthActivityResponse,
)
from app.schemas.auth import UserPublic
from app.schemas.chat import AIHealthResponse
from app.schemas.reports import MedicalReportResponse
from app.schemas.symptoms import SymptomAssessmentResponse
from app.services.ai_service import LocalAIService, get_ai_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummaryResponse)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_service: LocalAIService = Depends(get_ai_service),
):
    total_assessments = db.scalar(
        select(func.count(SymptomAssessment.id)).where(
            SymptomAssessment.user_id == current_user.id
        )
    ) or 0
    total_reports = db.scalar(
        select(func.count(MedicalReport.id)).where(
            MedicalReport.user_id == current_user.id
        )
    ) or 0
    total_conversations = db.scalar(
        select(func.count(Conversation.id)).where(
            Conversation.user_id == current_user.id
        )
    ) or 0
    total_activities = db.scalar(
        select(func.count(HealthActivity.id)).where(
            HealthActivity.user_id == current_user.id
        )
    ) or 0

    recent_assessments = db.scalars(
        select(SymptomAssessment)
        .where(SymptomAssessment.user_id == current_user.id)
        .order_by(SymptomAssessment.created_at.desc())
        .limit(5)
    ).all()

    recent_reports = db.scalars(
        select(MedicalReport)
        .where(MedicalReport.user_id == current_user.id)
        .order_by(MedicalReport.created_at.desc())
        .limit(5)
    ).all()

    recent_activities = db.scalars(
        select(HealthActivity)
        .where(HealthActivity.user_id == current_user.id)
        .order_by(HealthActivity.created_at.desc())
        .limit(8)
    ).all()

    ai_health = await ai_service.get_health()
    ai_status = AIHealthResponse(
        available=ai_health.available,
        provider=ai_health.provider,
        configured_provider=ai_health.configured_provider,
        model=ai_health.model,
        base_url=ai_health.base_url,
        status=ai_health.status,
        detail=ai_health.detail,
        setup_hint=ai_health.setup_hint,
        checked_at=ai_health.checked_at,
    )

    notifications: List[DashboardNotification] = []
    if not ai_status.available:
        notifications.append(
            DashboardNotification(
                id="ai-offline",
                title="Local AI Engine Offline",
                message="Start llama-server or Ollama locally to enable AI Chat replies. All health record features remain active.",
                severity="info",
                action_route="/chat",
            )
        )
    if not current_user.blood_group or not current_user.emergency_contact_phone:
        notifications.append(
            DashboardNotification(
                id="profile-incomplete",
                title="Complete Your Health Profile",
                message="Add blood group and emergency contact details in Profile so your health summary stays organized.",
                severity="info",
                action_route="/profile",
            )
        )
    urgent_recent = next(
        (a for a in recent_assessments if a.urgency_level == "urgent_emergency"),
        None,
    )
    if urgent_recent is not None:
        notifications.append(
            DashboardNotification(
                id="urgent-assessment",
                title="Recent Urgent Symptom Flag",
                message="Your recent assessment flagged warning symptoms. Seek professional or emergency care if symptoms persist.",
                severity="warning",
                action_route="/symptom-analysis",
            )
        )

    stats = DashboardStats(
        total_assessments=total_assessments,
        total_reports=total_reports,
        total_conversations=total_conversations,
        total_activities=total_activities,
        last_assessment_at=recent_assessments[0].created_at if recent_assessments else None,
        last_report_at=recent_reports[0].created_at if recent_reports else None,
    )

    return DashboardSummaryResponse(
        user=UserPublic.model_validate(current_user),
        stats=stats,
        recent_assessments=[
            SymptomAssessmentResponse.model_validate(a) for a in recent_assessments
        ],
        recent_reports=[MedicalReportResponse.model_validate(r) for r in recent_reports],
        recent_activities=[
            HealthActivityResponse.model_validate(act) for act in recent_activities
        ],
        ai_status=ai_status,
        notifications=notifications,
    )


@router.get("/activity", response_model=List[HealthActivityResponse])
def get_dashboard_activity(
    limit: int = Query(default=15, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(HealthActivity)
        .where(HealthActivity.user_id == current_user.id)
        .order_by(HealthActivity.created_at.desc())
        .limit(limit)
    ).all()
    return [HealthActivityResponse.model_validate(r) for r in rows]
