from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import hash_password, verify_password
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.profile import (
    ChangePasswordRequest,
    ProfileResponse,
    ProfileUpdateRequest,
)
from app.services.activity_service import record_activity

router = APIRouter(prefix="/profile", tags=["Profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return ProfileResponse.model_validate(current_user)


@router.patch("", response_model=ProfileResponse)
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    update_data = payload.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"]:
        new_email = update_data["email"]
        if new_email != current_user.email:
            existing = db.scalar(
                select(User).where(User.email == new_email, User.id != current_user.id)
            )
            if existing is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Another account is already using this email address",
                )

    for field, value in update_data.items():
        if isinstance(value, str):
            value = value.strip() or None
        setattr(current_user, field, value)

    record_activity(
        db,
        user_id=current_user.id,
        activity_type="profile_updated",
        title="Updated personal profile",
        description="Saved updated personal health profile information",
        reference_id=str(current_user.id),
        reference_type="user",
    )
    db.commit()
    db.refresh(current_user)
    return ProfileResponse.model_validate(current_user)


@router.post("/change-password", response_model=MessageResponse)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    current_user.hashed_password = hash_password(payload.new_password)
    record_activity(
        db,
        user_id=current_user.id,
        activity_type="password_changed",
        title="Changed account password",
        description="Updated account security password from profile settings",
        reference_id=str(current_user.id),
        reference_type="user",
    )
    db.commit()
    return MessageResponse(message="Password updated successfully")
