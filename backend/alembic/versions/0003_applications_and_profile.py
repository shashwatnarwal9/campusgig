"""Gig posting, applications and profiles.

Adds the applications table, gig duration, and the profile columns backing the
avatar / resume / bio on the profile page.

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-08
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("bio", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("avatar_path", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("resume_path", sa.Text(), nullable=True))

    op.add_column("gigs", sa.Column("duration_days", sa.Integer(), nullable=True))
    op.create_check_constraint(
        "ck_gigs_duration_range", "gigs", "duration_days IS NULL OR duration_days BETWEEN 1 AND 365"
    )

    op.create_table(
        "applications",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("gig_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("applicant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column(
            "status",
            sa.Enum("APPLIED", "ACCEPTED", "REJECTED", "COMPLETED", name="application_status"),
            server_default="APPLIED",
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["gig_id"], ["gigs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["applicant_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        # One application per person per gig.
        sa.UniqueConstraint("gig_id", "applicant_id", name="uq_applications_gig_applicant"),
    )
    op.create_index("ix_applications_gig_id", "applications", ["gig_id"])
    op.create_index("ix_applications_applicant_id", "applications", ["applicant_id"])
    op.create_index("ix_applications_applicant_status", "applications", ["applicant_id", "status"])


def downgrade() -> None:
    op.drop_table("applications")
    op.execute("DROP TYPE IF EXISTS application_status")
    op.drop_constraint("ck_gigs_duration_range", "gigs", type_="check")
    op.drop_column("gigs", "duration_days")
    op.drop_column("users", "resume_path")
    op.drop_column("users", "avatar_path")
    op.drop_column("users", "bio")
