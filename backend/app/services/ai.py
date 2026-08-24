import json
import logging
import time

import httpx

from app.config import settings
from app.schemas import GeminiComponentEval, JDExtract

log = logging.getLogger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _generate(prompt: str) -> dict:
    url = GEMINI_URL.format(model=settings.gemini_model)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }
    last_error = None
    with httpx.Client(timeout=60) as client:
        for attempt in range(5):
            response = client.post(url, params={"key": settings.gemini_api_key}, json=payload)
            if response.status_code == 429:
                wait = 8 * (attempt + 1)
                log.warning("Gemini rate limited, retrying in %ss", wait)
                time.sleep(wait)
                last_error = response
                continue
            response.raise_for_status()
            data = response.json()
            break
        else:
            if last_error is not None:
                last_error.raise_for_status()
            raise RuntimeError("Gemini request failed")
    text = (
        data.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    )
    return json.loads(text)


def extract_job_description(raw_text: str) -> JDExtract:
    prompt = f"""Extract hiring requirements from this job description.
Return JSON only with keys:
required_skills, preferred_skills, technologies, education_requirements,
experience_requirements, project_requirements.
Each value must be an array of short strings.
Do not invent requirements that are not in the text.
If a field is not mentioned, return an empty array.

JOB DESCRIPTION:
{raw_text}
"""
    try:
        parsed = _generate(prompt)
        return JDExtract.model_validate(parsed)
    except Exception:
        log.exception("JD extraction failed")
        return JDExtract()


def evaluate_candidate(
    jd: dict,
    candidate: dict,
    resume_text: str,
    github_summary: str,
    github_repos: list[dict],
) -> GeminiComponentEval:
    repo_lines = []
    for repo in github_repos[:8]:
        repo_lines.append(
            f"- {repo.get('full_name')}: {repo.get('description') or ''} | "
            f"lang={repo.get('language') or ''} | {repo.get('relevance_notes') or ''} | "
            f"readme={str(repo.get('readme_excerpt') or '')[:400]}"
        )
    prompt = f"""You are evaluating a candidate against a job description.
Use ONLY the evidence provided. If something is missing, score it low and list it in gaps.
Do not invent projects, papers, employers, or GitHub work.
Do not calculate a final weighted total. Return component scores only, each 0-100.

Return JSON with:
resume_score, skills_score, ai_project_score, research_score, github_eval_score,
matching_skills (array), strengths (array), gaps (array),
evidence (array of short quotes/facts from the materials),
github_evidence (array), reasoning (string).

JOB REQUIREMENTS:
{json.dumps(jd, default=str)}

CANDIDATE FIELDS:
name={candidate.get('name')}
college={candidate.get('college')}
branch={candidate.get('branch')}
cgpa={candidate.get('cgpa')}
best_ai_project={candidate.get('best_ai_project')}
research_work={candidate.get('research_work')}

RESUME TEXT:
{resume_text[:12000] if resume_text else "NO RESUME TEXT AVAILABLE"}

GITHUB SUMMARY:
{github_summary or "NO GITHUB EVIDENCE"}

GITHUB REPOS:
{chr(10).join(repo_lines) or "NONE"}
"""
    try:
        parsed = _generate(prompt)
        return GeminiComponentEval.model_validate(parsed)
    except Exception:
        log.exception("Candidate evaluation failed")
        return GeminiComponentEval(
            resume_score=0,
            skills_score=0,
            ai_project_score=20 if candidate.get("best_ai_project") else 0,
            research_score=20 if candidate.get("research_work") else 0,
            github_eval_score=0,
            matching_skills=[],
            strengths=[],
            gaps=["AI evaluation failed or returned invalid JSON"],
            evidence=[],
            github_evidence=[],
            reasoning="Fallback scores used because Gemini did not return valid structured JSON.",
        )
