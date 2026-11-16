"""Align auth, user profile, chat, report, and activity tables cleanly

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-11 14:25:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _get_columns(insp, table_name: str) -> set[str]:
    return {c["name"] for c in insp.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_tables = set(insp.get_table_names())

    # 1. Add missing columns to users without altering INTEGER PK or existing rows
    user_cols = _get_columns(insp, "users")
    user_additions = [
        ("role", sa.Column("role", sa.String(length=30), server_default="patient", nullable=False)),
        ("date_of_birth", sa.Column("date_of_birth", sa.Date(), nullable=True)),
        ("gender", sa.Column("gender", sa.String(length=40), nullable=True)),
        ("phone", sa.Column("phone", sa.String(length=30), nullable=True)),
        ("blood_group", sa.Column("blood_group", sa.String(length=10), nullable=True)),
        ("height_cm", sa.Column("height_cm", sa.Float(), nullable=True)),
        ("weight_kg", sa.Column("weight_kg", sa.Float(), nullable=True)),
        ("emergency_contact_name", sa.Column("emergency_contact_name", sa.String(length=120), nullable=True)),
        ("emergency_contact_phone", sa.Column("emergency_contact_phone", sa.String(length=30), nullable=True)),
        ("allergies", sa.Column("allergies", sa.Text(), nullable=True)),
        ("chronic_conditions", sa.Column("chronic_conditions", sa.Text(), nullable=True)),
        ("bio", sa.Column("bio", sa.Text(), nullable=True)),
    ]
    for col_name, col_def in user_additions:
        if col_name not in user_cols:
            op.add_column("users", col_def)

    # Backfill non-null profile attributes from legacy user_profiles if present
    if "user_profiles" in existing_tables and bind.dialect.name == "postgresql":
        op.execute(
            """
            UPDATE users AS u
            SET
                date_of_birth = COALESCE(u.date_of_birth, p.date_of_birth),
                gender = COALESCE(u.gender, p.gender),
                phone = COALESCE(u.phone, p.phone),
                height_cm = COALESCE(u.height_cm, p.height_cm::double precision),
                weight_kg = COALESCE(u.weight_kg, p.weight_kg::double precision),
                chronic_conditions = COALESCE(u.chronic_conditions, p.medical_history)
            FROM user_profiles AS p
            WHERE p.user_id = u.id
            """
        )

    # 2. Align chat_conversations & chat_messages
    if "chat_conversations" in existing_tables:
        conv_cols = _get_columns(insp, "chat_conversations")
        if "model_name" not in conv_cols:
            op.add_column("chat_conversations", sa.Column("model_name", sa.String(length=120), nullable=True))

    if "chat_messages" in existing_tables:
        msg_cols = _get_columns(insp, "chat_messages")
        if "provider" not in msg_cols:
            op.add_column("chat_messages", sa.Column("provider", sa.String(length=40), nullable=True))
        if "model_name" not in msg_cols:
            op.add_column("chat_messages", sa.Column("model_name", sa.String(length=120), nullable=True))
        if bind.dialect.name == "postgresql" and "is_emergency" in msg_cols:
            op.execute("ALTER TABLE chat_messages ALTER COLUMN is_emergency SET DEFAULT false")

    # 3. Align medical_reports without touching existing rows or uploaded_at/status
    if "medical_reports" in existing_tables:
        rep_cols = _get_columns(insp, "medical_reports")
        rep_additions = [
            ("storage_path", sa.Column("storage_path", sa.String(length=500), nullable=True)),
            ("category", sa.Column("category", sa.String(length=80), server_default="General Report", nullable=False)),
            ("notes", sa.Column("notes", sa.Text(), nullable=True)),
            ("processing_status", sa.Column("processing_status", sa.String(length=40), server_default="uploaded", nullable=False)),
            ("page_count", sa.Column("page_count", sa.Integer(), nullable=True)),
            ("image_width", sa.Column("image_width", sa.Integer(), nullable=True)),
            ("image_height", sa.Column("image_height", sa.Integer(), nullable=True)),
            ("created_at", sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)),
        ]
        for col_name, col_def in rep_additions:
            if col_name not in rep_cols:
                op.add_column("medical_reports", col_def)
        if bind.dialect.name == "postgresql":
            op.execute(
                """
                UPDATE medical_reports
                SET
                    created_at = COALESCE(uploaded_at, created_at),
                    processing_status = COALESCE(status, processing_status, 'uploaded')
                """
            )

    # 4. Create password_reset_tokens if missing
    if "password_reset_tokens" not in existing_tables:
        op.create_table(
            "password_reset_tokens",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("token_hash", sa.String(length=128), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_password_reset_tokens_token_hash", "password_reset_tokens", ["token_hash"], unique=True)
        op.create_index("ix_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"], unique=False)

    # 5. Create symptom_assessments if missing
    if "symptom_assessments" not in existing_tables:
        op.create_table(
            "symptom_assessments",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("symptoms", sa.JSON(), nullable=False),
            sa.Column("duration", sa.String(length=80), nullable=False),
            sa.Column("severity", sa.String(length=20), nullable=False),
            sa.Column("additional_details", sa.Text(), nullable=True),
            sa.Column("urgency_level", sa.String(length=30), nullable=False),
            sa.Column("educational_summary", sa.Text(), nullable=False),
            sa.Column("possible_causes", sa.JSON(), nullable=False),
            sa.Column("care_guidance", sa.JSON(), nullable=False),
            sa.Column("emergency_warning", sa.Text(), nullable=True),
            sa.Column("ai_enhanced", sa.Boolean(), server_default="false", nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_symptom_assessments_created_at", "symptom_assessments", ["created_at"], unique=False)
        op.create_index("ix_symptom_assessments_user_id", "symptom_assessments", ["user_id"], unique=False)

    # 6. Create health_activities if missing
    if "health_activities" not in existing_tables:
        op.create_table(
            "health_activities",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("user_id", sa.Integer(), nullable=False),
            sa.Column("activity_type", sa.String(length=50), nullable=False),
            sa.Column("title", sa.String(length=200), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("reference_id", sa.String(length=64), nullable=True),
            sa.Column("reference_type", sa.String(length=50), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_health_activities_activity_type", "health_activities", ["activity_type"], unique=False)
        op.create_index("ix_health_activities_created_at", "health_activities", ["created_at"], unique=False)
        op.create_index("ix_health_activities_user_id", "health_activities", ["user_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    existing_tables = set(insp.get_table_names())

    if "health_activities" in existing_tables:
        op.drop_table("health_activities")
    if "symptom_assessments" in existing_tables:
        op.drop_table("symptom_assessments")
    if "password_reset_tokens" in existing_tables:
        op.drop_table("password_reset_tokens")

    if "medical_reports" in existing_tables:
        rep_cols = _get_columns(insp, "medical_reports")
        for col in ["created_at", "image_height", "image_width", "page_count", "processing_status", "notes", "category", "storage_path"]:
            if col in rep_cols:
                op.drop_column("medical_reports", col)

    if "chat_messages" in existing_tables:
        msg_cols = _get_columns(insp, "chat_messages")
        for col in ["model_name", "provider"]:
            if col in msg_cols:
                op.drop_column("chat_messages", col)

    if "chat_conversations" in existing_tables:
        conv_cols = _get_columns(insp, "chat_conversations")
        if "model_name" in conv_cols:
            op.drop_column("chat_conversations", "model_name")

    user_cols = _get_columns(insp, "users")
    for col in [
        "bio",
        "chronic_conditions",
        "allergies",
        "emergency_contact_phone",
        "emergency_contact_name",
        "weight_kg",
        "height_cm",
        "blood_group",
        "phone",
        "gender",
        "date_of_birth",
        "role",
    ]:
        if col in user_cols:
            op.drop_column("users", col)
