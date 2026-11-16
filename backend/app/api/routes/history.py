from datetime import date, datetime, time, timezone
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.health_activity import HealthActivity
from app.models.medical_report import MedicalReport
from app.models.symptom_assessment import SymptomAssessment
from app.models.user import User
from app.schemas.analytics import HistoryEntry, HistoryListResponse
from app.schemas.auth import MessageResponse
from app.services.report_service import resolve_safe_report_path
from app.utils.file_validation import FileValidationError

router = APIRouter(prefix="/history", tags=["Health History"])


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


@router.get("", response_model=HistoryListResponse)
def get_health_history(
    record_type: Literal["all", "assessment", "report", "activity"] = Query(default="all"),
    search: Optional[str] = Query(default=None, max_length=120),
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entries: List[HistoryEntry] = []

    if record_type in {"all", "assessment"}:
        assessments = db.scalars(
            select(SymptomAssessment).where(
                SymptomAssessment.user_id == current_user.id
            )
        ).all()
        for a in assessments:
            entries.append(
                HistoryEntry(
                    id=a.id,
                    record_type="assessment",
                    title=f"Symptom Check: {', '.join(a.symptoms[:3])}"
                    + (f" (+{len(a.symptoms) - 3})" if len(a.symptoms) > 3 else ""),
                    subtitle=f"Severity: {a.severity.title()} · Duration: {a.duration}",
                    badge=a.urgency_level.replace("_", " ").title(),
                    created_at=_as_utc(a.created_at),
                    deletable=True,
                    details={
                        "symptoms": a.symptoms,
                        "duration": a.duration,
                        "severity": a.severity,
                        "urgency_level": a.urgency_level,
                        "educational_summary": a.educational_summary,
                        "possible_causes": a.possible_causes,
                        "care_guidance": a.care_guidance,
                        "emergency_warning": a.emergency_warning,
                    },
                )
            )

    if record_type in {"all", "report"}:
        reports = db.scalars(
            select(MedicalReport).where(MedicalReport.user_id == current_user.id)
        ).all()
        for r in reports:
            entries.append(
                HistoryEntry(
                    id=r.id,
                    record_type="report",
                    title=r.original_filename,
                    subtitle=f"{r.category} · {max(1, r.file_size // 1024)} KB",
                    badge=r.processing_status.replace("_", " ").title(),
                    created_at=_as_utc(r.created_at),
                    deletable=True,
                    details={
                        "category": r.category,
                        "content_type": r.content_type,
                        "file_size": r.file_size,
                        "notes": r.notes,
                        "processing_status": r.processing_status,
                        "extracted_text": r.extracted_text,
                    },
                )
            )

    if record_type in {"all", "activity"}:
        activities = db.scalars(
            select(HealthActivity).where(HealthActivity.user_id == current_user.id)
        ).all()
        for act in activities:
            entries.append(
                HistoryEntry(
                    id=act.id,
                    record_type="activity",
                    title=act.title,
                    subtitle=act.description or act.activity_type.replace("_", " ").title(),
                    badge=act.activity_type.replace("_", " ").title(),
                    created_at=_as_utc(act.created_at),
                    deletable=True,
                    details={
                        "activity_type": act.activity_type,
                        "description": act.description,
                        "reference_type": act.reference_type,
                    },
                )
            )

    if search and search.strip():
        q = search.strip().lower()
        entries = [
            e
            for e in entries
            if q in e.title.lower()
            or q in e.subtitle.lower()
            or q in e.badge.lower()
        ]

    if start_date is not None:
        start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
        entries = [e for e in entries if e.created_at >= start_dt]
    if end_date is not None:
        end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
        entries = [e for e in entries if e.created_at <= end_dt]

    entries.sort(key=lambda e: e.created_at, reverse=True)
    total = len(entries)
    start_idx = (page - 1) * page_size
    paginated = entries[start_idx : start_idx + page_size]

    return HistoryListResponse(
        items=paginated,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/{record_type}/{record_id}", response_model=MessageResponse)
def delete_history_entry(
    record_type: Literal["assessment", "report", "activity"],
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if record_type == "assessment":
        row = db.scalar(
            select(SymptomAssessment).where(
                SymptomAssessment.id == record_id,
                SymptomAssessment.user_id == current_user.id,
            )
        )
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
        db.delete(row)
        db.commit()
        return MessageResponse(message="Assessment deleted from history")

    if record_type == "report":
        row = db.scalar(
            select(MedicalReport).where(
                MedicalReport.id == record_id,
                MedicalReport.user_id == current_user.id,
            )
        )
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
        if row.storage_path:
            try:
                file_path = resolve_safe_report_path(row.storage_path)
                if file_path.exists() and file_path.is_file():
                    file_path.unlink()
            except FileValidationError:
                pass
        db.delete(row)
        db.commit()
        return MessageResponse(message="Medical report deleted from history")

    row = db.scalar(
        select(HealthActivity).where(
            HealthActivity.id == record_id,
            HealthActivity.user_id == current_user.id,
        )
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Record not found")
    db.delete(row)
    db.commit()
    return MessageResponse(message="Activity log removed from history")
