"""Development settings for GQT Student Portal."""

from .base import *  # noqa: F403
from .base import BASE_DIR, INSTALLED_APPS, MIDDLEWARE, env

DEBUG = True
ENVIRONMENT = "development"

# Database Configuration
# Uses Supabase PostgreSQL when DATABASE_URL is configured,
# or defaults to local SQLite file for standalone local development when DATABASE_URL is empty.
raw_db_url = env("DATABASE_URL", default="").strip()
if raw_db_url:
    DATABASES = {"default": env.db_url_config(raw_db_url)}
else:
    DATABASES = {"default": env.db_url_config(f"sqlite:///{BASE_DIR / 'dev_db.sqlite3'}")}

if DATABASES["default"].get("ENGINE") == "django.db.backends.postgresql":
    DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=600)
    DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
    if "OPTIONS" not in DATABASES["default"]:
        DATABASES["default"]["OPTIONS"] = {}
    DATABASES["default"]["OPTIONS"].setdefault("sslmode", env("DB_SSLMODE", default="require"))

# Development Cache Configuration:
# Default to ultra-fast in-memory cache in development unless explicitly instructed to use Redis
USE_REDIS_CACHE = env.bool("USE_REDIS_CACHE", default=False)
if not USE_REDIS_CACHE:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "gqt-portal-dev-cache",
            "TIMEOUT": 300,
        }
    }

# Development Email Backend: Echoes emails to console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Development CORS configuration
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
)
CORS_ALLOW_CREDENTIALS = True

# Development In-Memory Cache (avoids Redis socket timeouts during local development)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "gqt-portal-dev-cache",
    }
}

