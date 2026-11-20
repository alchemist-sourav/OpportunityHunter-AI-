"""Phase 2: user profiles and per-user encrypted API credentials.

Revision ID: 0001_phase2_users
Revises:
Create Date: 2026-11-19
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_phase2_users"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_profiles",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("experience_level", sa.String(length=32), nullable=False),
        sa.Column("preferred_job_roles", sa.JSON(), nullable=False),
        sa.Column("preferred_opportunity_types", sa.JSON(), nullable=False),
        sa.Column("preferred_locations", sa.JSON(), nullable=False),
        sa.Column("remote_preference", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("user_id"),
        sa.CheckConstraint(
            "experience_level IN ('student', 'fresher', 'junior', 'experienced')",
            name="ck_user_profiles_experience_level",
        ),
        sa.CheckConstraint(
            "remote_preference IN ('remote_only', 'hybrid', 'onsite_only', 'no_preference')",
            name="ck_user_profiles_remote_preference",
        ),
    )

    op.create_table(
        "user_api_credentials",
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("encrypted_key", sa.Text(), nullable=False),
        sa.Column("nonce", sa.String(length=64), nullable=False),
        sa.Column("tag", sa.String(length=64), nullable=False),
        sa.Column("algorithm", sa.String(length=32), nullable=False),
        sa.Column("key_version", sa.Integer(), nullable=False),
        sa.Column("associated_data", sa.Text(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("user_id", "provider"),
        sa.UniqueConstraint("user_id", "provider", name="uq_user_credentials_user_provider"),
    )
    op.create_index(
        "ix_user_api_credentials_user_id",
        "user_api_credentials",
        ["user_id"],
    )


def downgrade() -> None:
    op.drop_table("user_api_credentials")
    op.drop_table("user_profiles")
