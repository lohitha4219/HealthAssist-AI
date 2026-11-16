from datetime import datetime, timezone
from typing import Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.database.session import get_db
from app.models.medical_report import MedicalReport
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.reports import MedicalReportListResponse, MedicalReportResponse
from app.services.activity_service import record_activity
from app.services.ai_service import LocalAIService, get_ai_service
from app.services.report_analyzer import analyze_medical_report
from app.services.report_service import (
    resolve_safe_report_path,
    store_and_process_report,
)
from app.utils.file_validation import FileValidationError

router = APIRouter(prefix="/reports", tags=["Medical Reports"])


def _get_owned_report(
    db: Session, report_id: int, user_id: int
) -> MedicalReport:
    report = db.scalar(
        select(MedicalReport).where(
            MedicalReport.id == report_id,
            MedicalReport.user_id == user_id,
        )
    )
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medical report not found",
        )
    return report


@router.post(
    "/upload",
    response_model=MedicalReportResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_report(
    file: UploadFile = File(...),
    category: str = Form(default="General Report"),
    notes: Optional[str] = Form(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_service: LocalAIService = Depends(get_ai_service),
):
    settings = get_settings()
    raw_bytes = await file.read(settings.max_upload_bytes + 1)
    if len(raw_bytes) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB",
        )

    try:
        stored = store_and_process_report(
            user_id=current_user.id,
            filename=file.filename or "report",
            content_type=file.content_type,
            data=raw_bytes,
            settings=settings,
        )
    except FileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    analysis_out = await analyze_medical_report(
        filename=stored.original_filename,
        processing_status=stored.processing_status,
        extracted_text=stored.extracted_text,
        ai_service=ai_service,
    )

    clean_category = (category or "General Report").strip()[:80] or "General Report"
    clean_notes = notes.strip()[:2000] if notes and notes.strip() else None

    try:
        normalized_status = (
            "analyzed"
            if (analysis_out.get("summary") or analysis_out.get("analysis"))
            else "uploaded"
        )
        report = MedicalReport(
            user_id=current_user.id,
            original_filename=stored.original_filename,
            stored_filename=stored.stored_filename,
            storage_path=stored.storage_path,
            content_type=stored.content_type,
            file_size=stored.file_size,
            category=clean_category,
            notes=clean_notes,
            status=normalized_status,
            processing_status=stored.processing_status,
            extracted_text=stored.extracted_text,
            extraction_method="pypdf" if stored.content_type == "application/pdf" else "pillow",
            ai_summary=analysis_out["summary"],
            analysis=analysis_out["analysis"],
            page_count=stored.page_count,
            image_width=stored.image_width,
            image_height=stored.image_height,
            analyzed_at=datetime.now(timezone.utc),
        )
        db.add(report)
        db.flush()

        record_activity(
            db,
            user_id=current_user.id,
            activity_type="report_uploaded",
            title=f"Uploaded report: {stored.original_filename}",
            description=f"Category: {clean_category} | Status: {stored.processing_status}",
            reference_id=str(report.id),
            reference_type="medical_report",
        )
        db.commit()
        db.refresh(report)
        return MedicalReportResponse.model_validate(report)
    except Exception:
        db.rollback()
        try:
            saved_path = resolve_safe_report_path(stored.storage_path, settings=settings)
            if saved_path.exists() and saved_path.is_file():
                saved_path.unlink()
        except Exception:
            pass
        raise


@router.post("/{report_id}/analyze", response_model=MedicalReportResponse)
async def reanalyze_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_service: LocalAIService = Depends(get_ai_service),
):
    report = _get_owned_report(db, report_id, current_user.id)
    analysis_out = await analyze_medical_report(
        filename=report.original_filename,
        processing_status=report.processing_status,
        extracted_text=report.extracted_text,
        ai_service=ai_service,
    )
    report.ai_summary = analysis_out["summary"]
    report.analysis = analysis_out["analysis"]
    report.status = "analyzed"
    report.analyzed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(report)
    return MedicalReportResponse.model_validate(report)


@router.get("", response_model=MedicalReportListResponse)
def list_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=50),
    search: Optional[str] = Query(default=None, max_length=120),
    category: Optional[str] = Query(default=None, max_length=80),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conditions = [MedicalReport.user_id == current_user.id]
    if category and category.strip() and category.lower() != "all":
        conditions.append(MedicalReport.category == category.strip())
    if search and search.strip():
        term = f"%{search.strip()}%"
        conditions.append(
            or_(
                MedicalReport.original_filename.ilike(term),
                MedicalReport.notes.ilike(term),
                MedicalReport.extracted_text.ilike(term),
            )
        )

    total = db.scalar(
        select(func.count(MedicalReport.id)).where(*conditions)
    ) or 0
    rows = db.scalars(
        select(MedicalReport)
        .where(*conditions)
        .order_by(MedicalReport.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return MedicalReportListResponse(
        items=[MedicalReportResponse.model_validate(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{report_id}", response_model=MedicalReportResponse)
def get_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _get_owned_report(db, report_id, current_user.id)
    return MedicalReportResponse.model_validate(report)


@router.get("/{report_id}/download")
def download_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _get_owned_report(db, report_id, current_user.id)
    if not report.storage_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored report path is unavailable",
        )
    try:
        file_path = resolve_safe_report_path(report.storage_path)
    except FileValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Stored report file could not be found on disk",
        )

    return FileResponse(
        path=str(file_path),
        media_type=report.content_type,
        filename=report.original_filename,
    )


@router.delete("/{report_id}", response_model=MessageResponse)
def delete_report(
    report_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    report = _get_owned_report(db, report_id, current_user.id)
    filename = report.original_filename
    if report.storage_path:
        try:
            file_path = resolve_safe_report_path(report.storage_path)
            if file_path.exists() and file_path.is_file():
                file_path.unlink()
        except FileValidationError:
            pass

    db.delete(report)
    record_activity(
        db,
        user_id=current_user.id,
        activity_type="report_deleted",
        title=f"Deleted report: {filename}",
        description="Removed medical report from personal vault",
        reference_id=str(report_id),
        reference_type="medical_report",
    )
    db.commit()
    return MessageResponse(message="Medical report deleted")
