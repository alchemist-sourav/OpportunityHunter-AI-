from typing import Any


class AppException(Exception):
    status_code: int = 400
    error_code: str = "app_error"

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code


class DatabaseNotConfiguredError(AppException):
    status_code = 503
    error_code = "database_not_configured"

    def __init__(self) -> None:
        super().__init__("Database connection is not configured. Set DATABASE_URL to use this endpoint.")


class CredentialStoreNotAvailableError(AppException):
    status_code = 503
    error_code = "credential_store_not_available"

    def __init__(self) -> None:
        super().__init__("Per-user credential storage is available via /api/v1/credentials/firecrawl.")


class AuthenticationNotConfiguredError(AppException):
    status_code = 503
    error_code = "authentication_not_configured"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Supabase JWT verification is not configured on the server.")


class AuthenticationError(AppException):
    status_code = 401
    error_code = "unauthenticated"


class MissingTokenError(AuthenticationError):
    error_code = "missing_token"

    def __init__(self) -> None:
        super().__init__("Missing Authorization header with a Bearer token.")


class InvalidTokenError(AuthenticationError):
    error_code = "invalid_token"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Token is invalid or malformed.")


class TokenExpiredError(AuthenticationError):
    error_code = "token_expired"

    def __init__(self) -> None:
        super().__init__("Authentication token has expired. Sign in again.")


class InvalidIssuerError(AuthenticationError):
    error_code = "invalid_issuer"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Token issuer does not match the configured Supabase issuer.")


class InvalidAudienceError(AuthenticationError):
    error_code = "invalid_audience"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Token audience does not match the configured audience.")


class ForbiddenError(AppException):
    status_code = 403
    error_code = "forbidden"


class ProfileNotFoundError(AppException):
    status_code = 404
    error_code = "profile_not_found"

    def __init__(self) -> None:
        super().__init__("No profile exists for the authenticated user.")


class CredentialNotFoundError(AppException):
    status_code = 404
    error_code = "credential_not_found"

    def __init__(self, provider: str = "firecrawl") -> None:
        super().__init__(f"No stored credential for provider '{provider}'.")


class EncryptionKeyNotConfiguredError(AppException):
    status_code = 503
    error_code = "encryption_key_not_configured"

    def __init__(self, message: str = "Credential encryption key is not configured. Set FIRECRAWL_ENCRYPTION_KEY.") -> None:
        super().__init__(message)


class CredentialDecryptionError(AppException):
    status_code = 500
    error_code = "credential_decryption_failed"

    def __init__(self) -> None:
        super().__init__("Stored credential could not be decrypted. It may have been encrypted with a different key.")


class CredentialValidationError(AppException):
    status_code = 400
    error_code = "invalid_credential"


class DiscoveryError(AppException):
    status_code = 400
    error_code = "discovery_error"


class DiscoveryJobNotFoundError(AppException):
    status_code = 404
    error_code = "discovery_job_not_found"

    def __init__(self) -> None:
        super().__init__("Discovery job was not found.")


class DiscoveryCredentialMissingError(AppException):
    status_code = 503
    error_code = "discovery_credential_missing"

    def __init__(self) -> None:
        super().__init__("No Firecrawl credential is configured. Add one in Settings first.")


class DiscoveryConcurrencyLimitError(AppException):
    status_code = 429
    error_code = "discovery_concurrency_limit"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "You already have the maximum number of active discovery jobs.")


class DiscoveryQuotaExceededError(AppException):
    status_code = 429
    error_code = "discovery_quota_exceeded"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "You have reached your daily discovery quota.")


class DiscoveryDomainNotAllowedError(AppException):
    status_code = 403
    error_code = "discovery_domain_not_allowed"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "One or more source domains are not allowed.")


class DiscoveryInvalidUrlError(AppException):
    status_code = 400
    error_code = "discovery_invalid_url"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "One or more target URLs are invalid or unsafe.")


class DiscoveryBadCredentialError(AppException):
    status_code = 401
    error_code = "discovery_bad_credential"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "The Firecrawl API key was rejected. Re-check your credential.")


class DiscoveryRateLimitError(AppException):
    status_code = 429
    error_code = "discovery_rate_limited"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Firecrawl rate limit was exceeded. Try again later.")


class DiscoveryTimeoutError(AppException):
    status_code = 504
    error_code = "discovery_timeout"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "Discovery exceeded the allowable wait time.")


class DiscoveryUpstreamError(AppException):
    status_code = 502
    error_code = "discovery_upstream_error"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "A Firecrawl dependency failed. Try again later.")


class DiscoveryCancellationNotAllowedError(AppException):
    status_code = 409
    error_code = "discovery_cancel_not_allowed"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or "This discovery job can no longer be cancelled.")
