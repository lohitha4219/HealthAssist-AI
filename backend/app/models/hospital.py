from datetime import datetime
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(220), unique=True, index=True, nullable=False)
    hospital_type: Mapped[str] = mapped_column(String(80), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    district: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    state: Mapped[str] = mapped_column(
        String(80), default="Andhra Pradesh", server_default="Andhra Pradesh", nullable=False
    )
    pincode: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    emergency_phone: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    operating_hours: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    emergency_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    verification_status: Mapped[str] = mapped_column(
        String(30), default="verified", server_default="verified", nullable=False
    )
    source_reference: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_published: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    departments: Mapped[List["HospitalDepartment"]] = relationship(
        back_populates="hospital", cascade="all, delete-orphan"
    )
    facilities: Mapped[List["HospitalFacility"]] = relationship(
        back_populates="hospital", cascade="all, delete-orphan"
    )
    treatments: Mapped[List["HospitalTreatment"]] = relationship(
        back_populates="hospital", cascade="all, delete-orphan"
    )
    doctors: Mapped[List["DoctorProfile"]] = relationship(back_populates="hospital")
    appointments: Mapped[List["Appointment"]] = relationship(back_populates="hospital")


class HospitalDepartment(Base):
    __tablename__ = "hospital_departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hospital_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    hospital: Mapped["Hospital"] = relationship(back_populates="departments")


class HospitalFacility(Base):
    __tablename__ = "hospital_facilities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hospital_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    hospital: Mapped["Hospital"] = relationship(back_populates="facilities")


class HospitalTreatment(Base):
    __tablename__ = "hospital_treatments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    hospital_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("hospitals.id", ondelete="CASCADE"), index=True, nullable=False
    )
    department_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("hospital_departments.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    specialty: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_verified: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true", nullable=False
    )

    hospital: Mapped["Hospital"] = relationship(back_populates="treatments")
