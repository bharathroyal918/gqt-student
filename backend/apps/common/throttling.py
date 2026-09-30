from rest_framework.throttling import ScopedRateThrottle


class HealthCheckThrottle(ScopedRateThrottle):
    """Rate limit specifically for health probe endpoints to protect against DDoS."""

    scope = "health"


class OTPRateThrottle(ScopedRateThrottle):
    """Strict rate limit for OTP generation and verification requests."""

    scope = "otp"


class SubmissionRateThrottle(ScopedRateThrottle):
    """Rate limit for code execution submissions per student."""

    scope = "submissions"


class AIRateThrottle(ScopedRateThrottle):
    """Rate limit for external AI LLM tutor requests per student."""

    scope = "ai"
