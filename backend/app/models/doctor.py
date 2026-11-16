from datetime import date, datetime, time
from typing import List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    hospital_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("hospitals.id", ondelete="SET NULL"), index=True, nullable=True
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("hospital_departments.id", ondelete="SET NULL"),
        nullable=True,
    )
    qualification: Mapped[str] = mapped_column(String(160), nullable=False)
    specialization: Mapped[str] = mapped_column(String(120), index=True, nullable=False)
    experience_years: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    license_number: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
    languages: Mapped[List[str]] = mapped_column(JSON, default=list, nullable=False)
    consultation_fee: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    profile_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    designation: Mapped[Optional[str]] = mapped_column(String(140), nullable=True)
    published_timings: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    official_source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    listing_source: Mapped[str] = mapped_column(
        String(40), default="official_directory", server_default="official_directory", nullable=False
    )
    verification_status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        server_default="pending",
        index=True,
        nullable=False,
    )
    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="doctor_profile")
    hospital: Mapped[Optional["Hospital"]] = relationship(back_populates="doctors")
    department: Mapped[Optional["HospitalDepartment"]] = relationship()
    availability_slots: Mapped[List["DoctorAvailability"]] = relationship(
        back_populates="doctor", cascade="all, delete-orphan", order_by="DoctorAvailability.day_of_week"
    )
    leaves: Mapped[List["DoctorLeave"]] = relationship(
        back_populates="doctor", cascade="all, delete-orphan", order_by="DoctorLeave.leave_date"
    )
    appointments: Mapped[List["Appointment"]] = relationship(back_populates="doctor")


class DoctorInvitation(Base):
    __tablename__ = "doctor_invitations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    token_hash: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    hospital_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("hospitals.id", ondelete="SET NULL"), nullable=True
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("hospital_departments.id", ondelete="SET NULL"), nullable=True
    )
    specialization: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    used: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class DoctorAvailability(Base):
    __tablename__ = "doctor_availability"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctor_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Mon .. 6=Sun
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    slot_duration_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    break_start: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    break_end: Mapped[Optional[time]] = mapped_column(Time, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    doctor: Mapped["DoctorProfile"] = relationship(back_populates="availability_slots")


class DoctorLeave(Base):
    __tablename__ = "doctor_leaves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("doctor_profiles.id", ondelete="CASCADE"), index=True, nullable=False
    )
    leave_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_holiday: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    doctor: Mapped["DoctorProfile"] = relationship(back_populates="leaves")
