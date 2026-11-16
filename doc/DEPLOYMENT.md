# HealthAssist AI — Deployment Preparation Guide

## 1. Production Environment Variables

Configure these environment variables securely in your hosting environment (never commit `backend/.env`):

- `APP_ENV="production"`
- `DEBUG=false`
- `EXPOSE_DEV_RESET_TOKEN=false` (MUST stay `false` in production; configure `SMTP_*` below to deliver reset links via email)
- `DATABASE_URL="postgresql+psycopg://<db_user>:<db_password>@<db_host>:5432/healthcare_assistant"`
- `JWT_SECRET_KEY` (64+ random characters)
- `ACCESS_TOKEN_EXPIRE_MINUTES=30`
- `REFRESH_TOKEN_EXPIRE_DAYS=7`
- `CORS_ORIGINS="https://your-frontend-domain.com"`
- `UPLOAD_DIR="/var/app/storage/reports"` (persistent private volume outside static webroot)
- `MAX_UPLOAD_SIZE_MB=10`
- `DOCTOR_ONBOARDING_KEY` (strong secret for `POST /api/auth/doctor-invite`)
- `HOSPITAL_MAINTENANCE_KEY` (strong secret for `POST`/`PATCH /api/hospitals/maintain*`)
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL`, `SMTP_USE_TLS` (optional transactional email delivery)
- `SUPPORT_EMAIL`, `SUPPORT_PHONE`, `SUPPORT_ADDRESS` (optional verified public contact fields)
- `AI_PROVIDER` (`"llamacpp"`, `"ollama"`, or `"openai_compatible"` with `AI_BASE_URL`, `AI_API_KEY`, `AI_MODEL`)

## 2. Frontend Production Build

```bash
cd frontend
VITE_API_BASE_URL="https://api.your-domain.com/api" npm run build
```

Serve `frontend/dist/` behind a CDN or reverse proxy (Nginx/Caddy) with SPA fallback routing to `index.html`.

## 3. Backend Startup Configuration

Apply Alembic migrations before starting workers:

```bash
cd backend
./venv/bin/alembic upgrade head
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```

## 4. Secure File Storage & Role Separation Strategy

- Uploaded reports are validated by extension, Content-Type, and binary magic bytes (`%PDF-`, PNG, JPEG, WEBP) and saved using generated UUID filenames inside per-user subdirectories outside the public web root.
- If a database write fails during upload, the written file is immediately cleaned up from disk.
- Downloads are streamed only via authenticated `GET /api/reports/{id}/download` after verifying ownership or an authorized appointment share (`GET /api/doctor/appointments/{id}/reports`).
- Role boundaries are enforced at the FastAPI dependency layer (`require_patient`, `require_doctor`, `require_verified_doctor`, `require_onboarding_key`, `require_maintenance_key`), with no exposed Admin Panel UI.

## 5. AI Deployment Notes

A local AI server (`llama-server` or `Ollama`) bound to `127.0.0.1` on a personal Mac is **not accessible** from a publicly deployed server. Because AI inference is isolated inside `backend/app/services/ai_service.py`, configure `LLAMACPP_BASE_URL`, `OLLAMA_BASE_URL`, or `AI_PROVIDER="openai_compatible"` (`AI_BASE_URL` + `AI_API_KEY` + `AI_MODEL`) to point to an approved private/cloud inference endpoint.
