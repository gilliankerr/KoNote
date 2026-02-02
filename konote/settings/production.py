"""Production settings — secure defaults."""
import os
from .base import *  # noqa: F401, F403

DEBUG = False
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

# HTTPS — Railway handles TLS at the edge, so we don't redirect internally.
# SECURE_PROXY_SSL_HEADER tells Django to trust the proxy's forwarded header.
SECURE_SSL_REDIRECT = False  # Railway edge handles HTTPS redirect
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
