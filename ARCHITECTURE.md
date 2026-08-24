# Architecture

myNachiketa is an AI-assisted recruiting desk. A recruiter uploads candidates, pastes a job description, and the system scores each person against that JD using their resume, form fields, and public GitHub repositories. Shortlisted people can be invited to a test. After test scores are uploaded, the system ranks again and can book a Google Calendar interview with a Meet link.

The design is intentionally a **single FastAPI process + a Next.js UI + one Postgres database**. Screening is a background task inside that process. There is no Redis, Celery, message bus, or microservice split. That matches the workload: tens of candidates, not thousands of concurrent jobs.

## System shape

```
Browser (Next.js, localhost:3000)
        │  JSON over HTTP
        ▼
FastAPI (localhost:8000)
        ├── Gemini          job extract + component scores
        ├── GitHub REST     repo-level inspection
        ├── Google Drive    resume PDF download
        ├── Gmail SMTP      test / interview mail
        ├── Google Calendar OAuth + Meet
        └── Supabase Postgres
```

The frontend is a recruiter console only. It does not score, download PDFs, or talk to Google. Every integration lives on the backend so secrets stay in `backend/.env`.

### Why this split

| Piece | Responsibility |
|---|---|
| Next.js | Pages, polling, OAuth redirect landing (`/auth/callback`) |
| FastAPI | Validation, screening pipeline, scoring, email, calendar |
| Postgres | Candidates, evaluations, GitHub evidence, tests, interviews, OAuth tokens |
| Gemini | Structured JSON only — never the final weighted total |
| Python `config.py` | The only place weights and thresholds are defined |

## Recruitment workflow

```
Upload CSV / XLSX
        ↓
Save job description  →  Gemini extracts requirements
        ↓
Start screening (FastAPI BackgroundTasks, UI polls)
        ↓
For each candidate (isolated try/except):
   download resume PDF → extract text
   inspect GitHub repos (description, languages, README, recent commits)
   Gemini returns component scores + evidence
   Python computes pre-test score and status
        ↓
Ranking (explainable write-up per candidate)
        ↓
SMTP test invite  →  upload test CSV/XLSX  →  final score
        ↓
Google Calendar event with Meet  →  interview email
```

Candidate uniqueness on import is **name + email**, so a shared demo inbox can still import ten rows. Test results match by email first, then by name, because the sample Test Result sheet uses a different inbox than the Response sheet.

## AI evaluation approach

Gemini is used as a **grounded grader**, not as a ranker.

### What the model is allowed to see

For each candidate the prompt includes:

1. Extracted JD requirements (skills, tech, education, projects)
2. Form fields: college, branch, CGPA, best AI project, research
3. Resume text (from the PDF, truncated)
4. A GitHub summary plus up to eight inspected repositories (name, description, language, relevance notes, README excerpt)

The prompt tells the model to use **only that evidence**. If a signal is missing, it must score that component low and list it in `gaps`. It must not invent employers, papers, or repositories.

### What the model returns

JSON with `responseMimeType: application/json`:

- `resume_score`, `skills_score`, `ai_project_score`, `research_score`, `github_eval_score` (each 0–100)
- `matching_skills`, `strengths`, `gaps`
- `evidence`, `github_evidence` (short quotes / facts from the materials)
- `reasoning`

If Gemini fails or returns invalid JSON, the backend keeps going with conservative fallback scores and records a gap: *“AI evaluation failed…”*. One candidate never aborts the run.

### Why Gemini does not compute the final total

LLMs are inconsistent at weighted arithmetic, and recruiters need a formula they can defend. The model only grades **components**. Python always applies the same weights from `backend/app/config.py`. Changing a weight does not require a prompt change.

JD extraction is a separate Gemini call. It returns arrays of required/preferred skills, technologies, education, experience, and project requirements. Those arrays are stored on `job_descriptions` and reused for every candidate in the run, so the grader sees a stable JD.

## Scoring

All weights live in `backend/app/config.py`.

**Pre-test (before a trial score exists)**

| Signal | Weight | Source |
|---|---:|---|
| Resume vs JD | 30% | Gemini |
| Best AI project | 20% | Gemini, from form + resume |
| GitHub | 25% | Gemini, from repo inspection |
| Research | 10% | Gemini |
| CGPA | 15% | Deterministic: 10-point scale × 10, or 4-point × 25 |

```
pre_test = 0.30·resume + 0.20·ai_project + 0.25·github + 0.10·research + 0.15·cgpa
```

**Trial test**

```
test = 0.40·logical + 0.60·coding
```

**Final**

```
final = 0.80·pre_test + 0.20·test     if a test exists
final = pre_test                      otherwise
```

**Pipeline thresholds**

- Pre-test ≥ 60 → `SHORTLISTED` (eligible for a test invite)
- Final ≥ 70 after a test → `INTERVIEW_ELIGIBLE`

Statuses do not jump backwards past `INTERVIEW_SCHEDULED`.

## GitHub analysis

The assignment asks for **repository-level** evaluation, not star or follower counts.

`backend/app/services/github.py`:

1. Parse a username from a URL or a bare handle
2. `GET /users/{username}/repos?sort=updated`
3. Skip forks; inspect up to eight owner repos
4. For each repo: languages, README (decoded), last ~10 commits, description
5. Keyword overlap against the JD plus a small default tech list
6. Persist rows on `github_repositories` (name, languages JSON, README excerpt, relevance notes)
7. Pass that structured evidence into Gemini for `github_eval_score`

A missing GitHub URL is a warning, not a hard fail. The candidate is still scored on resume, project, research, and CGPA.

## Resume processing

Resume URLs in the sample set are Google Drive PDFs. The downloader follows Drive’s `uc?export=download` flow (including the confirm token) and extracts text with PyMuPDF. A resume failure is stored on `candidates.processing_error` and screening continues.

## Runtime and failure isolation

`POST /api/screening/start` inserts a `screening_runs` row and schedules `_run_screening` on FastAPI `BackgroundTasks`. The UI polls `GET /api/screening/{id}`.

Each candidate is wrapped in its own `try/except`. Resume, GitHub, and Gemini errors are recorded; the rest of the batch still runs. JSON payloads going to Gemini stringify datetimes so a JD `created_at` cannot crash the run.

This scales to the assignment size (a handful of candidates, one recruiter) without a worker queue. If volume grew, the same `_run_screening` function could be moved to a worker unchanged; the scoring contract would not change.

## Data model

| Table | Role |
|---|---|
| `candidates` | Form fields, resume text, component scores, status |
| `job_descriptions` | Raw JD + extracted requirement arrays |
| `screening_runs` | Progress the UI polls |
| `evaluations` | Per-run Gemini evidence (explainability) |
| `github_repositories` | Repo-level inspection |
| `test_results` | Uploaded trial scores, matched or unmatched |
| `interviews` | Calendar event id, Meet URL |
| `email_logs` | SMTP result or safe-mode log |
| `oauth_credentials` | Google Calendar tokens (backend only) |

Tables are created with SQLAlchemy `create_all` on startup.

## Frontend

Next.js App Router pages: Dashboard, Candidates, Screening, Ranking, Tests, Interviews. Ranking is sorted by Python `final_score` / `pre_test_score`. The candidate detail page shows Gemini `reasoning`, evidence quotes, gaps, and the inspected repos so a recruiter can see **why** a score landed.

Google OAuth: the backend builds the consent URL; Google redirects to `http://localhost:3000/auth/callback`; the page `POST`s the code to `/api/auth/google/exchange`; tokens are stored in Postgres.

## Email and calendar

- Gmail SMTP for test and interview mail
- `EMAIL_SAFE_MODE=true` writes `email_logs` with status `LOGGED` and does not send
- Calendar uses OAuth scopes `calendar` + `calendar.events`, creates an event with `conferenceData` `hangoutsMeet`, and stores the Meet URL on `interviews`

## Security

- Secrets only in environment variables; APIs never return keys or refresh tokens
- CORS locked to `FRONTEND_URL`
- Local OAuth allows HTTP via `OAUTHLIB_INSECURE_TRANSPORT`
- Upload validation continues past bad rows instead of rejecting the whole file

## HTTP API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness |
| GET | `/api/dashboard` | Counts, top candidates, latest run |
| POST | `/api/candidates/upload` | CSV / XLSX |
| GET | `/api/candidates` | List |
| GET | `/api/candidates/{id}` | Dossier + evidence |
| POST | `/api/jobs` | Save JD, Gemini extract |
| GET | `/api/jobs/latest` | Current JD |
| POST | `/api/screening/start` | Background run |
| GET | `/api/screening` | Latest run |
| GET | `/api/screening/{id}` | Poll |
| GET | `/api/rankings` | Ordered scores |
| POST | `/api/tests/invite` | SMTP test link |
| POST | `/api/tests/upload` | Trial CSV / XLSX |
| GET | `/api/tests` | Uploaded rows |
| GET | `/api/auth/google/login` | Consent URL |
| POST | `/api/auth/google/exchange` | Code → tokens |
| GET | `/api/calendar/status` | Connected? |
| GET | `/api/interviews` | Booked slots |
| POST | `/api/interviews/schedule` | Meet + invite |
| POST | `/api/interviews/{id}/send-invitation` | Retry mail |

## Deployment

Same three pieces: Vercel (UI), Render (API), Supabase (Postgres). Set `NEXT_PUBLIC_API_URL`, `FRONTEND_URL`, and `GOOGLE_REDIRECT_URI` to the public URLs, and add those URLs on the Google Cloud OAuth client. No extra infrastructure is required.
