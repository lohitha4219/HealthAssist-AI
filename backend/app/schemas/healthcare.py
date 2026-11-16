from datetime import date, datetime, time
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.schemas.auth import NAME_PATTERN, _validate_password_strength


# -------- Hospitals --------

class HospitalDepartmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None
    is_verified: bool


class HospitalFacilityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    details: Optional[str] = None
    is_verified: bool


class HospitalTreatmentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    department_id: Optional[int] = None
    name: str
    specialty: str
    description: Optional[str] = None
    is_verified: bool


class DoctorCompactOut(BaseModel):
    id: int
    user_id: int
    full_name: str
    qualification: str
    specialization: str
    experience_years: Optional[int] = None
    hospital_id: Optional[int] = None
    hospital_name: Optional[str] = None
    hospital_city: Optional[str] = None
    hospital_district: Optional[str] = None
    department_name: Optional[str] = None
    languages: List[str] = []
    consultation_fee: Optional[float] = None
    profile_image_url: Optional[str] = None
    verification_status: str
    designation: Optional[str] = None
    published_timings: Optional[str] = None
    official_source_url: Optional[str] = None
    listing_source: Optional[str] = None


class HospitalSummaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    slug: str
    hospital_type: str
    address: str
    city: str
    district: str
    state: str
    pincode: Optional[str] = None
    phone: Optional[str] = None
    emergency_phone: Optional[str] = None
    website: Optional[str] = None
    image_url: Optional[str] = None
    operating_hours: Optional[str] = None
    emergency_info: Optional[str] = None
    verification_status: str
    department_count: int = 0
    treatment_count: int = 0
    doctor_count: int = 0


class HospitalDetailOut(HospitalSummaryOut):
    email: Optional[str] = None
    description: Optional[str] = None
    source_reference: Optional[str] = None
    departments: List[HospitalDepartmentOut] = []
    facilities: List[HospitalFacilityOut] = []
    treatments: List[HospitalTreatmentOut] = []
    doctors: List[DoctorCompactOut] = []


class HospitalListResponse(BaseModel):
    items: List[HospitalSummaryOut]
    total: int
    page: int
    page_size: int


class HospitalMaintainCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=200)
    hospital_type: str = Field(..., min_length=3, max_length=80)
    address: str = Field(..., min_length=5)
    city: str = Field(..., min_length=2, max_length=100)
    district: str = Field(..., min_length=2, max_length=100)
    state: str = Field(default="Andhra Pradesh", max_length=80)
    pincode: Optional[str] = Field(default=None, max_length=16)
    phone: Optional[str] = Field(default=None, max_length=120)
    emergency_phone: Optional[str] = Field(default=None, max_length=120)
    email: Optional[EmailStr] = None
    website: Optional[str] = Field(default=None, max_length=255)
    operating_hours: Optional[str] = Field(default=None, max_length=200)
    emergency_info: Optional[str] = None
    description: Optional[str] = None
    source_reference: Optional[str] = Field(default=None, max_length=255)
    verification_status: Literal["verified", "unverified"] = "unverified"
    is_published: bool = False
    departments: List[str] = []
    facilities: List[str] = []
    treatments: List[Dict[str, str]] = []


class HospitalMaintainUpdateRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=3, max_length=200)
    hospital_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    phone: Optional[str] = None
    emergency_phone: Optional[str] = None
    website: Optional[str] = None
    operating_hours: Optional[str] = None
    emergency_info: Optional[str] = None
    description: Optional[str] = None
    source_reference: Optional[str] = None
    verification_status: Optional[Literal["verified", "unverified"]] = None
    is_published: Optional[bool] = None
    is_active: Optional[bool] = None


# -------- Doctors & Onboarding --------

class DoctorAvailabilityRuleIn(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: time
    end_time: time
    slot_duration_minutes: int = Field(default=30, ge=10, le=120)
    break_start: Optional[time] = None
    break_end: Optional[time] = None
    is_active: bool = True

    @model_validator(mode="after")
    def validate_times(self) -> "DoctorAvailabilityRuleIn":
        if self.end_time <= self.start_time:
            raise ValueError("End time must be after start time")
        if (self.break_start is None) != (self.break_end is None):
            raise ValueError("Both break_start and break_end must be provided together")
        if self.break_start and self.break_end and self.break_end <= self.break_start:
            raise ValueError("Break end time must be after break start time")
        return self


class DoctorAvailabilityRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    day_of_week: int
    start_time: time
    end_time: time
    slot_duration_minutes: int
    break_start: Optional[time] = None
    break_end: Optional[time] = None
    is_active: bool


class DoctorLeaveCreateRequest(BaseModel):
    leave_date: date
    reason: Optional[str] = Field(default=None, max_length=255)
    is_holiday: bool = False


class DoctorLeaveOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    leave_date: date
    reason: Optional[str] = None
    is_holiday: bool
    created_at: datetime


class DoctorDetailOut(DoctorCompactOut):
    bio: Optional[str] = None
    license_number: Optional[str] = None
    verified_at: Optional[datetime] = None
    hospital_address: Optional[str] = None
    hospital_phone: Optional[str] = None
    hospital_emergency_phone: Optional[str] = None
    hospital_website: Optional[str] = None
    availability: List[DoctorAvailabilityRuleOut] = []


class DoctorListResponse(BaseModel):
    items: List[DoctorCompactOut]
    total: int
    page: int
    page_size: int


class DoctorSlotItem(BaseModel):
    time: str
    display_time: str
    available: bool


class DoctorSlotsResponse(BaseModel):
    doctor_id: int
    date: date
    slots: List[DoctorSlotItem]
    unavailable_reason: Optional[str] = None


class DoctorInviteCreateRequest(BaseModel):
    email: EmailStr
    hospital_id: Optional[int] = None
    department_id: Optional[int] = None
    specialization: Optional[str] = Field(default=None, max_length=120)
    expires_hours: int = Field(default=72, ge=1, le=720)

    @field_validator("email")
    @classmethod
    def norm_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()


class DoctorInviteResponse(BaseModel):
    message: str
    invitation_token: str
    email: str
    expires_at: datetime
    email_sent: bool = False


class DoctorRegisterRequest(BaseModel):
    invitation_token: str = Field(..., min_length=10)
    full_name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str = Field(..., min_length=8, max_length=128)
    phone: Optional[str] = Field(default=None, max_length=30)
    qualification: str = Field(..., min_length=2, max_length=160)
    specialization: str = Field(..., min_length=2, max_length=120)
    experience_years: int = Field(..., ge=0, le=75)
    license_number: str = Field(..., min_length=4, max_length=100)
    hospital_id: Optional[int] = None
    department_id: Optional[int] = None
    languages: List[str] = ["English"]
    consultation_fee: Optional[float] = Field(default=None, ge=0, le=100000)
    bio: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("full_name")
    @classmethod
    def clean_name(cls, v: str) -> str:
        cleaned = " ".join(v.strip().split())
        if not NAME_PATTERN.match(cleaned):
            raise ValueError(
                "Full name may contain only letters, spaces, hyphens, apostrophes, and periods"
            )
        return cleaned

    @field_validator("email")
    @classmethod
    def norm_email(cls, v: EmailStr) -> str:
        return str(v).strip().lower()

    @field_validator("password")
    @classmethod
    def check_pw(cls, v: str) -> str:
        return _validate_password_strength(v)

    @model_validator(mode="after")
    def match_pw(self) -> "DoctorRegisterRequest":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self


class DoctorProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=30)
    languages: Optional[List[str]] = None
    consultation_fee: Optional[float] = Field(default=None, ge=0, le=100000)
    bio: Optional[str] = Field(default=None, max_length=2000)
    profile_image_url: Optional[str] = Field(default=None, max_length=500)


# -------- Appointments & Notes & Notifications --------

class AppointmentCreateRequest(BaseModel):
    doctor_id: int
    hospital_id: int
    department_id: Optional[int] = None
    appointment_date: date
    appointment_time: time
    reason: str = Field(..., min_length=5, max_length=2000)
    share_reports: bool = False


class AppointmentCancelRequest(BaseModel):
    cancellation_reason: str = Field(..., min_length=3, max_length=500)


class AppointmentRescheduleRequest(BaseModel):
    appointment_date: date
    appointment_time: time


class DoctorAppointmentActionRequest(BaseModel):
    status: Literal["confirmed", "rejected", "completed", "rescheduled"]
    reason: Optional[str] = Field(default=None, max_length=500)
    appointment_date: Optional[date] = None
    appointment_time: Optional[time] = None


class ConsultationNoteCreateRequest(BaseModel):
    observations: str = Field(..., min_length=3, max_length=4000)
    notes: Optional[str] = Field(default=None, max_length=4000)
    follow_up_recommendations: Optional[str] = Field(default=None, max_length=2000)
    treatment_info: Optional[str] = Field(default=None, max_length=2000)
    is_shareable: bool = True


class ConsultationNoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    appointment_id: int
    doctor_id: int
    patient_id: int
    observations: str
    notes: Optional[str] = None
    follow_up_recommendations: Optional[str] = None
    treatment_info: Optional[str] = None
    is_shareable: bool
    created_at: datetime


class AppointmentOut(BaseModel):
    id: int
    patient_id: int
    patient_name: str
    patient_email: str
    patient_phone: Optional[str] = None
    doctor_id: int
    doctor_name: str
    doctor_specialization: str
    hospital_id: int
    hospital_name: str
    hospital_city: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    appointment_date: date
    appointment_time: time
    reason: str
    status: str
    cancellation_reason: Optional[str] = None
    rescheduled_from_date: Optional[date] = None
    rescheduled_from_time: Optional[time] = None
    share_reports: bool
    consultation_notes: List[ConsultationNoteOut] = []
    created_at: datetime
    updated_at: datetime


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    message: str
    notification_type: str
    is_read: bool
    related_route: Optional[str] = None
    created_at: datetime


# -------- Treatment Education, Contact, Overview --------

class TreatmentEducationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    specialty: str
    slug: str
    description: str
    common_reasons: List[str]
    preparation: List[str]
    precautions: List[str]
    aftercare: List[str]
    when_to_consult: List[str]
    emergency_signs: List[str]
    sources: List[str]
    reviewed_by: Optional[str] = None
    last_reviewed_date: date
    verified_hospitals: List[Dict[str, Any]] = []


class ContactEnquiryRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    email: EmailStr
    subject: str = Field(..., min_length=3, max_length=200)
    message: str = Field(..., min_length=10, max_length=4000)


class ContactEnquiryResponse(BaseModel):
    id: int
    message: str
    created_at: datetime
    email_delivered: bool = False
    delivery_status: str = "received"


class PublicOverviewResponse(BaseModel):
    stats: Dict[str, int]
    featured_hospitals: List[HospitalSummaryOut]
    featured_doctors: List[DoctorCompactOut]
    support: Dict[str, Optional[str]]
