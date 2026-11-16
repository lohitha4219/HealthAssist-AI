# HealthAssist AI — PostgreSQL Database Schema

Target database: `healthcare_assistant` (PostgreSQL 18)
ORM: SQLAlchemy 2.x (`backend/app/models/`)
Migrations: Alembic (`0001_initial_schema` -> `0002_user_profile_columns` -> `0003_hospitals_doctors_appointments`)

> All active SQLAlchemy ORM tables use **integer** primary and foreign keys (`INTEGER`, auto-increment sequences in PostgreSQL) aligned directly with the live `healthcare_assistant` schema.

---

## Core Authentication & Personal Health Tables

1. **`users`**
   - Primary key: `id` (`Integer`)
   - Unique indexed column: `email`
   - Security & Role: `hashed_password` (salted bcrypt), `role` (`patient` | `doctor`), `is_active`
   - Profile attributes: `full_name`, `date_of_birth`, `gender`, `phone`, `blood_group`, `height_cm`, `weight_kg`, `emergency_contact_name`, `emergency_contact_phone`, `allergies`, `chronic_conditions`, `bio`
   - Timestamps: `created_at`, `updated_at`

2. **`refresh_tokens`** — `user_id -> users.id` (`ON DELETE CASCADE`), `token_hash`, `expires_at`, `revoked`, `created_at`
3. **`password_reset_tokens`** — `user_id -> users.id` (`ON DELETE CASCADE`), `token_hash`, `expires_at`, `used`, `created_at`
4. **`chat_conversations`** — `user_id -> users.id` (`ON DELETE CASCADE`), `title`, `model_name`, `created_at`, `updated_at`
5. **`chat_messages`** — `conversation_id -> chat_conversations.id` (`ON DELETE CASCADE`), `role`, `content`, `provider`, `model_name`, `created_at`
6. **`symptom_assessments`** — `user_id -> users.id` (`ON DELETE CASCADE`), `symptoms` (`JSON`), `duration`, `severity`, `additional_details`, `urgency_level`, `educational_summary`, `possible_causes` (`JSON`), `care_guidance` (`JSON`), `emergency_warning`, `ai_enhanced`, `created_at`
7. **`medical_reports`** — `user_id -> users.id` (`ON DELETE CASCADE`), `original_filename`, `stored_filename` (unique), `storage_path`, `content_type`, `file_size`, `category`, `notes`, `processing_status`, `extracted_text`, `ai_summary`, `analysis` (`JSON`), `analyzed_at`, `page_count`, `image_width`, `image_height`, `created_at`
8. **`health_activities`** — `user_id -> users.id` (`ON DELETE CASCADE`), `activity_type`, `title`, `description`, `reference_id`, `reference_type`, `created_at`

---

## Hospitals, Doctors, Appointments & Education Tables (`0003`)

9. **`hospitals`** — `name`, `slug` (unique), `registration_number`, `hospital_type`, `category`, `address`, `city`, `district`, `state`, `pincode`, `phone`, `emergency_phone`, `email`, `website`, `visiting_hours`, `emergency_24x7`, `bed_count`, `about`, `accreditations`, `is_verified`, `created_at`, `updated_at`
10. **`hospital_departments`** — `hospital_id -> hospitals.id` (`ON DELETE CASCADE`), `name`, `description`, `head_doctor_name`
11. **`hospital_facilities`** — `hospital_id -> hospitals.id` (`ON DELETE CASCADE`), `name`, `category`, `is_available`, `details`
12. **`hospital_treatments`** — `hospital_id -> hospitals.id` (`ON DELETE CASCADE`), `name`, `category`, `department_name`, `description`, `precautions`, `estimated_duration`, `consultation_fee`, `is_available`
13. **`doctor_profiles`** — `user_id -> users.id` (`ON DELETE CASCADE`), `hospital_id -> hospitals.id` (`ON DELETE SET NULL`), `specialization`, `qualification`, `registration_number`, `experience_years`, `bio`, `languages`, `consultation_fee`, `consultation_mode`, `is_verified`, `is_available`, `clinic_hours`, `created_at`, `updated_at`
14. **`doctor_availability`** — `doctor_id -> doctor_profiles.id` (`ON DELETE CASCADE`), `day_of_week`, `start_time`, `end_time`, `slot_duration_minutes`, `is_active`
15. **`doctor_leaves`** — `doctor_id -> doctor_profiles.id` (`ON DELETE CASCADE`), `leave_date`, `reason`, `created_at`
16. **`doctor_invitations`** — `token_hash` (unique), `email`, `full_name`, `hospital_id -> hospitals.id` (`ON DELETE SET NULL`), `specialization`, `registration_number`, `expires_at`, `used`, `used_at`, `created_at`
17. **`appointments`** — `appointment_code` (unique), `patient_id -> users.id` (`ON DELETE CASCADE`), `doctor_id -> doctor_profiles.id` (`ON DELETE CASCADE`), `hospital_id -> hospitals.id` (`ON DELETE SET NULL`), `appointment_date`, `appointment_time`, `consultation_type`, `status`, `reason`, `patient_notes`, `doctor_notes`, `attached_report_id -> medical_reports.id` (`ON DELETE SET NULL`), `created_at`, `updated_at`
    - **Concurrency Protection:** PostgreSQL partial unique index `uq_doctor_active_appointment_slot` on `(doctor_id, appointment_date, appointment_time) WHERE status IN ('pending', 'confirmed', 'rescheduled')` guarantees two concurrent requests cannot double-book the same doctor slot.
18. **`consultation_notes`** — `appointment_id -> appointments.id` (`ON DELETE CASCADE`), `doctor_id -> doctor_profiles.id` (`ON DELETE CASCADE`), `patient_id -> users.id` (`ON DELETE CASCADE`), `summary`, `recommendations`, `follow_up_date`, `visible_to_patient`, `created_at`
19. **`notifications`** — `user_id -> users.id` (`ON DELETE CASCADE`), `title`, `message`, `notification_type`, `reference_type`, `reference_id`, `is_read`, `created_at`
20. **`treatment_education`** — `slug` (unique), `title`, `category`, `overview`, `common_conditions`, `procedure_steps`, `precautions_before`, `precautions_after`, `when_to_seek_care`, `created_at`
21. **`contact_enquiries`** — `name`, `email`, `phone`, `subject`, `message`, `status`, `created_at`

*(Existing legacy tables in `healthcare_assistant` such as `health_insights`, `health_measurements`, `symptom_analyses`, `symptom_entries`, and `user_profiles` are left untouched on disk for data preservation alongside `alembic_version`.)*

## Running Migrations

```bash
cd backend
./venv/bin/alembic current
./venv/bin/alembic upgrade head
```
