"""Encryption utilities for sensitive data."""

import base64
import hashlib

from cryptography.fernet import Fernet

from app.core.config import settings


def _derive_key() -> bytes:
    """Derive a Fernet-compatible key from the app secret key."""
    # SHA-256 hash produces 32 bytes, then base64 encode to 44 chars (Fernet format)
    digest = hashlib.sha256(settings.secret_key.encode()).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_value(plaintext: str) -> str:
    """
    Encrypt a string value using Fernet symmetric encryption.

    Args:
        plaintext: The plaintext string to encrypt

    Returns:
        The encrypted ciphertext as a base64-encoded string
    """
    if not plaintext:
        return ""

    key = _derive_key()
    fernet = Fernet(key)
    encrypted = fernet.encrypt(plaintext.encode())
    return encrypted.decode()


def decrypt_value(ciphertext: str) -> str:
    """
    Decrypt a Fernet-encrypted string.

    Args:
        ciphertext: The encrypted ciphertext (base64-encoded)

    Returns:
        The decrypted plaintext string

    Raises:
        cryptography.fernet.InvalidToken: If the ciphertext is invalid or key is wrong
    """
    if not ciphertext:
        return ""

    key = _derive_key()
    fernet = Fernet(key)
    decrypted = fernet.decrypt(ciphertext.encode())
    return decrypted.decode()


def mask_api_key(api_key: str) -> str:
    """
    Mask an API key, showing only the last 4 characters.

    Args:
        api_key: The API key to mask

    Returns:
        Masked string like "...XXXX"
    """
    if not api_key or len(api_key) < 4:
        return "***"

    return f"...{api_key[-4:]}"
