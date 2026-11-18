# HealthAssist AI — AI-Powered Healthcare Assistant

A full-stack healthcare information, hospital & doctor discovery, appointment booking, and personal health management web application built with a frosted-glass (glassmorphism) React interface, FastAPI REST backend, PostgreSQL 18 persistence via SQLAlchemy + Alembic, JWT authentication with refresh-token rotation, validated PDF/image medical report parsing, Recharts insights, and cloud AI integration (Google Gemini via official `google-genai` SDK or generic OpenAI-compatible) plus local engine support (`llama.cpp` or `Ollama`).

> **Medical Disclaimer:** HealthAssist AI provides general educational health information and personal record organization only. It does **not** diagnose medical conditions, prescribe medications, or replace licensed medical care.

---

## Live Deployment

**HealthAssist AI is deployed and accessible online.**

| Component | Live URL |
|---|---|
| Frontend Website | https://frontend-seven-jet-60.vercel.app/ |
| Backend API | https://healthassist-ai-1xo7.onrender.com/ |
| API Documentation (Swagger) | https://healthassist-ai-1xo7.onrender.com/docs |
| Treatments API | https://healthassist-ai-1xo7.onrender.com/api/treatments |

**Frontend:** Hosted on Vercel  
**Backend:** Hosted on Render  
**Database:** PostgreSQL hosted on Render

---

## Technologies Used

### 1. Frontend Technologies

| Technology | Purpose |
|---|---|
| HTML5 | Webpage structure |
| CSS3 | Styling, responsive layouts, animations and glassmorphism UI |
| JavaScript (ES6+) | Frontend application logic |
| React 18 | Component-based user interface |
| Vite 6 | Frontend development server and build tool |
| React Router 7 | Client-side navigation and routing |
| Axios | HTTP requests and backend API integration |
| Recharts | Interactive charts and health analytics |
| Lucide React | Icons and interface elements |

### 2. Backend Technologies

| Technology | Purpose |
|---|---|
| Python 3.12 | Backend programming language |
| FastAPI | REST API development |
| Uvicorn | ASGI application server |
| SQLAlchemy 2.x | ORM and database operations |
| Alembic | Database migrations |
| Pydantic v2 | Data validation and request/response schemas |
| PyJWT | JWT authentication |
| bcrypt | Password hashing |
| psycopg 3 | PostgreSQL database connectivity |

### 3. Database

- **PostgreSQL 18** — Relational database management.
- **SQLAlchemy** — Database ORM and query management.
- **Alembic** — Database schema versioning and migrations.

### 4. Artificial Intelligence & Processing

| Technology | Purpose |
|---|---|
| Google Gemini | Cloud-based AI healthcare chatbot integration |
| google-genai | Official Google Gemini SDK |
| OpenAI-compatible API | Alternative cloud AI provider integration |
| llama.cpp | Local AI model support |
| Ollama | Local AI model execution |
| PyPDF | PDF medical report text extraction |
| Pillow | Image processing |

### 5. Authentication & Security

- JSON Web Token (JWT) authentication.
- Refresh-token rotation.
- bcrypt password hashing.
- Role-based access control.
- Protected API endpoints.
- Input validation using Pydantic.
- Secure file upload validation.

### 6. Testing Technologies

| Technology | Purpose |
|---|---|
| Pytest | Backend testing |
| Vitest | Frontend testing |
| React Testing Library | React component testing |
| Testing Library User Event | User interaction testing |
| HTTPX | API testing |

### 7. Deployment & Development Tools

| Tool | Purpose |
|---|---|
| Git | Version control |
| GitHub | Source code repository |
| Vercel | Frontend deployment |
| Render | Backend and PostgreSQL hosting |
| Swagger UI | API documentation and testing |

---

## Portals & Access Architecture

HealthAssist AI is built strictly around **two authenticated portals** alongside the **public website**:

1. **Public Website** — Home (`/`), About, 12 Features, 10-step How It Works, Hospital Directory (`/hospitals`, `/hospitals/:id`), Verified Doctor Directory (`/doctors`, `/doctors/:id`), Treatment & Precautions Library (`/treatments`), Contact form (`/api/contact`), Login (`/login`), Patient Registration (`/register`), Forgot/Reset Password (`/forgot-password`, `/reset-password`), and invite-token Doctor Onboarding (`/doctor-onboarding`).
2. **Patient Portal** (`/dashboard`, `/appointments`, `/symptoms`, `/chat`, `/reports`, `/insights`, `/history`, `/notifications`, `/profile`) — Health overview, hospital/doctor appointment booking & management, symptom analysis, AI healthcare chatbot, medical report upload & educational lab extraction, analytics, timeline, and profile.

There is **no Admin Panel or Admin UI**; hospital maintenance and doctor invite generation are exposed exclusively via key-protected backend endpoints (`X-Maintenance-Key` / `X-Onboarding-Key`).

---

## Project Structure

```text
aihealth/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── context/
│   │   ├── hooks/
│   │   ├── layouts/
│   │   ├── pages/
│   │   ├── routes/
│   │   ├── services/
│   │   ├── styles/
│   │   └── tests/
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── database/
│   │   ├── middleware/
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   └── utils/
│   ├── alembic/
│   ├── storage/reports/
│   ├── tests/
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

See [doc/SETUP.md](./doc/SETUP.md) for PostgreSQL 18 database setup, Alembic migrations, optional SMTP / operational keys, local AI setup (`llama.cpp` or `Ollama`), and startup/test commands.

## Deployment

- **Frontend:** [Vercel Deployment](https://frontend-seven-jet-60.vercel.app/)
- **Backend:** [Render Deployment](https://healthassist-ai-1xo7.onrender.com/)
- **API Documentation:** [Swagger UI](https://healthassist-ai-1xo7.onrender.com/docs)
