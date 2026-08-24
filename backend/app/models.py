from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), index=True)
    college: Mapped[str] = mapped_column(String(255), default="")
    branch: Mapped[str] = mapped_column(String(255), default="")
    cgpa: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_ai_project: Mapped[str] = mapped_column(Text, default="")
    research_work: Mapped[str] = mapped_column(Text, default="")
    github_url: Mapped[str] = mapped_column(String(500), default="")
    github_username: Mapped[str] = mapped_column(String(255), default="")
    resume_url: Mapped[str] = mapped_column(String(1000), default="")
    resume_text: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="UPLOADED", index=True)
    processing_error: Mapped[str] = mapped_column(Text, default="")

    resume_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    skills_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    ai_project_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    github_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    research_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cgpa_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    pre_test_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    test_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    final_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    evaluations = relationship("Evaluation", back_populates="candidate")
    github_repos = relationship("GithubRepository", back_populates="candidate")
    test_results = relationship("TestResult", back_populates="candidate")
    interviews = relationship("Interview", back_populates="candidate")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), default="Open Role")
    raw_text: Mapped[str] = mapped_column(Text)
    required_skills: Mapped[str] = mapped_column(Text, default="[]")
    preferred_skills: Mapped[str] = mapped_column(Text, default="[]")
    technologies: Mapped[str] = mapped_column(Text, default="[]")
    education_requirements: Mapped[str] = mapped_column(Text, default="[]")
    experience_requirements: Mapped[str] = mapped_column(Text, default="[]")
    project_requirements: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ScreeningRun(Base):
    __tablename__ = "screening_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    job_description_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_descriptions.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), default="PENDING")
    total: Mapped[int] = mapped_column(Integer, default=0)
    processed: Mapped[int] = mapped_column(Integer, default=0)
    failed: Mapped[int] = mapped_column(Integer, default=0)
    current_step: Mapped[str] = mapped_column(String(100), default="")
    current_candidate: Mapped[str] = mapped_column(String(255), default="")
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    screening_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("screening_runs.id"), nullable=True
    )
    resume_score: Mapped[float] = mapped_column(Float, default=0)
    skills_score: Mapped[float] = mapped_column(Float, default=0)
    ai_project_score: Mapped[float] = mapped_column(Float, default=0)
    research_score: Mapped[float] = mapped_column(Float, default=0)
    github_eval_score: Mapped[float] = mapped_column(Float, default=0)
    matching_skills: Mapped[str] = mapped_column(Text, default="[]")
    strengths: Mapped[str] = mapped_column(Text, default="[]")
    gaps: Mapped[str] = mapped_column(Text, default="[]")
    evidence: Mapped[str] = mapped_column(Text, default="[]")
    github_evidence: Mapped[str] = mapped_column(Text, default="[]")
    reasoning: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    candidate = relationship("Candidate", back_populates="evaluations")


class GithubRepository(Base):
    __tablename__ = "github_repositories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    repo_name: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    language: Mapped[str] = mapped_column(String(100), default="")
    languages_json: Mapped[str] = mapped_column(Text, default="{}")
    readme_excerpt: Mapped[str] = mapped_column(Text, default="")
    last_push: Mapped[str] = mapped_column(String(50), default="")
    commit_count_recent: Mapped[int] = mapped_column(Integer, default=0)
    is_relevant: Mapped[bool] = mapped_column(Boolean, default=False)
    relevance_notes: Mapped[str] = mapped_column(Text, default="")

    candidate = relationship("Candidate", back_populates="github_repos")


class TestResult(Base):
    __tablename__ = "test_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidates.id"), nullable=True
    )
    email: Mapped[str] = mapped_column(String(255), index=True)
    logical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    coding_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    computed_test_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    matched: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    candidate = relationship("Candidate", back_populates="test_results")


class Interview(Base):
    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("candidates.id"))
    scheduled_at: Mapped[datetime] = mapped_column(DateTime)
    duration_minutes: Mapped[int] = mapped_column(Integer, default=30)
    calendar_event_id: Mapped[str] = mapped_column(String(255), default="")
    meet_url: Mapped[str] = mapped_column(String(1000), default="")
    event_url: Mapped[str] = mapped_column(String(1000), default="")
    status: Mapped[str] = mapped_column(String(50), default="SCHEDULED")
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    candidate = relationship("Candidate", back_populates="interviews")


class EmailLog(Base):
    __tablename__ = "email_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_id: Mapped[int | None] = mapped_column(
        ForeignKey("candidates.id"), nullable=True
    )
    email_type: Mapped[str] = mapped_column(String(50))
    to_email: Mapped[str] = mapped_column(String(255))
    subject: Mapped[str] = mapped_column(String(500), default="")
    status: Mapped[str] = mapped_column(String(50), default="LOGGED")
    error: Mapped[str] = mapped_column(Text, default="")
    safe_mode: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class OAuthCredential(Base):
    __tablename__ = "oauth_credentials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(50), unique=True)
    access_token: Mapped[str] = mapped_column(Text, default="")
    refresh_token: Mapped[str] = mapped_column(Text, default="")
    token_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scopes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
