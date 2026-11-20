from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import CredentialValidationError
from app.models.user_models import UserApiCredential
from app.services.encryption import EncryptionService

PROVIDER_FIRECRAWL = "firecrawl"


def _associated_data(user_id: str, provider: str = PROVIDER_FIRECRAWL) -> str:
    return f"{provider}:{user_id}"


def validate_firecrawl_api_key(api_key: str, live: bool = False) -> str:
    key = api_key.strip()
    if not key:
        raise CredentialValidationError("Firecrawl API key must not be empty.")
    if len(key) < 16:
        raise CredentialValidationError("Firecrawl API key is too short to be valid.")
    if len(key) > 255:
        raise CredentialValidationError("Firecrawl API key is too long.")
    if any(character.isspace() for character in key):
        raise CredentialValidationError("Firecrawl API key must not contain whitespace.")
    if not live:
        return "format_valid"

    settings = get_settings()
    try:
        response = httpx.get(
            f"{settings.firecrawl_base_url.rstrip('/')}/health",
            headers={"Authorization": f"Bearer {key}"},
            timeout=min(settings.firecrawl_timeout_seconds, 10),
        )
    except httpx.HTTPError:
        return "unverified"
    if response.status_code in (401, 403):
        raise CredentialValidationError("Firecrawl rejected the API key.")
    if 200 <= response.status_code < 300:
        return "live_valid"
    return "unverified"


def save_firecrawl_credential(session: Session, user_id: str, api_key: str) -> tuple[UserApiCredential, str]:
    settings = get_settings()
    encryption = EncryptionService.from_settings()
    encrypted = encryption.encrypt(api_key, _associated_data(user_id))
    validation = validate_firecrawl_api_key(api_key, live=settings.firecrawl_validate_live)

    statement = select(UserApiCredential).where(
        UserApiCredential.user_id == user_id,
        UserApiCredential.provider == PROVIDER_FIRECRAWL,
    )
    credential = session.scalar(statement)
    if credential is None:
        credential = UserApiCredential(
            user_id=user_id,
            provider=PROVIDER_FIRECRAWL,
            encrypted_key=encrypted.ciphertext,
            nonce=encrypted.nonce,
            tag=encrypted.tag,
            algorithm=encrypted.algorithm,
            key_version=encrypted.key_version,
            associated_data=encrypted.associated_data,
            is_active=True,
        )
        session.add(credential)
    else:
        credential.encrypted_key = encrypted.ciphertext
        credential.nonce = encrypted.nonce
        credential.tag = encrypted.tag
        credential.algorithm = encrypted.algorithm
        credential.key_version = encrypted.key_version
        credential.associated_data = encrypted.associated_data
        credential.is_active = True
    session.commit()
    session.refresh(credential)
    return credential, validation


def get_firecrawl_credential(session: Session, user_id: str) -> UserApiCredential | None:
    return session.get(UserApiCredential, (user_id, PROVIDER_FIRECRAWL))


def delete_firecrawl_credential(session: Session, user_id: str) -> bool:
    credential = get_firecrawl_credential(session, user_id)
    if credential is None:
        return False
    session.delete(credential)
    session.commit()
    return True


def decrypt_firecrawl_credential(credential: UserApiCredential) -> str:
    from app.services.encryption import EncryptedData

    encryption = EncryptionService.from_settings()
    return encryption.decrypt(
        EncryptedData(
            ciphertext=credential.encrypted_key,
            nonce=credential.nonce,
            tag=credential.tag,
            algorithm=credential.algorithm,
            key_version=credential.key_version,
            associated_data=credential.associated_data,
        )
    )


def credential_to_status(credential: UserApiCredential | None) -> dict[str, Any]:
    if credential is None:
        return {
            "provider": PROVIDER_FIRECRAWL,
            "configured": False,
            "algorithm": None,
            "key_version": None,
            "updated_at": None,
        }
    return {
        "provider": credential.provider,
        "configured": credential.is_active,
        "algorithm": credential.algorithm,
        "key_version": credential.key_version,
        "updated_at": credential.updated_at.isoformat() if credential.updated_at else None,
    }
