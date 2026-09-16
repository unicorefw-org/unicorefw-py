"""
File: unicorefw/crypto.py
Authenticated string encryption utilities for UniCoreFW.

The helpers in this module use Fernet from the optional ``cryptography``
dependency. Applications remain responsible for storing and rotating keys in a
dedicated secret-management system.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info

This file is part of UniCoreFW. You can redistribute it and/or modify
it under the terms of the [BSD-3-Clause] as published by
the Free Software Foundation.
You should have received a copy of the [BSD-3-Clause] license
along with UniCoreFW. If not, see https://www.gnu.org/licenses/.
"""

try:
    from cryptography.fernet import (  # type: ignore
        Fernet,
    )
    from cryptography.fernet import (
        InvalidToken as FernetInvalidToken,
    )

    _fernet_generate_key = Fernet.generate_key
    CRYPTO_AVAILABLE = True
except ImportError:
    Fernet = None  # type: ignore
    FernetInvalidToken = None  # type: ignore
    _fernet_generate_key = None
    CRYPTO_AVAILABLE = False


class CryptoUnavailableError(RuntimeError):
    """Raised when the optional cryptography backend is unavailable."""


class InvalidKey(ValueError):
    """Raised when key material is not a valid Fernet key."""


class InvalidToken(ValueError):
    """Raised when Fernet ciphertext cannot be safely decrypted."""


def _require_crypto() -> None:
    if not CRYPTO_AVAILABLE:
        raise CryptoUnavailableError(
            "cryptography is required; install it with "
            "'pip install unicorefw[crypto]'"
        )


def _new_fernet(key: bytes):
    _require_crypto()
    if not isinstance(key, bytes):
        raise TypeError("key must be bytes")

    try:
        return Fernet(key)  # type: ignore[operator]
    except (TypeError, ValueError) as exc:
        raise InvalidKey("key must be a valid Fernet key") from exc


def _validate_ttl(ttl: int | None) -> None:
    if ttl is None:
        return
    if isinstance(ttl, bool) or not isinstance(ttl, int):
        raise TypeError("ttl must be a non-negative integer or None")
    if ttl < 0:
        raise ValueError("ttl must be a non-negative integer or None")


def generate_key() -> bytes:
    """Generate a URL-safe base64-encoded Fernet key.

    Raises:
        CryptoUnavailableError: If the optional cryptography backend is absent.
    """
    _require_crypto()
    return _fernet_generate_key()  # type: ignore[misc]


def encrypt_string(plaintext: str, key: bytes) -> str:
    """Encrypt a UTF-8 string with a Fernet key.

    Args:
        plaintext: The string to encrypt.
        key: A key returned by :func:`generate_key` or Fernet.

    Raises:
        TypeError: If ``plaintext`` is not a string or ``key`` is not bytes.
        InvalidKey: If ``key`` is not valid Fernet key material.
        CryptoUnavailableError: If the optional cryptography backend is absent.
    """
    if not isinstance(plaintext, str):
        raise TypeError("plaintext must be a string")

    fernet = _new_fernet(key)
    token = fernet.encrypt(plaintext.encode("utf-8"))
    return token.decode("ascii")


def decrypt_string(
    ciphertext: str,
    key: bytes,
    ttl: int | None = None,
) -> str:
    """Decrypt and authenticate a Fernet token.

    Args:
        ciphertext: A token returned by :func:`encrypt_string` or Fernet.
        key: The Fernet key used to encrypt the token.
        ttl: Optional maximum token age in seconds. ``None`` disables age
            validation, matching the historical behavior.

    Raises:
        TypeError: If an argument has an unsupported type.
        ValueError: If ``ttl`` is negative.
        InvalidKey: If ``key`` is not valid Fernet key material.
        InvalidToken: If the token is malformed, expired, was encrypted with a
            different key, or does not contain UTF-8 plaintext.
        CryptoUnavailableError: If the optional cryptography backend is absent.
    """
    if not isinstance(ciphertext, str):
        raise TypeError("ciphertext must be a string")
    _validate_ttl(ttl)
    fernet = _new_fernet(key)

    try:
        decrypted = fernet.decrypt(ciphertext.encode("utf-8"), ttl=ttl)
    except FernetInvalidToken as exc:  # type: ignore[misc]
        raise InvalidToken(
            "decryption failed: token is invalid, expired, or uses another key"
        ) from exc

    try:
        return decrypted.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InvalidToken("decryption failed: plaintext is not valid UTF-8") from exc
