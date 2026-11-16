from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.auth import UserPublic
from app.schemas.chat import AIHealthResponse
from app.schemas.reports import MedicalReportResponse
from app.schemas.symptoms import SymptomAssessmentResponse


class HealthActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activity_type: str
    title: str
    description: Optional[str] = None
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    created_at: datetime


class DashboardStats(BaseModel):
    total_assessments: int
    total_reports: int
    total_conversations: int
    total_activities: int
    last_assessment_at: Optional[datetime] = None
    last_report_at: Optional[datetime] = None


class DashboardNotification(BaseModel):
    id: str
    title: str
    message: str
    severity: str
    action_route: Optional[str] = None


class DashboardSummaryResponse(BaseModel):
    user: UserPublic
    stats: DashboardStats
    recent_assessments: List[SymptomAssessmentResponse]
    recent_reports: List[MedicalReportResponse]
    recent_activities: List[HealthActivityResponse]
    ai_status: AIHealthResponse
    notifications: List[DashboardNotification]


class BreakdownItem(BaseModel):
    label: str
    count: int


class InsightsSummaryResponse(BaseModel):
    total_assessments: int
    total_reports: int
    total_conversations: int
    severity_breakdown: List[BreakdownItem]
    urgency_breakdown: List[BreakdownItem]
    report_categories: List[BreakdownItem]
    top_symptoms: List[BreakdownItem]
    educational_guidance: List[str]
    has_data: bool


class TrendPoint(BaseModel):
    date: str
    assessments: int
    reports: int
    chats: int


class InsightsTrendsResponse(BaseModel):
    timeline: List[TrendPoint]
    has_sufficient_data: bool


class HistoryEntry(BaseModel):
    id: int
    record_type: str  # assessment | report | activity
    title: str
    subtitle: str
    badge: str
    created_at: datetime
    deletable: bool = True
    details: Dict[str, Any] = {}


class HistoryListResponse(BaseModel):
    items: List[HistoryEntry]
    total: int
    page: int
    page_size: int
