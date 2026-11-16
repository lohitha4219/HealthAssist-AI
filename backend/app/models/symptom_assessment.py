from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class SymptomAssessment(Base):
    __tablename__ = "symptom_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    symptoms: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    duration: Mapped[str] = mapped_column(String(80), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    additional_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    urgency_level: Mapped[str] = mapped_column(String(30), nullable=False)
    educational_summary: Mapped[str] = mapped_column(Text, nullable=False)
    possible_causes: Mapped[List[dict]] = mapped_column(JSON, nullable=False)
    care_guidance: Mapped[List[str]] = mapped_column(JSON, nullable=False)
    emergency_warning: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_enhanced: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default="false", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="symptom_assessments")
