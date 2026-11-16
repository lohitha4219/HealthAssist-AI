from datetime import date, datetime, time, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.doctor import DoctorAvailability, DoctorLeave, DoctorProfile


ACTIVE_APPOINTMENT_STATUSES = {"pending", "confirmed", "rescheduled"}


def compute_doctor_slots(
    db: Session,
    *,
    doctor: DoctorProfile,
    target_date: date,
    now_dt: Optional[datetime] = None,
) -> Tuple[List[dict], Optional[str]]:
    """Compute real bookable slots from doctor availability, leaves, and active bookings.

    Returns (slots_list, reason_if_unavailable). Never invents availability.
    """
    current_dt = now_dt or datetime.now()
    if target_date < current_dt.date():
        return [], "Cannot book appointments in the past."

    if doctor.verification_status != "verified":
        return [], "Doctor profile is pending credential verification."

    leave_row = db.scalar(
        select(DoctorLeave).where(
            DoctorLeave.doctor_id == doctor.id,
            DoctorLeave.leave_date == target_date,
        )
    )
    if leave_row is not None:
        note = leave_row.reason or ("Hospital/Doctor holiday" if leave_row.is_holiday else "Doctor unavailable / on leave")
        return [], f"Doctor unavailable on {target_date.isoformat()}: {note}"

    weekday = target_date.weekday()  # 0=Mon..6=Sun
    rules = db.scalars(
        select(DoctorAvailability)
        .where(
            DoctorAvailability.doctor_id == doctor.id,
            DoctorAvailability.day_of_week == weekday,
            DoctorAvailability.is_active.is_(True),
        )
        .order_by(DoctorAvailability.start_time.asc())
    ).all()

    if not rules:
        return [], "No consultation schedule configured for this day of the week."

    booked_times = set(
        db.scalars(
            select(Appointment.appointment_time).where(
                Appointment.doctor_id == doctor.id,
                Appointment.appointment_date == target_date,
                Appointment.status.in_(ACTIVE_APPOINTMENT_STATUSES),
            )
        ).all()
    )

    slots: List[dict] = []
    seen_times = set()

    for rule in rules:
        step = max(10, min(120, rule.slot_duration_minutes or 30))
        cursor = datetime.combine(target_date, rule.start_time)
        end_dt = datetime.combine(target_date, rule.end_time)

        while cursor + timedelta(minutes=step) <= end_dt:
            slot_time: time = cursor.time()
            in_break = (
                rule.break_start is not None
                and rule.break_end is not None
                and rule.break_start <= slot_time < rule.break_end
            )
            is_past_today = target_date == current_dt.date() and cursor <= current_dt

            if not in_break and not is_past_today and slot_time not in seen_times:
                seen_times.add(slot_time)
                slots.append(
                    {
                        "time": slot_time.strftime("%H:%M"),
                        "display_time": cursor.strftime("%I:%M %p").lstrip("0"),
                        "available": slot_time not in booked_times,
                    }
                )
            cursor += timedelta(minutes=step)

    if not slots:
        return [], "No open consultation slots remain for this date."
    return slots, None
