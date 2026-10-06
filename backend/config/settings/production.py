"""Production settings for GQT Student Portal."""

from .base import *  # noqa: F403
from .base import env

DEBUG = False
ENVIRONMENT = "production"

# Database Configuration (Supabase PostgreSQL / Render PostgreSQL)
raw_db_url = env("DATABASE_URL", default="").strip() or env("DJANGO_DATABASE_URL", default="").strip()
if raw_db_url:
    DATABASES = {
        "default": env.db_url_config(raw_db_url)
    }
    if DATABASES["default"].get("ENGINE") == "django.db.backends.postgresql":
        DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=0)
        DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
        if "OPTIONS" not in DATABASES["default"]:
            DATABASES["default"]["OPTIONS"] = {}
        DATABASES["default"]["OPTIONS"].setdefault("sslmode", env("DB_SSLMODE", default="require"))
else:
    # Fallback to base or local SQLite if running build checks without database attached
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "prod_db.sqlite3",
        }
    }

WHITENOISE_MANIFEST_STRICT = env.bool("WHITENOISE_MANIFEST_STRICT", default=False)

# Security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)

# Important when Django is behind HTTPS proxy / load balancer
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Production Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="smtp.sendgrid.net")
EMAIL_PORT = env.int("EMAIL_PORT", default=587)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="apikey")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env(
    "DEFAULT_FROM_EMAIL",
    default="Global Quality Technologies <no-reply@gqt.local>",
)
