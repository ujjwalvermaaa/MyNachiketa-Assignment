import math
import re

import pandas as pd

REQUIRED = {
    "name": ["name", "candidate", "candidate_name", "full_name"],
    "email": ["email", "email_id", "mail"],
    "college": ["college", "university", "institute"],
    "branch": ["branch", "department", "stream", "major"],
    "cgpa": ["cgpa", "gpa", "grade"],
    "best_ai_project": [
        "best_ai_project",
        "best ai project",
        "ai_project",
        "ai project",
        "project",
    ],
    "research_work": ["research_work", "research work", "research", "publications"],
    "github": ["github", "github_profile", "github profile", "github_url"],
    "resume": ["resume", "resume_link", "resume link", "cv", "cv_link"],
}

TEST_REQUIRED = {
    "email": ["email", "email_id", "mail"],
    "name": ["name", "candidate", "candidate_name"],
    "logical": [
        "logical",
        "test_la",
        "logical aptitude score",
        "logical_aptitude",
        "la",
    ],
    "coding": ["coding", "test_code", "coding test score", "coding_test", "code"],
}


def _norm(col: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(col).strip().lower()).strip()


def _map_columns(columns, mapping: dict[str, list[str]]) -> dict[str, str]:
    normalized = {_norm(c): c for c in columns}
    found = {}
    for field, aliases in mapping.items():
        for alias in aliases:
            if alias in normalized:
                found[field] = normalized[alias]
                break
            for key, original in normalized.items():
                if alias == key or alias in key.split():
                    found[field] = original
                    break
            if field in found:
                break
    return found


def _clean(value) -> str:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat"}:
        return ""
    return text


def read_table(content: bytes, filename: str, preferred_sheets: list[str] | None = None) -> pd.DataFrame:
    name = (filename or "").lower()
    from io import BytesIO

    buffer = BytesIO(content)
    if name.endswith(".xlsx") or name.endswith(".xls"):
        book = pd.ExcelFile(buffer)
        if preferred_sheets:
            for sheet in preferred_sheets:
                if sheet in book.sheet_names:
                    return book.parse(sheet)
        return book.parse(book.sheet_names[0])
    return pd.read_csv(buffer)


def parse_candidates(content: bytes, filename: str) -> dict:
    df = read_table(content, filename, ["Response", "Candidates", "candidates"])
    mapped = _map_columns(df.columns, REQUIRED)
    missing = [field for field in ["name", "email"] if field not in mapped]
    rows = []
    errors = []
    seen = set()
    duplicates = []
    for index, row in df.iterrows():
        item = {field: _clean(row[col]) if col in row else "" for field, col in mapped.items()}
        email = item.get("email", "").lower()
        name = item.get("name", "")
        if not name or not email:
            errors.append({"row": int(index) + 2, "error": "Name and email are required"})
            continue
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            errors.append({"row": int(index) + 2, "email": email, "error": "Invalid email"})
            continue
        if email in seen:
            duplicates.append(email)
            # keep the row; the sample dataset reuses demo inboxes
        seen.add(email)
        cgpa = None
        if item.get("cgpa"):
            try:
                cgpa = float(item["cgpa"])
            except ValueError:
                errors.append({"row": int(index) + 2, "error": f"Invalid CGPA: {item['cgpa']}"})
        rows.append(
            {
                "name": name,
                "email": email,
                "college": item.get("college", ""),
                "branch": item.get("branch", ""),
                "cgpa": cgpa,
                "best_ai_project": item.get("best_ai_project", ""),
                "research_work": item.get("research_work", ""),
                "github": item.get("github", ""),
                "resume": item.get("resume", ""),
            }
        )
    return {
        "rows": rows,
        "errors": errors,
        "duplicates_in_file": duplicates,
        "mapped_columns": mapped,
        "missing_optional": [f for f in REQUIRED if f not in mapped and f not in {"name", "email"}],
    }


def parse_tests(content: bytes, filename: str) -> dict:
    df = read_table(content, filename, ["Test Result", "Test Results", "Tests"])
    mapped = _map_columns(df.columns, TEST_REQUIRED)
    if "email" not in mapped:
        raise ValueError("Test CSV must include an Email column")
    rows = []
    errors = []
    for index, row in df.iterrows():
        email = _clean(row[mapped["email"]]).lower()
        if not email:
            errors.append({"row": int(index) + 2, "error": "Missing email"})
            continue
        logical = coding = None
        try:
            if "logical" in mapped:
                logical = float(row[mapped["logical"]])
        except (TypeError, ValueError):
            errors.append({"row": int(index) + 2, "error": "Invalid logical score"})
            continue
        try:
            if "coding" in mapped:
                coding = float(row[mapped["coding"]])
        except (TypeError, ValueError):
            errors.append({"row": int(index) + 2, "error": "Invalid coding score"})
            continue
        rows.append({
            "email": email,
            "name": _clean(row[mapped["name"]]) if "name" in mapped else "",
            "logical": logical,
            "coding": coding,
        })
    return {"rows": rows, "errors": errors, "mapped_columns": mapped}
