"""Tests for PII field encryption (Fernet AES)."""
from django.test import TestCase, override_settings
from cryptography.fernet import Fernet

from KoNote2.encryption import encrypt_field, decrypt_field, _get_fernet
import KoNote2.encryption as enc_module


TEST_KEY = Fernet.generate_key().decode()


@override_settings(FIELD_ENCRYPTION_KEY=TEST_KEY)
class EncryptionUtilsTest(TestCase):
    """Test encrypt_field / decrypt_field round-trip and edge cases."""

    def setUp(self):
        # Reset cached Fernet instance so test key is picked up
        enc_module._fernet = None

    def tearDown(self):
        enc_module._fernet = None

    def test_round_trip(self):
        """Encrypting then decrypting returns original text."""
        plaintext = "Jane Doe"
        ciphertext = encrypt_field(plaintext)
        self.assertIsInstance(ciphertext, bytes)
        self.assertNotEqual(ciphertext, plaintext.encode())
        self.assertEqual(decrypt_field(ciphertext), plaintext)

    def test_unicode_round_trip(self):
        """Unicode characters survive encryption round-trip."""
        plaintext = "Éloïse Côté-Tremblay"
        self.assertEqual(decrypt_field(encrypt_field(plaintext)), plaintext)

    def test_empty_string_returns_empty_bytes(self):
        self.assertEqual(encrypt_field(""), b"")
        self.assertEqual(decrypt_field(b""), "")

    def test_none_returns_empty_bytes(self):
        self.assertEqual(encrypt_field(None), b"")

    def test_invalid_ciphertext_returns_error_marker(self):
        """Corrupted data returns a safe error string, not an exception."""
        result = decrypt_field(b"not-valid-fernet-data")
        self.assertEqual(result, "[decryption error]")

    def test_memoryview_input(self):
        """BinaryField values come as memoryview — decryption handles this."""
        ciphertext = encrypt_field("Test")
        mv = memoryview(ciphertext)
        self.assertEqual(decrypt_field(mv), "Test")


@override_settings(FIELD_ENCRYPTION_KEY=TEST_KEY)
class ClientPIIEncryptionTest(TestCase):
    """Test that ClientFile model encrypts and decrypts PII via property accessors."""

    def setUp(self):
        enc_module._fernet = None

    def tearDown(self):
        enc_module._fernet = None

    def test_client_name_encryption(self):
        from apps.clients.models import ClientFile

        client = ClientFile()
        client.first_name = "Jane"
        client.last_name = "Doe"

        # Raw field should be encrypted bytes, not plaintext
        self.assertIsInstance(client._first_name_encrypted, bytes)
        self.assertNotIn(b"Jane", client._first_name_encrypted)

        # Property accessor returns plaintext
        self.assertEqual(client.first_name, "Jane")
        self.assertEqual(client.last_name, "Doe")

    def test_user_email_encryption(self):
        from apps.auth_app.models import User

        user = User(username="test", display_name="Test")
        user.email = "test@example.com"

        self.assertIsInstance(user._email_encrypted, bytes)
        self.assertEqual(user.email, "test@example.com")
