"""Development settings for GQT Student Portal."""

from .base import *  # noqa: F403
from .base import BASE_DIR, INSTALLED_APPS, MIDDLEWARE, env

DEBUG = True
ENVIRONMENT = "development"

# Database Configuration
# Uses PostgreSQL when DATABASE_URL is configured (e.g. docker dev),
# or defaults to local SQLite file for standalone local development.
default_db = f"sqlite:///{BASE_DIR / 'dev_db.sqlite3'}"
DATABASES = {"default": env.db("DATABASE_URL", default=default_db)}

# Development Email Backend: Echoes emails to console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Development CORS configuration
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
)
CORS_ALLOW_CREDENTIALS = True
