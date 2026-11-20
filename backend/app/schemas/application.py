from enum import Enum
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApplicationStatus(str, Enum):
    INTERESTED = "interested"
    SAVED = "saved"
    APPLIED = "applied"
    ASSESSMENT = "assessment"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class ApplicationCreate(BaseModel):
    opportunity_id: str
    status: ApplicationStatus | None = Field(default=ApplicationStatus.INTERESTED, description="Initial status when saving an opportunity")
    notes: str | None = Field(default=None, description="Optional notes about the application")
    deadline: datetime | None = Field(default=None, description="Application deadline date")


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus | None = Field(default=None, description="Update the application status")
    notes: str | None = Field(default=None, description="Update notes about the application")
    deadline: datetime | None = Field(default=None, description="Update the application deadline")


class ApplicationResponse(BaseModel):
    id: str
    user_id: str
    opportunity_id: str
    status: str
    applied_date: datetime | None
    deadline: datetime | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationListItem(BaseModel):
    id: str
    opportunity_id: str
    status: str
    applied_date: datetime | None
    deadline: datetime | None
    notes: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationListResponse(BaseModel):
    total: int
    items: list[ApplicationListItem]
    limit: int
    offset: int