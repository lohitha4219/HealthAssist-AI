# HealthAssist AI — REST API Reference

Base prefix: `/api`
Authentication: Bearer JWT access token (`Authorization: Bearer <token>`) on protected routes; operational key headers (`X-Onboarding-Key` / `X-Maintenance-Key`) on backend maintenance endpoints. Role-restricted routes return HTTP `403` when accessed by the wrong role.

---

## System & Public Overview (`/api/health`, `/api/public`, `/api/contact`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/health` | Public | API health status & environment |
| `GET` | `/api/public/overview` | Public | Real DB-backed landing stats, featured hospitals & verified doctors, treatment categories, optional support contact fields |
| `POST` | `/api/contact` | Public | Persist contact enquiry to `contact_enquiries` |

## Authentication & Doctor Onboarding (`/api/auth`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | Public | Create a `patient` account (always `patient` role) and issue access + refresh tokens |
| `POST` | `/api/auth/login` | Public | Authenticate patient or doctor with email & password |
| `GET` | `/api/auth/me` | Bearer | Retrieve authenticated user summary & verification metadata |
| `POST` | `/api/auth/refresh` | Public | Rotate refresh token and issue new token pair |
| `POST` | `/api/auth/logout` | Bearer | Revoke refresh token(s) |
| `POST` | `/api/auth/forgot-password` | Public | Generate single-use password reset token; sends email only if SMTP is configured (`email_sent` reflects delivery) |
| `POST` | `/api/auth/reset-password` | Public | Reset password using single-use token |
| `POST` | `/api/auth/doctor-invite` | `X-Onboarding-Key` | Generate single-use doctor onboarding invitation linked to a verified hospital |
| `POST` | `/api/auth/doctor-register` | Invite Token | Redeem single-use invite token to register a verified `doctor` account & profile |

## Hospitals Directory & Maintenance (`/api/hospitals`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/hospitals` | Public | Search/filter hospitals (`search`, `district`, `city`, `specialization`, `treatment`, `facility`, `emergency_only`, `verified_only`) |
| `GET` | `/api/hospitals/filters` | Public | Distinct districts, cities, specializations, and facilities for directory filters |
| `GET` | `/api/hospitals/{hospital_id}` | Public | Full hospital profile with departments, facilities, treatments, and verified doctors |
| `POST` | `/api/hospitals/maintain` | `X-Maintenance-Key` | Backend maintenance endpoint to create hospital records (no Admin UI) |
| `PATCH` | `/api/hospitals/maintain/{hospital_id}` | `X-Maintenance-Key` | Backend maintenance endpoint to update hospital details, departments, facilities, or treatments |

## Doctors & Slots (`/api/doctors`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/doctors` | Public | Search/filter doctors (`search`, `specialization`, `hospital_id`, `district`, `verified_only`) |
| `GET` | `/api/doctors/{doctor_id}` | Public | Doctor detail with hospital, bio, fee, experience, and weekly availability |
| `GET` | `/api/doctors/{doctor_id}/slots` | Public | Compute open time slots for a target date respecting doctor schedule, leaves, and booked slots |

## Treatments & Precautions (`/api/treatments`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/treatments` | Public | Educational treatment library with category & search filters |
| `GET` | `/api/treatments/{slug}` | Public | Detailed treatment information, precautions, and linked verified hospitals |

## Patient Appointments (`/api/appointments`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/appointments` | Patient Bearer | Book an appointment slot (protected against past dates, leaves, and double booking) |
| `GET` | `/api/appointments/my` | Patient Bearer | List patient's appointments with doctor, hospital, status, and shared consultation notes |
| `PATCH` | `/api/appointments/{appointment_id}/cancel` | Patient Bearer | Cancel patient's own pending/confirmed/rescheduled appointment |
| `PATCH` | `/api/appointments/{appointment_id}/reschedule` | Patient Bearer | Move appointment to a new available date/time slot |

## Doctor Portal (`/api/doctor`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/doctor/dashboard` | Doctor Bearer | Today's queue, upcoming schedule, status counts, and unverified/verified status |
| `GET` | `/api/doctor/appointments` | Doctor Bearer | List doctor's patient appointments (`status`, `date_filter`) |
| `PATCH` | `/api/doctor/appointments/{appointment_id}/status` | Verified Doctor Bearer | Confirm, reschedule, cancel, or complete an appointment |
| `GET` | `/api/doctor/appointments/{appointment_id}/reports` | Verified Doctor Bearer | Review medical reports attached/shared for a specific appointment |
| `POST` | `/api/doctor/appointments/{appointment_id}/notes` | Verified Doctor Bearer | Create consultation note (optional patient visibility) & notify patient |
| `GET` | `/api/doctor/availability` | Doctor Bearer | Retrieve recurring weekly schedule slots |
| `PUT` | `/api/doctor/availability` | Verified Doctor Bearer | Replace weekly schedule slots across weekdays |
| `GET` | `/api/doctor/leaves` | Doctor Bearer | List scheduled doctor leaves / blocked dates |
| `POST` | `/api/doctor/leaves` | Verified Doctor Bearer | Block a future leave date |
| `DELETE` | `/api/doctor/leaves/{leave_id}` | Verified Doctor Bearer | Remove a scheduled leave entry |
| `GET` | `/api/doctor/profile` | Doctor Bearer | Get doctor professional profile |
| `PATCH` | `/api/doctor/profile` | Doctor Bearer | Update doctor qualifications, bio, fee, consultation mode, or clinic hours |

## Notifications (`/api/notifications`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/notifications` | Bearer | Paginated user notifications and unread count |
| `PATCH` | `/api/notifications/{notification_id}/read` | Bearer | Mark single owned notification read |
| `POST` | `/api/notifications/read-all` | Bearer | Mark all unread notifications read |

## Dashboard (`/api/dashboard`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/dashboard/summary` | Bearer | Real counts, recent assessments/reports/activities, local AI status, and notifications |
| `GET` | `/api/dashboard/activity` | Bearer | Recent chronological health activity items |

## Symptom Analysis (`/api/symptoms`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/symptoms/catalog` | Bearer | Searchable symptom catalog with red-flag markers |
| `POST` | `/api/symptoms/assess` | Bearer | Evaluate symptoms educationally and save record |
| `GET` | `/api/symptoms/history` | Bearer | Paginated user symptom assessments |
| `GET` | `/api/symptoms/{assessment_id}` | Bearer | Get single owned assessment |
| `DELETE` | `/api/symptoms/{assessment_id}` | Bearer | Delete owned assessment |

## AI Chat (`/api/chat`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/chat/health` | Bearer | AI engine availability (`llama.cpp` / `Ollama` / `openai_compatible`), active model, and honest setup status |
| `POST` | `/api/chat/conversations` | Bearer | Create a new conversation |
| `GET` | `/api/chat/conversations` | Bearer | List user conversations ordered by most recently updated |
| `GET` | `/api/chat/conversations/{conversation_id}` | Bearer | Get owned conversation and ordered message history |
| `PATCH` | `/api/chat/conversations/{conversation_id}` | Bearer | Rename owned conversation |
| `DELETE` | `/api/chat/conversations/{conversation_id}` | Bearer | Delete owned conversation and messages |
| `GET` | `/api/chat/conversations/{conversation_id}/messages` | Bearer | Retrieve messages for owned conversation |
| `POST` | `/api/chat/conversations/{conversation_id}/messages` | Bearer | Send message, retain bounded context, persist user & AI reply |
| `POST` | `/api/chat/conversations/{conversation_id}/stream` | Bearer | Stream AI assistant response via Server-Sent Events (SSE) and persist reply |

## Medical Reports (`/api/reports`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/api/reports/upload` | Bearer | Upload validated PDF/PNG/JPG/JPEG/WEBP (`<= 10 MB`), extract PDF text, parse conservative educational lab values |
| `GET` | `/api/reports` | Bearer | Paginated, searchable, category-filterable report list |
| `GET` | `/api/reports/{report_id}` | Bearer | Inspect owned report metadata, extracted text, `ai_summary`, and structured `analysis` |
| `POST` | `/api/reports/{report_id}/analyze` | Bearer | Re-run conservative educational parsing and/or local AI summary on existing owned report |
| `GET` | `/api/reports/{report_id}/download` | Bearer | Authenticated download of owned report file |
| `DELETE` | `/api/reports/{report_id}` | Bearer | Delete owned report record and stored file |

## Health Insights & History (`/api/insights`, `/api/history`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/insights/summary` | Bearer | Aggregated counts, severity/urgency/category breakdowns, top symptoms |
| `GET` | `/api/insights/trends` | Bearer | Daily chronological counts across assessments, reports, and chats |
| `GET` | `/api/history` | Bearer | Unified chronological timeline (`record_type`, `search`, `start_date`, `end_date`, pagination) |
| `DELETE` | `/api/history/{record_type}/{record_id}` | Bearer | Delete owned `assessment`, `report`, or `activity` entry |

## Profile (`/api/profile`)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/profile` | Bearer | Retrieve full user health profile |
| `PATCH` | `/api/profile` | Bearer | Update personal details, health fields, and email |
| `POST` | `/api/profile/change-password` | Bearer | Verify current password and store new bcrypt hash |
