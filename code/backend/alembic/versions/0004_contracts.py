"""Add contract snapshots and immutable status history.

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-28
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

contract_status = postgresql.ENUM(
    "OPEN",
    "ACCEPTED",
    "DELIVERED",
    "REVISION",
    "DISPUTED",
    "RELEASED",
    "REFUNDED",
    "SPLIT",
    name="contract_status",
    create_type=False,
)


def upgrade() -> None:
    contract_status.create(op.get_bind(), checkfirst=True)
    op.create_unique_constraint(
        "uq_applications_contract_ref", "applications", ["id", "gig_id", "applicant_id"]
    )

    op.create_table(
        "contracts",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("gig_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("application_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("worker_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("gig_title", sa.Text(), nullable=False),
        sa.Column("gig_description", sa.Text(), nullable=False),
        sa.Column(
            "gig_category",
            postgresql.ENUM(name="gig_category", create_type=False),
            nullable=False,
        ),
        sa.Column("amount_paise", sa.BigInteger(), nullable=False),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_days", sa.Integer(), nullable=True),
        sa.Column("status", contract_status, nullable=False),
        sa.Column("confirmation_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revisions_used", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["gig_id"], ["gigs.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["application_id", "gig_id", "worker_id"],
            ["applications.id", "applications.gig_id", "applications.applicant_id"],
            name="fk_contracts_selected_application",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["worker_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("gig_id", name="uq_contracts_gig_id"),
        sa.UniqueConstraint("application_id", name="uq_contracts_application_id"),
        sa.CheckConstraint("amount_paise > 0", name="ck_contracts_amount_positive"),
        sa.CheckConstraint("revisions_used >= 0", name="ck_contracts_revisions_nonnegative"),
        sa.CheckConstraint(
            "duration_days IS NULL OR duration_days BETWEEN 1 AND 365",
            name="ck_contracts_duration_range",
        ),
    )
    op.create_index(
        "ix_contracts_worker_created_at",
        "contracts",
        ["worker_id", sa.text("created_at DESC")],
    )

    op.create_table(
        "contract_status_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("contract_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("previous_status", contract_status, nullable=False),
        sa.Column("new_status", contract_status, nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(["contract_id"], ["contracts.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_contract_history_contract_created",
        "contract_status_history",
        ["contract_id", "created_at"],
    )

    op.execute(
        """
        CREATE FUNCTION reject_contract_history_mutation() RETURNS trigger
        LANGUAGE plpgsql AS $$
        BEGIN
            RAISE EXCEPTION 'contract status history is append-only'
                USING ERRCODE = 'integrity_constraint_violation';
        END;
        $$
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_contract_history_immutable
        BEFORE UPDATE OR DELETE ON contract_status_history
        FOR EACH ROW EXECUTE FUNCTION reject_contract_history_mutation()
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_contract_history_no_truncate
        BEFORE TRUNCATE ON contract_status_history
        FOR EACH STATEMENT EXECUTE FUNCTION reject_contract_history_mutation()
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_contract_history_no_truncate ON contract_status_history")
    op.execute("DROP TRIGGER IF EXISTS trg_contract_history_immutable ON contract_status_history")
    op.execute("DROP FUNCTION IF EXISTS reject_contract_history_mutation()")
    op.drop_index("ix_contract_history_contract_created", table_name="contract_status_history")
    op.drop_table("contract_status_history")
    op.drop_index("ix_contracts_worker_created_at", table_name="contracts")
    op.drop_table("contracts")
    op.drop_constraint("uq_applications_contract_ref", "applications", type_="unique")
    contract_status.drop(op.get_bind(), checkfirst=True)
