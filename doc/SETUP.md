# HealthAssist AI — Local Development Setup Guide

## 1. Environment Requirements

Verified local environment:
- macOS Ventura 13.7.8 (Intel `x86_64`, ~8 GB RAM)
- Python 3.12 (`backend/venv`)
- Node.js 24+ / npm 11+
- PostgreSQL 18 (`/Library/PostgreSQL/18/bin/psql`)

---

## 2. Configure PostgreSQL (`healthcare_assistant`)

Ensure PostgreSQL 18 is running on port `5432`, then create the database (substitute your PostgreSQL superuser or role):

```bash
/Library/PostgreSQL/18/bin/psql -h localhost -p 5432 -U postgres -c "CREATE DATABASE healthcare_assistant;"
```

Copy `.env.example` to `backend/.env` and set your PostgreSQL password and secrets:

```bash
cp .env.example backend/.env
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Update `backend/.env`:

```env
DATABASE_URL="postgresql+psycopg://postgres:YOUR_PASSWORD@localhost:5432/healthcare_assistant"
JWT_SECRET_KEY="YOUR_GENERATED_SECRET"
DOCTOR_ONBOARDING_KEY="OPTIONAL_SECRET_FOR_DOCTOR_INVITE_GENERATION"
HOSPITAL_MAINTENANCE_KEY="OPTIONAL_SECRET_FOR_HOSPITAL_MAINTENANCE_API"
```

Optional environment variables in `backend/.env`:
- **SMTP Email Delivery** (`SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_USE_TLS`): used for password reset & appointment email dispatch when configured; `/api/auth/forgot-password` reports `email_sent: false` if SMTP is unconfigured.
- **Public Support Contact** (`SUPPORT_EMAIL`, `SUPPORT_PHONE`, `SUPPORT_ADDRESS`): optional public contact metadata surfaced via `/api/public/overview`; leaves unspecified fields hidden rather than displaying placeholder numbers.
- **Google Gemini Cloud AI (Recommended)**: Set `GEMINI_API_KEY` in `backend/.env` (free key available from Google AI Studio at `https://aistudio.google.com/`) and optionally `GEMINI_MODEL="gemini-2.5-flash"`. With `AI_PROVIDER="auto"`, Gemini is automatically activated.
- **OpenAI-Compatible AI** (`AI_PROVIDER="openai_compatible"`, `AI_BASE_URL`, `AI_API_KEY`, `AI_MODEL`): optional alternative to Gemini or local `llama.cpp` / `Ollama`.

Run Alembic database migrations (`0001 -> 0002 -> 0003`):

```bash
cd backend
./venv/bin/alembic upgrade head
```

---

## 3. Verified Doctor Onboarding (No Admin Panel)

Public `/register` creates `patient` accounts exclusively. Verified doctor accounts are created using a single-use invite token:

1. Set `DOCTOR_ONBOARDING_KEY` in `backend/.env`.
2. Call `POST /api/auth/doctor-invite` with header `X-Onboarding-Key: <DOCTOR_ONBOARDING_KEY>` and hospital details to receive an invite token.
3. Open `http://localhost:5173/doctor-onboarding` (or post to `/api/auth/doctor-register`) with the invite token to complete the doctor account and linked `doctor_profiles` record.

---

## 4. AI Engine Configuration

### Option A: Google Gemini Cloud AI (Recommended)
1. Obtain a free API key from [Google AI Studio](https://aistudio.google.com/).
2. Add your key to `backend/.env`:
   ```env
   AI_PROVIDER="auto"
   GEMINI_API_KEY="AIzaSyYourActualKeyHere..."
   GEMINI_MODEL="gemini-2.5-flash"
   ```
3. Restart or start FastAPI (`uvicorn app.main:app --port 8000`). With `AI_PROVIDER="auto"`, HealthAssist AI automatically detects and uses the Gemini API.

### Option B: Local Inference with `llama.cpp` (`llama-server`)
On macOS 13 Ventura Intel x86_64:
```bash
brew install llama.cpp
llama-server -m ./models/qwen2.5-1.5b-instruct-q4_k_m.gguf --host 127.0.0.1 --port 8080 -t 4 -c 2048
```

### Option C: OpenAI-Compatible Provider
Configure `AI_PROVIDER="openai_compatible"`, `AI_BASE_URL`, `AI_API_KEY`, and `AI_MODEL` in `backend/.env`.

When no AI provider key is set, HealthAssist AI truthfully displays unconfigured offline status with setup instructions, while all hospital directories, doctor profiles, appointment bookings, symptom analysis, medical reports, insights, and user profiles remain 100% operational.

---

## 5. Start Backend & Frontend

Terminal 1 (Backend):
```bash
cd backend
./venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` (FastAPI Swagger UI available at `http://127.0.0.1:8000/docs`).

---

## 6. Run Tests & Production Build

Backend (`pytest`):
```bash
cd backend
./venv/bin/python -m pytest -q
```

Frontend (`Vitest` & production build):
```bash
cd frontend
CI=true npm test
npm run build
```
