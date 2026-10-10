"""Staging environment settings for GQT Student Portal."""

from .base import *
from .base import env

DEBUG = False
ENVIRONMENT = "staging"

ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=[
        "localhost",
        "127.0.0.1",
        "testserver",
        "staging-api.portal.gqt.edu",
        "gqt-student.onrender.com",
    ],
)

raw_db_url = (
    env("DATABASE_URL", default="").strip()
    or env("DJANGO_DATABASE_URL", default="").strip()
)
if raw_db_url:
    DATABASES = {"default": env.db_url_config(raw_db_url)}
    if DATABASES["default"].get("ENGINE") == "django.db.backends.postgresql":
        DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=0)
        DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
        if "OPTIONS" not in DATABASES["default"]:
            DATABASES["default"]["OPTIONS"] = {}
        DATABASES["default"]["OPTIONS"].setdefault(
            "sslmode", env("DB_SSLMODE", default="require")
        )
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "staging_db.sqlite3",
        }
    }

redis_url = env("REDIS_URL", default="").strip()
if redis_url:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": redis_url,
            "OPTIONS": {
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "IGNORE_EXCEPTIONS": True,
            },
            "KEY_PREFIX": "gqt_portal_staging",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "staging-locmem-cache",
        }
    }

# Security Settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Staging email can log to console or mock SMTP
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
