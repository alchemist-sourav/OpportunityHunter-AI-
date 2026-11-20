"""Phase 7: application tracker.

Revision ID: 0004_application_tracker
Revises: 0003_opportunities
Create Date: 2026-11-19
"""
from alembic import op
import sqlalchemy as sa


revision = "0004_application_tracker"
down_revision = "0003_opportunities"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_applications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="interested"),
        sa.Column("applied_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["user_profiles.user_id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "opportunity_id", name="uq_user_application_unique"),
        sa.CheckConstraint(
            "status IN ('interested', 'saved', 'applied', 'assessment', 'interview', 'offer', 'rejected', 'withdrawn')",
            name="ck_user_applications_status",
        ),
    )
    op.create_index("ix_user_applications_user_id", "user_applications", ["user_id"])
    op.create_index("ix_user_applications_opportunity_id", "user_applications", ["opportunity_id"])
    op.create_index("ix_user_applications_user_status", "user_applications", ["user_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_user_applications_user_status", table_name="user_applications")
    op.drop_index("ix_user_applications_opportunity_id", table_name="user_applications")
    op.drop_index("ix_user_applications_user_id", table_name="user_applications")
    op.drop_table("user_applications")
