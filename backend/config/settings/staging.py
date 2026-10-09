"""Staging environment settings for GQT Student Portal."""

from .base import *
from .base import env

DEBUG = False
ENVIRONMENT = "staging"

raw_db_url = env("DATABASE_URL", default="").strip()
if not raw_db_url:
    raise ValueError(
        "DATABASE_URL environment variable must be set in staging to your Supabase PostgreSQL connection string."
    )

DATABASES = {"default": env.db_url_config(raw_db_url)}

if DATABASES["default"].get("ENGINE") == "django.db.backends.postgresql":
    DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=0)
    DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
    if "OPTIONS" not in DATABASES["default"]:
        DATABASES["default"]["OPTIONS"] = {}
    DATABASES["default"]["OPTIONS"].setdefault(
        "sslmode", env("DB_SSLMODE", default="require")
    )

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Staging email can log to console or mock SMTP
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
