import base64
import json

import httpx

from app.config import settings
from app.services.scoring import parse_github_username

API = "https://api.github.com"


def _headers() -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "mynachiketa-screening",
    }
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers


def analyze_github(profile: str, relevant_keywords: list[str] | None = None) -> dict:
    username = parse_github_username(profile)
    if not username:
        return {
            "ok": False,
            "username": "",
            "error": "No GitHub profile provided",
            "repos": [],
            "summary": "No GitHub username available.",
        }

    keywords = [k.lower() for k in (relevant_keywords or []) if k]
    with httpx.Client(timeout=25, headers=_headers()) as client:
        user_resp = client.get(f"{API}/users/{username}")
        if user_resp.status_code == 404:
            return {
                "ok": False,
                "username": username,
                "error": "GitHub user not found",
                "repos": [],
                "summary": f"GitHub user '{username}' was not found.",
            }
        if user_resp.status_code == 403:
            return {
                "ok": False,
                "username": username,
                "error": "GitHub API rate limit or permission error",
                "repos": [],
                "summary": "GitHub API rate limit reached while fetching this profile.",
            }
        if user_resp.status_code >= 400:
            return {
                "ok": False,
                "username": username,
                "error": f"GitHub user lookup failed ({user_resp.status_code})",
                "repos": [],
                "summary": "Could not load this GitHub profile.",
            }

        repos_resp = client.get(
            f"{API}/users/{username}/repos",
            params={"per_page": 20, "sort": "updated", "type": "owner"},
        )
        if repos_resp.status_code >= 400:
            return {
                "ok": False,
                "username": username,
                "error": f"GitHub repos failed ({repos_resp.status_code})",
                "repos": [],
                "summary": "Could not fetch repositories.",
            }
        raw_repos = repos_resp.json()
        if not raw_repos:
            return {
                "ok": True,
                "username": username,
                "error": "",
                "repos": [],
                "summary": f"GitHub user '{username}' has no public repositories.",
            }

        analyzed = []
        for repo in raw_repos[:12]:
            if repo.get("fork"):
                continue
            item = _inspect_repo(client, repo, keywords)
            analyzed.append(item)
            if len(analyzed) >= 8:
                break

        relevant = [r for r in analyzed if r["is_relevant"]]
        summary_bits = [
            f"{r['full_name']} ({r['language'] or 'n/a'}): {r['description'] or r['relevance_notes']}"
            for r in (relevant or analyzed)[:6]
        ]
        return {
            "ok": True,
            "username": username,
            "error": "",
            "repos": analyzed,
            "summary": " | ".join(summary_bits) if summary_bits else "Repositories inspected but little technical signal found.",
        }


def _inspect_repo(client: httpx.Client, repo: dict, keywords: list[str]) -> dict:
    full_name = repo.get("full_name") or ""
    description = repo.get("description") or ""
    language = repo.get("language") or ""
    languages = {}
    readme = ""
    commit_count = 0

    try:
        lang_resp = client.get(f"{API}/repos/{full_name}/languages")
        if lang_resp.status_code == 200:
            languages = lang_resp.json()
    except httpx.HTTPError:
        pass

    try:
        readme_resp = client.get(f"{API}/repos/{full_name}/readme")
        if readme_resp.status_code == 200:
            content = readme_resp.json().get("content") or ""
            readme = base64.b64decode(content).decode("utf-8", "replace")[:2500]
    except (httpx.HTTPError, ValueError):
        pass

    try:
        commits_resp = client.get(
            f"{API}/repos/{full_name}/commits",
            params={"per_page": 10},
        )
        if commits_resp.status_code == 200:
            commit_count = len(commits_resp.json())
    except httpx.HTTPError:
        pass

    blob = " ".join(
        [
            full_name,
            description,
            language,
            " ".join(languages.keys()),
            readme[:800],
        ]
    ).lower()
    hits = [k for k in keywords if k and k in blob] if keywords else []
    default_tech = [
        "python", "ml", "ai", "react", "next", "fastapi", "tensorflow",
        "pytorch", "nlp", "llm", "data", "vision", "keras", "javascript",
        "typescript", "go", "rust", "java",
    ]
    tech_hits = [k for k in default_tech if k in blob]
    is_relevant = bool(hits or tech_hits or language)
    notes = []
    if hits:
        notes.append("JD keyword matches: " + ", ".join(hits[:8]))
    if tech_hits:
        notes.append("Technical signals: " + ", ".join(tech_hits[:8]))
    if language:
        notes.append(f"Primary language: {language}")
    if commit_count:
        notes.append(f"Recent commit pages returned: {commit_count}")

    return {
        "repo_name": repo.get("name") or "",
        "full_name": full_name,
        "description": description,
        "language": language,
        "languages_json": json.dumps(languages),
        "readme_excerpt": readme,
        "last_push": repo.get("pushed_at") or "",
        "commit_count_recent": commit_count,
        "is_relevant": is_relevant,
        "relevance_notes": "; ".join(notes),
    }
