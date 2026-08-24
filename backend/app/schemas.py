from datetime import datetime

from pydantic import BaseModel, Field


class CandidateOut(BaseModel):
    id: int
    name: str
    email: str
    college: str
    branch: str
    cgpa: float | None
    best_ai_project: str
    research_work: str
    github_url: str
    github_username: str
    resume_url: str
    status: str
    processing_error: str
    resume_score: float | None
    skills_score: float | None
    ai_project_score: float | None
    github_score: float | None
    research_score: float | None
    cgpa_score: float | None
    pre_test_score: float | None
    test_score: float | None
    final_score: float | None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class CandidateDetail(CandidateOut):
    resume_text: str = ""
    evaluation: dict | None = None
    github_repos: list[dict] = []
    interviews: list[dict] = []


class JobIn(BaseModel):
    title: str = "Open Role"
    raw_text: str


class JobOut(BaseModel):
    id: int
    title: str
    raw_text: str
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    technologies: list[str] = []
    education_requirements: list[str] = []
    experience_requirements: list[str] = []
    project_requirements: list[str] = []
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class GeminiComponentEval(BaseModel):
    resume_score: float = Field(ge=0, le=100)
    skills_score: float = Field(ge=0, le=100)
    ai_project_score: float = Field(ge=0, le=100)
    research_score: float = Field(ge=0, le=100)
    github_eval_score: float = Field(ge=0, le=100)
    matching_skills: list[str] = []
    strengths: list[str] = []
    gaps: list[str] = []
    evidence: list[str] = []
    github_evidence: list[str] = []
    reasoning: str = ""


class JDExtract(BaseModel):
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    technologies: list[str] = []
    education_requirements: list[str] = []
    experience_requirements: list[str] = []
    project_requirements: list[str] = []


class ScreeningStart(BaseModel):
    job_id: int | None = None


class InterviewScheduleIn(BaseModel):
    candidate_id: int
    scheduled_at: datetime
    duration_minutes: int = 30


class TestInviteIn(BaseModel):
    candidate_ids: list[int] = []
    send_all_shortlisted: bool = False


class GoogleCodeIn(BaseModel):
    code: str
