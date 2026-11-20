"""Phase 4: opportunities and sources tables.

Revision ID: 0003_opportunities
Revises: 0002_discovery_jobs
Create Date: 2026-11-19
"""
from alembic import op
import sqlalchemy as sa


revision = "0003_opportunities"
down_revision = "0002_discovery_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "opportunities",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=True),
        sa.Column("company_name", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("opportunity_type", sa.String(length=32), nullable=True),
        sa.Column("required_skills", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("experience_level", sa.String(length=32), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("remote_preference", sa.String(length=32), nullable=True),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("salary_max", sa.Integer(), nullable=True),
        sa.Column("salary_currency", sa.String(length=3), nullable=True),
        sa.Column("application_url", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_domain", sa.String(length=255), nullable=False),
        sa.Column("application_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("employment_type", sa.String(length=32), nullable=True),
        sa.Column("verification_status", sa.String(length=32), nullable=False, server_default="unverified"),
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("verification_evidence", sa.Text(), nullable=True),
        sa.Column("verification_failure_reason", sa.Text(), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("extracted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "experience_level IS NULL OR experience_level IN ('student', 'fresher', 'junior', 'experienced')",
            name="ck_opportunities_experience_level",
        ),
        sa.CheckConstraint(
            "remote_preference IS NULL OR remote_preference IN ('remote_only', 'hybrid', 'onsite_only', 'no_preference')",
            name="ck_opportunities_remote_preference",
        ),
        sa.CheckConstraint(
            "salary_min IS NULL OR salary_min >= 0",
            name="ck_opportunities_salary_min_nonneg",
        ),
        sa.CheckConstraint(
            "salary_max IS NULL OR salary_max >= 0",
            name="ck_opportunities_salary_max_nonneg",
        ),
        sa.CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max",
            name="ck_opportunities_salary_min_le_max",
        ),
        sa.CheckConstraint(
            "salary_currency IS NULL OR length(salary_currency) = 3",
            name="ck_opportunities_salary_currency_len",
        ),
    )
    op.create_index("ix_opportunities_fingerprint", "opportunities", ["fingerprint"], unique=True)
    op.create_index("ix_opportunities_opportunity_type", "opportunities", ["opportunity_type"])
    op.create_index("ix_opportunities_verification_status", "opportunities", ["verification_status"])
    op.create_index("ix_opportunities_source_domain", "opportunities", ["source_domain"])
    op.create_index("ix_opportunities_is_public", "opportunities", ["is_public"])
    op.create_index("ix_opportunities_type_status", "opportunities", ["opportunity_type", "verification_status"])
    op.create_index("ix_opportunities_domain_type", "opportunities", ["source_domain", "opportunity_type"])
    op.create_index("ix_opportunities_created_public", "opportunities", ["created_at", "is_public"])

    op.create_table(
        "opportunity_sources",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("opportunity_id", sa.String(length=36), nullable=False),
        sa.Column("discovery_job_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_domain", sa.String(length=255), nullable=False),
        sa.Column("raw_content_hash", sa.String(length=64), nullable=False),
        sa.Column("extracted_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["opportunity_id"], ["opportunities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["discovery_job_id"], ["discovery_jobs.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("opportunity_id", "discovery_job_id", "source_url", name="uq_opportunity_source_unique"),
    )
    op.create_index("ix_opportunity_sources_user_id", "opportunity_sources", ["user_id"])
    op.create_index("ix_opportunity_sources_opportunity_id", "opportunity_sources", ["opportunity_id"])
    op.create_index("ix_opportunity_sources_discovery_job_id", "opportunity_sources", ["discovery_job_id"])
    op.create_index("ix_opportunity_sources_user_opportunity", "opportunity_sources", ["user_id", "opportunity_id"])


def downgrade() -> None:
    op.drop_index("ix_opportunity_sources_user_opportunity", table_name="opportunity_sources")
    op.drop_index("ix_opportunity_sources_discovery_job_id", table_name="opportunity_sources")
    op.drop_index("ix_opportunity_sources_opportunity_id", table_name="opportunity_sources")
    op.drop_index("ix_opportunity_sources_user_id", table_name="opportunity_sources")
    op.drop_table("opportunity_sources")
    op.drop_index("ix_opportunities_created_public", table_name="opportunities")
    op.drop_index("ix_opportunities_domain_type", table_name="opportunities")
    op.drop_index("ix_opportunities_type_status", table_name="opportunities")
    op.drop_index("ix_opportunities_is_public", table_name="opportunities")
    op.drop_index("ix_opportunities_source_domain", table_name="opportunities")
    op.drop_index("ix_opportunities_verification_status", table_name="opportunities")
    op.drop_index("ix_opportunities_opportunity_type", table_name="opportunities")
    op.drop_index("ix_opportunities_fingerprint", table_name="opportunities")
    op.drop_table("opportunities")