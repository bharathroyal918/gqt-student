"""System checks for GQT Student Portal."""

from django.conf import settings
from django.core.checks import Error, Tags, register


@register(Tags.caches, Tags.security)
def check_production_cache(app_configs, **kwargs):
    """Ensure production environment requires and enforces shared Redis cache."""
    errors = []
    if getattr(settings, "ENVIRONMENT", "").lower() == "production":
        default_cache = getattr(settings, "CACHES", {}).get("default", {})
        backend = default_cache.get("BACKEND", "")

        if "redis" not in backend.lower() and "RedisCache" not in backend:
            errors.append(
                Error(
                    "Production requires a shared Redis cache backend to ensure rate limiting "
                    "and security controls function across processes.",
                    hint="Configure CACHES['default']['BACKEND'] to use django_redis.cache.RedisCache with REDIS_URL.",
                    id="common.E001",
                )
            )

        options = default_cache.get("OPTIONS", {})
        if options.get("IGNORE_EXCEPTIONS") is True:
            errors.append(
                Error(
                    "Production cache has IGNORE_EXCEPTIONS=True. A Redis outage could silently "
                    "bypass rate limiting and security controls.",
                    hint="Set IGNORE_EXCEPTIONS=False in cache OPTIONS to fail securely.",
                    id="common.E002",
                )
            )
    return errors


@register(Tags.database, Tags.security)
def check_production_database(app_configs, **kwargs):
    """Ensure production environment requires a managed PostgreSQL database and never SQLite or unsupported engines."""
    errors = []
    if getattr(settings, "ENVIRONMENT", "").lower() == "production":
        default_db = getattr(settings, "DATABASES", {}).get("default", {})
        engine = default_db.get("ENGINE", "")

        if engine != "django.db.backends.postgresql":
            errors.append(
                Error(
                    "Production environment requires a managed PostgreSQL database ('django.db.backends.postgresql').",
                    hint="Configure a managed Supabase PostgreSQL connection using DATABASE_URL or DJANGO_DATABASE_URL.",
                    id="common.E003",
                )
            )
    return errors
