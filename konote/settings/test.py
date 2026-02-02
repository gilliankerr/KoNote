"""Test settings — SQLite in-memory for fast tests without PostgreSQL."""
from .base import *  # noqa: F401, F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
    "audit": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

# Use fast password hasher for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable CSP in tests
MIDDLEWARE = [m for m in MIDDLEWARE if m != "csp.middleware.CSPMiddleware"]

# Use simple static files storage (no manifest needed)
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
