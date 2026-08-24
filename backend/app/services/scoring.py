import math
import re

from app.config import settings


def clamp(value: float, low: float = 0, high: float = 100) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 0.0
    return max(low, min(high, float(value)))


def cgpa_to_score(cgpa: float | None) -> float:
    if cgpa is None:
        return 0.0
    value = float(cgpa)
    if value <= 0:
        return 0.0
    if value <= 4:
        return clamp((value / 4.0) * 100)
    if value <= 10:
        return clamp((value / 10.0) * 100)
    return 100.0


def pre_test_score(
    resume_score: float,
    ai_project_score: float,
    github_score: float,
    research_score: float,
    cgpa_score: float,
) -> float:
    total = (
        clamp(resume_score) * settings.weight_resume
        + clamp(ai_project_score) * settings.weight_ai_project
        + clamp(github_score) * settings.weight_github
        + clamp(research_score) * settings.weight_research
        + clamp(cgpa_score) * settings.weight_cgpa
    )
    return round(clamp(total), 2)


def compute_test_score(logical: float | None, coding: float | None) -> float | None:
    if logical is None or coding is None:
        return None
    total = clamp(logical) * settings.weight_test_logical + clamp(coding) * settings.weight_test_coding
    return round(clamp(total), 2)


def final_score(pre: float | None, test: float | None) -> float | None:
    if pre is None:
        return None
    if test is None:
        return round(clamp(pre), 2)
    return round(
        clamp(pre) * settings.weight_pretest + clamp(test) * settings.weight_test,
        2,
    )


def parse_github_username(value: str | None) -> str:
    if not value:
        return ""
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "n/a", "-"}:
        return ""
    text = text.replace("https://", "").replace("http://", "")
    text = text.split("?")[0].strip("/")
    match = re.search(r"(?:www\.)?github\.com/([A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)", text, re.I)
    if match:
        return match.group(1)
    if re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?", text):
        return text
    return ""


def next_status(pre: float | None, test: float | None, current: str) -> str:
    if current in {"INTERVIEW_SCHEDULED"}:
        return current
    if test is not None and pre is not None:
        final = final_score(pre, test)
        if final is not None and final >= settings.interview_threshold:
            return "INTERVIEW_ELIGIBLE"
        return "TEST_COMPLETED"
    if pre is not None and pre >= settings.shortlist_threshold:
        if current in {"TEST_INVITED", "TEST_COMPLETED", "INTERVIEW_ELIGIBLE"}:
            return current
        return "SHORTLISTED"
    if pre is not None:
        return "SCREENED"
    return current or "UPLOADED"
