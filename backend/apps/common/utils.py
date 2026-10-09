import secrets
from datetime import datetime, timezone
from typing import Any


def get_client_ip(request) -> str:
    """Extract real client IP address considering proxy headers."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        # First IP in the comma-separated list is the original client
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "127.0.0.1")


def mask_email(email: str | None) -> str:
    """Mask email for safe audit logging, e.g. a***o@example.com."""
    if not email or "@" not in email:
        return ""
    name, domain = email.split("@", 1)
    if len(name) <= 2:
        masked_name = name[0] + "*"
    else:
        masked_name = name[0] + "*" * (len(name) - 2) + name[-1]
    return f"{masked_name}@{domain}"


def mask_phone(phone: str | None) -> str:
    """Mask phone number for safe logging, e.g. +91*****4321."""
    if not phone or len(phone) < 4:
        return ""
    return (
        phone[:3] + "*" * (len(phone) - 7) + phone[-4:]
        if len(phone) >= 7
        else phone[:2] + "***"
    )


def generate_secure_numeric_code(length: int = 6) -> str:
    """Generate cryptographically secure numeric OTP of fixed length."""
    return "".join(str(secrets.randbelow(10)) for _ in range(length))


def generate_secure_token(nbytes: int = 32) -> str:
    """Generate URL-safe cryptographic token."""
    return secrets.token_urlsafe(nbytes)


def format_datetime_iso(dt: datetime | None) -> str | None:
    """Format datetime object into standard ISO 8601 UTC string."""
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert value to integer with default fallback."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert value to float with default fallback."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
