from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Candidate, EmailLog, TestResult
from app.schemas import TestInviteIn
from app.services.email import send_email, test_invitation_body
from app.services.scoring import final_score, next_status, compute_test_score
from app.utils.validation import parse_tests

router = APIRouter(prefix="/api/tests", tags=["tests"])


@router.post("/upload")
def upload_tests(file: UploadFile = File(...), db: Session = Depends(get_db)):
    parsed = parse_tests(file.file.read(), file.filename or "tests.csv")
    matched = []
    unmatched = []
    for row in parsed["rows"]:
        candidates = db.query(Candidate).filter(Candidate.email == row["email"]).all()
        candidate = candidates[0] if len(candidates) == 1 else None
        if not candidate and row.get("name"):
            candidate = (
                db.query(Candidate)
                .filter(Candidate.name.ilike(row["name"]))
                .first()
            )
        if not candidate and len(candidates) > 1:
            candidate = None
        computed = compute_test_score(row["logical"], row["coding"])
        result = TestResult(
            candidate_id=candidate.id if candidate else None,
            email=row["email"],
            logical_score=row["logical"],
            coding_score=row["coding"],
            computed_test_score=computed,
            matched=bool(candidate),
        )
        db.add(result)
        if not candidate:
            unmatched.append(row)
            continue
        candidate.test_score = computed
        candidate.final_score = final_score(candidate.pre_test_score, computed)
        candidate.status = next_status(candidate.pre_test_score, computed, candidate.status)
        matched.append(
            {
                "email": row["email"],
                "name": candidate.name,
                "test_score": computed,
                "final_score": candidate.final_score,
                "status": candidate.status,
            }
        )
    db.commit()
    return {
        "matched": matched,
        "unmatched": unmatched,
        "validation_errors": parsed["errors"],
        "mapped_columns": parsed["mapped_columns"],
    }


@router.get("")
def list_tests(db: Session = Depends(get_db)):
    rows = db.query(TestResult).order_by(TestResult.id.desc()).all()
    return [
        {
            "id": r.id,
            "email": r.email,
            "candidate_id": r.candidate_id,
            "logical_score": r.logical_score,
            "coding_score": r.coding_score,
            "computed_test_score": r.computed_test_score,
            "matched": r.matched,
            "created_at": r.created_at,
        }
        for r in rows
    ]


@router.post("/invite")
def invite(payload: TestInviteIn, db: Session = Depends(get_db)):
    query = db.query(Candidate)
    if payload.send_all_shortlisted:
        candidates = query.filter(
            Candidate.status.in_(["SHORTLISTED", "SCREENED", "TEST_INVITED"])
        ).filter(Candidate.pre_test_score >= settings.shortlist_threshold).all()
    else:
        if not payload.candidate_ids:
            raise HTTPException(400, "Select at least one candidate")
        candidates = query.filter(Candidate.id.in_(payload.candidate_ids)).all()
    sent = []
    for candidate in candidates:
        subject, body = test_invitation_body(candidate.name)
        log: EmailLog = send_email(
            db,
            to_email=candidate.email,
            subject=subject,
            body=body,
            email_type="TEST_INVITE",
            candidate_id=candidate.id,
        )
        if log.status in {"SENT", "LOGGED"}:
            candidate.status = "TEST_INVITED"
        sent.append(
            {
                "candidate_id": candidate.id,
                "email": candidate.email,
                "status": log.status,
                "error": log.error,
                "safe_mode": log.safe_mode,
            }
        )
    db.commit()
    return {"results": sent, "safe_mode": settings.email_safe_mode}
