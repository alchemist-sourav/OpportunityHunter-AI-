import pytest

from app.core.config import Settings
from app.core.exceptions import (
    CredentialDecryptionError,
    EncryptionKeyNotConfiguredError,
)
from app.services import encryption as encryption_mod
from app.services.encryption import ALGORITHM, EncryptedData, EncryptionService

TEST_KEY_HEX = "aa" * 32


@pytest.fixture()
def service() -> EncryptionService:
    return EncryptionService.from_hex_key(TEST_KEY_HEX)


def test_from_hex_key_rejects_non_hex() -> None:
    with pytest.raises(EncryptionKeyNotConfiguredError):
        EncryptionService.from_hex_key("zzzz")


def test_from_hex_key_rejects_wrong_length() -> None:
    with pytest.raises(EncryptionKeyNotConfiguredError):
        EncryptionService.from_hex_key("abcd")


def test_from_settings_raises_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(encryption_mod, "get_settings", lambda: Settings(firecrawl_encryption_key=None))
    with pytest.raises(EncryptionKeyNotConfiguredError):
        EncryptionService.from_settings()


def test_round_trip_encrypt_decrypt(service: EncryptionService) -> None:
    secret = "fc_live_1234567890abcdef"
    data = service.encrypt(secret, associated_data="firecrawl:user-1")
    assert isinstance(data, EncryptedData)
    assert data.algorithm == ALGORITHM
    assert data.ciphertext and data.nonce and data.tag
    assert service.decrypt(data) == secret


def test_to_record_is_serializable(service: EncryptionService) -> None:
    data = service.encrypt("topsecret", associated_data="firecrawl:user-1")
    record = data.to_record()
    assert record["algorithm"] == "aes-256-gcm"
    assert record["key_version"] == 1
    assert set(record) == {
        "ciphertext",
        "nonce",
        "tag",
        "algorithm",
        "key_version",
        "associated_data",
    }


def test_decrypt_tampered_ciphertext_raises(service: EncryptionService) -> None:
    data = service.encrypt("topsecret", associated_data="firecrawl:user-1")
    mangled = EncryptedData(
        ciphertext="AAAA" + data.ciphertext[4:],
        nonce=data.nonce,
        tag=data.tag,
        algorithm=data.algorithm,
        key_version=data.key_version,
        associated_data=data.associated_data,
    )
    with pytest.raises(CredentialDecryptionError):
        service.decrypt(mangled)


def test_decrypt_wrong_associated_data_raises(service: EncryptionService) -> None:
    data = service.encrypt("topsecret", associated_data="firecrawl:user-1")
    with pytest.raises(CredentialDecryptionError):
        service.decrypt(EncryptedData(**{**data.to_record(), "associated_data": "firecrawl:user-2"}))


def test_decrypt_requires_same_key(service: EncryptionService) -> None:
    data = service.encrypt("topsecret", associated_data="firecrawl:user-1")
    other = EncryptionService.from_hex_key("bb" * 32)
    with pytest.raises(CredentialDecryptionError):
        other.decrypt(data)


def test_encrypted_data_uses_aad_per_user(service: EncryptionService) -> None:
    a = service.encrypt("same-secret", associated_data="firecrawl:user-a")
    b = service.encrypt("same-secret", associated_data="firecrawl:user-b")
    assert a.ciphertext != b.ciphertext
    assert service.decrypt(a) == "same-secret"
    assert service.decrypt(b) == "same-secret"
