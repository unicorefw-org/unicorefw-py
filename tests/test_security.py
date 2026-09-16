#!/usr/bin/env python3
##############################################################################
# /tests/test_security.py - Tests for Unicore utilities            #
# Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.Info                #
#                                                                            #
# This file is part of UniCoreFW. You can redistribute it and/or modify      #
# it under the terms of the [BSD-3-Clause] as published by                   #
# the Free Software Foundation.                                              #
# You should have received a copy of the [BSD-3-Clause] license              #
# along with UniCoreFW. If not, see https://www.gnu.org/licenses/.           #
##############################################################################

import os
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unicorefw import (
    AuditLogger,
    AuthorizationError,
    InputValidationError,
    RateLimiter,
    SanitizationError,
    SecurityError,
    sanitize_string,
    validate_callable,
    validate_type,
)


class TestSecurity(unittest.TestCase):
    def test_rate_limiter(self):
        current_time = [0.0]
        limiter = RateLimiter(
            max_calls=2,
            time_window=1,
            clock=lambda: current_time[0],
        ) # type: ignore
        # First two enters should pass
        with limiter:
            pass
        with limiter:
            pass
        # Third enter within the same second => raises SecurityError
        with self.assertRaises(SecurityError), limiter: # type: ignore
            pass

        # The exact window boundary expires the older calls.
        current_time[0] = 1.0
        with limiter:
            pass  # No error

    def test_audit_logger(self):
        with tempfile.NamedTemporaryFile(delete=False) as tf:
            log_path = tf.name
        logger = AuditLogger(log_file=log_path) # type: ignore
        logger.log("LOGIN", "User123 logged in.")
        with open(log_path, "r") as f:
            content = f.read()
        self.assertIn("LOGIN: User123 logged in.", content)
        os.remove(log_path)

    def test_validate_type(self):
        self.assertEqual(validate_type(123, int, "my_param"), 123) # type: ignore
        with self.assertRaises(InputValidationError): # type: ignore
            validate_type("abc", int) # type: ignore

    def test_validate_callable(self):
        def myfunc():
            pass

        self.assertEqual(validate_callable(myfunc), myfunc) # type: ignore
        with self.assertRaises(InputValidationError): # type: ignore
            validate_callable("not a function") # type: ignore

    def test_sanitize_string(self):
        good_str = sanitize_string(" hello ", max_length=10, allowed_chars="a-zA-Z ") # type: ignore
        self.assertEqual(good_str, "hello")

        # Check length violation
        with self.assertRaises(SanitizationError): # type: ignore
            sanitize_string("value-is-too-long", max_length=5) # type: ignore

        # Check invalid characters
        with self.assertRaises(SanitizationError): # type: ignore
            sanitize_string("abc!", allowed_chars="a-z") # type: ignore

    def test_custom_security_errors(self):
        # Just ensure they can be raised/caught
        with self.assertRaises(AuthorizationError): # type: ignore
            raise AuthorizationError("Not allowed.") # type: ignore
        with self.assertRaises(SanitizationError): # type: ignore
            raise SanitizationError("Invalid data.") # type: ignore


if __name__ == "__main__":
    unittest.main()
