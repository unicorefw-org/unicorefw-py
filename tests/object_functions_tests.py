#!/usr/bin/env python3
##############################################################################
# /tests/object_functions_tests.py - Tests for Unicore objects               #
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


class TestUniCoreFWObjects(unittest.TestCase):
    def test_deep_copy(self):
        data = {
            "numbers": [1, 2, 3],
            "nested": {"x": 10, "y": [100, 101]},
        }
        copy_data = UniCoreFW.deep_copy(data)

        self.assertEqual(copy_data, data, "Deep-copied object should match original")
        self.assertIsNot(copy_data, data, "Should not be the same reference (dict)")
        self.assertIsNot(
            copy_data["numbers"], data["numbers"], "Inner list should also be copied"
        )
        self.assertIsNot(
            copy_data["nested"], data["nested"], "Nested dict should be copied"
        )
        self.assertIsNot(
            copy_data["nested"]["y"],
            data["nested"]["y"],
            "Nested list should be copied",
        )

    def test_all_keys(self):
        obj = {"a": 1, "b": 2, "c": 3}
        self.assertEqual(
            UniCoreFW.all_keys(obj),
            ["a", "b", "c"],
            "Should return all keys of the object",
        )

    def test_clone(self):
        obj = {"a": 1, "b": 2}
        cloned_obj = UniCoreFW.clone(obj)
        self.assertEqual(cloned_obj, obj, "Cloned object should match the original")
        self.assertIsNot(
            cloned_obj,
            obj,
            "Cloned object should not be the same instance as the original",
        )

    def test_create(self):
        proto = {"a": 1}
        new_obj = UniCoreFW.create(proto)
        self.assertEqual(
            new_obj["a"], 1, "Should create an object with the prototype properties"
        )

    def test_defaults(self):
        obj = {"a": 1}
        UniCoreFW.defaults(obj, {"a": 0, "b": 2})
        self.assertEqual(obj, {"a": 1, "b": 2})

    def test_extend(self):
        obj = {"a": 1}
        source = {"b": 2}
        self.assertEqual(
            UniCoreFW.extend(obj, source),
            {"a": 1, "b": 2},
            "Should extend the object with source properties",
        )

    def test_functions(self):
        obj = {"a": lambda: 1, "b": 2, "c": lambda: 3}
        self.assertEqual(
            UniCoreFW.functions(obj),
            ["a", "c"],
            "Should return names of all functions in the object",
        )

    def test_has(self):
        obj = {"a": 1}
        self.assertTrue(
            UniCoreFW.has(obj, "a"), "Should return True if the object has the key"
        )
        self.assertFalse(
            UniCoreFW.has(obj, "b"),
            "Should return False if the object does not have the key",
        )

    def test_invert(self):
        obj = {"a": 1, "b": 2}
        self.assertEqual(
            UniCoreFW.invert(obj),
            {1: "a", 2: "b"},
            "Should invert the keys and values of the object",
        )

    def test_is_arguments(self):
        def func(*args):
            return UniCoreFW.is_arguments(args)

        self.assertTrue(func(1, 2, 3), "Should return True for arguments object")

    def test_is_array_buffer(self):
        from array import array

        buffer = array("i", [1, 2, 3])
        self.assertTrue(
            UniCoreFW.is_array_buffer(buffer), "Should recognize array buffer"
        )

    def test_is_boolean(self):
        self.assertTrue(
            UniCoreFW.is_boolean(True), "True should be recognized as a boolean"
        )
        self.assertTrue(
            UniCoreFW.is_boolean(False), "False should be recognized as a boolean"
        )
        self.assertFalse(
            UniCoreFW.is_boolean(0), "0 should not be recognized as a boolean"
        )

    def test_is_data_view(self):
        buffer = memoryview(bytearray([1, 2, 3]))
        self.assertTrue(UniCoreFW.is_data_view(buffer), "Should recognize data view")

    def test_is_date(self):
        from datetime import datetime

        self.assertTrue(
            UniCoreFW.is_date(datetime.now()),
            "datetime object should be recognized as a date",
        )
        self.assertFalse(
            UniCoreFW.is_date("2024-01-01"), "String should not be recognized as a date"
        )

    def test_is_element(self):
        from xml.etree.ElementTree import Element

        element = Element("test")
        self.assertTrue(UniCoreFW.is_element(element), "Should recognize XML element")

    def test_is_empty(self):
        self.assertTrue(UniCoreFW.is_empty([]))
        self.assertTrue(UniCoreFW.is_empty({}))
        self.assertFalse(UniCoreFW.is_empty([1, 2]))

    def test_is_equal(self):
        obj1 = {"a": 1, "b": {"c": 2}}
        obj2 = {"a": 1, "b": {"c": 2}}
        self.assertTrue(
            UniCoreFW.is_equal(obj1, obj2), "Should recognize deeply equal objects"
        )

    def test_is_error(self):
        try:
            raise ValueError("Test error")
        except ValueError as e:
            self.assertTrue(
                UniCoreFW.is_error(e), "Exception should be recognized as an error"
            )
        self.assertFalse(
            UniCoreFW.is_error("Error"), "String should not be recognized as an error"
        )

    def test_is_finite(self):
        self.assertTrue(UniCoreFW.is_finite(100), "100 should be recognized as finite")
        self.assertFalse(
            UniCoreFW.is_finite(float("inf")),
            "Infinity should not be recognized as finite",
        )

    def test_is_function(self):
        self.assertTrue(
            UniCoreFW.is_function(lambda x: x),
            "Lambda should be recognized as a function",
        )
        self.assertFalse(
            UniCoreFW.is_function(5), "5 should not be recognized as a function"
        )

    def test_is_map(self):
        self.assertTrue(
            UniCoreFW.is_map({}), "Dictionary should be recognized as a map"
        )
        self.assertFalse(UniCoreFW.is_map([]), "List should not be recognized as a map")

    def test_is_match(self):
        self.assertTrue(UniCoreFW.is_match({"a": 1, "b": 2}, {"a": 1}))
        self.assertFalse(UniCoreFW.is_match({"a": 1, "b": 2}, {"a": 2}))

    def test_is_nan(self):
        self.assertTrue(
            UniCoreFW.is_nan(float("nan")), "NaN should be recognized as NaN"
        )
        self.assertFalse(UniCoreFW.is_nan(10), "10 should not be recognized as NaN")

    def test_is_null(self):
        self.assertTrue(UniCoreFW.is_null(None), "None should be recognized as null")
        self.assertFalse(UniCoreFW.is_null(0), "0 should not be recognized as null")

    def test_is_number(self):
        self.assertTrue(UniCoreFW.is_number(5), "5 should be recognized as a number")
        self.assertFalse(
            UniCoreFW.is_number("5"), '"5" should not be recognized as a number'
        )

    def test_is_object(self):
        self.assertTrue(
            UniCoreFW.is_object({}), "Should recognize a dictionary as an object"
        )
        self.assertFalse(
            UniCoreFW.is_object([]), "Should not recognize a list as an object"
        )

    def test_is_reg_exp(self):
        import re

        self.assertTrue(
            UniCoreFW.is_reg_exp(re.compile("abc")),
            "Regex object should be recognized as a regular expression",
        )
        self.assertFalse(
            UniCoreFW.is_reg_exp("abc"),
            "String should not be recognized as a regular expression",
        )

    def test_is_set(self):
        self.assertTrue(UniCoreFW.is_set(set()), "Set should be recognized as a set")
        self.assertFalse(UniCoreFW.is_set([]), "List should not be recognized as a set")

    def test_is_string(self):
        self.assertTrue(UniCoreFW.is_string("hello"))
        self.assertFalse(UniCoreFW.is_string(123))

    def test_is_symbol(self):
        import types

        self.assertTrue(
            UniCoreFW.is_symbol(types.ModuleType),
            "Should recognize module type as a symbol",
        )

    def test_is_typed_array(self):
        import array

        typed_array = array.array("i", [1, 2, 3])
        self.assertTrue(
            UniCoreFW.is_typed_array(typed_array), "Should recognize typed array"
        )

    def test_is_undefined(self):
        try:
            value = getattr(UniCoreFW, "some_nonexistent_variable")
        except AttributeError:
            value = None  # Simulate an undefined variable scenario
        self.assertTrue(
            UniCoreFW.is_undefined(value),
            "Simulated undefined variable should be recognized as undefined",
        )
        self.assertFalse(
            UniCoreFW.is_undefined(5), "5 should not be recognized as undefined"
        )

    def test_is_weak_map(self):
        from weakref import WeakKeyDictionary

        weak_map = WeakKeyDictionary()
        self.assertTrue(UniCoreFW.is_weak_map(weak_map), "Should recognize WeakMap")

    def test_is_weak_set(self):
        from weakref import WeakSet

        weak_set = WeakSet()
        self.assertTrue(UniCoreFW.is_weak_set(weak_set), "Should recognize WeakSet")

    def test_keys(self):
        result = UniCoreFW.keys({"a": 1, "b": 2})
        self.assertEqual(result, ["a", "b"])

    def test_map_object(self):
        result = UniCoreFW.map_object({"a": 1, "b": 2}, lambda x: x * 2)
        self.assertEqual(result, {"a": 2, "b": 4})

    def test_matcher(self):
        matcher_func = UniCoreFW.matcher({"a": 1})
        self.assertTrue(
            matcher_func({"a": 1, "b": 2}),
            "Should match the object with the given attributes",
        )

    def test_pairs(self):
        obj = {"a": 1, "b": 2}
        self.assertEqual(
            UniCoreFW.pairs(obj),
            [("a", 1), ("b", 2)],
            "Should return key-value pairs as tuples",
        )

    def test_property_of(self):
        obj = {"key": "value"}
        prop_of = UniCoreFW.property_of(obj)
        self.assertEqual(
            prop_of("key"),
            "value",
            "PropertyOf should return the value of the given property in the object",
        )

    def test_tap(self):
        arr = [1, 2, 3]
        result = []

        def side_effect(x):
            result.append(
                x.copy()
            )  # Use copy to capture the array state without nesting

        returned_array = UniCoreFW.tap(arr, side_effect)
        self.assertEqual(
            result,
            [arr],
            "Should execute side effect and keep the original array intact",
        )
        self.assertEqual(
            returned_array, arr, "Should return the original array unaltered"
        )

    def test_values(self):
        result = UniCoreFW.values({"a": 1, "b": 2})
        self.assertEqual(result, [1, 2])


if __name__ == "__main__":
    unittest.main()
