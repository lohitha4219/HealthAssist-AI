"""Add verified doctor directory fields and nullable experience_years

Revision ID: 0004
Revises: 0003
Create Date: 2026-11-12 20:55:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if "doctor_profiles" not in insp.get_table_names():
        return

    existing_cols = {
        c["name"] for c in insp.get_columns("doctor_profiles")
    }

    with op.batch_alter_table("doctor_profiles") as batch_op:
        if "experience_years" in existing_cols:
            batch_op.alter_column(
                "experience_years",
                existing_type=sa.Integer(),
                nullable=True,
            )

        if "designation" not in existing_cols:
            batch_op.add_column(
                sa.Column("designation", sa.String(length=140), nullable=True)
            )

        if "published_timings" not in existing_cols:
            batch_op.add_column(
                sa.Column("published_timings", sa.String(length=255), nullable=True)
            )

        if "official_source_url" not in existing_cols:
            batch_op.add_column(
                sa.Column("official_source_url", sa.String(length=500), nullable=True)
            )

        if "listing_source" not in existing_cols:
            batch_op.add_column(
                sa.Column(
                    "listing_source",
                    sa.String(length=40),
                    server_default="portal",
                    nullable=False,
                )
            )


def downgrade() -> None:
    with op.batch_alter_table("doctor_profiles") as batch_op:
        batch_op.drop_column("listing_source")
        batch_op.drop_column("official_source_url")
        batch_op.drop_column("published_timings")
        batch_op.drop_column("designation")
