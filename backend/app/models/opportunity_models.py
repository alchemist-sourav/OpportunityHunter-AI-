from datetime import datetime
from enum import Enum as PyEnum

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class OpportunityType(str, PyEnum):
    INTERNSHIP = "internship"
    FRESHER_JOB = "fresher_job"
    FULL_TIME_JOB = "full_time_job"
    FREELANCE_PROJECT = "freelance_project"


class VerificationStatus(str, PyEnum):
    UNVERIFIED = "unverified"
    ACTIVE = "active"
    EXPIRED = "expired"
    CLOSED = "closed"
    INACCESSIBLE = "inaccessible"
    UNCERTAIN = "uncertain"


class EmploymentType(str, PyEnum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"
    UNKNOWN = "unknown"


class OpportunitySource(Base):
    __tablename__ = "opportunity_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    opportunity_id: Mapped[str] = mapped_column(String(36), ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False, index=True)
    discovery_job_id: Mapped[str] = mapped_column(String(36), ForeignKey("discovery_jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_domain: Mapped[str] = mapped_column(String(255), nullable=False)
    raw_content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("opportunity_id", "discovery_job_id", "source_url", name="uq_opportunity_source_unique"),
        Index("ix_opportunity_sources_user_opportunity", "user_id", "opportunity_id"),
    )


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    title: Mapped[str | None] = mapped_column(String(500), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    opportunity_type: Mapped[OpportunityType | None] = mapped_column(Enum(OpportunityType, native_enum=False), nullable=True, index=True)
    required_skills: Mapped[list] = mapped_column(JSON, default=list)
    experience_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    remote_preference: Mapped[str | None] = mapped_column(String(32), nullable=True)

    salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_currency: Mapped[str | None] = mapped_column(String(3), nullable=True)

    application_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    source_domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    application_deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    employment_type: Mapped[EmploymentType | None] = mapped_column(Enum(EmploymentType, native_enum=False), nullable=True)

    verification_status: Mapped[VerificationStatus] = mapped_column(Enum(VerificationStatus, native_enum=False), nullable=False, default=VerificationStatus.UNVERIFIED, index=True)
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verification_evidence: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)

    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    sources: Mapped[list[OpportunitySource]] = relationship("OpportunitySource", backref="opportunity", cascade="all, delete-orphan", lazy="selectin")

    __table_args__ = (
        CheckConstraint(
            "experience_level IS NULL OR experience_level IN ('student', 'fresher', 'junior', 'experienced')",
            name="ck_opportunities_experience_level",
        ),
        CheckConstraint(
            "remote_preference IS NULL OR remote_preference IN ('remote_only', 'hybrid', 'onsite_only', 'no_preference')",
            name="ck_opportunities_remote_preference",
        ),
        CheckConstraint(
            "salary_min IS NULL OR salary_min >= 0",
            name="ck_opportunities_salary_min_nonneg",
        ),
        CheckConstraint(
            "salary_max IS NULL OR salary_max >= 0",
            name="ck_opportunities_salary_max_nonneg",
        ),
        CheckConstraint(
            "salary_min IS NULL OR salary_max IS NULL OR salary_min <= salary_max",
            name="ck_opportunities_salary_min_le_max",
        ),
        CheckConstraint(
            "salary_currency IS NULL OR length(salary_currency) = 3",
            name="ck_opportunities_salary_currency_len",
        ),
        Index("ix_opportunities_type_status", "opportunity_type", "verification_status"),
        Index("ix_opportunities_domain_type", "source_domain", "opportunity_type"),
        Index("ix_opportunities_created_public", "created_at", "is_public"),
    )