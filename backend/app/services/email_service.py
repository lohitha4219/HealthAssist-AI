import logging
import smtplib
from email.message import EmailMessage
from typing import Tuple

from app.core.config import get_settings
from app.models.education_contact import ContactEnquiry

logger = logging.getLogger(__name__)


def is_smtp_configured() -> bool:
    """Check if SMTP outbound delivery settings are set."""
    settings = get_settings()
    return settings.smtp_configured


def send_contact_enquiry_email(enquiry: ContactEnquiry) -> Tuple[bool, str]:
    """
    Sends a visitor contact enquiry email to support (nslohitha2924@gmail.com) via SMTP.
    Returns:
        (success: bool, detail: str)
    """
    settings = get_settings()
    recipient = (settings.SUPPORT_EMAIL or "nslohitha2924@gmail.com").strip()

    if not settings.SMTP_HOST:
        return (
            False,
            "SMTP is not configured in backend/.env (SMTP_HOST is not set). Enquiry saved in database only.",
        )

    smtp_user = (settings.SMTP_USERNAME or settings.SMTP_USER or "").strip()
    smtp_pass = (settings.SMTP_PASSWORD or "").strip()
    from_addr = (settings.SMTP_FROM_EMAIL or smtp_user or recipient).strip()
    from_name = (getattr(settings, "SUPPORT_FROM_NAME", None) or "HealthAssist AI").strip()

    subject = f"HealthAssist AI – New Contact Enquiry: {enquiry.subject.strip()}"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_addr}>"
    msg["To"] = recipient
    msg["Reply-To"] = f"{enquiry.name.strip()} <{enquiry.email.strip()}>"

    created_str = (
        enquiry.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
        if enquiry.created_at
        else "Just now"
    )

    plain_body = f"""New Contact Enquiry received on HealthAssist AI:

From: {enquiry.name} <{enquiry.email}>
Subject: {enquiry.subject}
Received At: {created_str}

Message:
--------------------------------------------------
{enquiry.message}
--------------------------------------------------

Reply directly to this email to respond to {enquiry.name} ({enquiry.email}).
--
HealthAssist AI Platform
"""

    html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; color: #1e293b; padding: 20px; margin: 0; }}
    .card {{ max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05); }}
    .header {{ background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color: #ffffff; padding: 24px; text-align: left; }}
    .header h2 {{ margin: 0; font-size: 20px; font-weight: 700; }}
    .header p {{ margin: 6px 0 0; font-size: 13px; opacity: 0.9; color: #e0f2fe; }}
    .content {{ padding: 24px; }}
    .field {{ margin-bottom: 16px; }}
    .label {{ font-size: 11px; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.05em; margin-bottom: 4px; }}
    .value {{ font-size: 15px; color: #0f172a; font-weight: 500; }}
    .message-box {{ background: #f1f5f9; border-radius: 8px; padding: 16px; font-size: 14px; line-height: 1.6; color: #334155; white-space: pre-wrap; }}
    .footer {{ background: #f8fafc; padding: 16px 24px; font-size: 12px; color: #94a3b8; border-top: 1px solid #e2e8f0; text-align: center; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="header">
      <h2>HealthAssist AI – New Contact Enquiry</h2>
      <p>A new visitor enquiry was submitted via the HealthAssist AI website.</p>
    </div>
    <div class="content">
      <div class="field">
        <div class="label">Sender Full Name</div>
        <div class="value">{enquiry.name}</div>
      </div>
      <div class="field">
        <div class="label">Sender Email Address</div>
        <div class="value"><a href="mailto:{enquiry.email}">{enquiry.email}</a></div>
      </div>
      <div class="field">
        <div class="label">Subject</div>
        <div class="value">{enquiry.subject}</div>
      </div>
      <div class="field">
        <div class="label">Message</div>
        <div class="message-box">{enquiry.message}</div>
      </div>
      <div class="field" style="margin-bottom: 0;">
        <div class="label">Submitted At</div>
        <div class="value" style="font-size: 13px; color: #64748b;">{created_str}</div>
      </div>
    </div>
    <div class="footer">
      Hit 'Reply' in your email client to respond directly to {enquiry.name} (<a href="mailto:{enquiry.email}">{enquiry.email}</a>).<br>
      Delivered by HealthAssist AI
    </div>
  </div>
</body>
</html>
"""

    msg.set_content(plain_body)
    msg.add_alternative(html_body, subtype="html")

    try:
        if settings.SMTP_PORT == 465 or getattr(settings, "SMTP_USE_SSL", False):
            server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT, timeout=12)
        else:
            server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=12)
            server.ehlo()
            if settings.SMTP_USE_TLS:
                server.starttls()
                server.ehlo()

        if smtp_user and smtp_pass:
            server.login(smtp_user, smtp_pass)

        server.send_message(msg)
        server.quit()
        logger.info(
            "Successfully sent contact enquiry email #%s to %s via SMTP",
            enquiry.id,
            recipient,
        )
        return (True, f"Email delivered successfully to {recipient}.")
    except Exception as exc:
        err_msg = f"{type(exc).__name__}: {str(exc)}"
        logger.error(
            "Failed to deliver contact enquiry email #%s via SMTP: %s",
            enquiry.id,
            err_msg,
        )
        return (False, err_msg)
