from datetime import date
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_doctor, require_verified_doctor
from app.api.routes.appointments import serialize_appointment
from app.database.session import get_db
from app.models.appointment import Appointment, ConsultationNote
from app.models.doctor import DoctorAvailability, DoctorLeave, DoctorProfile
from app.models.medical_report import MedicalReport
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.healthcare import (
    AppointmentOut,
    ConsultationNoteCreateRequest,
    ConsultationNoteOut,
    DoctorAppointmentActionRequest,
    DoctorAvailabilityRuleIn,
    DoctorAvailabilityRuleOut,
    DoctorDetailOut,
    DoctorLeaveCreateRequest,
    DoctorLeaveOut,
    DoctorProfileUpdateRequest,
)
from app.schemas.reports import MedicalReportResponse
from app.services.appointment_service import (
    ACTIVE_APPOINTMENT_STATUSES,
    compute_doctor_slots,
)
from app.services.notification_service import create_notification

router = APIRouter(prefix="/doctor", tags=["Doctor Portal"])


@router.get("/dashboard")
def doctor_dashboard(
    doctor_ctx: Tuple[User, DoctorProfile] = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    user, profile = doctor_ctx
    today = date.today()

    today_count = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.doctor_id == profile.id,
            Appointment.appointment_date == today,
            Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES),
        )
    ) or 0
    upcoming_count = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.doctor_id == profile.id,
            Appointment.appointment_date >= today,
            Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES),
        )
    ) or 0
    pending_count = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.doctor_id == profile.id, Appointment.status == "pending"
        )
    ) or 0
    confirmed_count = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.doctor_id == profile.id, Appointment.status == "confirmed"
        )
    ) or 0
    completed_count = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.doctor_id == profile.id, Appointment.status == "completed"
        )
    ) or 0
    cancelled_count = db.scalar(
        select(func.count(Appointment.id)).where(
            Appointment.doctor_id == profile.id,
            Appointment.status.in_(["cancelled", "rejected"]),
        )
    ) or 0
    patient_count = db.scalar(
        select(func.count(func.distinct(Appointment.patient_id))).where(
            Appointment.doctor_id == profile.id
        )
    ) or 0

    recent_appts = db.scalars(
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor).joinedload(DoctorProfile.user),
            joinedload(Appointment.hospital),
            joinedload(Appointment.department),
            joinedload(Appointment.consultation_notes),
        )
        .where(Appointment.doctor_id == profile.id)
        .order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc())
        .limit(8)
    ).unique().all()

    return {
        "doctor": {
            "id": profile.id,
            "full_name": user.full_name,
            "email": user.email,
            "specialization": profile.specialization,
            "qualification": profile.qualification,
            "verification_status": profile.verification_status,
            "hospital_name": profile.hospital.name if profile.hospital else None,
        },
        "stats": {
            "today_appointments": today_count,
            "upcoming_appointments": upcoming_count,
            "pending_requests": pending_count,
            "confirmed_appointments": confirmed_count,
            "completed_appointments": completed_count,
            "cancelled_appointments": cancelled_count,
            "patient_count": patient_count,
        },
        "recent_appointments": [
            serialize_appointment(a, include_private_notes=True) for a in recent_appts
        ],
    }


@router.get("/appointments", response_model=List[AppointmentOut])
def doctor_list_appointments(
    status_filter: Optional[str] = Query(default=None),
    doctor_ctx: Tuple[User, DoctorProfile] = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    _, profile = doctor_ctx
    stmt = (
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor).joinedload(DoctorProfile.user),
            joinedload(Appointment.hospital),
            joinedload(Appointment.department),
            joinedload(Appointment.consultation_notes),
        )
        .where(Appointment.doctor_id == profile.id)
    )
    if status_filter and status_filter != "all":
        stmt = stmt.where(Appointment.status == status_filter)
    rows = db.scalars(
        stmt.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
    ).unique().all()
    return [serialize_appointment(a, include_private_notes=True) for a in rows]


@router.patch("/appointments/{appointment_id}/status", response_model=AppointmentOut)
def doctor_update_appointment_status(
    appointment_id: int,
    payload: DoctorAppointmentActionRequest,
    doctor_ctx: Tuple[User, DoctorProfile] = Depends(require_verified_doctor),
    db: Session = Depends(get_db),
):
    user, profile = doctor_ctx
    appt = db.scalar(
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor).joinedload(DoctorProfile.user),
            joinedload(Appointment.hospital),
            joinedload(Appointment.department),
            joinedload(Appointment.consultation_notes),
        )
        .where(
            Appointment.id == appointment_id,
            Appointment.doctor_id == profile.id,
        )
    )
    if appt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    if payload.status == "rejected":
        if not payload.reason or not payload.reason.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide a rejection reason",
            )
        appt.status = "rejected"
        appt.cancellation_reason = payload.reason.strip()
        notif_title = "Appointment Request Declined"
        notif_msg = f"{user.full_name} declined the appointment on {appt.appointment_date.isoformat()}: {appt.cancellation_reason}"
    elif payload.status == "confirmed":
        appt.status = "confirmed"
        notif_title = "Appointment Confirmed"
        notif_msg = f"Your appointment with {user.full_name} on {appt.appointment_date.isoformat()} at {appt.appointment_time.strftime('%H:%M')} is confirmed."
    elif payload.status == "completed":
        appt.status = "completed"
        notif_title = "Consultation Completed"
        notif_msg = f"Your consultation on {appt.appointment_date.isoformat()} with {user.full_name} has been marked completed."
    else:  # rescheduled
        if not payload.appointment_date or not payload.appointment_time:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New appointment_date and appointment_time are required to reschedule",
            )
        slots, reason = compute_doctor_slots(
            db, doctor=profile, target_date=payload.appointment_date
        )
        if reason:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)
        target_hhmm = payload.appointment_time.strftime("%H:%M")
        matched = next((s for s in slots if s["time"] == target_hhmm), None)
        if matched is None or not matched["available"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Selected reschedule slot is unavailable",
            )
        appt.rescheduled_from_date = appt.appointment_date
        appt.rescheduled_from_time = appt.appointment_time
        appt.appointment_date = payload.appointment_date
        appt.appointment_time = payload.appointment_time.replace(second=0, microsecond=0)
        appt.status = "rescheduled"
        notif_title = "Appointment Rescheduled by Doctor"
        notif_msg = f"{user.full_name} rescheduled your appointment to {appt.appointment_date.isoformat()} at {appt.appointment_time.strftime('%H:%M')}."

    create_notification(
        db,
        user_id=appt.patient_id,
        title=notif_title,
        message=notif_msg,
        notification_type="appointment",
        related_route="/appointments",
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Slot conflict occurred while updating appointment.",
        )
    db.refresh(appt)
    return serialize_appointment(appt, include_private_notes=True)


@router.get("/appointments/{appointment_id}/reports", response_model=List[MedicalReportResponse])
def doctor_view_authorized_patient_reports(
    appointment_id: int,
    doctor_ctx: Tuple[User, DoctorProfile] = Depends(require_verified_doctor),
    db: Session = Depends(get_db),
):
    _, profile = doctor_ctx
    appt = db.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.doctor_id == profile.id,
        )
    )
    if appt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if not appt.share_reports:
        return []
    reports = db.scalars(
        select(MedicalReport)
        .where(MedicalReport.user_id == appt.patient_id)
        .order_by(MedicalReport.created_at.desc())
        .limit(20)
    ).all()
    return [MedicalReportResponse.model_validate(r) for r in reports]


@router.post(
    "/appointments/{appointment_id}/notes",
    response_model=ConsultationNoteOut,
    status_code=status.HTTP_201_CREATED,
)
def doctor_add_consultation_note(
    appointment_id: int,
    payload: ConsultationNoteCreateRequest,
    doctor_ctx: Tuple[User, DoctorProfile] = Depends(require_verified_doctor),
    db: Session = Depends(get_db),
):
    user, profile = doctor_ctx
    appt = db.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id,
            Appointment.doctor_id == profile.id,
        )
    )
    if appt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")

    note = ConsultationNote(
        appointment_id=appt.id,
        doctor_id=profile.id,
        patient_id=appt.patient_id,
        observations=payload.observations.strip(),
        notes=payload.notes.strip() if payload.notes else None,
        follow_up_recommendations=(
            payload.follow_up_recommendations.strip()
            if payload.follow_up_recommendations
            else None
        ),
        treatment_info=payload.treatment_info.strip() if payload.treatment_info else None,
        is_shareable=payload.is_shareable,
    )
    db.add(note)
    if payload.is_shareable:
        create_notification(
            db,
            user_id=appt.patient_id,
            title="New Consultation Note Available",
            message=f"{user.full_name} added consultation notes for your {appt.appointment_date.isoformat()} appointment.",
            notification_type="consultation_note",
            related_route="/appointments",
        )
    db.commit()
    db.refresh(note)
    return ConsultationNoteOut.model_validate(note)


@router.get("/availability", response_model=List[DoctorAvailabilityRuleOut])
def doctor_get_availability(
    doctor_ctx: Tuple[User, DoctorProfile] = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    _, profile = doctor_ctx
    rows = db.scalars(
        select(DoctorAvailability)
        .where(DoctorAvailability.doctor_id == profile.id)
        .order_by(DoctorAvailability.day_of_week.asc(), DoctorAvailability.start_time.asc())
    ).all()
    return [DoctorAvailabilityRuleOut.model_validate(r) for r in rows]


@router.put("/availability", response_model=List[DoctorAvailabilityRuleOut])
def doctor_replace_availability(
    rules: List[DoctorAvailabilityRuleIn],
    doctor_ctx: Tuple[User, DoctorProfile] = Depends(require_verified_doctor),
    db: Session = Depends(get_db),
):
    _, profile = doctor_ctx
    existing = db.scalars(
        select(DoctorAvailability).where(DoctorAvailability.doctor_id == profile.id)
    ).all()
    for row in existing:
        db.delete(row)
    db.flush()

    created = []
    for r in rules:
        row = DoctorAvailability(
            doctor_id=profile.id,
            day_of_week=r.day_of_week,
            start_time=r.start_time,
            end_time=r.end_time,
            slot_duration_minutes=r.slot_duration_minutes,
            break_start=r.break_start,
            break_end=r.break_end,
            is_active=r.is_active,
        )
        db.add(row)
        created.append(row)
    db.commit()
    for row in created:
        db.refresh(row)
    return [DoctorAvailabilityRuleOut.model_validate(r) for r in created]


@router.get("/leaves", response_model=List[DoctorLeaveOut])
def doctor_list_leaves(
    doctor_ctx: Tuple[User, DoctorProfile] = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    _, profile = doctor_ctx
    rows = db.scalars(
        select(DoctorLeave)
        .where(DoctorLeave.doctor_id == profile.id)
        .order_by(DoctorLeave.leave_date.asc())
    ).all()
    return [DoctorLeaveOut.model_validate(r) for r in rows]


@router.post(
    "/leaves",
    response_model=DoctorLeaveOut,
    status_code=status.HTTP_201_CREATED,
)
def doctor_add_leave(
    payload: DoctorLeaveCreateRequest,
    doctor_ctx: Tuple[User, DoctorProfile] = Depends(require_verified_doctor),
    db: Session = Depends(get_db),
):
    _, profile = doctor_ctx
    leave = DoctorLeave(
        doctor_id=profile.id,
        leave_date=payload.leave_date,
        reason=payload.reason.strip() if payload.reason else None,
        is_holiday=payload.is_holiday,
    )
    db.add(leave)
    db.commit()
    db.refresh(leave)
    return DoctorLeaveOut.model_validate(leave)


@router.delete("/leaves/{leave_id}", response_model=MessageResponse)
def doctor_delete_leave(
    leave_id: int,
    doctor_ctx: Tuple[User, DoctorProfile] = Depends(require_verified_doctor),
    db: Session = Depends(get_db),
):
    _, profile = doctor_ctx
    leave = db.scalar(
        select(DoctorLeave).where(
            DoctorLeave.id == leave_id,
            DoctorLeave.doctor_id == profile.id,
        )
    )
    if leave is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Leave entry not found")
    db.delete(leave)
    db.commit()
    return MessageResponse(message="Leave date removed")


@router.get("/profile", response_model=DoctorDetailOut)
def doctor_get_own_profile(
    doctor_ctx: Tuple[User, DoctorProfile] = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    user, profile = doctor_ctx
    return DoctorDetailOut(
        id=profile.id,
        user_id=user.id,
        full_name=user.full_name,
        qualification=profile.qualification,
        specialization=profile.specialization,
        experience_years=profile.experience_years,
        hospital_id=profile.hospital_id,
        hospital_name=profile.hospital.name if profile.hospital else None,
        hospital_city=profile.hospital.city if profile.hospital else None,
        hospital_district=profile.hospital.district if profile.hospital else None,
        department_name=profile.department.name if profile.department else None,
        languages=profile.languages or [],
        consultation_fee=profile.consultation_fee,
        profile_image_url=profile.profile_image_url,
        verification_status=profile.verification_status,
        bio=profile.bio,
        license_number=profile.license_number,
        verified_at=profile.verified_at,
        hospital_address=profile.hospital.address if profile.hospital else None,
        hospital_phone=profile.hospital.phone if profile.hospital else None,
        availability=[
            DoctorAvailabilityRuleOut.model_validate(a)
            for a in profile.availability_slots
            if a.is_active
        ],
    )


@router.patch("/profile", response_model=DoctorDetailOut)
def doctor_update_own_profile(
    payload: DoctorProfileUpdateRequest,
    doctor_ctx: Tuple[User, DoctorProfile] = Depends(require_doctor),
    db: Session = Depends(get_db),
):
    user, profile = doctor_ctx
    if payload.full_name is not None:
        user.full_name = payload.full_name.strip()
    if payload.phone is not None:
        user.phone = payload.phone.strip() or None
    if payload.languages is not None:
        profile.languages = [l.strip() for l in payload.languages if l.strip()] or ["English"]
    if payload.consultation_fee is not None:
        profile.consultation_fee = payload.consultation_fee
    if payload.bio is not None:
        profile.bio = payload.bio.strip() or None
    if payload.profile_image_url is not None:
        profile.profile_image_url = payload.profile_image_url.strip() or None

    db.commit()
    db.refresh(user)
    db.refresh(profile)
    return doctor_get_own_profile(doctor_ctx=(user, profile), db=db)
