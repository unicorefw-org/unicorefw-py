"""Regression tests for the optional Fernet boundary."""

from __future__ import annotations

import builtins
import importlib.util
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

import unicorefw
from unicorefw import crypto
from unicorefw.core import UniCoreFW


@pytest.fixture
def fernet_module():
    return pytest.importorskip("cryptography.fernet")


@pytest.mark.parametrize("plaintext", ["", "Grüße 🔐", "x" * (1024 * 1024)])
def test_string_round_trip_supports_empty_unicode_and_large_inputs(
    fernet_module,
    plaintext,
):
    key = crypto.generate_key()

    token = crypto.encrypt_string(plaintext, key)

    assert isinstance(key, bytes)
    assert isinstance(token, str)
    assert crypto.decrypt_string(token, key) == plaintext


def test_crypto_functions_remain_available_through_public_entry_points(
    fernet_module,
):
    key = unicorefw.generate_key() # type: ignore

    token = UniCoreFW.encrypt_string("compatible", key) # type: ignore

    assert unicorefw.decrypt_string(token, key) == "compatible" # type: ignore


@pytest.mark.parametrize("plaintext", [None, b"bytes", 42])
def test_encrypt_rejects_non_string_plaintext(fernet_module, plaintext):
    with pytest.raises(TypeError, match="plaintext must be a string"):
        crypto.encrypt_string(plaintext, crypto.generate_key())


@pytest.mark.parametrize("ciphertext", [None, b"token", 42])
def test_decrypt_rejects_non_string_ciphertext(fernet_module, ciphertext):
    with pytest.raises(TypeError, match="ciphertext must be a string"):
        crypto.decrypt_string(ciphertext, crypto.generate_key())


@pytest.mark.parametrize("operation", [crypto.encrypt_string, crypto.decrypt_string])
def test_crypto_operations_reject_non_bytes_keys(fernet_module, operation):
    with pytest.raises(TypeError, match="key must be bytes"):
        operation("value", "not-bytes")


def test_invalid_key_material_raises_stable_exception_without_disclosure(
    fernet_module,
):
    invalid_key = b"sensitive-invalid-key"

    with pytest.raises(crypto.InvalidKey, match="valid Fernet key") as captured:
        crypto.encrypt_string("value", invalid_key)

    assert isinstance(captured.value, ValueError)
    assert captured.value.__cause__ is not None
    assert invalid_key.decode("ascii") not in str(captured.value)


@pytest.mark.parametrize("ttl", [True, 1.5, "1"])
def test_decrypt_rejects_non_integer_ttl(fernet_module, ttl):
    key = crypto.generate_key()
    token = crypto.encrypt_string("value", key)

    with pytest.raises(TypeError, match="non-negative integer"):
        crypto.decrypt_string(token, key, ttl=ttl)


def test_decrypt_rejects_negative_ttl(fernet_module):
    key = crypto.generate_key()
    token = crypto.encrypt_string("value", key)

    with pytest.raises(ValueError, match="non-negative integer"):
        crypto.decrypt_string(token, key, ttl=-1)


def test_wrong_key_raises_package_invalid_token_with_backend_cause(fernet_module):
    key = crypto.generate_key()
    wrong_key = crypto.generate_key()
    token = crypto.encrypt_string("secret", key)

    with pytest.raises(crypto.InvalidToken) as captured:
        crypto.decrypt_string(token, wrong_key)

    assert isinstance(captured.value, ValueError)
    assert isinstance(captured.value.__cause__, fernet_module.InvalidToken)
    assert token not in str(captured.value)
    assert wrong_key.decode("ascii") not in str(captured.value)


def test_corrupted_token_raises_package_invalid_token(fernet_module):
    key = crypto.generate_key()
    token = crypto.encrypt_string("secret", key)
    corrupted_token = token[:-1] + "A"

    with pytest.raises(crypto.InvalidToken) as captured:
        crypto.decrypt_string(corrupted_token, key)

    assert isinstance(captured.value.__cause__, fernet_module.InvalidToken)


def test_expired_token_is_rejected_when_ttl_is_supplied(fernet_module):
    key = crypto.generate_key()
    token = fernet_module.Fernet(key).encrypt_at_time(
        b"expired",
        current_time=0,
    )

    with pytest.raises(crypto.InvalidToken) as captured:
        crypto.decrypt_string(token.decode("ascii"), key, ttl=1)

    assert isinstance(captured.value.__cause__, fernet_module.InvalidToken)


def test_non_utf8_plaintext_raises_package_invalid_token(fernet_module):
    key = crypto.generate_key()
    token = fernet_module.Fernet(key).encrypt(b"\xff")

    with pytest.raises(crypto.InvalidToken) as captured:
        crypto.decrypt_string(token.decode("ascii"), key)

    assert isinstance(captured.value.__cause__, UnicodeDecodeError)


def test_missing_dependency_has_a_stable_install_error(monkeypatch):
    original_import = builtins.__import__

    def import_without_cryptography(name, *args, **kwargs):
        if name == "cryptography" or name.startswith("cryptography."):
            raise ImportError("blocked for missing-dependency test")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", import_without_cryptography)
    spec = importlib.util.spec_from_file_location(
        "unicorefw_crypto_without_backend",
        Path(crypto.__file__),
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.CRYPTO_AVAILABLE is False
    for operation, args in (
        (module.generate_key, ()),
        (module.encrypt_string, ("value", b"key")),
        (module.decrypt_string, ("token", b"key")),
    ):
        with pytest.raises(
            module.CryptoUnavailableError,
            match=r"unicorefw\[crypto\]",
        ) as captured:
            operation(*args)
        assert isinstance(captured.value, RuntimeError)
