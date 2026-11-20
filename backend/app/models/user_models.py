from datetime import datetime

from sqlalchemy import JSON, CheckConstraint, DateTime, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base

EXPERIENCE_LEVELS = ("student", "fresher", "junior", "experienced")
OPPORTUNITY_TYPES = ("internship", "fresher_job", "full_time_job", "freelance_project")
REMOTE_PREFERENCES = ("remote_only", "hybrid", "onsite_only", "no_preference")


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    full_name: Mapped[str | None] = mapped_column(String(255))
    skills: Mapped[list] = mapped_column(JSON, default=list)
    experience_level: Mapped[str] = mapped_column(String(32))
    preferred_job_roles: Mapped[list] = mapped_column(JSON, default=list)
    preferred_opportunity_types: Mapped[list] = mapped_column(JSON, default=list)
    preferred_locations: Mapped[list] = mapped_column(JSON, default=list)
    remote_preference: Mapped[str] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        CheckConstraint(
            "experience_level IN ('student', 'fresher', 'junior', 'experienced')",
            name="ck_user_profiles_experience_level",
        ),
        CheckConstraint(
            "remote_preference IN ('remote_only', 'hybrid', 'onsite_only', 'no_preference')",
            name="ck_user_profiles_remote_preference",
        ),
    )


class UserApiCredential(Base):
    __tablename__ = "user_api_credentials"

    user_id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)
    provider: Mapped[str] = mapped_column(String(64), primary_key=True)
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)
    nonce: Mapped[str] = mapped_column(String(64), nullable=False)
    tag: Mapped[str] = mapped_column(String(64), nullable=False)
    algorithm: Mapped[str] = mapped_column(String(32), nullable=False, default="aes-256-gcm")
    key_version: Mapped[int] = mapped_column(default=1)
    associated_data: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_credentials_user_provider"),)
