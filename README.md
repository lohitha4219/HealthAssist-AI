# HealthAssist AI — AI-Powered Healthcare Assistant

A full-stack healthcare information, hospital & doctor discovery, appointment booking, and personal health management web application built with a frosted-glass (glassmorphism) React interface, FastAPI REST backend, PostgreSQL 18 persistence via SQLAlchemy + Alembic, JWT authentication with refresh-token rotation, validated PDF/image medical report parsing, Recharts insights, and cloud AI integration (Google Gemini via official `google-genai` SDK or generic OpenAI-compatible) plus local engine support (`llama.cpp` or `Ollama`).

> **Medical Disclaimer:** HealthAssist AI provides general educational health information and personal record organization only. It does **not** diagnose medical conditions, prescribe medications, or replace licensed medical care.

---

## Portals & Access Architecture

HealthAssist AI is built strictly around **two authenticated portals** alongside the **public website**:

1. **Public Website** — Home (`/`), About, 12 Features, 10-step How It Works, Hospital Directory (`/hospitals`, `/hospitals/:id`), Verified Doctor Directory (`/doctors`, `/doctors/:id`), Treatment & Precautions Library (`/treatments`), Contact form (`/api/contact`), Login (`/login`), Patient Registration (`/register`), Forgot/Reset Password (`/forgot-password`, `/reset-password`), and invite-token Doctor Onboarding (`/doctor-onboarding`).
2. **Patient Portal** (`/dashboard`, `/appointments`, `/symptoms`, `/chat`, `/reports`, `/insights`, `/history`, `/notifications`, `/profile`) — Health overview, hospital/doctor appointment booking & management, symptom analysis, AI healthcare chatbot, medical report upload & educational lab extraction, analytics, timeline, and profile.
3. **Doctor Portal** (`/doctor/dashboard`, `/doctor/appointments`, `/doctor/availability`, `/doctor/notifications`, `/doctor/profile`) — Verified doctor schedule overview, patient appointment confirmation/completion/rescheduling, shared consultation notes & educational patient report review, weekly schedule & leave management, and professional profile editing.

There is **no Admin Panel or Admin UI**; hospital maintenance and doctor invite generation are exposed exclusively via key-protected backend endpoints (`X-Maintenance-Key` / `X-Onboarding-Key`).

---

## Project Structure

```text
aihealth/
├── frontend/                      # React 18 + Vite + React Router + Axios + Recharts + Lucide
│   ├── src/
│   │   ├── components/            # PublicNavbar, Footer, ProtectedRoute/RoleRoute, Toast, UI cards
│   │   ├── context/               # AuthContext, ToastContext
│   │   ├── hooks/                 # Scroll reveal hook
│   │   ├── layouts/               # Role-aware AuthenticatedLayout (Patient & Doctor sidebars)
│   │   ├── pages/                 # Landing, Hospitals, Doctors, Treatments, Auth, Patient & Doctor Portals
│   │   ├── routes/                # Lazy-loaded React Router configuration
│   │   ├── services/              # Centralized Axios client, auth, chat/reports, healthcareService
│   │   ├── styles/                # Design tokens, glassmorphism surfaces, animations, global CSS
│   │   └── tests/                 # Vitest + Testing Library suite
│   ├── package.json
│   └── vite.config.js
├── backend/                       # Python 3.12 + FastAPI + SQLAlchemy 2.x + Alembic + Pydantic v2
│   ├── app/
│   │   ├── api/
│   │   │   ├── deps.py            # JWT auth + role guards (patient/doctor/verified_doctor) + operational keys
│   │   │   └── routes/            # auth, public, hospitals, doctors, appointments, doctor_portal, dashboard, symptoms, chat, reports, insights, history, profile
│   │   ├── core/                  # Settings (.env) and bcrypt/JWT security utilities
│   │   ├── database/              # SQLAlchemy engine, Base, and session dependency
│   │   ├── middleware/            # Security headers middleware
│   │   ├── models/                # 21 SQLAlchemy ORM models (integer PKs/FKs)
│   │   ├── schemas/               # Pydantic v2 request/response schemas
│   │   ├── services/              # AI (llama.cpp/Ollama/OpenAI-compatible), appointments, report parsing, symptoms, notifications, activity logging
│   │   └── utils/                 # File magic-byte, filename, and size validation
│   ├── alembic/                   # Migrations: 0001 -> 0002 -> 0003_hospitals_doctors_appointments
│   ├── storage/reports/           # Private per-user uploaded file storage
│   ├── tests/                     # Pytest API, appointment concurrency, onboarding & service test suite
│   └── requirements.txt
├── doc/
│   ├── API.md
│   ├── DATABASE.md
│   ├── SETUP.md
│   └── DEPLOYMENT.md
├── .env.example
└── .gitignore
```

## Quick Start

See [doc/SETUP.md](./doc/SETUP.md) for PostgreSQL 18 database setup, Alembic migrations (`0001 -> 0003`), optional SMTP / operational keys, local AI setup (`llama.cpp` or `Ollama`), and startup/test commands.
