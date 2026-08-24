from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Candidate
from app.schemas import CandidateDetail, CandidateOut
from app.services.scoring import parse_github_username
from app.utils.validation import parse_candidates
import json

router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@router.post("/upload")
def upload_candidates(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = file.file.read()
    parsed = parse_candidates(content, file.filename or "upload.csv")
    created = []
    duplicates = []
    duplicate_emails = []
    seen_emails = set()
    for row in parsed["rows"]:
        existing = (
            db.query(Candidate)
            .filter(Candidate.email == row["email"], Candidate.name == row["name"])
            .one_or_none()
        )
        if existing:
            duplicates.append(f"{row['name']} <{row['email']}>")
            continue
        if row["email"] in seen_emails:
            duplicate_emails.append(row["email"])
        seen_emails.add(row["email"])
        already_email = db.query(Candidate).filter(Candidate.email == row["email"]).first()
        if already_email:
            duplicate_emails.append(row["email"])
        candidate = Candidate(
            name=row["name"],
            email=row["email"],
            college=row["college"],
            branch=row["branch"],
            cgpa=row["cgpa"],
            best_ai_project=row["best_ai_project"],
            research_work=row["research_work"],
            github_url=row["github"],
            github_username=parse_github_username(row["github"]),
            resume_url=row["resume"],
            status="UPLOADED",
        )
        db.add(candidate)
        created.append(row)
    db.commit()
    preview = created[:8]
    return {
        "imported": len(created),
        "duplicates": duplicates + parsed["duplicates_in_file"],
        "duplicate_emails": sorted(set(duplicate_emails)),
        "validation_errors": parsed["errors"],
        "mapped_columns": parsed["mapped_columns"],
        "preview": preview,
        "total_candidates": db.query(Candidate).count(),
    }


@router.get("", response_model=list[CandidateOut])
def list_candidates(db: Session = Depends(get_db)):
    return db.query(Candidate).order_by(Candidate.id.asc()).all()


@router.get("/{candidate_id}", response_model=CandidateDetail)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == candidate_id).one_or_none()
    if not candidate:
        raise HTTPException(404, "Candidate not found")
    evaluation = candidate.evaluations[-1] if candidate.evaluations else None
    eval_payload = None
    if evaluation:
        eval_payload = {
            "resume_score": evaluation.resume_score,
            "skills_score": evaluation.skills_score,
            "ai_project_score": evaluation.ai_project_score,
            "research_score": evaluation.research_score,
            "github_eval_score": evaluation.github_eval_score,
            "matching_skills": json.loads(evaluation.matching_skills or "[]"),
            "strengths": json.loads(evaluation.strengths or "[]"),
            "gaps": json.loads(evaluation.gaps or "[]"),
            "evidence": json.loads(evaluation.evidence or "[]"),
            "github_evidence": json.loads(evaluation.github_evidence or "[]"),
            "reasoning": evaluation.reasoning,
        }
    return CandidateDetail(
        **CandidateOut.model_validate(candidate).model_dump(),
        resume_text=candidate.resume_text or "",
        evaluation=eval_payload,
        github_repos=[
            {
                "repo_name": r.repo_name,
                "full_name": r.full_name,
                "description": r.description,
                "language": r.language,
                "readme_excerpt": r.readme_excerpt,
                "is_relevant": r.is_relevant,
                "relevance_notes": r.relevance_notes,
                "commit_count_recent": r.commit_count_recent,
            }
            for r in candidate.github_repos
        ],
        interviews=[
            {
                "id": i.id,
                "scheduled_at": i.scheduled_at.isoformat() if i.scheduled_at else None,
                "duration_minutes": i.duration_minutes,
                "meet_url": i.meet_url,
                "event_url": i.event_url,
                "status": i.status,
                "email_sent": i.email_sent,
            }
            for i in candidate.interviews
        ],
    )
