from datetime import date, datetime, time
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user, require_patient
from app.database.session import get_db
from app.models.appointment import Appointment, ConsultationNote, Notification
from app.models.doctor import DoctorProfile
from app.models.hospital import Hospital
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.healthcare import (
    AppointmentCancelRequest,
    AppointmentCreateRequest,
    AppointmentOut,
    AppointmentRescheduleRequest,
    ConsultationNoteOut,
    NotificationOut,
)
from app.services.activity_service import record_activity
from app.services.appointment_service import (
    ACTIVE_APPOINTMENT_STATUSES,
    compute_doctor_slots,
)
from app.services.notification_service import create_notification

router = APIRouter(tags=["Appointments & Notifications"])


def serialize_appointment(
    appt: Appointment, *, include_private_notes: bool = False
) -> AppointmentOut:
    notes_list = [
        ConsultationNoteOut.model_validate(n)
        for n in appt.consultation_notes
        if include_private_notes or n.is_shareable
    ]
    return AppointmentOut(
        id=appt.id,
        patient_id=appt.patient_id,
        patient_name=appt.patient.full_name,
        patient_email=appt.patient.email,
        patient_phone=appt.patient.phone,
        doctor_id=appt.doctor_id,
        doctor_name=appt.doctor.user.full_name,
        doctor_specialization=appt.doctor.specialization,
        hospital_id=appt.hospital_id,
        hospital_name=appt.hospital.name,
        hospital_city=appt.hospital.city,
        department_id=appt.department_id,
        department_name=appt.department.name if appt.department else None,
        appointment_date=appt.appointment_date,
        appointment_time=appt.appointment_time,
        reason=appt.reason,
        status=appt.status,
        cancellation_reason=appt.cancellation_reason,
        rescheduled_from_date=appt.rescheduled_from_date,
        rescheduled_from_time=appt.rescheduled_from_time,
        share_reports=appt.share_reports,
        consultation_notes=notes_list,
        created_at=appt.created_at,
        updated_at=appt.updated_at,
    )


def _validate_slot_for_booking(
    db: Session,
    *,
    doctor: DoctorProfile,
    target_date: date,
    target_time: time,
) -> None:
    slots, reason = compute_doctor_slots(db, doctor=doctor, target_date=target_date)
    if reason:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=reason)
    target_hhmm = target_time.strftime("%H:%M")
    matched = next((s for s in slots if s["time"] == target_hhmm), None)
    if matched is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected time is outside the doctor's available slot schedule",
        )
    if not matched["available"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This appointment slot has already been booked",
        )


@router.post(
    "/appointments",
    response_model=AppointmentOut,
    status_code=status.HTTP_201_CREATED,
)
def book_appointment(
    payload: AppointmentCreateRequest,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    doctor = db.scalar(
        select(DoctorProfile)
        .options(joinedload(DoctorProfile.user))
        .where(
            DoctorProfile.id == payload.doctor_id,
            DoctorProfile.verification_status == "verified",
        )
    )
    if doctor is None or not doctor.user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verified doctor not found",
        )

    hospital = db.scalar(
        select(Hospital).where(
            Hospital.id == payload.hospital_id,
            Hospital.is_published.is_(True),
            Hospital.is_active.is_(True),
        )
    )
    if hospital is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")

    if doctor.hospital_id and doctor.hospital_id != hospital.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Selected doctor is not affiliated with this hospital",
        )

    # Prevent duplicate booking by same patient for the same doctor & date/time
    dup_patient = db.scalar(
        select(Appointment).where(
            Appointment.patient_id == current_user.id,
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_date == payload.appointment_date,
            Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES),
        )
    )
    if dup_patient is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have an active appointment with this doctor on the selected date",
        )

    _validate_slot_for_booking(
        db,
        doctor=doctor,
        target_date=payload.appointment_date,
        target_time=payload.appointment_time,
    )

    appt = Appointment(
        patient_id=current_user.id,
        doctor_id=doctor.id,
        hospital_id=hospital.id,
        department_id=payload.department_id or doctor.department_id,
        appointment_date=payload.appointment_date,
        appointment_time=payload.appointment_time.replace(second=0, microsecond=0),
        reason=payload.reason.strip(),
        status="pending",
        share_reports=payload.share_reports,
    )
    db.add(appt)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This appointment slot was just booked by another patient. Please pick another slot.",
        )

    create_notification(
        db,
        user_id=current_user.id,
        title="Appointment Request Submitted",
        message=f"Appointment with {doctor.user.full_name} at {hospital.name} on {payload.appointment_date.isoformat()} at {payload.appointment_time.strftime('%H:%M')} is pending confirmation.",
        notification_type="appointment",
        related_route="/appointments",
    )
    create_notification(
        db,
        user_id=doctor.user_id,
        title="New Appointment Request",
        message=f"Patient {current_user.full_name} requested a consultation on {payload.appointment_date.isoformat()} at {payload.appointment_time.strftime('%H:%M')}.",
        notification_type="appointment",
        related_route="/doctor/appointments",
    )
    record_activity(
        db,
        user_id=current_user.id,
        activity_type="appointment_booked",
        title=f"Booked appointment with {doctor.user.full_name}",
        description=f"{hospital.name} · {payload.appointment_date.isoformat()} {payload.appointment_time.strftime('%H:%M')}",
        reference_id=str(appt.id),
        reference_type="appointment",
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This appointment slot is no longer available.",
        )

    loaded = db.scalar(
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor).joinedload(DoctorProfile.user),
            joinedload(Appointment.hospital),
            joinedload(Appointment.department),
            joinedload(Appointment.consultation_notes),
        )
        .where(Appointment.id == appt.id)
    )
    return serialize_appointment(loaded, include_private_notes=False)


@router.get("/appointments/my", response_model=List[AppointmentOut])
def list_my_appointments(
    status_filter: Optional[str] = Query(default=None),
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Appointment)
        .options(
            joinedload(Appointment.patient),
            joinedload(Appointment.doctor).joinedload(DoctorProfile.user),
            joinedload(Appointment.hospital),
            joinedload(Appointment.department),
            joinedload(Appointment.consultation_notes),
        )
        .where(Appointment.patient_id == current_user.id)
    )
    if status_filter and status_filter != "all":
        stmt = stmt.where(Appointment.status == status_filter)
    rows = db.scalars(
        stmt.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
    ).unique().all()
    return [serialize_appointment(a, include_private_notes=False) for a in rows]


@router.patch("/appointments/{appointment_id}/cancel", response_model=AppointmentOut)
def cancel_my_appointment(
    appointment_id: int,
    payload: AppointmentCancelRequest,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
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
            Appointment.patient_id == current_user.id,
        )
    )
    if appt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if appt.status not in ACTIVE_APPOINTMENT_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel an appointment with status '{appt.status}'",
        )

    appt.status = "cancelled"
    appt.cancellation_reason = payload.cancellation_reason.strip()
    create_notification(
        db,
        user_id=current_user.id,
        title="Appointment Cancelled",
        message=f"Your appointment on {appt.appointment_date.isoformat()} with {appt.doctor.user.full_name} was cancelled.",
        notification_type="appointment",
        related_route="/appointments",
    )
    create_notification(
        db,
        user_id=appt.doctor.user_id,
        title="Patient Cancelled Appointment",
        message=f"{current_user.full_name} cancelled the {appt.appointment_date.isoformat()} {appt.appointment_time.strftime('%H:%M')} appointment.",
        notification_type="appointment",
        related_route="/doctor/appointments",
    )
    db.commit()
    db.refresh(appt)
    return serialize_appointment(appt, include_private_notes=False)


@router.patch("/appointments/{appointment_id}/reschedule", response_model=AppointmentOut)
def reschedule_my_appointment(
    appointment_id: int,
    payload: AppointmentRescheduleRequest,
    current_user: User = Depends(require_patient),
    db: Session = Depends(get_db),
):
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
            Appointment.patient_id == current_user.id,
        )
    )
    if appt is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appointment not found")
    if appt.status not in ACTIVE_APPOINTMENT_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot reschedule an appointment with status '{appt.status}'",
        )

    _validate_slot_for_booking(
        db,
        doctor=appt.doctor,
        target_date=payload.appointment_date,
        target_time=payload.appointment_time,
    )

    appt.rescheduled_from_date = appt.appointment_date
    appt.rescheduled_from_time = appt.appointment_time
    appt.appointment_date = payload.appointment_date
    appt.appointment_time = payload.appointment_time.replace(second=0, microsecond=0)
    appt.status = "rescheduled"

    create_notification(
        db,
        user_id=current_user.id,
        title="Appointment Rescheduled",
        message=f"Rescheduled to {payload.appointment_date.isoformat()} at {payload.appointment_time.strftime('%H:%M')} with {appt.doctor.user.full_name}.",
        notification_type="appointment",
        related_route="/appointments",
    )
    create_notification(
        db,
        user_id=appt.doctor.user_id,
        title="Appointment Rescheduled by Patient",
        message=f"{current_user.full_name} moved appointment to {payload.appointment_date.isoformat()} at {payload.appointment_time.strftime('%H:%M')}.",
        notification_type="appointment",
        related_route="/doctor/appointments",
    )
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Selected reschedule slot is already taken.",
        )
    db.refresh(appt)
    return serialize_appointment(appt, include_private_notes=False)


# -------- Notifications --------

@router.get("/notifications", response_model=List[NotificationOut])
def list_notifications(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(Notification)
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
        .limit(50)
    ).all()
    return [NotificationOut.model_validate(n) for n in rows]


@router.patch("/notifications/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notif = db.scalar(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    if notif is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return NotificationOut.model_validate(notif)


@router.post("/notifications/read-all", response_model=MessageResponse)
def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = db.scalars(
        select(Notification).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    ).all()
    for n in rows:
        n.is_read = True
    db.commit()
    return MessageResponse(message="All notifications marked as read")
