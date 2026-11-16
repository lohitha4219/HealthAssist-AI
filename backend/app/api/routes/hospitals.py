import re
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_maintenance_key
from app.api.routes.public import _to_hospital_summary, to_doctor_compact
from app.database.session import get_db
from app.models.doctor import DoctorProfile
from app.models.hospital import (
    Hospital,
    HospitalDepartment,
    HospitalFacility,
    HospitalTreatment,
)
from app.schemas.healthcare import (
    HospitalDepartmentOut,
    HospitalDetailOut,
    HospitalFacilityOut,
    HospitalListResponse,
    HospitalMaintainCreateRequest,
    HospitalMaintainUpdateRequest,
    HospitalTreatmentOut,
)

router = APIRouter(prefix="/hospitals", tags=["Hospitals"])


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:200] or "hospital"


@router.get("/filters", response_model=Dict[str, List[str]])
def get_hospital_filters(db: Session = Depends(get_db)):
    districts = sorted(
        {
            d
            for d in db.scalars(
                select(Hospital.district).where(
                    Hospital.is_published.is_(True), Hospital.is_active.is_(True)
                )
            ).all()
            if d
        }
    )
    cities = sorted(
        {
            c
            for c in db.scalars(
                select(Hospital.city).where(
                    Hospital.is_published.is_(True), Hospital.is_active.is_(True)
                )
            ).all()
            if c
        }
    )
    specialties = sorted(
        {
            s
            for s in db.scalars(
                select(HospitalTreatment.specialty)
                .join(Hospital, HospitalTreatment.hospital_id == Hospital.id)
                .where(Hospital.is_published.is_(True), Hospital.is_active.is_(True))
            ).all()
            if s
        }
    )
    facilities = sorted(
        {
            f
            for f in db.scalars(
                select(HospitalFacility.name)
                .join(Hospital, HospitalFacility.hospital_id == Hospital.id)
                .where(Hospital.is_published.is_(True), Hospital.is_active.is_(True))
            ).all()
            if f
        }
    )
    return {
        "districts": districts,
        "cities": cities,
        "specialties": specialties,
        "facilities": facilities,
    }


@router.get("", response_model=HospitalListResponse)
def list_hospitals(
    search: Optional[str] = Query(default=None, max_length=120),
    district: Optional[str] = Query(default=None, max_length=100),
    city: Optional[str] = Query(default=None, max_length=100),
    specialization: Optional[str] = Query(default=None, max_length=120),
    treatment: Optional[str] = Query(default=None, max_length=120),
    facility: Optional[str] = Query(default=None, max_length=120),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    stmt = select(Hospital).where(
        Hospital.is_published.is_(True), Hospital.is_active.is_(True)
    )

    if district and district.strip() and district.lower() != "all":
        stmt = stmt.where(func.lower(Hospital.district) == district.strip().lower())
    if city and city.strip() and city.lower() != "all":
        stmt = stmt.where(func.lower(Hospital.city) == city.strip().lower())
    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                Hospital.name.ilike(term),
                Hospital.city.ilike(term),
                Hospital.district.ilike(term),
                Hospital.hospital_type.ilike(term),
            )
        )
    if specialization and specialization.strip() and specialization.lower() != "all":
        spec_term = f"%{specialization.strip()}%"
        dept_sub = select(HospitalDepartment.hospital_id).where(
            HospitalDepartment.name.ilike(spec_term)
        )
        treat_sub = select(HospitalTreatment.hospital_id).where(
            HospitalTreatment.specialty.ilike(spec_term)
        )
        stmt = stmt.where(or_(Hospital.id.in_(dept_sub), Hospital.id.in_(treat_sub)))
    if treatment and treatment.strip():
        t_term = f"%{treatment.strip()}%"
        treat_sub = select(HospitalTreatment.hospital_id).where(
            or_(
                HospitalTreatment.name.ilike(t_term),
                HospitalTreatment.specialty.ilike(t_term),
            )
        )
        stmt = stmt.where(Hospital.id.in_(treat_sub))
    if facility and facility.strip() and facility.lower() != "all":
        f_term = f"%{facility.strip()}%"
        fac_sub = select(HospitalFacility.hospital_id).where(
            HospitalFacility.name.ilike(f_term)
        )
        stmt = stmt.where(Hospital.id.in_(fac_sub))

    all_matching = db.scalars(stmt.order_by(Hospital.name.asc())).all()
    total = len(all_matching)
    page_items = all_matching[(page - 1) * page_size : page * page_size]

    return HospitalListResponse(
        items=[_to_hospital_summary(db, h) for h in page_items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{hospital_id}", response_model=HospitalDetailOut)
def get_hospital_detail(hospital_id: int, db: Session = Depends(get_db)):
    hospital = db.scalar(
        select(Hospital).where(
            Hospital.id == hospital_id,
            Hospital.is_published.is_(True),
            Hospital.is_active.is_(True),
        )
    )
    if hospital is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hospital not found",
        )

    departments = db.scalars(
        select(HospitalDepartment)
        .where(HospitalDepartment.hospital_id == hospital.id)
        .order_by(HospitalDepartment.name.asc())
    ).all()
    facilities = db.scalars(
        select(HospitalFacility)
        .where(HospitalFacility.hospital_id == hospital.id)
        .order_by(HospitalFacility.name.asc())
    ).all()
    treatments = db.scalars(
        select(HospitalTreatment)
        .where(HospitalTreatment.hospital_id == hospital.id)
        .order_by(HospitalTreatment.name.asc())
    ).all()
    doctors = db.scalars(
        select(DoctorProfile)
        .options(
            joinedload(DoctorProfile.user),
            joinedload(DoctorProfile.hospital),
            joinedload(DoctorProfile.department),
        )
        .where(
            DoctorProfile.hospital_id == hospital.id,
            DoctorProfile.verification_status == "verified",
        )
        .order_by(DoctorProfile.id.asc())
    ).all()

    summary = _to_hospital_summary(db, hospital)
    return HospitalDetailOut(
        **summary.model_dump(),
        email=hospital.email,
        description=hospital.description,
        source_reference=hospital.source_reference,
        departments=[HospitalDepartmentOut.model_validate(d) for d in departments],
        facilities=[HospitalFacilityOut.model_validate(f) for f in facilities],
        treatments=[HospitalTreatmentOut.model_validate(t) for t in treatments],
        doctors=[to_doctor_compact(d) for d in doctors],
    )


@router.post(
    "/maintain",
    response_model=HospitalDetailOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_maintenance_key)],
)
def maintain_create_hospital(
    payload: HospitalMaintainCreateRequest,
    db: Session = Depends(get_db),
):
    base_slug = _slugify(payload.name)
    slug = base_slug
    idx = 2
    while db.scalar(select(Hospital).where(Hospital.slug == slug)) is not None:
        slug = f"{base_slug}-{idx}"
        idx += 1

    hospital = Hospital(
        name=payload.name.strip(),
        slug=slug,
        hospital_type=payload.hospital_type.strip(),
        address=payload.address.strip(),
        city=payload.city.strip(),
        district=payload.district.strip(),
        state=payload.state.strip(),
        pincode=payload.pincode,
        phone=payload.phone,
        emergency_phone=payload.emergency_phone,
        email=str(payload.email) if payload.email else None,
        website=payload.website,
        operating_hours=payload.operating_hours,
        emergency_info=payload.emergency_info,
        description=payload.description,
        source_reference=payload.source_reference,
        verification_status=payload.verification_status,
        is_published=payload.is_published and payload.verification_status == "verified",
        is_active=True,
    )
    db.add(hospital)
    db.flush()

    for dept_name in payload.departments:
        if dept_name.strip():
            db.add(
                HospitalDepartment(
                    hospital_id=hospital.id,
                    name=dept_name.strip(),
                    is_verified=payload.verification_status == "verified",
                )
            )
    for fac_name in payload.facilities:
        if fac_name.strip():
            db.add(
                HospitalFacility(
                    hospital_id=hospital.id,
                    name=fac_name.strip(),
                    is_verified=payload.verification_status == "verified",
                )
            )
    for tr in payload.treatments:
        t_name = (tr.get("name") or "").strip()
        t_spec = (tr.get("specialty") or "").strip()
        if t_name and t_spec:
            db.add(
                HospitalTreatment(
                    hospital_id=hospital.id,
                    name=t_name,
                    specialty=t_spec,
                    description=tr.get("description"),
                    is_verified=payload.verification_status == "verified",
                )
            )
    db.commit()
    db.refresh(hospital)
    summary = _to_hospital_summary(db, hospital)
    return HospitalDetailOut(
        **summary.model_dump(),
        email=hospital.email,
        description=hospital.description,
        source_reference=hospital.source_reference,
    )


@router.patch(
    "/maintain/{hospital_id}",
    response_model=HospitalDetailOut,
    dependencies=[Depends(require_maintenance_key)],
)
def maintain_update_hospital(
    hospital_id: int,
    payload: HospitalMaintainUpdateRequest,
    db: Session = Depends(get_db),
):
    hospital = db.get(Hospital, hospital_id)
    if hospital is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")

    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(hospital, field, val)
    if hospital.verification_status != "verified":
        hospital.is_published = False

    db.commit()
    db.refresh(hospital)
    summary = _to_hospital_summary(db, hospital)
    return HospitalDetailOut(
        **summary.model_dump(),
        email=hospital.email,
        description=hospital.description,
        source_reference=hospital.source_reference,
    )
