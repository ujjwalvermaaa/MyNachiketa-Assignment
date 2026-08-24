import os
from datetime import datetime, timedelta, timezone

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.config import settings
from app.models import OAuthCredential

# Local HTTP OAuth is required for localhost development.
os.environ.setdefault("OAUTHLIB_INSECURE_TRANSPORT", "1")
# Google often returns extra scopes (openid/email); don't fail the exchange.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "https://www.googleapis.com/auth/calendar",
]


def _client_config() -> dict:
    return {
        "web": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uris": [settings.google_redirect_uri],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def _flow() -> Flow:
    # Web clients have a secret, so PKCE is optional. A new Flow is created
    # for login and again for token exchange, so a generated verifier would
    # be lost and Google would reject the code.
    flow = Flow.from_client_config(
        _client_config(),
        scopes=SCOPES,
        autogenerate_code_verifier=False,
    )
    flow.redirect_uri = settings.google_redirect_uri
    return flow


def login_url() -> str:
    url, _ = _flow().authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )
    return url


def exchange_code(db: Session, code: str) -> None:
    flow = _flow()
    flow.fetch_token(code=code)
    creds = flow.credentials
    expiry = creds.expiry
    row = db.query(OAuthCredential).filter_by(provider="google").one_or_none()
    if not row:
        row = OAuthCredential(provider="google")
        db.add(row)
    row.access_token = creds.token or ""
    if creds.refresh_token:
        row.refresh_token = creds.refresh_token
    row.token_expiry = expiry
    row.scopes = " ".join(creds.scopes or SCOPES)
    db.commit()


def calendar_connected(db: Session) -> bool:
    row = db.query(OAuthCredential).filter_by(provider="google").one_or_none()
    return bool(row and (row.refresh_token or row.access_token))


def _credentials(db: Session) -> Credentials:
    row = db.query(OAuthCredential).filter_by(provider="google").one_or_none()
    if not row:
        raise RuntimeError("Google Calendar is not connected")
    creds = Credentials(
        token=row.access_token,
        refresh_token=row.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES,
    )
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        row.access_token = creds.token or row.access_token
        row.token_expiry = creds.expiry
        db.commit()
    return creds


def create_meet_event(
    db: Session,
    summary: str,
    start: datetime,
    duration_minutes: int,
    attendee_email: str,
) -> dict:
    creds = _credentials(db)
    service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    end = start + timedelta(minutes=duration_minutes)
    body = {
        "summary": summary,
        "description": "Interview scheduled via myNachiketa screening platform.",
        "start": {"dateTime": start.isoformat(), "timeZone": "UTC"},
        "end": {"dateTime": end.isoformat(), "timeZone": "UTC"},
        "attendees": [{"email": attendee_email}],
        "conferenceData": {
            "createRequest": {
                "requestId": f"mn-{int(datetime.now(timezone.utc).timestamp())}-{attendee_email[:8]}",
                "conferenceSolutionKey": {"type": "hangoutsMeet"},
            }
        },
    }
    event = (
        service.events()
        .insert(calendarId="primary", body=body, conferenceDataVersion=1, sendUpdates="none")
        .execute()
    )
    meet = ""
    entry_points = (event.get("conferenceData") or {}).get("entryPoints") or []
    for point in entry_points:
        if point.get("entryPointType") == "video":
            meet = point.get("uri") or ""
            break
    return {
        "event_id": event.get("id") or "",
        "event_url": event.get("htmlLink") or "",
        "meet_url": meet or event.get("hangoutLink") or "",
    }
