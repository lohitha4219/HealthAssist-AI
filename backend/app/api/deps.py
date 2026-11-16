import hmac
from typing import Tuple

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.database.session import get_db
from app.models.doctor import DoctorProfile
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(credentials.credentials)
        user_id = int(str(payload["sub"]))
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_patient(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "patient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Patient portal access required",
        )
    return current_user


def require_doctor(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Tuple[User, DoctorProfile]:
    if current_user.role != "doctor":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor portal access required",
        )
    doctor_profile = db.scalar(
        select(DoctorProfile).where(DoctorProfile.user_id == current_user.id)
    )
    if doctor_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor profile is not initialized",
        )
    return current_user, doctor_profile


def require_verified_doctor(
    doctor_ctx: Tuple[User, DoctorProfile] = Depends(require_doctor),
) -> Tuple[User, DoctorProfile]:
    user, profile = doctor_ctx
    if profile.verification_status != "verified":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Doctor credentials must be verified before performing this action",
        )
    return user, profile


def require_maintenance_key(
    x_maintenance_key: str | None = Header(default=None, alias="X-Maintenance-Key"),
) -> None:
    settings = get_settings()
    if not settings.HOSPITAL_MAINTENANCE_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Hospital maintenance key is not configured on this server",
        )
    if not x_maintenance_key or not hmac.compare_digest(
        x_maintenance_key, settings.HOSPITAL_MAINTENANCE_KEY
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid maintenance authorization key",
        )


def require_onboarding_key(
    x_onboarding_key: str | None = Header(default=None, alias="X-Onboarding-Key"),
) -> None:
    settings = get_settings()
    if not settings.DOCTOR_ONBOARDING_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Doctor onboarding key is not configured on this server",
        )
    if not x_onboarding_key or not hmac.compare_digest(
        x_onboarding_key, settings.DOCTOR_ONBOARDING_KEY
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid doctor onboarding authorization key",
        )
