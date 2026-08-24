import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Candidate, Interview
from app.schemas import GoogleCodeIn, InterviewScheduleIn
from app.services import calendar as calendar_service
from app.services.email import interview_invitation_body, send_email

router = APIRouter(tags=["interviews"])
log = logging.getLogger(__name__)


@router.get("/api/auth/google/login")
def google_login():
    return {
        "url": calendar_service.login_url(),
        "redirect_uri": settings.google_redirect_uri,
    }


@router.post("/api/auth/google/exchange")
def google_exchange(payload: GoogleCodeIn, db: Session = Depends(get_db)):
    try:
        calendar_service.exchange_code(db, payload.code)
    except Exception as exc:
        log.exception("Google OAuth token exchange failed")
        raise HTTPException(400, f"Google OAuth failed: {exc}")
    return {"connected": True}


@router.get("/api/auth/google/callback")
def google_callback(code: str = "", error: str = "", db: Session = Depends(get_db)):
    if error:
        return RedirectResponse(f"{settings.frontend_url}/interviews?google=error")
    if not code:
        raise HTTPException(400, "Missing OAuth code")
    try:
        calendar_service.exchange_code(db, code)
    except Exception:
        return RedirectResponse(f"{settings.frontend_url}/interviews?google=error")
    return RedirectResponse(f"{settings.frontend_url}/interviews?google=connected")


@router.get("/api/calendar/status")
def calendar_status(db: Session = Depends(get_db)):
    return {
        "connected": calendar_service.calendar_connected(db),
        "safe_email_mode": settings.email_safe_mode,
        "redirect_uri": settings.google_redirect_uri,
        "javascript_origin": settings.frontend_url,
    }


@router.get("/api/interviews")
def list_interviews(db: Session = Depends(get_db)):
    rows = db.query(Interview).order_by(Interview.scheduled_at.asc()).all()
    return [
        {
            "id": row.id,
            "candidate_id": row.candidate_id,
            "candidate_name": row.candidate.name if row.candidate else "",
            "candidate_email": row.candidate.email if row.candidate else "",
            "scheduled_at": row.scheduled_at,
            "duration_minutes": row.duration_minutes,
            "meet_url": row.meet_url,
            "event_url": row.event_url,
            "status": row.status,
            "email_sent": row.email_sent,
        }
        for row in rows
    ]


@router.post("/api/interviews/schedule")
def schedule_interview(payload: InterviewScheduleIn, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == payload.candidate_id).one_or_none()
    if not candidate:
        raise HTTPException(404, "Candidate not found")
    event = calendar_service.create_meet_event(
        db,
        summary=f"Interview: {candidate.name}",
        start=payload.scheduled_at,
        duration_minutes=payload.duration_minutes,
        attendee_email=candidate.email,
    )
    interview = Interview(
        candidate_id=candidate.id,
        scheduled_at=payload.scheduled_at,
        duration_minutes=payload.duration_minutes,
        calendar_event_id=event["event_id"],
        meet_url=event["meet_url"],
        event_url=event["event_url"],
        status="SCHEDULED",
    )
    db.add(interview)
    candidate.status = "INTERVIEW_SCHEDULED"
    db.commit()
    db.refresh(interview)

    subject, body = interview_invitation_body(
        candidate.name,
        payload.scheduled_at.strftime("%d %b %Y, %H:%M UTC"),
        payload.duration_minutes,
        event["meet_url"],
    )
    log = send_email(
        db,
        to_email=candidate.email,
        subject=subject,
        body=body,
        email_type="INTERVIEW_INVITE",
        candidate_id=candidate.id,
    )
    interview.email_sent = log.status in {"SENT", "LOGGED"}
    db.commit()
    return {
        "id": interview.id,
        "meet_url": interview.meet_url,
        "event_url": interview.event_url,
        "status": candidate.status,
        "email_status": log.status,
        "email_error": log.error,
        "safe_mode": log.safe_mode,
    }


@router.post("/api/interviews/{interview_id}/send-invitation")
def retry_invitation(interview_id: int, db: Session = Depends(get_db)):
    interview = db.query(Interview).filter(Interview.id == interview_id).one_or_none()
    if not interview:
        raise HTTPException(404, "Interview not found")
    candidate = interview.candidate
    subject, body = interview_invitation_body(
        candidate.name,
        interview.scheduled_at.strftime("%d %b %Y, %H:%M UTC"),
        interview.duration_minutes,
        interview.meet_url,
    )
    log = send_email(
        db,
        to_email=candidate.email,
        subject=subject,
        body=body,
        email_type="INTERVIEW_INVITE",
        candidate_id=candidate.id,
    )
    if log.status in {"SENT", "LOGGED"}:
        interview.email_sent = True
    db.commit()
    return {"email_status": log.status, "email_error": log.error, "safe_mode": log.safe_mode}
