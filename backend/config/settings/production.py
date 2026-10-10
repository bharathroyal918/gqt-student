"""Production settings for GQT Student Portal."""

from .base import *
from .base import env

DEBUG = False
ENVIRONMENT = "production"

ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=env.list(
        "ALLOWED_HOSTS",
        default=[
            "localhost",
            "127.0.0.1",
            "backend",
            ".onrender.com",
            "gqt-student.onrender.com",
            "gqt-student-portal-backend.onrender.com",
        ],
    ),
)
render_hostname = env("RENDER_EXTERNAL_HOSTNAME", default="").strip()
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)
if ".onrender.com" not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(".onrender.com")

for trusted_origin in ["https://*.vercel.app", "https://*.onrender.com"]:
    if trusted_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(trusted_origin)


# Database Configuration (Supabase PostgreSQL / Render PostgreSQL)
raw_db_url = (
    env("DATABASE_URL", default="").strip()
    or env("DJANGO_DATABASE_URL", default="").strip()
)
if raw_db_url:
    DATABASES = {"default": env.db_url_config(raw_db_url)}
    if DATABASES["default"].get("ENGINE") == "django.db.backends.postgresql":
        DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=600)
        DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
        if "OPTIONS" not in DATABASES["default"]:
            DATABASES["default"]["OPTIONS"] = {}
        DATABASES["default"]["OPTIONS"].setdefault(
            "sslmode", env("DB_SSLMODE", default="require")
        )
else:
    # Fallback to base or local SQLite if running build checks without database attached
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "prod_db.sqlite3",
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
            "KEY_PREFIX": "gqt_portal_prod",
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "prod-locmem-cache",
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
