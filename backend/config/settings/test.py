"""Test settings for GQT Student Portal."""

from .base import *

DEBUG = False
ENVIRONMENT = "test"
SECRET_KEY = "test-secret-key-for-isolated-testing-environment-only"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Relax throttling during test execution
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"] = {
    "anon": "10000/day",
    "user": "10000/day",
    "health": "10000/minute",
    "otp": "1000/minute",
    "submissions": "1000/minute",
    "ai": "1000/minute",
}


# Disable production HTTPS enforcement during tests.
# Django's test client uses HTTP by default.
SECURE_SSL_REDIRECT = False
SECURE_PROXY_SSL_HEADER = None

# Test requests must not require secure cookies.
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1"]