from django.test import SimpleTestCase
from rest_framework import status
from rest_framework.exceptions import NotAuthenticated, ValidationError

from apps.common.exceptions import DomainException, ModuleLockedException, custom_exception_handler


class ExceptionHandlerTests(SimpleTestCase):
    """Test suite for standardized API exception handling and envelopes."""

    def test_domain_exception_handled(self):
        exc = DomainException("Invalid state transition.")
        context = {"request": None}
        response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.data
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "DOMAIN_ERROR")
        self.assertEqual(data["error"]["message"], "Invalid state transition.")
        self.assertIn("request_id", data["error"])
        self.assertIn("timestamp", data["meta"])

    def test_module_locked_exception(self):
        exc = ModuleLockedException()
        context = {"request": None}
        response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        data = response.data
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "MODULE_LOCKED")

    def test_validation_error_handled(self):
        exc = ValidationError({"email": ["Invalid email address."]})
        context = {"request": None}
        response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        data = response.data
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "INVALID")
        self.assertIn("email", data["error"]["details"])

    def test_unauthenticated_error_handled(self):
        exc = NotAuthenticated("Authentication credentials were not provided.")
        context = {"request": None}
        response = custom_exception_handler(exc, context)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        data = response.data
        self.assertFalse(data["success"])
        self.assertEqual(data["error"]["code"], "NOT_AUTHENTICATED")
