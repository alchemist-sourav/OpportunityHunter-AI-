from datetime import datetime

from pydantic import BaseModel, Field


class FirecrawlCredentialPut(BaseModel):
    api_key: str = Field(min_length=16, max_length=255)


class FirecrawlCredentialStatus(BaseModel):
    provider: str
    configured: bool
    algorithm: str | None = None
    key_version: int | None = None
    updated_at: datetime | None = None


class FirecrawlCredentialStored(BaseModel):
    provider: str
    configured: bool
    updated_at: datetime | None = None
    validation: str
