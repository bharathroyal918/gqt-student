"""Tests for production database, cache configuration enforcement, and system checks."""

import os
import runpy
from unittest import mock

import environ
import pytest
from django.core.checks import Error
from django.core.exceptions import ImproperlyConfigured
from django.test import override_settings

from apps.common.checks import check_production_cache, check_production_database


class TestProductionConfiguration:
    """Validate production settings fail fast on missing PostgreSQL or Redis."""

    def test_missing_database_url_raises_improperly_configured(self):
        with mock.patch.object(environ.Env, "read_env"):
            with mock.patch.dict(
                os.environ,
                {"DATABASE_URL": "", "DJANGO_DATABASE_URL": "", "REDIS_URL": "redis://127.0.0.1:6379/0"},
            ):
                with pytest.raises(ImproperlyConfigured) as exc_info:
                    runpy.run_module("config.settings.production")
                msg = str(exc_info.value)
                assert "requires a configured Supabase database connection" in msg
                assert "Neither 'DATABASE_URL' nor 'DJANGO_DATABASE_URL'" in msg

    def test_sqlite_url_in_production_raises_improperly_configured(self):
        with mock.patch.object(environ.Env, "read_env"):
            with mock.patch.dict(
                os.environ,
                {
                    "DATABASE_URL": "sqlite:///prod_db.sqlite3",
                    "DJANGO_DATABASE_URL": "",
                    "REDIS_URL": "redis://127.0.0.1:6379/0",
                },
            ):
                with pytest.raises(ImproperlyConfigured) as exc_info:
                    runpy.run_module("config.settings.production")
                msg = str(exc_info.value)
                assert "does not allow a local SQLite database" in msg

    def test_missing_redis_url_raises_improperly_configured(self):
        with mock.patch.object(environ.Env, "read_env"):
            with mock.patch.dict(
                os.environ,
                {
                    "DATABASE_URL": "postgresql://test_user:test_pass@aws-db.supabase.com:5432/postgres",
                    "DJANGO_DATABASE_URL": "",
                    "REDIS_URL": "",
                },
            ):
                with pytest.raises(ImproperlyConfigured) as exc_info:
                    runpy.run_module("config.settings.production")
                msg = str(exc_info.value)
                assert "requires a configured shared Redis cache" in msg
                assert "'REDIS_URL' environment variable is not set" in msg

    def test_production_configuration_configures_postgres_and_redis(self):
        with mock.patch.object(environ.Env, "read_env"):
            with mock.patch.dict(
                os.environ,
                {
                    "DATABASE_URL": "postgresql://test_user:test_pass@aws-db.supabase.com:5432/postgres",
                    "DJANGO_DATABASE_URL": "",
                    "REDIS_URL": "redis://127.0.0.1:6379/0",
                },
            ):
                prod_conf = runpy.run_module("config.settings.production")

                # Verify database configuration
                assert prod_conf["DATABASES"]["default"]["ENGINE"] == "django.db.backends.postgresql"
                assert prod_conf["DATABASES"]["default"]["CONN_HEALTH_CHECKS"] is True
                assert prod_conf["DATABASES"]["default"]["OPTIONS"]["sslmode"] == "require"

                # Verify cache configuration
                assert prod_conf["CACHES"]["default"]["BACKEND"] == "django_redis.cache.RedisCache"
                assert prod_conf["CACHES"]["default"]["LOCATION"] == "redis://127.0.0.1:6379/0"
                # IGNORE_EXCEPTIONS must be False in production to fail securely on Redis outage
                assert prod_conf["CACHES"]["default"]["OPTIONS"]["IGNORE_EXCEPTIONS"] is False

    def test_production_configuration_does_not_silently_select_sqlite_or_locmem(self):
        with mock.patch.object(environ.Env, "read_env"):
            with mock.patch.dict(
                os.environ,
                {
                    "DATABASE_URL": "postgresql://test_user:test_pass@aws-db.supabase.com:5432/postgres",
                    "REDIS_URL": "redis://127.0.0.1:6379/0",
                },
            ):
                prod_conf = runpy.run_module("config.settings.production")
                assert "sqlite" not in prod_conf["DATABASES"]["default"]["ENGINE"].lower()
                assert "locmem" not in prod_conf["CACHES"]["default"]["BACKEND"].lower()

    def test_unsupported_database_engine_in_production_raises_improperly_configured(self):
        with mock.patch.object(environ.Env, "read_env"):
            with mock.patch.dict(
                os.environ,
                {
                    "DATABASE_URL": "mysql://db_user:db_pass@mysql-host.internal:3306/db",
                    "DJANGO_DATABASE_URL": "",
                    "REDIS_URL": "redis://127.0.0.1:6379/0",
                },
            ):
                with pytest.raises(ImproperlyConfigured) as exc_info:
                    runpy.run_module("config.settings.production")
                msg = str(exc_info.value)
                assert "requires a managed Supabase PostgreSQL database connection" in msg
                assert "mysql-host" not in msg
                assert "db_pass" not in msg

    def test_production_prohibits_redis_ignore_exceptions_true(self):
        with mock.patch.object(environ.Env, "read_env"):
            with mock.patch.dict(
                os.environ,
                {
                    "DATABASE_URL": "postgresql://test_user:test_pass@aws-db.supabase.com:5432/postgres",
                    "REDIS_URL": "redis://127.0.0.1:6379/0",
                    "REDIS_IGNORE_EXCEPTIONS": "True",
                },
            ):
                with pytest.raises(ImproperlyConfigured) as exc_info:
                    runpy.run_module("config.settings.production")
                msg = str(exc_info.value)
                assert "prohibits REDIS_IGNORE_EXCEPTIONS=True" in msg

    def test_production_cors_and_csrf_hardened(self):
        with mock.patch.object(environ.Env, "read_env"):
            with mock.patch.dict(
                os.environ,
                {
                    "DATABASE_URL": "postgresql://test_user:test_pass@aws-db.supabase.com:5432/postgres",
                    "REDIS_URL": "redis://127.0.0.1:6379/0",
                },
            ):
                prod_conf = runpy.run_module("config.settings.production")
                assert prod_conf["CORS_ALLOW_ALL_ORIGINS"] is False
                assert prod_conf["CORS_ALLOWED_ORIGIN_REGEXES"] == []
                assert "http://127.0.0.1:4173" in prod_conf["CORS_ALLOWED_ORIGINS"]
                assert "http://localhost:4173" in prod_conf["CORS_ALLOWED_ORIGINS"]
                assert "https://gqt-student.onrender.com" in prod_conf["CORS_ALLOWED_ORIGINS"]
                assert "http://malicious.example.com" not in prod_conf["CORS_ALLOWED_ORIGINS"]
                for origin in prod_conf["CSRF_TRUSTED_ORIGINS"]:
                    assert "*" not in origin

    def test_production_cors_preview_toggle(self):
        with mock.patch.object(environ.Env, "read_env"):
            with mock.patch.dict(
                os.environ,
                {
                    "DATABASE_URL": "postgresql://test_user:test_pass@aws-db.supabase.com:5432/postgres",
                    "REDIS_URL": "redis://127.0.0.1:6379/0",
                    "CORS_ALLOWED_ORIGINS": "https://gqt-student.onrender.com",
                    "ALLOW_LOCAL_PREVIEW_CORS": "False",
                },
            ):
                prod_conf = runpy.run_module("config.settings.production")
                assert "https://gqt-student.onrender.com" in prod_conf["CORS_ALLOWED_ORIGINS"]
                assert "http://127.0.0.1:4173" not in prod_conf["CORS_ALLOWED_ORIGINS"]

    def test_production_allowed_hosts_rejects_broad_subdomains(self):
        with mock.patch.object(environ.Env, "read_env"):
            with mock.patch.dict(
                os.environ,
                {
                    "DATABASE_URL": "postgresql://test_user:test_pass@aws-db.supabase.com:5432/postgres",
                    "REDIS_URL": "redis://127.0.0.1:6379/0",
                    "DJANGO_ALLOWED_HOSTS": "gqt-student.onrender.com,.onrender.com,*.vercel.app,myportal.com",
                },
            ):
                prod_conf = runpy.run_module("config.settings.production")
                assert ".onrender.com" not in prod_conf["ALLOWED_HOSTS"]
                assert "*.vercel.app" not in prod_conf["ALLOWED_HOSTS"]
                assert "myportal.com" in prod_conf["ALLOWED_HOSTS"]



class TestProductionSystemChecks:
    """Validate Django system checks for production cache and database."""

    def test_system_check_reports_locmem_cache_in_production(self):
        with override_settings(
            ENVIRONMENT="production",
            CACHES={
                "default": {
                    "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
                    "OPTIONS": {"IGNORE_EXCEPTIONS": False},
                }
            },
        ):
            errors = check_production_cache(None)
            error_ids = [e.id for e in errors]
            assert "common.E001" in error_ids

    def test_system_check_reports_ignore_exceptions_true_in_production(self):
        with override_settings(
            ENVIRONMENT="production",
            CACHES={
                "default": {
                    "BACKEND": "django_redis.cache.RedisCache",
                    "OPTIONS": {"IGNORE_EXCEPTIONS": True},
                }
            },
        ):
            errors = check_production_cache(None)
            error_ids = [e.id for e in errors]
            assert "common.E002" in error_ids

    def test_system_check_passes_for_secure_production_cache(self):
        with override_settings(
            ENVIRONMENT="production",
            CACHES={
                "default": {
                    "BACKEND": "django_redis.cache.RedisCache",
                    "OPTIONS": {"IGNORE_EXCEPTIONS": False},
                }
            },
        ):
            errors = check_production_cache(None)
            assert len(errors) == 0

    def test_system_check_reports_sqlite_in_production(self):
        with override_settings(
            ENVIRONMENT="production",
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3"}},
        ):
            errors = check_production_database(None)
            error_ids = [e.id for e in errors]
            assert "common.E003" in error_ids

    def test_system_check_reports_unsupported_engine_in_production(self):
        with override_settings(
            ENVIRONMENT="production",
            DATABASES={"default": {"ENGINE": "django.db.backends.mysql"}},
        ):
            errors = check_production_database(None)
            error_ids = [e.id for e in errors]
            assert "common.E003" in error_ids

    def test_system_check_passes_for_postgresql_in_production(self):
        with override_settings(
            ENVIRONMENT="production",
            DATABASES={"default": {"ENGINE": "django.db.backends.postgresql"}},
        ):
            errors = check_production_database(None)
            assert len(errors) == 0

    def test_system_checks_inactive_in_test_environment(self):
        with override_settings(
            ENVIRONMENT="test",
            CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3"}},
        ):
            assert len(check_production_cache(None)) == 0
            assert len(check_production_database(None)) == 0

    def test_system_checks_do_not_expose_credentials_or_urls(self):
        with override_settings(
            ENVIRONMENT="production",
            CACHES={"default": {"BACKEND": "locmem", "OPTIONS": {"IGNORE_EXCEPTIONS": True}}},
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3"}},
        ):
            all_errors = check_production_cache(None) + check_production_database(None)
            for err in all_errors:
                assert "password" not in err.msg.lower()
                assert "secret" not in err.msg.lower()
                assert "postgres://" not in err.msg.lower()
                assert "redis://" not in err.msg.lower()
