#!/usr/bin/env python3
##############################################################################
# /tests/utility_functions_tests.py - Tests for Unicore utilities            #
# Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.Info                #
#                                                                            #
# This file is part of UniCoreFW. You can redistribute it and/or modify      #
# it under the terms of the [BSD-3-Clause] as published by                   #
# the Free Software Foundation.                                              #
# You should have received a copy of the [BSD-3-Clause] license              #
# along with UniCoreFW. If not, see https://www.gnu.org/licenses/.           #
##############################################################################

import unittest
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from unicorefw import UniCoreFW  # Now you can import Unicore as usual


class TestUnicoreUtilities(unittest.TestCase):
    def test_compress_decompress(self):
        original = "aaabbbbccddaaa"
        compressed = UniCoreFW.compress(original)
        # Basic check => run-length encoded but max of 9 in a chunk
        # Example: "3a4b2c2d3a", etc. (Exact format depends on your code.)
        self.assertNotEqual(compressed, original, "Should compress repeated chars")

        round_trip = UniCoreFW.decompress(compressed)
        self.assertEqual(round_trip, original, "Decompressed should match original")

    def test_compress_empty(self):
        self.assertEqual(UniCoreFW.compress(""), "")

    def test_decompress_empty(self):
        self.assertEqual(UniCoreFW.decompress(""), "")

    def test_compress_multi_digit_counts(self):
        # If the string has more than 9 consecutive same chars, the code loops them in blocks of 9
        big_string = "aaaaaaaaaaaa"  # 12 'a'
        compressed = UniCoreFW.compress(big_string)
        # Should produce something like "9a3a" 
        self.assertIn("9a", compressed)
        self.assertIn("3a", compressed)
        decompressed = UniCoreFW.decompress(compressed)
        self.assertEqual(decompressed, big_string)
            
    def test_chain(self):
        result = (
            UniCoreFW.chain([1, 2, 3])
            .map(lambda x: x * 2)
            .filter(lambda x: x > 2)
            .value()
        )
        self.assertEqual(result, [4, 6])

    def test_constant(self):
        const_func = UniCoreFW.constant(42)
        self.assertEqual(const_func(), 42)

    def test_escape(self):
        self.assertEqual(
            UniCoreFW.escape("<div>"), "&lt;div&gt;", "Should escape HTML entities"
        )

    def test_identity(self):
        self.assertEqual(
            UniCoreFW.identity(5),
            5,
            "Identity function should return the same value passed to it",
        )

    def test_iteratee(self):
        func = UniCoreFW.iteratee(lambda x: x * 2)
        self.assertEqual(func(3), 6, "Should return a valid function from iteratee")

    def test_mixin(self):
        def custom_method(x):
            return x * 2

        UniCoreFW.mixin({"custom_method": custom_method})
        self.assertTrue(
            hasattr(UniCoreFW, "custom_method"),
            "Unicore should have the custom method after mixin",
        )
        self.assertEqual(
            UniCoreFW.custom_method(3), 6, "Custom method should function correctly"
        )

    def test_noop(self):
        self.assertIsNone(UniCoreFW.noop(), "Noop should return None")

    def test_now(self):
        import time

        before = int(time.time() * 1000)
        now = UniCoreFW.now()
        after = int(time.time() * 1000)
        self.assertTrue(before <= now <= after, "Should return the current timestamp")

    def test_random(self):
        result = UniCoreFW.random(1, 10)
        self.assertTrue(1 <= result <= 10)

    def test_result(self):
        obj = {"name": "Alice", "greet": lambda greeting: f"{greeting}, {obj['name']}!"}
        self.assertEqual(
            UniCoreFW.result(obj, "name"), "Alice", "Should return the property value"
        )
        self.assertEqual(
            UniCoreFW.result(obj, "greet", "Hello"),
            "Hello, Alice!",
            "Should invoke the function with arguments",
        )

    def test_template(self):
        template = "Name: <%= name %>, Age: <%= age %>"
        context = {"name": "Alice", "age": 25}
        result = UniCoreFW.template(template, context)
        self.assertEqual(
            result, "Name: Alice, Age: 25", "Template should interpolate correctly"
        )

    def test_times(self):
        self.assertEqual(
            UniCoreFW.times(3, lambda i: i * 2),
            [0, 2, 4],
            "Should repeat the function call 3 times",
        )

    def test_unescape(self):
        self.assertEqual(
            UniCoreFW.unescape("&lt;div&gt;"), "<div>", "Should unescape HTML entities"
        )

    def test_unique_id(self):
        id1 = UniCoreFW.unique_id()
        id2 = UniCoreFW.unique_id()
        self.assertNotEqual(id1, id2, "Unique IDs should not be the same")

    def test_values(self):
        result = UniCoreFW.values({"a": 1, "b": 2})
        self.assertEqual(result, [1, 2])


if __name__ == "__main__":
    unittest.main()
