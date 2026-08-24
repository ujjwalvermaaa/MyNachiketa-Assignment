# myNachiketa Screening

Recruiter console that screens internship candidates against a job description. It reads resumes, inspects GitHub repositories, scores with Gemini plus Python weights, sends a test invite, then books a Google Meet interview.

Design notes: [ARCHITECTURE.md](./ARCHITECTURE.md)

## Stack

| Layer | Choice |
|---|---|
| UI | Next.js 16, TypeScript, Tailwind |
| API | FastAPI |
| Database | Supabase Postgres |
| AI | Gemini (`gemini-3.6-flash`) |
| Other | GitHub REST, Gmail SMTP, Google Calendar / Meet |

## Quick start

You need Python 3.11+, Node 18+, and a Supabase project.

```bash
# API
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # fill in secrets

# UI
cd ../frontend
npm install
```

Terminal 1:

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Terminal 2:

```bash
cd frontend
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Health check: [http://localhost:8000/health](http://localhost:8000/health)

```bash
cd backend && source .venv/bin/activate && pytest
```

## Environment

Copy `backend/.env.example` to `backend/.env`. Do not commit `.env` or `api_keys.txt`.

| Variable | Notes |
|---|---|
| `DATABASE_URL` | Supabase **session pooler**, port `5432`. If the password contains `@`, encode it as `%40`. Do not leave `[YOUR-PASSWORD]` in the URL. |
| `GEMINI_API_KEY` | Gemini key |
| `GEMINI_MODEL` | `gemini-3.6-flash` |
| `GITHUB_TOKEN` | PAT; avoids unauthenticated rate limits |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | OAuth **Web application** client |
| `GOOGLE_REDIRECT_URI` | Must be `http://localhost:3000/auth/callback` locally |
| `FRONTEND_URL` | `http://localhost:3000` |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | Gmail address + 16-character app password |
| `EMAIL_SAFE_MODE` | `true` logs mail and does not send. Set `false` for a live send. |

Frontend (only needed when the API is not on localhost:8000):

```bash
# frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Tables are created automatically when the API starts.

## Google Calendar

1. Google Cloud → APIs & Services → enable **Google Calendar API**
2. Create an OAuth client, type **Web application**
3. Authorized JavaScript origin: `http://localhost:3000`
4. Authorized redirect URI: `http://localhost:3000/auth/callback`
5. If the app is in Testing, add your Google account under **Audience → Test users**
6. In the app: **Interviews → Connect Google Calendar**

`redirect_uri_mismatch` means the URI on that OAuth client is not exactly the redirect above.

## Demo walkthrough

Sample file: `candidate_dataset.xlsx` (sheets `Response` and `Test Result`).

1. **Candidates** — upload the xlsx (or a CSV with the same columns). Shared demo emails still import; uniqueness is name + email.
2. **Screening** — paste a JD, **Save JD**, **Start screening**. The page polls until the run completes.
3. **Ranking** — open a name for evidence, GitHub repos, and the write-up.
4. **Tests** — invite shortlisted people, then upload the Test Result sheet. Unmatched rows stay visible if emails differ from the candidate sheet.
5. **Interviews** — connect Calendar, pick a candidate and time. Meet is created by Google, not faked.

With `EMAIL_SAFE_MODE=true` the dashboard shows that invitations are logged, not sent.

## Scoring (short)

Gemini grades components 0–100. Python weights them:

- Pre-test: resume 30% · AI project 20% · GitHub 25% · research 10% · CGPA 15%
- Trial: logical 40% · coding 60%
- Final: pre-test 80% · trial 20% (pre-test only until a trial exists)

Weights and thresholds: `backend/app/config.py`.

## Deploy

- Frontend → Vercel (`NEXT_PUBLIC_API_URL` = public API URL)
- Backend → Render, start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Database → the same Supabase project
- Add the production origin and `https://YOUR_APP/auth/callback` on the Google OAuth client
- Set `FRONTEND_URL` and `GOOGLE_REDIRECT_URI` to those production URLs

`GET /health` must return `{"status":"ok"}`.
