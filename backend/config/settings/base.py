"""Base settings for GQT Student Learning and Coding Assessment Platform."""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ENVIRONMENT=(str, "development"),
    TIMEZONE=(str, "Asia/Kolkata"),
    DJANGO_SECRET_KEY=(str, "django-insecure-change-in-production-stage-32-chars-min"),
)

# Read environment file from backend root or parent repo root
if (BASE_DIR / ".env").exists():
    environ.Env.read_env(str(BASE_DIR / ".env"), overwrite=True)
elif (BASE_DIR.parent / ".env").exists():
    environ.Env.read_env(str(BASE_DIR.parent / ".env"), overwrite=True)

SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default=env(
        "SECRET_KEY", default="django-insecure-change-in-production-stage-32-chars-min"
    ),
)
DEBUG = env("DEBUG")
ENVIRONMENT = env("ENVIRONMENT")

ALLOWED_HOSTS = env.list(
    "DJANGO_ALLOWED_HOSTS",
    default=env.list(
        "ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "backend", "*"]
    ),
)
render_hostname = env("RENDER_EXTERNAL_HOSTNAME", default="").strip()
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)

# ------------------------------------------------------------------------------
# APPLICATION DEFINITION
# ------------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.common.apps.CommonConfig",
    "apps.accounts.apps.AccountsConfig",
    "apps.students.apps.StudentsConfig",
    "apps.courses.apps.CoursesConfig",
    "apps.modules.apps.ModulesConfig",
    "apps.assignments.apps.AssignmentsConfig",
    "apps.execution.apps.ExecutionConfig",
    "apps.scoring.apps.ScoringConfig",
    "apps.leaderboard.apps.LeaderboardConfig",
    "apps.tasks.apps.TasksConfig",
    "apps.projects.apps.ProjectsConfig",
    "apps.ai_assistant.apps.AiAssistantConfig",
    "apps.notifications.apps.NotificationsConfig",
    "apps.analytics.apps.AnalyticsConfig",
    "apps.reports.apps.ReportsConfig",
    "apps.certificates.apps.CertificatesConfig",
    "apps.contact.apps.ContactConfig",
    "apps.placements.apps.PlacementsConfig",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ------------------------------------------------------------------------------
# MIDDLEWARE PIPELINE
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "apps.common.middleware.RequestIDMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

# ------------------------------------------------------------------------------
# USER MODEL & SECURE PASSWORD HASHING
# ------------------------------------------------------------------------------
AUTH_USER_MODEL = "accounts.User"

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ------------------------------------------------------------------------------
# INTERNATIONALIZATION & TIMEZONE
# ------------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = env("TIMEZONE", default="Asia/Kolkata")
USE_I18N = True
USE_TZ = True

# ------------------------------------------------------------------------------
# STATIC & MEDIA ASSETS
# ------------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------------------
# DJANGO REST FRAMEWORK (DRF)
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    # Authentication & Permissions
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    # API Versioning
    "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    "DEFAULT_VERSION": "v1",
    "ALLOWED_VERSIONS": ["v1"],
    "VERSION_PARAM": "version",
    # Filtering & Ordering
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    # Pagination
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 20,
    # Centralized Exception Handler
    "EXCEPTION_HANDLER": "apps.common.exceptions.custom_exception_handler",
    # Throttling Foundation
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "health": "120/minute",
        "otp": "5/minute",
        "submissions": "20/minute",
        "ai": "30/hour",
    },
    # OpenAPI Schema Documentation
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# ------------------------------------------------------------------------------
# JWT AUTHENTICATION (SIMPLE_JWT)
# ------------------------------------------------------------------------------
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(
        minutes=env.int("JWT_ACCESS_TOKEN_LIFETIME_MINUTES", default=15)
    ),
    "REFRESH_TOKEN_LIFETIME": timedelta(
        days=env.int("JWT_REFRESH_TOKEN_LIFETIME_DAYS", default=7)
    ),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": env("JWT_ALGORITHM", default="HS256"),
    "SIGNING_KEY": env("JWT_SIGNING_KEY", default=SECRET_KEY),
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

# ------------------------------------------------------------------------------
# CORS & CSRF CONFIGURATION
# ------------------------------------------------------------------------------
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=False)

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
)

CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https:\/\/.*\.vercel\.app$",
    r"^https:\/\/.*\.onrender\.com$",
]

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://*.onrender.com",
    ],
)
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-request-id",
]
CORS_EXPOSE_HEADERS = ["x-request-id", "content-range"]

# ------------------------------------------------------------------------------
# REDIS & CACHING
# ------------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL", default="redis://127.0.0.1:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,  # Prevent crash if Redis cache misses or blips in dev
            "SOCKET_CONNECT_TIMEOUT": 0.5,
            "SOCKET_TIMEOUT": 0.5,
        },
        "KEY_PREFIX": "gqt_portal",
    }
}

# ------------------------------------------------------------------------------
# CELERY & TASK INFRASTRUCTURE
# ------------------------------------------------------------------------------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/1")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://127.0.0.1:6379/2")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TIME_LIMIT = 300
CELERY_TASK_SOFT_TIME_LIMIT = 240
CELERY_TASK_QUEUES = {
    "code_execution": {"exchange": "code_execution", "routing_key": "code_execution"},
    "ai": {"exchange": "ai", "routing_key": "ai"},
    "notifications": {"exchange": "notifications", "routing_key": "notifications"},
    "reports": {"exchange": "reports", "routing_key": "reports"},
    "default": {"exchange": "default", "routing_key": "default"},
}
CELERY_TASK_DEFAULT_QUEUE = "default"

# ------------------------------------------------------------------------------
# OPENAPI / SPECTACULAR DOCUMENTATION
# ------------------------------------------------------------------------------
# SPECTACULAR_SETTINGS = {
#     "TITLE": "GQT Student Learning & Assessment API",
#     "DESCRIPTION": "Production-grade REST API backend for GQT Student Portal",
#     "VERSION": "1.0.0",
#     "SERVE_INCLUDE_SCHEMA": False,
#     "COMPONENT_SPLIT_REQUEST": True,
# }
SPECTACULAR_SETTINGS = {
    "TITLE": "GQT Student Learning & Assessment API",
    "DESCRIPTION": "Production-grade REST API backend for GQT Student Portal",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "ENUM_NAME_OVERRIDES": {
        "AttendanceStatusEnum": "apps.students.models.AttendanceRecord.AttendanceStatus",
        "CourseEnrollmentStatusEnum": "apps.courses.models.CourseEnrollment.EnrollmentStatus",
        "ContactInquiryStatusEnum": "apps.contact.models.ContactInquiry.InquiryStatus",
        "ProjectSubmissionStatusEnum": "apps.projects.models.ProjectSubmission.SubmissionStatus",
        "CodeSubmissionStatusEnum": "apps.assignments.models.CodeSubmission.SubmissionStatus",
        "ExecutionResultStatusEnum": "apps.assignments.models.ExecutionResult.ResultStatus",
        "PlacementDriveStatusEnum": "apps.placements.models.PlacementDrive.DriveStatus",
        "PlacementApplicationStatusEnum": "apps.placements.models.PlacementApplication.ApplicationStatus",
        "StudentModuleStatusEnum": "apps.modules.models.StudentModuleProgress.ModuleStatus",
        "ExportJobStatusEnum": "apps.analytics.models.ExportJob.JobStatus",
        "LoginStatusEnum": "apps.accounts.models.LoginActivity.LoginStatus",
    },
    "DISABLE_ERRORS_AND_WARNINGS": False,
}


# ------------------------------------------------------------------------------
# STRUCTURED LOGGING
# ------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_id": {
            "()": "apps.common.logging.RequestIDFilter",
        },
    },
    "formatters": {
        "structured_json": {
            "()": "apps.common.logging.StructuredJSONFormatter",
        },
        "standard_verbose": {
            "format": "[{asctime}] [{request_id}] {levelname} {name}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured_json" if not DEBUG else "standard_verbose",
            "filters": ["request_id"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": "DEBUG" if DEBUG else "INFO",
            "propagate": False,
        },
    },
}

# ------------------------------------------------------------------------------
# SUPABASE CONFIGURATION
# ------------------------------------------------------------------------------
SUPABASE_URL = env("SUPABASE_URL", default="")
SUPABASE_ANON_KEY = env("SUPABASE_ANON_KEY", default="")
SUPABASE_SERVICE_ROLE_KEY = env(
    "SUPABASE_SERVICE_ROLE_KEY",
    default=env("SUPABASE_SERVICE_KEY", default=""),
)
SUPABASE_STORAGE_BUCKET = env("SUPABASE_STORAGE_BUCKET", default="media")
