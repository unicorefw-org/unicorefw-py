# tests/test_security.py

import unittest
import sys
import os
import time
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from unicorefw import (
    RateLimiter,
    SecurityError,
    InputValidationError,
    AuthorizationError,
    SanitizationError,
    validate_type,
    validate_callable,
    sanitize_string,
    AuditLogger,
)


class TestSecurity(unittest.TestCase):
    def test_rate_limiter(self):
        limiter = RateLimiter(max_calls=2, time_window=1)  # 2 calls per 1 second
        # First two enters should pass
        with limiter:
            pass
        with limiter:
            pass
        # Third enter within the same second => raises SecurityError
        with self.assertRaises(SecurityError):
            with limiter:
                pass

        # Wait for time window to expire
        time.sleep(1.1)
        # Should reset now
        with limiter:
            pass  # No error

    def test_audit_logger(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            log_path = tf.name
        logger = AuditLogger(log_file=log_path)
        logger.log("LOGIN", "User123 logged in.")
        with open(log_path, "r") as f:
            content = f.read()
        self.assertIn("LOGIN: User123 logged in.", content)
        os.remove(log_path)

    def test_validate_type(self):
        self.assertEqual(validate_type(123, int, "my_param"), 123)
        with self.assertRaises(InputValidationError):
            validate_type("abc", int)

    def test_validate_callable(self):
        def myfunc():
            pass

        self.assertEqual(validate_callable(myfunc), myfunc)
        with self.assertRaises(InputValidationError):
            validate_callable("not a function")

    def test_sanitize_string(self):
        good_str = sanitize_string(" hello ", max_length=10, allowed_chars="a-zA-Z ")
        self.assertEqual(good_str, "hello")

        # Check length violation
        with self.assertRaises(SanitizationError):
            sanitize_string("1234567890abc", max_length=5)

        # Check invalid characters
        with self.assertRaises(SanitizationError):
            sanitize_string("abc!", allowed_chars="a-z")

    def test_custom_security_errors(self):
        # Just ensure they can be raised/caught
        with self.assertRaises(AuthorizationError):
            raise AuthorizationError("Not allowed.")
        with self.assertRaises(SanitizationError):
            raise SanitizationError("Invalid data.")


if __name__ == "__main__":
    unittest.main()
