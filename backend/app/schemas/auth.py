from pydantic import BaseModel


class CurrentUserResponse(BaseModel):
    user_id: str
    email: str | None = None
    role: str
    provider: str | None = None
    email_verified: bool
