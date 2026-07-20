# HiringBuddy — AI Recruitment Operating System

An AI-native recruitment platform: post jobs, auto-screen resumes, run AI video
interviews with live proctoring, generate skill assessments, and manage the whole
pipeline — with a natural-language HR copilot on top.

Multi-tenant SaaS: every recruiter belongs to an **organization**, and all jobs,
candidates, and assessments are scoped to that org.

---

## Architecture

```
frontend/  React 19 + Vite + Tailwind (design tokens, light/dark/system themes)
backend/   FastAPI + SQLAlchemy (SQLite in dev, Postgres in prod)
           services/  ai_client · resume_parser · role_engine · skill_engine
                      interview_engine · assessment_engine · job_engine
                      email_service · copilot · security
```

**AI layer** — a single provider abstraction (`services/ai_client.py`) speaks the
OpenAI-compatible API. It supports **Groq** (default), SambaNova, or OpenAI via
`AI_PROVIDER`. Every AI feature is **offline-first**: deterministic logic always
produces a result, and the LLM only *enriches* it — so the app works (and never
hangs) even with no API key.

## Features

- **Jobs** — create roles; AI drafts the description, responsibilities,
  requirements, benefits, interview plan, and technical/HR questions. Public
  careers link + apply-with-resume.
- **Resume intelligence** — 3-layer PDF extraction, skill/role/experience
  detection, explainable match scoring (never random; never fake emails —
  unresolved emails are flagged for review).
- **Screening & ranking** — per-dimension scores with reasoning, candidate
  categories, sort/filter.
- **AI interviews** — adaptive, role-tailored questions + follow-ups, answer
  scoring, transcript, summary, WebRTC video, and live proctoring (integrity
  starts at 100 and deducts on violations).
- **Skill assessments** — role-based MCQ tests (AI-generated, offline fallback),
  auto-scored; correct answers never leave the server.
- **Email automation** — 9 responsive templates (invite, reminder, reschedule,
  shortlist, reject, offer, welcome, follow-up, confirmation) with `{{tokens}}`.
- **HR Copilot** — natural-language queries: “top 5”, “find React devs”,
  “compare A and B”, “who's below 70%”.
- **Auth** — org + JWT + bcrypt; recruiter APIs protected, candidate interview &
  public careers routes open (token-secured).

## Local setup

**Backend**
```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in values
uvicorn main:app --reload   # http://localhost:8000  (docs at /docs)
```

**Frontend**
```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

## Environment variables (`backend/.env`)

| Variable | Purpose |
|---|---|
| `AI_PROVIDER` | `groq` \| `sambanova` \| `openai` (empty = auto-detect from key) |
| `GROQ_API_KEY` | Groq key (or `OPENAI_API_KEY` for the others). Blank ⇒ offline mode |
| `SECRET_KEY` | JWT signing secret — **set a strong 32+ byte value in prod** |
| `DATABASE_URL` | Defaults to SQLite; use a Postgres URL in production |
| `SMTP_USERNAME` / `SMTP_PASSWORD` | Outbound email (also configurable in Settings) |
| `FRONTEND_URL` | Allowed CORS origin for the deployed frontend |

Copy `backend/.env.example` to get started. **Never commit `.env`.**

## Testing

```bash
cd backend
PYTHONPATH="$(pwd)" ./venv/bin/python -m pytest tests/   # or: python tests/test_api.py
```

## Deployment

- **Backend → Render**: the repo includes `render.yaml`. Set `GROQ_API_KEY`,
  `FRONTEND_URL` (and optionally `DATABASE_URL`) in the dashboard.
- **Frontend → Vercel**: `frontend/vercel.json` handles the SPA rewrite. Set
  `VITE_API_URL` to your Render API URL (e.g. `https://hiringbuddy-api.onrender.com/api`).
