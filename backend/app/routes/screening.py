import json
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal, get_db
from app.models import Candidate, Evaluation, GithubRepository, JobDescription, ScreeningRun
from app.schemas import JobIn, ScreeningStart
from app.services import ai, github, resume
from app.services.scoring import (
    cgpa_to_score,
    final_score,
    next_status,
    parse_github_username,
    pre_test_score,
)

router = APIRouter(tags=["screening"])


def _job_payload(job: JobDescription) -> dict:
    def loads(raw: str) -> list:
        try:
            return json.loads(raw or "[]")
        except json.JSONDecodeError:
            return []

    return {
        "id": job.id,
        "title": job.title,
        "raw_text": job.raw_text,
        "required_skills": loads(job.required_skills),
        "preferred_skills": loads(job.preferred_skills),
        "technologies": loads(job.technologies),
        "education_requirements": loads(job.education_requirements),
        "experience_requirements": loads(job.experience_requirements),
        "project_requirements": loads(job.project_requirements),
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


@router.post("/api/jobs")
def save_job(payload: JobIn, db: Session = Depends(get_db)):
    extracted = ai.extract_job_description(payload.raw_text)
    job = JobDescription(
        title=payload.title or "Open Role",
        raw_text=payload.raw_text,
        required_skills=json.dumps(extracted.required_skills),
        preferred_skills=json.dumps(extracted.preferred_skills),
        technologies=json.dumps(extracted.technologies),
        education_requirements=json.dumps(extracted.education_requirements),
        experience_requirements=json.dumps(extracted.experience_requirements),
        project_requirements=json.dumps(extracted.project_requirements),
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return _job_payload(job)


@router.get("/api/jobs/latest")
def latest_job(db: Session = Depends(get_db)):
    job = db.query(JobDescription).order_by(JobDescription.id.desc()).first()
    if not job:
        return None
    return _job_payload(job)


def _run_screening(run_id: int):
    db = SessionLocal()
    try:
        run = db.query(ScreeningRun).filter(ScreeningRun.id == run_id).one()
        job = db.query(JobDescription).filter(JobDescription.id == run.job_description_id).one()
        jd = _job_payload(job)
        keywords = (
            jd["required_skills"]
            + jd["preferred_skills"]
            + jd["technologies"]
            + jd["project_requirements"]
        )
        candidates = db.query(Candidate).order_by(Candidate.id.asc()).all()
        run.status = "RUNNING"
        run.total = len(candidates)
        db.commit()

        for candidate in candidates:
            run.current_candidate = candidate.name
            run.current_step = "Resume processing"
            candidate.status = "SCREENING"
            candidate.processing_error = ""
            db.commit()
            try:
                resume_text = ""
                try:
                    resume_text = resume.download_resume(candidate.resume_url)
                    candidate.resume_text = resume_text
                except Exception as exc:
                    candidate.processing_error = f"Resume: {exc}"

                run.current_step = "GitHub analysis"
                db.commit()
                gh = github.analyze_github(candidate.github_url or candidate.github_username, keywords)
                candidate.github_username = gh.get("username") or parse_github_username(candidate.github_url)
                db.query(GithubRepository).filter(GithubRepository.candidate_id == candidate.id).delete()
                for repo in gh.get("repos") or []:
                    db.add(
                        GithubRepository(
                            candidate_id=candidate.id,
                            repo_name=repo.get("repo_name") or "",
                            full_name=repo.get("full_name") or "",
                            description=repo.get("description") or "",
                            language=repo.get("language") or "",
                            languages_json=repo.get("languages_json") or "{}",
                            readme_excerpt=repo.get("readme_excerpt") or "",
                            last_push=repo.get("last_push") or "",
                            commit_count_recent=repo.get("commit_count_recent") or 0,
                            is_relevant=bool(repo.get("is_relevant")),
                            relevance_notes=repo.get("relevance_notes") or "",
                        )
                    )
                if gh.get("error"):
                    extra = f"GitHub: {gh['error']}"
                    candidate.processing_error = (candidate.processing_error + " | " + extra).strip(" |")

                run.current_step = "AI evaluation"
                db.commit()
                evaluation = ai.evaluate_candidate(
                    jd={k: v for k, v in jd.items() if k != "created_at"},
                    candidate={
                        "name": candidate.name,
                        "college": candidate.college,
                        "branch": candidate.branch,
                        "cgpa": candidate.cgpa,
                        "best_ai_project": candidate.best_ai_project,
                        "research_work": candidate.research_work,
                    },
                    resume_text=resume_text,
                    github_summary=gh.get("summary") or "",
                    github_repos=gh.get("repos") or [],
                )
                db.add(
                    Evaluation(
                        candidate_id=candidate.id,
                        screening_run_id=run.id,
                        resume_score=evaluation.resume_score,
                        skills_score=evaluation.skills_score,
                        ai_project_score=evaluation.ai_project_score,
                        research_score=evaluation.research_score,
                        github_eval_score=evaluation.github_eval_score,
                        matching_skills=json.dumps(evaluation.matching_skills),
                        strengths=json.dumps(evaluation.strengths),
                        gaps=json.dumps(evaluation.gaps),
                        evidence=json.dumps(evaluation.evidence),
                        github_evidence=json.dumps(evaluation.github_evidence),
                        reasoning=evaluation.reasoning,
                    )
                )
                candidate.resume_score = evaluation.resume_score
                candidate.skills_score = evaluation.skills_score
                candidate.ai_project_score = evaluation.ai_project_score
                candidate.research_score = evaluation.research_score
                candidate.github_score = evaluation.github_eval_score
                candidate.cgpa_score = cgpa_to_score(candidate.cgpa)
                candidate.pre_test_score = pre_test_score(
                    evaluation.resume_score,
                    evaluation.ai_project_score,
                    evaluation.github_eval_score,
                    evaluation.research_score,
                    candidate.cgpa_score,
                )
                candidate.final_score = final_score(candidate.pre_test_score, candidate.test_score)
                candidate.status = next_status(
                    candidate.pre_test_score, candidate.test_score, candidate.status
                )
                run.processed += 1
                db.commit()
            except Exception as exc:
                candidate.status = "FAILED"
                candidate.processing_error = str(exc)
                run.failed += 1
                run.processed += 1
                db.commit()

        run.status = "COMPLETED"
        run.current_step = "Done"
        run.current_candidate = ""
        run.completed_at = datetime.utcnow()
        db.commit()
    except Exception as exc:
        run = db.query(ScreeningRun).filter(ScreeningRun.id == run_id).one_or_none()
        if run:
            run.status = "FAILED"
            run.error = str(exc)
            db.commit()
    finally:
        db.close()


@router.post("/api/screening/start")
def start_screening(
    payload: ScreeningStart,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    job = None
    if payload.job_id:
        job = db.query(JobDescription).filter(JobDescription.id == payload.job_id).one_or_none()
    if not job:
        job = db.query(JobDescription).order_by(JobDescription.id.desc()).first()
    if not job:
        raise HTTPException(400, "Save a job description first")
    if db.query(Candidate).count() == 0:
        raise HTTPException(400, "Upload candidates first")
    active = (
        db.query(ScreeningRun)
        .filter(ScreeningRun.status.in_(["PENDING", "RUNNING"]))
        .first()
    )
    if active:
        return {"id": active.id, "status": active.status, "message": "Screening already running"}

    run = ScreeningRun(job_description_id=job.id, status="PENDING")
    db.add(run)
    db.commit()
    db.refresh(run)
    background.add_task(_run_screening, run.id)
    return {"id": run.id, "status": run.status}


@router.get("/api/screening/{run_id}")
def get_screening(run_id: int, db: Session = Depends(get_db)):
    run = db.query(ScreeningRun).filter(ScreeningRun.id == run_id).one_or_none()
    if not run:
        raise HTTPException(404, "Screening run not found")
    return {
        "id": run.id,
        "status": run.status,
        "total": run.total,
        "processed": run.processed,
        "failed": run.failed,
        "current_step": run.current_step,
        "current_candidate": run.current_candidate,
        "error": run.error,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
    }


@router.get("/api/screening")
def latest_screening(db: Session = Depends(get_db)):
    run = db.query(ScreeningRun).order_by(ScreeningRun.id.desc()).first()
    if not run:
        return None
    return get_screening(run.id, db)


@router.get("/api/rankings")
def rankings(db: Session = Depends(get_db)):
    candidates = (
        db.query(Candidate)
        .order_by(
            Candidate.final_score.desc().nullslast(),
            Candidate.pre_test_score.desc().nullslast(),
            Candidate.id.asc(),
        )
        .all()
    )
    ranked = []
    scored = 0
    for candidate in candidates:
        if candidate.pre_test_score is not None:
            scored += 1
            rank = scored
        else:
            rank = None
        ranked.append(
            {
                "rank": rank,
                "id": candidate.id,
                "name": candidate.name,
                "email": candidate.email,
                "college": candidate.college,
                "branch": candidate.branch,
                "cgpa": candidate.cgpa,
                "best_ai_project": candidate.best_ai_project,
                "research_work": candidate.research_work,
                "github_url": candidate.github_url,
                "github_username": candidate.github_username,
                "resume_url": candidate.resume_url,
                "resume_score": candidate.resume_score,
                "ai_project_score": candidate.ai_project_score,
                "github_score": candidate.github_score,
                "research_score": candidate.research_score,
                "pre_test_score": candidate.pre_test_score,
                "test_score": candidate.test_score,
                "final_score": candidate.final_score,
                "status": candidate.status,
            }
        )
    return ranked
