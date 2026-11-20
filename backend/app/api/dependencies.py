from typing import Annotated

from fastapi import Depends, Header

from app.core.exceptions import InvalidTokenError, MissingTokenError
from app.core.security import AuthUser, verify_supabase_token


async def get_current_user(authorization: str | None = Header(default=None, alias="Authorization")) -> AuthUser:
    if not authorization:
        raise MissingTokenError()
    parts = authorization.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise InvalidTokenError("Authorization header must use the Bearer scheme.")
    token = parts[1].strip()
    if not token:
        raise MissingTokenError()
    return verify_supabase_token(token)


CurrentUser = Annotated[AuthUser, Depends(get_current_user)]
