from email.message import EmailMessage
import logging
import smtplib
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.appointment import Notification

logger = logging.getLogger("healthassist.notifications")


def create_notification(
    db: Session,
    *,
    user_id: int,
    title: str,
    message: str,
    notification_type: str = "appointment",
    related_route: Optional[str] = None,
) -> Notification:
    notif = Notification(
        user_id=user_id,
        title=title[:200],
        message=message,
        notification_type=notification_type[:50],
        related_route=related_route,
    )
    db.add(notif)
    return notif


def send_email_if_configured(
    *,
    to_email: str,
    subject: str,
    body_text: str,
) -> Tuple[bool, str]:
    """Send an actual SMTP email only when SMTP credentials are configured.

    Never simulates email delivery when unconfigured.
    """
    settings = get_settings()
    if not settings.smtp_configured:
        return False, "SMTP provider is not configured"

    msg = EmailMessage()
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body_text)

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
        return True, "Email sent via configured SMTP provider"
    except Exception as exc:
        logger.warning("SMTP delivery failed (%s)", type(exc).__name__)
        return False, "Configured SMTP delivery failed"
