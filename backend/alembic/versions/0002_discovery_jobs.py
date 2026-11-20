"""Phase 3: discovery jobs.

Revision ID: 0002_discovery_jobs
Revises: 0001_phase2_users
Create Date: 2026-11-19
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_discovery_jobs"
down_revision = "0001_phase2_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "discovery_jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("keywords", sa.Text(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("locations", sa.JSON(), nullable=False),
        sa.Column("remote_preference", sa.String(length=32), nullable=False),
        sa.Column("experience_level", sa.String(length=32), nullable=True),
        sa.Column("max_results", sa.Integer(), nullable=False),
        sa.Column("source_domains", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("external_job_id", sa.String(length=64), nullable=True),
        sa.Column("cancel_requested", sa.Boolean(), nullable=False),
        sa.Column("total_pages", sa.Integer(), nullable=False),
        sa.Column("completed_pages", sa.Integer(), nullable=False),
        sa.Column("result_count", sa.Integer(), nullable=False),
        sa.Column("credits_used", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("results", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "category IN ('internship', 'fresher_job', 'full_time_job', 'freelance_project')",
            name="ck_discovery_jobs_category",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_discovery_jobs_status",
        ),
        sa.CheckConstraint(
            "remote_preference IN ('remote_only', 'hybrid', 'onsite_only', 'no_preference')",
            name="ck_discovery_jobs_remote_preference",
        ),
        sa.CheckConstraint(
            "experience_level IS NULL OR experience_level IN ('student', 'fresher', 'junior', 'experienced')",
            name="ck_discovery_jobs_experience_level",
        ),
    )
    op.create_index("ix_discovery_jobs_user_id", "discovery_jobs", ["user_id"])
    op.create_index("ix_discovery_jobs_status", "discovery_jobs", ["status"])
    op.create_index("ix_discovery_jobs_external_job_id", "discovery_jobs", ["external_job_id"])


def downgrade() -> None:
    op.drop_index("ix_discovery_jobs_external_job_id", table_name="discovery_jobs")
    op.drop_index("ix_discovery_jobs_status", table_name="discovery_jobs")
    op.drop_index("ix_discovery_jobs_user_id", table_name="discovery_jobs")
    op.drop_table("discovery_jobs")
