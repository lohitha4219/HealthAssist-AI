from datetime import date, time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.routes.public import to_doctor_compact
from app.database.session import get_db
from app.models.doctor import DoctorProfile
from app.models.hospital import Hospital
from app.models.user import User
from app.schemas.healthcare import (
    DoctorAvailabilityRuleOut,
    DoctorDetailOut,
    DoctorListResponse,
    DoctorSlotItem,
    DoctorSlotsResponse,
)
from app.services.appointment_service import compute_doctor_slots

router = APIRouter(prefix="/doctors", tags=["Doctors"])


@router.get("", response_model=DoctorListResponse)
def list_doctors(
    search: Optional[str] = Query(default=None, max_length=120),
    specialization: Optional[str] = Query(default=None, max_length=120),
    hospital_id: Optional[int] = Query(default=None),
    city: Optional[str] = Query(default=None, max_length=100),
    district: Optional[str] = Query(default=None, max_length=100),
    available_date: Optional[date] = Query(default=None),
    available_time: Optional[time] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    stmt = (
        select(DoctorProfile)
        .join(User, DoctorProfile.user_id == User.id)
        .outerjoin(Hospital, DoctorProfile.hospital_id == Hospital.id)
        .options(
            joinedload(DoctorProfile.user),
            joinedload(DoctorProfile.hospital),
            joinedload(DoctorProfile.department),
        )
        .where(
            DoctorProfile.verification_status == "verified",
            User.is_active.is_(True),
        )
    )

    if hospital_id is not None:
        stmt = stmt.where(DoctorProfile.hospital_id == hospital_id)
    if specialization and specialization.strip() and specialization.lower() != "all":
        stmt = stmt.where(DoctorProfile.specialization.ilike(f"%{specialization.strip()}%"))
    if city and city.strip() and city.lower() != "all":
        stmt = stmt.where(func.lower(Hospital.city) == city.strip().lower())
    if district and district.strip() and district.lower() != "all":
        stmt = stmt.where(func.lower(Hospital.district) == district.strip().lower())
    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                User.full_name.ilike(term),
                DoctorProfile.specialization.ilike(term),
                DoctorProfile.qualification.ilike(term),
                Hospital.name.ilike(term),
            )
        )

    candidates = db.scalars(stmt.order_by(DoctorProfile.id.asc())).all()

    if available_date is not None:
        filtered = []
        target_hhmm = available_time.strftime("%H:%M") if available_time else None
        for doc in candidates:
            slots, _ = compute_doctor_slots(db, doctor=doc, target_date=available_date)
            open_slots = [s for s in slots if s["available"]]
            if target_hhmm:
                if any(s["time"] == target_hhmm for s in open_slots):
                    filtered.append(doc)
            elif open_slots:
                filtered.append(doc)
        candidates = filtered

    total = len(candidates)
    page_items = candidates[(page - 1) * page_size : page * page_size]

    return DoctorListResponse(
        items=[to_doctor_compact(d) for d in page_items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{doctor_id}", response_model=DoctorDetailOut)
def get_doctor_detail(doctor_id: int, db: Session = Depends(get_db)):
    doc = db.scalar(
        select(DoctorProfile)
        .options(
            joinedload(DoctorProfile.user),
            joinedload(DoctorProfile.hospital),
            joinedload(DoctorProfile.department),
            joinedload(DoctorProfile.availability_slots),
        )
        .where(
            DoctorProfile.id == doctor_id,
            DoctorProfile.verification_status == "verified",
        )
    )
    if doc is None or not doc.user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    base = to_doctor_compact(doc)
    return DoctorDetailOut(
        **base.model_dump(),
        bio=doc.bio,
        license_number=doc.license_number,
        verified_at=doc.verified_at,
        hospital_address=doc.hospital.address if doc.hospital else None,
        hospital_phone=doc.hospital.phone if doc.hospital else None,
        hospital_emergency_phone=doc.hospital.emergency_phone if doc.hospital else None,
        hospital_website=doc.hospital.website if doc.hospital else None,
        availability=[
            DoctorAvailabilityRuleOut.model_validate(a)
            for a in doc.availability_slots
            if a.is_active
        ],
    )


@router.get("/{doctor_id}/slots", response_model=DoctorSlotsResponse)
def get_doctor_slots(
    doctor_id: int,
    date_param: date = Query(..., alias="date"),
    db: Session = Depends(get_db),
):
    doc = db.scalar(
        select(DoctorProfile)
        .options(joinedload(DoctorProfile.user))
        .where(
            DoctorProfile.id == doctor_id,
            DoctorProfile.verification_status == "verified",
        )
    )
    if doc is None or not doc.user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Doctor not found")

    slots, reason = compute_doctor_slots(db, doctor=doc, target_date=date_param)
    return DoctorSlotsResponse(
        doctor_id=doc.id,
        date=date_param,
        slots=[DoctorSlotItem(**s) for s in slots],
        unavailable_reason=reason,
    )
