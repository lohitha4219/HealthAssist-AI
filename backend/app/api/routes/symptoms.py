from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.symptom_assessment import SymptomAssessment
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.symptoms import (
    SymptomAssessRequest,
    SymptomAssessmentResponse,
    SymptomCatalogItem,
    SymptomHistoryResponse,
)
from app.services.activity_service import record_activity
from app.services.ai_service import LocalAIService, get_ai_service
from app.services.symptom_service import SYMPTOM_CATALOG, evaluate_symptoms

router = APIRouter(prefix="/symptoms", tags=["Symptoms"])


@router.get("/catalog", response_model=List[SymptomCatalogItem])
def get_symptom_catalog(current_user: User = Depends(get_current_user)):
    return SYMPTOM_CATALOG


@router.post(
    "/assess",
    response_model=SymptomAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def assess_symptoms(
    payload: SymptomAssessRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_service: LocalAIService = Depends(get_ai_service),
):
    evaluation = await evaluate_symptoms(
        symptoms=payload.symptoms,
        duration=payload.duration,
        severity=payload.severity,
        additional_details=payload.additional_details,
        ai_service=ai_service,
    )

    assessment = SymptomAssessment(
        user_id=current_user.id,
        symptoms=payload.symptoms,
        duration=payload.duration,
        severity=payload.severity,
        additional_details=payload.additional_details,
        urgency_level=evaluation["urgency_level"],
        educational_summary=evaluation["educational_summary"],
        possible_causes=evaluation["possible_causes"],
        care_guidance=evaluation["care_guidance"],
        emergency_warning=evaluation["emergency_warning"],
        ai_enhanced=evaluation["ai_enhanced"],
    )
    db.add(assessment)
    db.flush()

    record_activity(
        db,
        user_id=current_user.id,
        activity_type="symptom_assessment",
        title=f"Symptom assessment ({len(payload.symptoms)} symptom{'s' if len(payload.symptoms) != 1 else ''})",
        description=f"Severity: {payload.severity} | Duration: {payload.duration} | Urgency: {evaluation['urgency_level']}",
        reference_id=str(assessment.id),
        reference_type="symptom_assessment",
    )
    db.commit()
    db.refresh(assessment)
    return SymptomAssessmentResponse.model_validate(assessment)


@router.get("/history", response_model=SymptomHistoryResponse)
def get_symptom_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    total = db.scalar(
        select(func.count(SymptomAssessment.id)).where(
            SymptomAssessment.user_id == current_user.id
        )
    ) or 0
    rows = db.scalars(
        select(SymptomAssessment)
        .where(SymptomAssessment.user_id == current_user.id)
        .order_by(SymptomAssessment.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return SymptomHistoryResponse(
        items=[SymptomAssessmentResponse.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{assessment_id}", response_model=SymptomAssessmentResponse)
def get_symptom_assessment(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.scalar(
        select(SymptomAssessment).where(
            SymptomAssessment.id == assessment_id,
            SymptomAssessment.user_id == current_user.id,
        )
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symptom assessment not found",
        )
    return SymptomAssessmentResponse.model_validate(row)


@router.delete("/{assessment_id}", response_model=MessageResponse)
def delete_symptom_assessment(
    assessment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = db.scalar(
        select(SymptomAssessment).where(
            SymptomAssessment.id == assessment_id,
            SymptomAssessment.user_id == current_user.id,
        )
    )
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Symptom assessment not found",
        )
    db.delete(row)
    db.commit()
    return MessageResponse(message="Symptom assessment deleted")
