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
            "gqt-student.onrender.com",
            "gqt-student-portal-backend.onrender.com",
        ],
    ),
)
render_hostname = env("RENDER_EXTERNAL_HOSTNAME", default="").strip()
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)
ALLOWED_HOSTS = [
    h for h in ALLOWED_HOSTS
    if not h.startswith(".") and not h.startswith("*") and h != "*" and h not in (".onrender.com", ".vercel.app")
]

# Hardened Production CORS & CSRF: Strict explicit origins without wildcards
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGIN_REGEXES = []

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "https://gqt-student.onrender.com",
        "https://gqt-student-portal-backend.onrender.com",
        "http://127.0.0.1:4173",
        "http://localhost:4173",
    ],
)

# Ensure verified production service origins are always present
for prod_origin in [
    "https://gqt-student.onrender.com",
    "https://gqt-student-portal-backend.onrender.com",
]:
    if prod_origin not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(prod_origin)

# When local preview access to the deployed API is allowed, ensure exact preview origins
# are accepted even if CORS_ALLOWED_ORIGINS environment variable was configured with only prod domains
if env.bool("ALLOW_LOCAL_PREVIEW_CORS", default=True):
    for preview_origin in ["http://127.0.0.1:4173", "http://localhost:4173"]:
        if preview_origin not in CORS_ALLOWED_ORIGINS:
            CORS_ALLOWED_ORIGINS.append(preview_origin)
else:
    CORS_ALLOWED_ORIGINS = [
        o for o in CORS_ALLOWED_ORIGINS if o not in ("http://127.0.0.1:4173", "http://localhost:4173")
    ]

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "https://gqt-student.onrender.com",
        "https://gqt-student-portal-backend.onrender.com",
    ],
)

frontend_url = env("FRONTEND_URL", default="").strip()
if frontend_url:
    if frontend_url not in CORS_ALLOWED_ORIGINS:
        CORS_ALLOWED_ORIGINS.append(frontend_url)
    if frontend_url not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(frontend_url)

CSRF_TRUSTED_ORIGINS = [
    origin for origin in CSRF_TRUSTED_ORIGINS if "*" not in origin
]


from django.core.exceptions import ImproperlyConfigured


# Database Configuration (Supabase PostgreSQL / Render PostgreSQL)
raw_db_url = (
    env("DATABASE_URL", default="").strip()
    or env("DJANGO_DATABASE_URL", default="").strip()
)
if not raw_db_url:
    raise ImproperlyConfigured(
        "Production environment requires a configured Supabase database connection. "
        "Neither 'DATABASE_URL' nor 'DJANGO_DATABASE_URL' environment variable is set."
    )

DATABASES = {"default": env.db_url_config(raw_db_url)}
engine = DATABASES["default"].get("ENGINE", "")
if "sqlite" in engine.lower():
    raise ImproperlyConfigured(
        "Production environment does not allow a local SQLite database. "
        "A managed Supabase PostgreSQL database connection is required."
    )
if engine != "django.db.backends.postgresql":
    raise ImproperlyConfigured(
        "Production environment requires a managed Supabase PostgreSQL database connection "
        "('django.db.backends.postgresql'). Unsupported database engine configured."
    )

DATABASES["default"]["CONN_MAX_AGE"] = env.int("CONN_MAX_AGE", default=600)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
if "OPTIONS" not in DATABASES["default"]:
    DATABASES["default"]["OPTIONS"] = {}
DATABASES["default"]["OPTIONS"].setdefault(
    "sslmode", env("DB_SSLMODE", default="require")
)

# Shared Cache Configuration (Redis)
redis_url = env("REDIS_URL", default="").strip()
if not redis_url:
    raise ImproperlyConfigured(
        "Production environment requires a configured shared Redis cache for rate limiting "
        "and security controls. The 'REDIS_URL' environment variable is not set."
    )

if env.bool("REDIS_IGNORE_EXCEPTIONS", default=False):
    raise ImproperlyConfigured(
        "Production environment prohibits REDIS_IGNORE_EXCEPTIONS=True. "
        "Rate limiting and security controls must fail securely on cache failure."
    )

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": redis_url,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": False,
        },
        "KEY_PREFIX": "gqt_portal_prod",
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
