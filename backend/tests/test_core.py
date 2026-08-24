import json
from datetime import datetime
from types import SimpleNamespace

from app.routes.screening import _job_payload
from app.services.scoring import (
    cgpa_to_score,
    compute_test_score,
    final_score,
    next_status,
    parse_github_username,
    pre_test_score,
)
from app.utils.validation import parse_candidates, parse_tests


def test_job_payload_is_json_serializable():
    job = SimpleNamespace(
        id=1,
        title="Role",
        raw_text="Python",
        required_skills="[\"Python\"]",
        preferred_skills="[]",
        technologies="[]",
        education_requirements="[]",
        experience_requirements="[]",
        project_requirements="[]",
        created_at=datetime.utcnow(),
    )
    json.dumps(_job_payload(job))


def test_github_url_parsing():
    assert parse_github_username("https://github.com/pranchalkumar001") == "pranchalkumar001"
    assert parse_github_username("github.com/Saurav2K03/") == "Saurav2K03"
    assert parse_github_username("anvragsingh") == "anvragsingh"
    assert parse_github_username("") == ""
    assert parse_github_username("nan") == ""


def test_cgpa_and_pretest_scoring():
    assert cgpa_to_score(8.2) == 82.0
    assert cgpa_to_score(4.0) == 100.0
    score = pre_test_score(80, 70, 60, 50, 90)
    assert 65 <= score <= 75


def test_test_and_final_score():
    ts = compute_test_score(50, 100)
    assert ts == 80.0
    assert final_score(80, 50) == 74.0
    assert final_score(80, None) == 80.0


def test_status_transitions():
    assert next_status(70, None, "SCREENING") == "SHORTLISTED"
    assert next_status(40, None, "SCREENING") == "SCREENED"
    assert next_status(80, 90, "TEST_INVITED") == "INTERVIEW_ELIGIBLE"
    assert next_status(80, 10, "TEST_INVITED") == "TEST_COMPLETED"
    assert next_status(90, 90, "INTERVIEW_SCHEDULED") == "INTERVIEW_SCHEDULED"


def test_csv_validation(tmp_path):
    csv = (
        "name,email,college,branch,cgpa,best_ai_project,research_work,github,resume\n"
        "Ada,ada@test.com,MIT,CSE,9.1,LLM rag,,https://github.com/octocat,https://example.com/a.pdf\n"
        "Ada2,not-an-email,MIT,CSE,9,x,y,https://github.com/octocat,https://example.com/a.pdf\n"
        "Ada3,ada@test.com,MIT,CSE,9,x,y,https://github.com/octocat,https://example.com/a.pdf\n"
    ).encode()
    parsed = parse_candidates(csv, "c.csv")
    assert parsed["rows"][0]["email"] == "ada@test.com"
    assert parsed["duplicates_in_file"] == ["ada@test.com"] or any(
        err["error"] == "Invalid email" for err in parsed["errors"]
    )
    assert any("Invalid email" in e["error"] for e in parsed["errors"])


def test_test_csv_validation():
    csv = (
        "Email,Logical Aptitude Score,Coding Test Score\n"
        "ada@test.com,40,80\n"
    ).encode()
    parsed = parse_tests(csv, "t.csv")
    assert parsed["rows"][0]["logical"] == 40
    assert parsed["rows"][0]["coding"] == 80
