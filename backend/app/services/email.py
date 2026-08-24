import logging
import smtplib
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.config import settings
from app.models import EmailLog

log = logging.getLogger(__name__)


def send_email(
    db: Session,
    to_email: str,
    subject: str,
    body: str,
    email_type: str,
    candidate_id: int | None = None,
) -> EmailLog:
    safe = settings.email_safe_mode
    record = EmailLog(
        candidate_id=candidate_id,
        email_type=email_type,
        to_email=to_email,
        subject=subject,
        status="LOGGED" if safe else "PENDING",
        safe_mode=safe,
    )
    db.add(record)
    db.flush()

    if safe:
        log.info("EMAIL_SAFE_MODE to=%s type=%s subject=%s", to_email, email_type, subject)
        record.status = "LOGGED"
        return record

    try:
        message = EmailMessage()
        message["From"] = settings.smtp_username
        message["To"] = to_email
        message["Subject"] = subject
        message.set_content(body)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(settings.smtp_username, settings.smtp_password)
            smtp.send_message(message)
        record.status = "SENT"
    except Exception as exc:
        log.exception("Email send failed")
        record.status = "FAILED"
        record.error = str(exc)
    return record


def test_invitation_body(name: str) -> tuple[str, str]:
    subject = "myNachiketa screening test invitation"
    body = (
        f"Hi {name},\n\n"
        "You have been shortlisted for the next step of our screening process.\n"
        f"Please complete the assessment here: {settings.test_link}\n\n"
        "Thank you,\nmyNachiketa Recruiting\n"
    )
    return subject, body


def interview_invitation_body(
    name: str,
    when_label: str,
    duration: int,
    meet_url: str,
) -> tuple[str, str]:
    subject = "Interview scheduled — myNachiketa"
    body = (
        f"Hi {name},\n\n"
        "Your interview has been scheduled.\n\n"
        f"Date and time: {when_label}\n"
        f"Duration: {duration} minutes\n"
        f"Google Meet: {meet_url or 'will be shared shortly'}\n\n"
        "Please join using the Meet link at the scheduled time.\n\n"
        "Thank you,\nmyNachiketa Recruiting\n"
    )
    return subject, body
