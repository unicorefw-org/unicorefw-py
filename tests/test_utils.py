#!/usr/bin/env python3
##############################################################################
# /tests/test_utils.py - Tests for Unicore utilities            #
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
import unittest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from unicorefw import UniCoreFW, _  # Now you can import Unicore as usual
from unicorefw.security import ResourceLimitError
from unicorefw.utils import decompress, memoize, mixin
from unicorefw.utils import now as now_impl


class TestUnicoreUtilities(unittest.TestCase):
    def test_chain(self):
        result = (
            _.chain([1, 2, 3])
            .map(lambda x: x * 2)
            .filter(lambda x: x > 2)
            .value()
        )
        self.assertEqual(result, [4, 6])

    def test_constant(self):
        const_func = _.constant(42)
        self.assertEqual(const_func(), 42)

    def test_escape(self):
        self.assertEqual(
            _.escape("<div>"), "&lt;div&gt;", "Should escape HTML entities"
        )

    def test_identity(self):
        self.assertEqual(
            _.identity(5),
            5,
            "Identity function should return the same value passed to it",
        )

    def test_iteratee(self):
        func = _.iteratee(lambda x: x * 2)
        self.assertEqual(func(3), 6, "Should return a valid function from iteratee")

    def test_mixin(self):
        def custom_method(x):
            return x * 2

        _.mixin({"custom_method": custom_method})
        self.assertTrue(
            hasattr(UniCoreFW, "custom_method"),
            "Unicore should have the custom method after mixin",
        )
        self.assertEqual(
            UniCoreFW.custom_method(3), 6, "Custom method should function correctly"
        )
        mixin({"ignored_value": 42})
        self.assertFalse(hasattr(UniCoreFW, "ignored_value"))

    def test_memoize_expiry_and_decompress_output_boundary(self):
        clock = [0.0]
        calls = []

        def calculate(value):
            calls.append(value)
            return value

        cached = memoize(calculate, ttl_seconds=1, clock=lambda: clock[0])
        self.assertEqual(cached(1), 1)
        clock[0] = 2
        self.assertEqual(cached(1), 1)
        self.assertEqual(calls, [1, 1])
        with self.assertRaises(ResourceLimitError):
            decompress("2a", max_output_length=1)
        with self.assertRaises(ResourceLimitError):
            decompress("1a1b", max_output_length=1)

    def test_memoize_expiry_after_recomputation_and_digit_only_input(self):
        clock = [0.0]

        def calculate(value):
            if value == 1:
                clock[0] = 2.0
            return value

        cached = memoize(calculate, ttl_seconds=1, clock=lambda: clock[0])
        self.assertEqual(cached(1), 1)
        self.assertEqual(cached(1), 1)
        self.assertEqual(decompress("123"), "")

    def test_noop(self):
        self.assertIsNone(_.noop(), "Noop should return None")

    def test_now(self):
        import time

        before = int(time.time() * 1000)
        now = _.now()
        after = int(time.time() * 1000)
        self.assertTrue(before <= now <= after, "Should return the current timestamp")
        self.assertIsInstance(now_impl(), int)

    def test_random(self):
        result = _.random(1, 10)
        self.assertTrue(1 <= result <= 10)

    def test_result(self):
        obj = {"name": "Alice", "greet": lambda greeting: f"{greeting}, {obj['name']}!"}
        self.assertEqual(
            _.result(obj, "name"), "Alice", "Should return the property value"
        )
        self.assertEqual(
            _.result(obj, "greet", "Hello"),
            "Hello, Alice!",
            "Should invoke the function with arguments",
        )

    def test_template(self):
        template = "Name: <%= name %>, Age: <%= age %>"
        context = {"name": "Alice", "age": 25}
        result = _.template(template, context)
        self.assertEqual(
            result, "Name: Alice, Age: 25", "Template should interpolate correctly"
        )

    def test_times(self):
        self.assertEqual(
            _.times(3, lambda i: i * 2),
            [0, 2, 4],
            "Should repeat the function call 3 times",
        )

    def test_unescape(self):
        self.assertEqual(
            _.unescape("&lt;div&gt;"), "<div>", "Should unescape HTML entities"
        )

    def test_unique_id(self):
        id1 = _.unique_id()
        id2 = _.unique_id()
        self.assertNotEqual(id1, id2, "Unique IDs should not be the same")

    def test_values(self):
        result = _.values({"a": 1, "b": 2})
        self.assertEqual(result, [1, 2])


if __name__ == "__main__":
    unittest.main()
