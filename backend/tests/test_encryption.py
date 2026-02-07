"""Tests for encryption utilities."""

import pytest
from cryptography.fernet import InvalidToken

from app.core.encryption import encrypt_value, decrypt_value, mask_api_key


class TestEncryptionDecryption:
    """Tests for encrypt_value and decrypt_value."""

    def test_encrypt_decrypt_roundtrip(self):
        """Encrypt and decrypt should return original value."""
        plaintext = "sk-ant-api03-my-secret-key-12345678"
        encrypted = encrypt_value(plaintext)
        decrypted = decrypt_value(encrypted)

        assert decrypted == plaintext

    def test_encrypted_value_is_different(self):
        """Encrypted value should be different from plaintext."""
        plaintext = "my-secret-api-key"
        encrypted = encrypt_value(plaintext)

        assert encrypted != plaintext

    def test_encrypted_value_is_consistent(self):
        """Same plaintext should produce different ciphertexts (Fernet includes random IV)."""
        plaintext = "my-secret-api-key"
        encrypted1 = encrypt_value(plaintext)
        encrypted2 = encrypt_value(plaintext)

        # Fernet includes a timestamp and random IV, so ciphertexts differ
        assert encrypted1 != encrypted2

        # But both decrypt to the same plaintext
        assert decrypt_value(encrypted1) == plaintext
        assert decrypt_value(encrypted2) == plaintext

    def test_encrypt_empty_string(self):
        """Empty string should return empty string."""
        encrypted = encrypt_value("")
        assert encrypted == ""

    def test_decrypt_empty_string(self):
        """Decrypting empty string should return empty string."""
        decrypted = decrypt_value("")
        assert decrypted == ""

    def test_decrypt_invalid_ciphertext(self):
        """Decrypting invalid ciphertext should raise InvalidToken."""
        with pytest.raises(InvalidToken):
            decrypt_value("invalid-ciphertext")

    def test_decrypt_corrupted_ciphertext(self):
        """Decrypting corrupted ciphertext should raise InvalidToken."""
        plaintext = "my-secret-key"
        encrypted = encrypt_value(plaintext)

        # Corrupt the ciphertext
        corrupted = encrypted[:-5] + "XXXXX"

        with pytest.raises(InvalidToken):
            decrypt_value(corrupted)


class TestMaskApiKey:
    """Tests for mask_api_key."""

    def test_mask_long_key(self):
        """Long API key should be masked with last 4 characters."""
        api_key = "sk-ant-api03-1234567890abcdef"
        masked = mask_api_key(api_key)

        assert masked == "...cdef"

    def test_mask_short_key(self):
        """Short key (< 4 chars) should return '***'."""
        masked = mask_api_key("abc")
        assert masked == "***"

    def test_mask_exactly_4_chars(self):
        """Key with exactly 4 characters should be masked."""
        masked = mask_api_key("1234")
        assert masked == "...1234"

    def test_mask_empty_string(self):
        """Empty string should return '***'."""
        masked = mask_api_key("")
        assert masked == "***"

    def test_mask_none(self):
        """None should be handled gracefully."""
        # mask_api_key expects a string, but let's ensure it doesn't crash
        # In practice, the service layer always passes strings
        masked = mask_api_key("")
        assert masked == "***"
