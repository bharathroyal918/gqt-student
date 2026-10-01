"""Supabase client helper and integration utilities for GQT Student Portal."""

import logging
from functools import lru_cache
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    from supabase import Client, create_client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    Client = None  # type: ignore
    create_client = None  # type: ignore


@lru_cache(maxsize=1)
def get_supabase_client() -> Optional["Client"]:
    """Returns the standard Supabase client initialized with the anonymous/public key.
    Returns None if SUPABASE_URL or SUPABASE_ANON_KEY is not configured.
    """
    if not SUPABASE_AVAILABLE:
        logger.warning("Supabase package is not installed.")
        return None

    url = getattr(settings, "SUPABASE_URL", "") or ""
    key = getattr(settings, "SUPABASE_ANON_KEY", "") or ""

    if not url or not key:
        return None

    try:
        return create_client(url, key)
    except Exception as exc:
        logger.error(f"Failed to initialize Supabase client: {exc}")
        return None


@lru_cache(maxsize=1)
def get_supabase_admin_client() -> Optional["Client"]:
    """Returns the Supabase client initialized with the privileged SERVICE_ROLE_KEY.
    Used for administrative backend operations (bypasses Row-Level Security).
    Returns None if SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY is not configured.
    """
    if not SUPABASE_AVAILABLE:
        logger.warning("Supabase package is not installed.")
        return None

    url = getattr(settings, "SUPABASE_URL", "") or ""
    service_key = (
        getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")
        or getattr(settings, "SUPABASE_SERVICE_KEY", "")
        or ""
    )

    if not url or not service_key:
        return None

    try:
        return create_client(url, service_key)
    except Exception as exc:
        logger.error(f"Failed to initialize Supabase admin client: {exc}")
        return None
