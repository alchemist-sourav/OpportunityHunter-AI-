import jwt

from app.core.config import get_settings
from app.core.exceptions import (
    AuthenticationNotConfiguredError,
    ForbiddenError,
    InvalidAudienceError,
    InvalidIssuerError,
    InvalidTokenError,
    TokenExpiredError,
)

ALGORITHM = "HS256"
DEFAULT_AUDIENCE = "authenticated"
REQUIRED_CLAIMS = ("exp", "sub", "iss", "aud")


class AuthUser:
    def __init__(
        self,
        user_id: str,
        email: str | None = None,
        role: str = "authenticated",
        provider: str | None = None,
        email_verified: bool = False,
    ) -> None:
        self.user_id = user_id
        self.email = email
        self.role = role
        self.provider = provider
        self.email_verified = email_verified

    def to_dict(self) -> dict[str, object]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "role": self.role,
            "provider": self.provider,
            "email_verified": self.email_verified,
        }


def resolve_issuer() -> str | None:
    settings = get_settings()
    if settings.supabase_jwt_issuer:
        return settings.supabase_jwt_issuer.rstrip("/")
    if settings.supabase_url:
        return f"{settings.supabase_url.rstrip('/')}/auth/v1"
    return None


def resolve_audience() -> str:
    settings = get_settings()
    return settings.supabase_jwt_audience or DEFAULT_AUDIENCE


def verify_supabase_token(token: str) -> AuthUser:
    settings = get_settings()
    if not settings.supabase_jwt_secret:
        raise AuthenticationNotConfiguredError()
    issuer = resolve_issuer()
    if not issuer:
        raise AuthenticationNotConfiguredError("Supabase URL or JWT issuer must be configured.")

    try:
        payload = jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=[ALGORITHM],
            audience=resolve_audience(),
            issuer=issuer,
            options={"require": list(REQUIRED_CLAIMS)},
        )
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpiredError() from exc
    except jwt.InvalidIssuerError as exc:
        raise InvalidIssuerError() from exc
    except jwt.InvalidAudienceError as exc:
        raise InvalidAudienceError() from exc
    except jwt.PyJWTError as exc:
        raise InvalidTokenError() from exc

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id.strip():
        raise InvalidTokenError("Token is missing a valid subject claim.")

    role = str(payload.get("role", "authenticated"))
    if role != "authenticated":
        raise ForbiddenError("Token role must be 'authenticated' to access this API.")

    app_metadata = payload.get("app_metadata") or {}
    provider = app_metadata.get("provider") if isinstance(app_metadata, dict) else None
    email = payload.get("email")
    email_verified = bool(payload.get("email_verified", True))

    return AuthUser(
        user_id=user_id.strip(),
        email=email if isinstance(email, str) else None,
        role=role,
        provider=provider if isinstance(provider, str) else None,
        email_verified=email_verified,
    )
