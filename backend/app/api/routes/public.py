from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.database.session import get_db
from app.models.appointment import Appointment
from app.models.doctor import DoctorProfile
from app.models.education_contact import ContactEnquiry, TreatmentEducation
from app.models.hospital import (
    Hospital,
    HospitalDepartment,
    HospitalTreatment,
)
from app.schemas.healthcare import (
    ContactEnquiryRequest,
    ContactEnquiryResponse,
    DoctorCompactOut,
    HospitalSummaryOut,
    PublicOverviewResponse,
    TreatmentEducationOut,
)
from app.services.email_service import is_smtp_configured, send_contact_enquiry_email

router = APIRouter(tags=["Public & Education"])


def _to_hospital_summary(db: Session, h: Hospital) -> HospitalSummaryOut:
    dept_count = db.scalar(
        select(func.count(HospitalDepartment.id)).where(
            HospitalDepartment.hospital_id == h.id
        )
    ) or 0
    treat_count = db.scalar(
        select(func.count(HospitalTreatment.id)).where(
            HospitalTreatment.hospital_id == h.id
        )
    ) or 0
    doc_count = db.scalar(
        select(func.count(DoctorProfile.id)).where(
            DoctorProfile.hospital_id == h.id,
            DoctorProfile.verification_status == "verified",
        )
    ) or 0
    return HospitalSummaryOut(
        id=h.id,
        name=h.name,
        slug=h.slug,
        hospital_type=h.hospital_type,
        address=h.address,
        city=h.city,
        district=h.district,
        state=h.state,
        pincode=h.pincode,
        phone=h.phone,
        emergency_phone=h.emergency_phone,
        website=h.website,
        image_url=h.image_url,
        operating_hours=h.operating_hours,
        emergency_info=h.emergency_info,
        verification_status=h.verification_status,
        department_count=dept_count,
        treatment_count=treat_count,
        doctor_count=doc_count,
    )


def to_doctor_compact(doc: DoctorProfile) -> DoctorCompactOut:
    return DoctorCompactOut(
        id=doc.id,
        user_id=doc.user_id,
        full_name=doc.user.full_name if doc.user else "Verified Specialist",
        qualification=doc.qualification,
        specialization=doc.specialization,
        experience_years=doc.experience_years,
        hospital_id=doc.hospital_id,
        hospital_name=doc.hospital.name if doc.hospital else None,
        hospital_city=doc.hospital.city if doc.hospital else None,
        hospital_district=doc.hospital.district if doc.hospital else None,
        department_name=doc.department.name if doc.department else None,
        languages=doc.languages or [],
        consultation_fee=doc.consultation_fee,
        profile_image_url=doc.profile_image_url,
        verification_status=doc.verification_status,
        designation=getattr(doc, "designation", None),
        published_timings=getattr(doc, "published_timings", None),
        official_source_url=getattr(doc, "official_source_url", None),
        listing_source=getattr(doc, "listing_source", "official_directory"),
    )


@router.get("/public/overview", response_model=PublicOverviewResponse)
def get_public_overview(db: Session = Depends(get_db)):
    settings = get_settings()
    hospitals_count = db.scalar(
        select(func.count(Hospital.id)).where(
            Hospital.is_published.is_(True), Hospital.is_active.is_(True)
        )
    ) or 0
    doctors_count = db.scalar(
        select(func.count(DoctorProfile.id)).where(
            DoctorProfile.verification_status == "verified"
        )
    ) or 0
    specialties_count = db.scalar(select(func.count(TreatmentEducation.id))) or 0
    appointments_count = db.scalar(select(func.count(Appointment.id))) or 0
    departments_count = db.scalar(select(func.count(HospitalDepartment.id))) or 0

    featured_hospitals = db.scalars(
        select(Hospital)
        .where(Hospital.is_published.is_(True), Hospital.is_active.is_(True))
        .order_by(Hospital.id.asc())
        .limit(6)
    ).all()

    featured_doctors = db.scalars(
        select(DoctorProfile)
        .options(
            joinedload(DoctorProfile.user),
            joinedload(DoctorProfile.hospital),
            joinedload(DoctorProfile.department),
        )
        .where(DoctorProfile.verification_status == "verified")
        .order_by(DoctorProfile.id.asc())
        .limit(6)
    ).all()

    return PublicOverviewResponse(
        stats={
            "verified_hospitals": hospitals_count,
            "verified_doctors": doctors_count,
            "specialties": specialties_count,
            "departments": departments_count,
            "appointments": appointments_count,
        },
        featured_hospitals=[_to_hospital_summary(db, h) for h in featured_hospitals],
        featured_doctors=[to_doctor_compact(d) for d in featured_doctors],
        support={
            "email": settings.SUPPORT_EMAIL,
            "phone": settings.SUPPORT_PHONE,
            "address": settings.SUPPORT_ADDRESS,
        },
    )


@router.post(
    "/contact",
    response_model=ContactEnquiryResponse,
    status_code=status.HTTP_201_CREATED,
)
def submit_contact_enquiry(
    payload: ContactEnquiryRequest,
    db: Session = Depends(get_db),
):
    enquiry = ContactEnquiry(
        name=payload.name.strip(),
        email=str(payload.email).strip().lower(),
        subject=payload.subject.strip(),
        message=payload.message.strip(),
        status="received",
    )
    db.add(enquiry)
    db.commit()
    db.refresh(enquiry)

    # Attempt real SMTP email delivery to nslohitha2924@gmail.com
    delivered, detail = send_contact_enquiry_email(enquiry)
    if delivered:
        enquiry.status = "sent"
        db.commit()
        return ContactEnquiryResponse(
            id=enquiry.id,
            message=f"Thank you, {enquiry.name}! Your enquiry has been delivered successfully to our support team at nslohitha2924@gmail.com.",
            created_at=enquiry.created_at,
            email_delivered=True,
            delivery_status="sent",
        )
    else:
        enquiry.status = "failed" if is_smtp_configured() else "unconfigured"
        db.commit()
        return ContactEnquiryResponse(
            id=enquiry.id,
            message=(
                f"Your enquiry has been saved to our database. Note: {detail}"
            ),
            created_at=enquiry.created_at,
            email_delivered=False,
            delivery_status=enquiry.status,
        )


@router.get("/treatments", response_model=List[TreatmentEducationOut])
def list_treatments(db: Session = Depends(get_db)):
    items = db.scalars(
        select(TreatmentEducation).order_by(TreatmentEducation.specialty.asc())
    ).all()
    results: List[TreatmentEducationOut] = []
    for item in items:
        verified_rows = db.execute(
            select(Hospital.id, Hospital.name, Hospital.city, Hospital.district, HospitalTreatment.name)
            .join(HospitalTreatment, HospitalTreatment.hospital_id == Hospital.id)
            .where(
                Hospital.is_published.is_(True),
                Hospital.is_active.is_(True),
                HospitalTreatment.is_verified.is_(True),
                func.lower(HospitalTreatment.specialty) == item.specialty.lower(),
            )
        ).all()
        out = TreatmentEducationOut.model_validate(item)
        out.verified_hospitals = [
            {
                "hospital_id": r[0],
                "hospital_name": r[1],
                "city": r[2],
                "district": r[3],
                "treatment_name": r[4],
            }
            for r in verified_rows
        ]
        results.append(out)
    return results


@router.get("/treatments/{slug}", response_model=TreatmentEducationOut)
def get_treatment_detail(slug: str, db: Session = Depends(get_db)):
    item = db.scalar(select(TreatmentEducation).where(TreatmentEducation.slug == slug))
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Treatment education specialty not found",
        )
    verified_rows = db.execute(
        select(Hospital.id, Hospital.name, Hospital.city, Hospital.district, HospitalTreatment.name)
        .join(HospitalTreatment, HospitalTreatment.hospital_id == Hospital.id)
        .where(
            Hospital.is_published.is_(True),
            Hospital.is_active.is_(True),
            HospitalTreatment.is_verified.is_(True),
            func.lower(HospitalTreatment.specialty) == item.specialty.lower(),
        )
    ).all()
    out = TreatmentEducationOut.model_validate(item)
    out.verified_hospitals = [
        {
            "hospital_id": r[0],
            "hospital_name": r[1],
            "city": r[2],
            "district": r[3],
            "treatment_name": r[4],
        }
        for r in verified_rows
    ]
    return out
