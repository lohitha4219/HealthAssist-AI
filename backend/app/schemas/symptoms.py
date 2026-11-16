from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SymptomCatalogItem(BaseModel):
    id: str
    name: str
    category: str
    is_red_flag: bool = False


class PossibleCauseItem(BaseModel):
    title: str
    description: str
    category: str


class SymptomAssessRequest(BaseModel):
    symptoms: List[str] = Field(..., min_length=1, max_length=20)
    duration: str = Field(..., min_length=2, max_length=80)
    severity: Literal["mild", "moderate", "severe"]
    additional_details: Optional[str] = Field(default=None, max_length=2000)

    @field_validator("symptoms")
    @classmethod
    def clean_symptoms(cls, values: List[str]) -> List[str]:
        cleaned: List[str] = []
        seen = set()
        for item in values:
            s = item.strip()
            if s and s.lower() not in seen:
                seen.add(s.lower())
                cleaned.append(s[:100])
        if not cleaned:
            raise ValueError("Please select or enter at least one symptom")
        return cleaned


class SymptomAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symptoms: List[str]
    duration: str
    severity: str
    additional_details: Optional[str] = None
    urgency_level: str
    educational_summary: str
    possible_causes: List[PossibleCauseItem]
    care_guidance: List[str]
    emergency_warning: Optional[str] = None
    ai_enhanced: bool
    disclaimer: str = (
        "Educational health information only. HealthAssist AI does not diagnose "
        "medical conditions or prescribe treatments. Always consult a qualified "
        "healthcare professional for medical advice."
    )
    created_at: datetime


class SymptomHistoryResponse(BaseModel):
    items: List[SymptomAssessmentResponse]
    total: int
    page: int
    page_size: int
