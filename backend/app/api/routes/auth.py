from datetime import datetime, timedelta, timezone
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_onboarding_key
from app.core.config import get_settings
from app.core.rate_limit import rate_limit_auth
from app.core.security import (
    create_access_token,
    generate_secure_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.database.session import get_db
from app.models.auth_tokens import PasswordResetToken, RefreshToken
from app.models.doctor import DoctorInvitation, DoctorProfile
from app.models.hospital import Hospital, HospitalDepartment
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserPublic,
)
from app.schemas.healthcare import (
    DoctorInviteCreateRequest,
    DoctorInviteResponse,
    DoctorRegisterRequest,
)
from app.services.activity_service import record_activity
from app.services.notification_service import send_email_if_configured

logger = logging.getLogger("healthassist.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _issue_tokens(
    db: Session,
    user: User,
    *,
    message: str = "Authentication successful",
    remember_me: bool = False,
) -> TokenResponse:
    settings = get_settings()
    access_token = create_access_token(subject=str(user.id), role=user.role)
    raw_refresh = generate_secure_token(48)
    refresh_days = (
        max(settings.REFRESH_TOKEN_EXPIRE_DAYS, 30)
        if remember_me
        else settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    refresh_record = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(raw_refresh),
        expires_at=datetime.now(timezone.utc) + timedelta(days=refresh_days),
    )
    db.add(refresh_record)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        message=message,
        access_token=access_token,
        refresh_token=raw_refresh,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserPublic.model_validate(user),
    )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_auth("register", max_requests=15, window_seconds=60))],
)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        existing = db.scalar(select(User).where(User.email == payload.email))
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists",
            )

        user = User(
            full_name=payload.full_name,
            email=payload.email,
            hashed_password=hash_password(payload.password),
            role="patient",
            is_active=True,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender,
            phone=payload.phone,
        )
        db.add(user)
        db.flush()

        record_activity(
            db,
            user_id=user.id,
            activity_type="account_created",
            title="Created HealthAssist AI account",
            description="Registered personal health workspace",
            reference_id=str(user.id),
            reference_type="user",
        )
        tokens = _issue_tokens(
            db, user, message="Registration successful", remember_me=False
        )
        logger.info("Registered new user id=%s", user.id)
        return tokens
    except HTTPException:
        raise
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )
    except SQLAlchemyError as exc:
        db.rollback()
        logger.exception("Database error during registration: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is temporarily unavailable. Please try again shortly.",
        )


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit_auth("login", max_requests=20, window_seconds=60))],
)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.scalar(select(User).where(User.email == payload.email))
        if user is None or not verify_password(payload.password, user.hashed_password):
            logger.warning("Failed login attempt for email=%s", payload.email)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
        if not user.is_active:
            logger.warning("Inactive account login attempt user_id=%s", user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This user account is inactive",
            )
        tokens = _issue_tokens(
            db,
            user,
            message="Login successful",
            remember_me=payload.remember_me,
        )
        logger.info("User logged in user_id=%s", user.id)
        return tokens
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        logger.exception("Database error during login: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database service is temporarily unavailable. Please try again shortly.",
        )


@router.get("/me", response_model=UserPublic)
def get_me(current_user: User = Depends(get_current_user)):
    return UserPublic.model_validate(current_user)


@router.post("/refresh", response_model=TokenResponse)
def refresh_session(payload: RefreshRequest, db: Session = Depends(get_db)):
    hashed = hash_token(payload.refresh_token)
    record = db.scalar(select(RefreshToken).where(RefreshToken.token_hash == hashed))
    now = datetime.now(timezone.utc)

    if record is None or record.revoked or _ensure_utc(record.expires_at) <= now:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token is invalid or expired",
        )

    user = db.get(User, record.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found or inactive",
        )

    record.revoked = True
    return _issue_tokens(db, user, message="Session refreshed")


@router.post("/logout", response_model=MessageResponse)
def logout(
    payload: LogoutRequest | None = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload and payload.refresh_token:
        hashed = hash_token(payload.refresh_token)
        token_row = db.scalar(
            select(RefreshToken).where(
                RefreshToken.token_hash == hashed,
                RefreshToken.user_id == current_user.id,
            )
        )
        if token_row is not None:
            token_row.revoked = True
    else:
        tokens = db.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == current_user.id,
                RefreshToken.revoked.is_(False),
            )
        ).all()
        for t in tokens:
            t.revoked = True
    db.commit()
    logger.info("User logged out user_id=%s", current_user.id)
    return MessageResponse(message="Logged out successfully")


@router.post(
    "/forgot-password",
    response_model=MessageResponse,
    dependencies=[Depends(rate_limit_auth("forgot_password", max_requests=10, window_seconds=60))],
)
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    user = db.scalar(select(User).where(User.email == payload.email))
    dev_token = None
    email_sent = False

    if user is not None and user.is_active:
        raw_token = generate_secure_token(32)
        reset_row = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
        )
        db.add(reset_row)
        db.commit()

        if settings.smtp_configured:
            email_sent, _ = send_email_if_configured(
                to_email=user.email,
                subject="HealthAssist AI — Password Reset Token",
                body_text=(
                    f"Hello {user.full_name},\n\n"
                    f"Use this single-use password reset token within "
                    f"{settings.PASSWORD_RESET_EXPIRE_MINUTES} minutes:\n\n"
                    f"{raw_token}\n\n"
                    "If you did not request a password reset, please ignore this email."
                ),
            )
        if settings.EXPOSE_DEV_RESET_TOKEN and settings.APP_ENV == "development":
            dev_token = raw_token

    if settings.smtp_configured and email_sent:
        msg = "If an account exists for that email, a reset token has been sent via email."
    elif settings.EXPOSE_DEV_RESET_TOKEN and settings.APP_ENV == "development":
        msg = "SMTP email is not configured; a development reset token was generated below."
    else:
        msg = (
            "Password reset token created, but SMTP email delivery is not configured on this server. "
            "Configure SMTP_* environment variables in backend/.env to deliver reset emails."
        )

    return MessageResponse(
        message=msg,
        dev_reset_token=dev_token,
        email_sent=email_sent,
    )


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    hashed = hash_token(payload.token)
    reset_row = db.scalar(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == hashed)
    )
    now = datetime.now(timezone.utc)

    if reset_row is None or reset_row.used or _ensure_utc(reset_row.expires_at) <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token is invalid or has expired",
        )

    user = db.get(User, reset_row.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is unavailable for password reset",
        )

    user.hashed_password = hash_password(payload.new_password)
    reset_row.used = True

    active_tokens = db.scalars(
        select(RefreshToken).where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked.is_(False),
        )
    ).all()
    for token in active_tokens:
        token.revoked = True

    record_activity(
        db,
        user_id=user.id,
        activity_type="password_changed",
        title="Password reset completed",
        description="Account password was reset via recovery token",
        reference_id=str(user.id),
        reference_type="user",
    )
    db.commit()
    return MessageResponse(message="Password has been reset successfully. Please sign in.")


@router.post(
    "/doctor-invite",
    response_model=DoctorInviteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_onboarding_key)],
)
def create_doctor_invitation(
    payload: DoctorInviteCreateRequest,
    db: Session = Depends(get_db),
):
    if payload.hospital_id is not None and db.get(Hospital, payload.hospital_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")
    if payload.department_id is not None and db.get(HospitalDepartment, payload.department_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    raw_token = generate_secure_token(32)
    expires_at = datetime.now(timezone.utc) + timedelta(hours=payload.expires_hours)
    invite = DoctorInvitation(
        email=payload.email,
        token_hash=hash_token(raw_token),
        hospital_id=payload.hospital_id,
        department_id=payload.department_id,
        specialization=payload.specialization,
        expires_at=expires_at,
    )
    db.add(invite)
    db.commit()

    email_sent, _ = send_email_if_configured(
        to_email=payload.email,
        subject="HealthAssist AI — Verified Doctor Onboarding Invitation",
        body_text=(
            "You have been invited to register your verified Doctor Portal account on HealthAssist AI.\n\n"
            f"Invitation Token: {raw_token}\n"
            f"Expires: {expires_at.isoformat()}\n"
        ),
    )
    return DoctorInviteResponse(
        message="Doctor invitation generated.",
        invitation_token=raw_token,
        email=payload.email,
        expires_at=expires_at,
        email_sent=email_sent,
    )


@router.post(
    "/doctor-register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_auth("doctor_register", max_requests=10, window_seconds=60))],
)
def register_doctor(payload: DoctorRegisterRequest, db: Session = Depends(get_db)):
    hashed = hash_token(payload.invitation_token)
    invite = db.scalar(
        select(DoctorInvitation).where(DoctorInvitation.token_hash == hashed)
    )
    now = datetime.now(timezone.utc)
    if (
        invite is None
        or invite.used
        or _ensure_utc(invite.expires_at) <= now
        or invite.email != payload.email
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Doctor invitation token is invalid, expired, or does not match email",
        )

    if db.scalar(select(User).where(User.email == payload.email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    if (
        db.scalar(
            select(DoctorProfile).where(
                DoctorProfile.license_number == payload.license_number.strip()
            )
        )
        is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A doctor profile with this medical license number is already registered",
        )

    hospital_id = invite.hospital_id or payload.hospital_id
    department_id = invite.department_id or payload.department_id
    if hospital_id is not None and db.get(Hospital, hospital_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not found")
    if department_id is not None and db.get(HospitalDepartment, department_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role="doctor",
        is_active=True,
        phone=payload.phone,
    )
    db.add(user)
    db.flush()

    profile = DoctorProfile(
        user_id=user.id,
        hospital_id=hospital_id,
        department_id=department_id,
        qualification=payload.qualification.strip(),
        specialization=(invite.specialization or payload.specialization).strip(),
        experience_years=payload.experience_years,
        license_number=payload.license_number.strip(),
        languages=[lang.strip() for lang in payload.languages if lang.strip()] or ["English"],
        consultation_fee=payload.consultation_fee,
        bio=payload.bio.strip() if payload.bio else None,
        verification_status="verified",
        verified_at=now,
    )
    db.add(profile)
    invite.used = True

    record_activity(
        db,
        user_id=user.id,
        activity_type="account_created",
        title="Verified Doctor account onboarded",
        description=f"Specialization: {profile.specialization}",
        reference_id=str(user.id),
        reference_type="doctor_profile",
    )
    return _issue_tokens(
        db, user, message="Doctor onboarding completed successfully", remember_me=False
    )
