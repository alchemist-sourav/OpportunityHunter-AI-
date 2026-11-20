import base64
import os

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings
from app.core.exceptions import CredentialDecryptionError, EncryptionKeyNotConfiguredError

ALGORITHM = "aes-256-gcm"
KEY_BYTES = 32
NONCE_BYTES = 12
TAG_BYTES = 16


def _b64encode(value: bytes) -> str:
    return base64.b64encode(value).decode("ascii")


def _b64decode(value: str) -> bytes:
    return base64.b64decode(value.encode("ascii"))


class EncryptedData:
    def __init__(
        self,
        ciphertext: str,
        nonce: str,
        tag: str,
        algorithm: str = ALGORITHM,
        key_version: int = 1,
        associated_data: str = "",
    ) -> None:
        self.ciphertext = ciphertext
        self.nonce = nonce
        self.tag = tag
        self.algorithm = algorithm
        self.key_version = key_version
        self.associated_data = associated_data

    def to_record(self) -> dict[str, object]:
        return {
            "ciphertext": self.ciphertext,
            "nonce": self.nonce,
            "tag": self.tag,
            "algorithm": self.algorithm,
            "key_version": self.key_version,
            "associated_data": self.associated_data,
        }


class EncryptionService:
    def __init__(self, key: bytes, key_version: int = 1) -> None:
        if len(key) != KEY_BYTES:
            raise ValueError("Encryption key must be exactly 32 bytes.")
        self._key = key
        self.key_version = key_version
        self._aesgcm = AESGCM(key)

    @classmethod
    def from_hex_key(cls, key_hex: str, key_version: int = 1) -> "EncryptionService":
        try:
            key = bytes.fromhex(key_hex)
        except ValueError as exc:
            raise EncryptionKeyNotConfiguredError(
                "FIRECRAWL_ENCRYPTION_KEY must be valid hexadecimal."
            ) from exc
        if len(key) != KEY_BYTES:
            raise EncryptionKeyNotConfiguredError(
                "FIRECRAWL_ENCRYPTION_KEY must decode to exactly 32 bytes (64 hex characters)."
            )
        return cls(key, key_version)

    @classmethod
    def from_settings(cls, key_version: int = 1) -> "EncryptionService":
        settings = get_settings()
        if not settings.firecrawl_encryption_key:
            raise EncryptionKeyNotConfiguredError()
        return cls.from_hex_key(settings.firecrawl_encryption_key, key_version)

    def encrypt(self, plaintext: str, associated_data: str) -> EncryptedData:
        nonce = os.urandom(NONCE_BYTES)
        combined = self._aesgcm.encrypt(
            nonce,
            plaintext.encode("utf-8"),
            associated_data.encode("utf-8"),
        )
        ciphertext, tag = combined[:-TAG_BYTES], combined[-TAG_BYTES:]
        return EncryptedData(
            ciphertext=_b64encode(ciphertext),
            nonce=_b64encode(nonce),
            tag=_b64encode(tag),
            algorithm=ALGORITHM,
            key_version=self.key_version,
            associated_data=associated_data,
        )

    def decrypt(self, data: EncryptedData) -> str:
        try:
            combined = _b64decode(data.ciphertext) + _b64decode(data.tag)
            plaintext = self._aesgcm.decrypt(
                _b64decode(data.nonce),
                combined,
                data.associated_data.encode("utf-8"),
            )
        except Exception as exc:
            raise CredentialDecryptionError() from exc
        return plaintext.decode("utf-8")
