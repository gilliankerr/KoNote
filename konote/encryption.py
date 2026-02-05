"""
Application-level PII encryption using Fernet (AES-128-CBC + HMAC-SHA256).

Usage in models:
    from KoNote2.encryption import encrypt_field, decrypt_field

    class MyModel(models.Model):
        _name_encrypted = models.BinaryField()

        @property
        def name(self):
            return decrypt_field(self._name_encrypted)

        @name.setter
        def name(self, value):
            self._name_encrypted = encrypt_field(value)
"""
from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings

_fernet = None


def _get_fernet():
    """Lazy-initialise the Fernet cipher from the configured key."""
    global _fernet
    if _fernet is None:
        key = settings.FIELD_ENCRYPTION_KEY
        if not key:
            raise ValueError(
                "FIELD_ENCRYPTION_KEY is not set. "
                "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt_field(plaintext):
    """Encrypt a string value. Returns bytes for storage in BinaryField."""
    if plaintext is None or plaintext == "":
        return b""
    f = _get_fernet()
    return f.encrypt(plaintext.encode("utf-8"))


def decrypt_field(ciphertext):
    """Decrypt a BinaryField value back to string."""
    if not ciphertext:
        return ""
    f = _get_fernet()
    try:
        if isinstance(ciphertext, memoryview):
            ciphertext = bytes(ciphertext)
        return f.decrypt(ciphertext).decode("utf-8")
    except InvalidToken:
        return "[decryption error]"


def generate_key():
    """Generate a new Fernet key for initial setup."""
    return Fernet.generate_key().decode()
