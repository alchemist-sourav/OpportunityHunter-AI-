from datetime import datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base

DISCOVERY_STATUSES = ("pending", "running", "completed", "failed", "cancelled")


class DiscoveryJob(Base):
    __tablename__ = "discovery_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(32), nullable=False)
    keywords: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[list] = mapped_column(JSON, default=list)
    locations: Mapped[list] = mapped_column(JSON, default=list)
    remote_preference: Mapped[str] = mapped_column(String(32), nullable=False)
    experience_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    max_results: Mapped[int] = mapped_column(Integer, nullable=False)
    source_domains: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    external_job_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    total_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_pages: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    result_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    credits_used: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    results: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "category IN ('internship', 'fresher_job', 'full_time_job', 'freelance_project')",
            name="ck_discovery_jobs_category",
        ),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'cancelled')",
            name="ck_discovery_jobs_status",
        ),
        CheckConstraint(
            "remote_preference IN ('remote_only', 'hybrid', 'onsite_only', 'no_preference')",
            name="ck_discovery_jobs_remote_preference",
        ),
        CheckConstraint(
            "experience_level IS NULL OR experience_level IN ('student', 'fresher', 'junior', 'experienced')",
            name="ck_discovery_jobs_experience_level",
        ),
    )
