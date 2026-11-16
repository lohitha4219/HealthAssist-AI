from datetime import datetime, timezone
import json
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.session import get_db
from app.models.chat import ChatMessage, Conversation
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.chat import (
    AIHealthResponse,
    ChatMessageCreateRequest,
    ChatMessageResponse,
    ConversationCreateRequest,
    ConversationDetailResponse,
    ConversationResponse,
    ConversationUpdateRequest,
    SendMessageResponse,
)
from app.services.activity_service import record_activity
from app.services.ai_service import (
    AIUnavailableError,
    LocalAIService,
    get_ai_service,
)

router = APIRouter(prefix="/chat", tags=["AI Chat"])


def _get_owned_conversation(
    db: Session, conversation_id: int, user_id: int
) -> Conversation:
    conv = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    if conv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conv


def _build_conversation_summary(db: Session, conv: Conversation) -> ConversationResponse:
    msg_count = db.scalar(
        select(func.count(ChatMessage.id)).where(ChatMessage.conversation_id == conv.id)
    ) or 0
    last_msg = db.scalar(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conv.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(1)
    )
    preview = None
    if last_msg and last_msg.content:
        preview = last_msg.content[:90].replace("\n", " ")
        if len(last_msg.content) > 90:
            preview += "..."
    return ConversationResponse(
        id=conv.id,
        title=conv.title,
        model_name=conv.model_name,
        message_count=msg_count,
        last_message_preview=preview,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
    )


def _auto_title(text: str) -> str:
    cleaned = " ".join(text.strip().split())
    if len(cleaned) <= 48:
        return cleaned or "New Conversation"
    return cleaned[:45].rstrip() + "..."


@router.get("/health", response_model=AIHealthResponse)
async def chat_ai_health(
    current_user: User = Depends(get_current_user),
    ai_service: LocalAIService = Depends(get_ai_service),
):
    health = await ai_service.get_health()
    return AIHealthResponse(
        available=health.available,
        provider=health.provider,
        configured_provider=health.configured_provider,
        model=health.model,
        base_url=health.base_url,
        status=health.status,
        detail=health.detail,
        setup_hint=health.setup_hint,
        checked_at=health.checked_at,
    )


@router.post(
    "/conversations",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    payload: ConversationCreateRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    title = (payload.title if payload and payload.title else None) or "New Conversation"
    conv = Conversation(user_id=current_user.id, title=title)
    db.add(conv)
    db.flush()

    record_activity(
        db,
        user_id=current_user.id,
        activity_type="chat_started",
        title=f"Started AI conversation: {title}",
        description="Created a new AI Assistant conversation",
        reference_id=str(conv.id),
        reference_type="conversation",
    )
    db.commit()
    db.refresh(conv)
    return _build_conversation_summary(db, conv)


@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    convs = db.scalars(
        select(Conversation)
        .where(Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    ).all()
    return [_build_conversation_summary(db, c) for c in convs]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _get_owned_conversation(db, conversation_id, current_user.id)
    messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conv.id)
        .order_by(ChatMessage.created_at.asc())
    ).all()
    summary = _build_conversation_summary(db, conv)
    return ConversationDetailResponse(
        **summary.model_dump(),
        messages=[ChatMessageResponse.model_validate(m) for m in messages],
    )


@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
def rename_conversation(
    conversation_id: int,
    payload: ConversationUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _get_owned_conversation(db, conversation_id, current_user.id)
    conv.title = payload.title
    conv.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(conv)
    return _build_conversation_summary(db, conv)


@router.delete("/conversations/{conversation_id}", response_model=MessageResponse)
def delete_conversation(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _get_owned_conversation(db, conversation_id, current_user.id)
    db.delete(conv)
    db.commit()
    return MessageResponse(message="Conversation deleted")


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[ChatMessageResponse],
)
def get_conversation_messages(
    conversation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    conv = _get_owned_conversation(db, conversation_id, current_user.id)
    messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conv.id)
        .order_by(ChatMessage.created_at.asc())
    ).all()
    return [ChatMessageResponse.model_validate(m) for m in messages]


@router.post(
    "/conversations/{conversation_id}/messages",
    response_model=SendMessageResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_chat_message(
    conversation_id: int,
    payload: ChatMessageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_service: LocalAIService = Depends(get_ai_service),
):
    conv = _get_owned_conversation(db, conversation_id, current_user.id)

    prior_messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conv.id)
        .order_by(ChatMessage.created_at.asc())
    ).all()

    context_messages = [
        {"role": m.role, "content": m.content}
        for m in prior_messages
        if m.role in {"user", "assistant"}
    ]
    context_messages.append({"role": "user", "content": payload.content})

    try:
        reply = await ai_service.generate_chat_reply(context_messages)
    except AIUnavailableError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    user_msg = ChatMessage(
        conversation_id=conv.id,
        role="user",
        content=payload.content,
    )
    db.add(user_msg)
    db.flush()

    assistant_msg = ChatMessage(
        conversation_id=conv.id,
        role="assistant",
        content=reply.content,
        provider=reply.provider,
        model_name=reply.model,
    )
    db.add(assistant_msg)

    if conv.title == "New Conversation" and len(prior_messages) == 0:
        conv.title = _auto_title(payload.content)
    conv.model_name = reply.model
    conv.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(conv)
    db.refresh(user_msg)
    db.refresh(assistant_msg)

    return SendMessageResponse(
        conversation=_build_conversation_summary(db, conv),
        user_message=ChatMessageResponse.model_validate(user_msg),
        assistant_message=ChatMessageResponse.model_validate(assistant_msg),
    )


@router.post("/conversations/{conversation_id}/stream")
async def stream_chat_message(
    conversation_id: int,
    payload: ChatMessageCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    ai_service: LocalAIService = Depends(get_ai_service),
):
    conv = _get_owned_conversation(db, conversation_id, current_user.id)

    # Pre-flight AI health check: fail fast with 503 before opening stream or modifying DB
    health = await ai_service.get_health()
    if not health.available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{health.detail} {health.setup_hint}",
        )

    prior_messages = db.scalars(
        select(ChatMessage)
        .where(ChatMessage.conversation_id == conv.id)
        .order_by(ChatMessage.created_at.asc())
    ).all()

    context_messages = [
        {"role": m.role, "content": m.content}
        for m in prior_messages
        if m.role in {"user", "assistant"}
    ]
    context_messages.append({"role": "user", "content": payload.content})

    async def event_generator():
        collected_chunks = []
        try:
            async for chunk in ai_service.generate_chat_stream(context_messages):
                collected_chunks.append(chunk)
                yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        except AIUnavailableError as exc:
            yield f"data: {json.dumps({'error': exc.detail})}\n\n"
            return
        except Exception as exc:
            yield f"data: {json.dumps({'error': str(exc)})}\n\n"
            return

        full_content = "".join(collected_chunks).strip()
        if full_content:
            c = db.scalar(
                select(Conversation).where(Conversation.id == conv.id)
            )
            if c:
                u_msg = ChatMessage(
                    conversation_id=c.id,
                    role="user",
                    content=payload.content,
                )
                db.add(u_msg)
                db.flush()

                asst_msg = ChatMessage(
                    conversation_id=c.id,
                    role="assistant",
                    content=full_content,
                    provider=health.provider,
                    model_name=health.model,
                )
                db.add(asst_msg)
                if c.title == "New Conversation" and len(prior_messages) == 0:
                    c.title = _auto_title(payload.content)
                c.model_name = health.model
                c.updated_at = datetime.now(timezone.utc)
                db.commit()
                db.refresh(u_msg)
                db.refresh(asst_msg)
                yield f"data: {json.dumps({'done': True, 'user_message_id': u_msg.id, 'message_id': asst_msg.id, 'title': c.title})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
