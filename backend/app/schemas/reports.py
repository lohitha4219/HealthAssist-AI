from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict


class MedicalReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    original_filename: str
    content_type: str
    file_size: int
    category: str
    notes: Optional[str] = None
    processing_status: str
    extracted_text: Optional[str] = None
    ai_summary: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None
    page_count: Optional[int] = None
    image_width: Optional[int] = None
    image_height: Optional[int] = None
    analyzed_at: Optional[datetime] = None
    created_at: datetime


class MedicalReportListResponse(BaseModel):
    items: List[MedicalReportResponse]
    total: int
    page: int
    page_size: int
