"""Staging environment settings for GQT Student Portal."""

from .base import *  # noqa: F403
from .base import env

DEBUG = False
ENVIRONMENT = "staging"

DATABASES = {"default": env.db("DATABASE_URL")}
# Production-grade PostgreSQL connection pooling
DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=600)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

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
