from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ConversationCreateRequest(BaseModel):
    title: Optional[str] = Field(default=None, max_length=200)

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        cleaned = v.strip()
        return cleaned if cleaned else None


class ConversationUpdateRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)

    @field_validator("title")
    @classmethod
    def clean_title(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Conversation title cannot be empty")
        return cleaned


class ChatMessageCreateRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=8000)

    @field_validator("content")
    @classmethod
    def clean_content(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Message content cannot be empty")
        return cleaned


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    conversation_id: int
    role: str
    content: str
    provider: Optional[str] = None
    model_name: Optional[str] = None
    created_at: datetime


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    model_name: Optional[str] = None
    message_count: int = 0
    last_message_preview: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ConversationDetailResponse(ConversationResponse):
    messages: List[ChatMessageResponse] = []


class SendMessageResponse(BaseModel):
    conversation: ConversationResponse
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


class AIHealthResponse(BaseModel):
    available: bool
    provider: str
    configured_provider: str
    model: Optional[str] = None
    base_url: Optional[str] = None
    status: str
    detail: str
    setup_hint: str
    checked_at: datetime
