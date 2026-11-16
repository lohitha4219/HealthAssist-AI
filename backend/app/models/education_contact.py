from datetime import date, datetime
from typing import List, Optional

from sqlalchemy import JSON, Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TreatmentEducation(Base):
    __tablename__ = "treatment_education"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    specialty: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(140), unique=True, index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    common_reasons: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    preparation: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    precautions: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    aftercare: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    when_to_consult: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    emergency_signs: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    sources: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(160), nullable=True)
    last_reviewed_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ContactEnquiry(Base):
    __tablename__ = "contact_enquiries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30), default="received", server_default="received", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
