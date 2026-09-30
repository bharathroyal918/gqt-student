from django.test import SimpleTestCase

from apps.common.utils import (
    generate_secure_numeric_code,
    generate_secure_token,
    mask_email,
    mask_phone,
    safe_float,
    safe_int,
)


class CommonUtilsTests(SimpleTestCase):
    """Test suite for reusable utility functions."""

    def test_mask_email(self):
        self.assertEqual(mask_email("student@gqt.local"), "s*****t@gqt.local")
        self.assertEqual(mask_email("a@b.com"), "a*@b.com")
        self.assertEqual(mask_email(""), "")
        self.assertEqual(mask_email(None), "")

    def test_mask_phone(self):
        self.assertEqual(mask_phone("+919876543210"), "+91******3210")
        self.assertEqual(mask_phone("12"), "")
        self.assertEqual(mask_phone(None), "")

    def test_generate_secure_numeric_code(self):
        code = generate_secure_numeric_code(6)
        self.assertEqual(len(code), 6)
        self.assertTrue(code.isdigit())

    def test_generate_secure_token(self):
        token = generate_secure_token(16)
        self.assertTrue(len(token) >= 16)

    def test_safe_int(self):
        self.assertEqual(safe_int("42"), 42)
        self.assertEqual(safe_int("invalid", default=10), 10)
        self.assertEqual(safe_int(None, default=0), 0)

    def test_safe_float(self):
        self.assertEqual(safe_float("3.14"), 3.14)
        self.assertEqual(safe_float("invalid", default=1.0), 1.0)
