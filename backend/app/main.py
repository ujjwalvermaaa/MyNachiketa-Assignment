from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine, SessionLocal
from app.models import Candidate, Interview, ScreeningRun
from app.routes import candidates, interviews, screening, tests

app = FastAPI(title="myNachiketa Screening", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(candidates.router)
app.include_router(screening.router)
app.include_router(tests.router)
app.include_router(interviews.router)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/dashboard")
def dashboard():
    db = SessionLocal()
    try:
        total = db.query(Candidate).count()
        screened = db.query(Candidate).filter(Candidate.pre_test_score.isnot(None)).count()
        shortlisted = (
            db.query(Candidate)
            .filter(
                Candidate.status.in_(
                    ["SHORTLISTED", "TEST_INVITED", "TEST_COMPLETED", "INTERVIEW_ELIGIBLE", "INTERVIEW_SCHEDULED"]
                )
            )
            .count()
        )
        tests_completed = db.query(Candidate).filter(Candidate.test_score.isnot(None)).count()
        interview_eligible = (
            db.query(Candidate)
            .filter(Candidate.status.in_(["INTERVIEW_ELIGIBLE", "INTERVIEW_SCHEDULED"]))
            .count()
        )
        interviews_scheduled = (
            db.query(Candidate).filter(Candidate.status == "INTERVIEW_SCHEDULED").count()
        )
        top = (
            db.query(Candidate)
            .filter(Candidate.final_score.isnot(None))
            .order_by(Candidate.final_score.desc())
            .limit(5)
            .all()
        )
        upcoming = (
            db.query(Interview)
            .order_by(Interview.scheduled_at.asc())
            .limit(5)
            .all()
        )
        run = db.query(ScreeningRun).order_by(ScreeningRun.id.desc()).first()
        return {
            "totals": {
                "candidates": total,
                "screened": screened,
                "shortlisted": shortlisted,
                "tests_completed": tests_completed,
                "interview_eligible": interview_eligible,
                "interviews_scheduled": interviews_scheduled,
            },
            "top_candidates": [
                {
                    "id": c.id,
                    "name": c.name,
                    "college": c.college,
                    "final_score": c.final_score,
                    "status": c.status,
                    "github_url": c.github_url,
                    "resume_url": c.resume_url,
                    "best_ai_project": (c.best_ai_project or "")[:180],
                }
                for c in top
            ],
            "upcoming_interviews": [
                {
                    "id": i.id,
                    "candidate_name": i.candidate.name if i.candidate else "",
                    "scheduled_at": i.scheduled_at,
                    "meet_url": i.meet_url,
                }
                for i in upcoming
            ],
            "latest_run": {
                "id": run.id,
                "status": run.status,
                "processed": run.processed,
                "total": run.total,
                "failed": run.failed,
                "current_step": run.current_step,
            }
            if run
            else None,
            "email_safe_mode": settings.email_safe_mode,
        }
    finally:
        db.close()
