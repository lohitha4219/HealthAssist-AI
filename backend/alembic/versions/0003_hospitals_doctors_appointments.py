"""Hospitals, doctors, appointments, notifications, education, and contact tables

Revision ID: 0003
Revises: 0002
Create Date: 2026-11-11 23:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names())

    if "hospitals" not in existing:
        op.create_table(
            "hospitals",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=200), nullable=False),
            sa.Column("slug", sa.String(length=220), nullable=False),
            sa.Column("hospital_type", sa.String(length=80), nullable=False),
            sa.Column("address", sa.Text(), nullable=False),
            sa.Column("city", sa.String(length=100), nullable=False),
            sa.Column("district", sa.String(length=100), nullable=False),
            sa.Column("state", sa.String(length=80), server_default="Andhra Pradesh", nullable=False),
            sa.Column("pincode", sa.String(length=16), nullable=True),
            sa.Column("phone", sa.String(length=120), nullable=True),
            sa.Column("emergency_phone", sa.String(length=120), nullable=True),
            sa.Column("email", sa.String(length=150), nullable=True),
            sa.Column("website", sa.String(length=255), nullable=True),
            sa.Column("image_url", sa.String(length=500), nullable=True),
            sa.Column("operating_hours", sa.String(length=200), nullable=True),
            sa.Column("emergency_info", sa.Text(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("verification_status", sa.String(length=30), server_default="verified", nullable=False),
            sa.Column("source_reference", sa.String(length=255), nullable=True),
            sa.Column("is_published", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_hospitals_city", "hospitals", ["city"])
        op.create_index("ix_hospitals_district", "hospitals", ["district"])
        op.create_index("ix_hospitals_name", "hospitals", ["name"])
        op.create_index("ix_hospitals_slug", "hospitals", ["slug"], unique=True)

    if "hospital_departments" not in existing:
        op.create_table(
            "hospital_departments",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("hospital_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_verified", sa.Boolean(), server_default="true", nullable=False),
            sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_hospital_departments_hospital_id", "hospital_departments", ["hospital_id"])

    if "hospital_facilities" not in existing:
        op.create_table(
            "hospital_facilities",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("hospital_id", sa.Integer(), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("details", sa.Text(), nullable=True),
            sa.Column("is_verified", sa.Boolean(), server_default="true", nullable=False),
            sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_hospital_facilities_hospital_id", "hospital_facilities", ["hospital_id"])

    if "hospital_treatments" not in existing:
        op.create_table(
            "hospital_treatments",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("hospital_id", sa.Integer(), nullable=False),
            sa.Column("department_id", sa.Integer(), nullable=True),
            sa.Column("name", sa.String(length=150), nullable=False),
            sa.Column("specialty", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("is_verified", sa.Boolean(), server_default="true", nullable=False),
            sa.ForeignKeyConstraint(["department_id"], ["hospital_departments.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_hospital_treatments_hospital_id", "hospital_treatments", ["hospital_id"])
        op.create_index("ix_hospital_treatments_specialty", "hospital_treatments", ["specialty"])

    if "doctor_profiles" not in existing:
        op.create_table(
            "doctor_profiles",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("hospital_id", sa.Integer(), nullable=True),
            sa.Column("department_id", sa.Integer(), nullable=True),
            sa.Column("qualification", sa.String(length=160), nullable=False),
            sa.Column("specialization", sa.String(length=120), nullable=False),
            sa.Column("experience_years", sa.Integer(), nullable=False),
            sa.Column("license_number", sa.String(length=100), nullable=True),
            sa.Column("languages", sa.JSON(), nullable=False),
            sa.Column("consultation_fee", sa.Float(), nullable=True),
            sa.Column("bio", sa.Text(), nullable=True),
            sa.Column("profile_image_url", sa.String(length=500), nullable=True),
            sa.Column("verification_status", sa.String(length=30), server_default="pending", nullable=False),
            sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["department_id"], ["hospital_departments.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("license_number"),
            sa.UniqueConstraint("user_id"),
        )
        op.create_index("ix_doctor_profiles_hospital_id", "doctor_profiles", ["hospital_id"])
        op.create_index("ix_doctor_profiles_specialization", "doctor_profiles", ["specialization"])
        op.create_index("ix_doctor_profiles_verification_status", "doctor_profiles", ["verification_status"])

    if "doctor_invitations" not in existing:
        op.create_table(
            "doctor_invitations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("token_hash", sa.String(length=128), nullable=False),
            sa.Column("hospital_id", sa.Integer(), nullable=True),
            sa.Column("department_id", sa.Integer(), nullable=True),
            sa.Column("specialization", sa.String(length=120), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["department_id"], ["hospital_departments.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="SET NULL"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_doctor_invitations_email", "doctor_invitations", ["email"])
        op.create_index("ix_doctor_invitations_token_hash", "doctor_invitations", ["token_hash"], unique=True)

    if "doctor_availability" not in existing:
        op.create_table(
            "doctor_availability",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("doctor_id", sa.Integer(), nullable=False),
            sa.Column("day_of_week", sa.Integer(), nullable=False),
            sa.Column("start_time", sa.Time(), nullable=False),
            sa.Column("end_time", sa.Time(), nullable=False),
            sa.Column("slot_duration_minutes", sa.Integer(), nullable=False),
            sa.Column("break_start", sa.Time(), nullable=True),
            sa.Column("break_end", sa.Time(), nullable=True),
            sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
            sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_doctor_availability_doctor_id", "doctor_availability", ["doctor_id"])

    if "doctor_leaves" not in existing:
        op.create_table(
            "doctor_leaves",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("doctor_id", sa.Integer(), nullable=False),
            sa.Column("leave_date", sa.Date(), nullable=False),
            sa.Column("reason", sa.String(length=255), nullable=True),
            sa.Column("is_holiday", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_doctor_leaves_doctor_id", "doctor_leaves", ["doctor_id"])
        op.create_index("ix_doctor_leaves_leave_date", "doctor_leaves", ["leave_date"])

    if "appointments" not in existing:
        op.create_table(
            "appointments",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("patient_id", sa.Integer(), nullable=False),
            sa.Column("doctor_id", sa.Integer(), nullable=False),
            sa.Column("hospital_id", sa.Integer(), nullable=False),
            sa.Column("department_id", sa.Integer(), nullable=True),
            sa.Column("appointment_date", sa.Date(), nullable=False),
            sa.Column("appointment_time", sa.Time(), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=30), server_default="pending", nullable=False),
            sa.Column("cancellation_reason", sa.Text(), nullable=True),
            sa.Column("rescheduled_from_date", sa.Date(), nullable=True),
            sa.Column("rescheduled_from_time", sa.Time(), nullable=True),
            sa.Column("share_reports", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["department_id"], ["hospital_departments.id"], ondelete="SET NULL"),
            sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["hospital_id"], ["hospitals.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["patient_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_appointments_appointment_date", "appointments", ["appointment_date"])
        op.create_index("ix_appointments_doctor_id", "appointments", ["doctor_id"])
        op.create_index("ix_appointments_hospital_id", "appointments", ["hospital_id"])
        op.create_index("ix_appointments_patient_id", "appointments", ["patient_id"])
        op.create_index("ix_appointments_status", "appointments", ["status"])
        if bind.dialect.name == "postgresql":
            op.execute(
                """
                CREATE UNIQUE INDEX uq_doctor_active_appointment_slot
                ON appointments (doctor_id, appointment_date, appointment_time)
                WHERE status IN ('pending', 'confirmed', 'rescheduled')
                """
            )

    if "consultation_notes" not in existing:
        op.create_table(
            "consultation_notes",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("appointment_id", sa.Integer(), nullable=False),
            sa.Column("doctor_id", sa.Integer(), nullable=False),
            sa.Column("patient_id", sa.Integer(), nullable=False),
            sa.Column("observations", sa.Text(), nullable=False),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("follow_up_recommendations", sa.Text(), nullable=True),
            sa.Column("treatment_info", sa.Text(), nullable=True),
            sa.Column("is_shareable", sa.Boolean(), server_default="true", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["appointment_id"], ["appointments.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["doctor_id"], ["doctor_profiles.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["patient_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_consultation_notes_appointment_id", "consultation_notes", ["appointment_id"])

    if "notifications" not in existing:
        op.create_table(
            "notifications",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("notification_type", sa.String(length=50), server_default="appointment", nullable=False),
            sa.Column("is_read", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("related_route", sa.String(length=200), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
        op.create_index("ix_notifications_user_id", "notifications", ["user_id"])

    if "treatment_education" not in existing:
        op.create_table(
            "treatment_education",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("specialty", sa.String(length=120), nullable=False),
            sa.Column("slug", sa.String(length=140), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("common_reasons", sa.JSON(), nullable=False),
            sa.Column("preparation", sa.JSON(), nullable=False),
            sa.Column("precautions", sa.JSON(), nullable=False),
            sa.Column("aftercare", sa.JSON(), nullable=False),
            sa.Column("when_to_consult", sa.JSON(), nullable=False),
            sa.Column("emergency_signs", sa.JSON(), nullable=False),
            sa.Column("sources", sa.JSON(), nullable=False),
            sa.Column("reviewed_by", sa.String(length=160), nullable=True),
            sa.Column("last_reviewed_date", sa.Date(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("specialty"),
        )
        op.create_index("ix_treatment_education_slug", "treatment_education", ["slug"], unique=True)

    if "contact_enquiries" not in existing:
        op.create_table(
            "contact_enquiries",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(length=150), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("subject", sa.String(length=200), nullable=False),
            sa.Column("message", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=30), server_default="received", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    for tbl in [
        "contact_enquiries",
        "treatment_education",
        "notifications",
        "consultation_notes",
        "appointments",
        "doctor_leaves",
        "doctor_availability",
        "doctor_invitations",
        "doctor_profiles",
        "hospital_treatments",
        "hospital_facilities",
        "hospital_departments",
        "hospitals",
    ]:
        op.drop_table(tbl)
