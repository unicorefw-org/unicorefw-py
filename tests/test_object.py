#!/usr/bin/env python3
##############################################################################
# /tests/test_object.py - Tests for Unicore objects               #
# Copyright (C) 2024 Kenny Ngo / _.Org / IIPTech.Info                #
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
from collections import UserDict, namedtuple
from importlib import import_module

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from unicorefw import UniCoreFW, _

object_impl = import_module("unicorefw.object")

class TestUniCoreFWObjects(unittest.TestCase):
    def test_deep_copy(self):
        data = {
            "numbers": [1, 2, 3],
            "nested": {"x": 10, "y": [100, 101]},
        }
        copy_data = _.deep_copy(data)

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
            _.all_keys(obj),
            ["a", "b", "c"],
            "Should return all keys of the object",
        )

    def test_clone(self):
        obj = {"a": 1, "b": 2}
        cloned_obj = _.clone(obj)
        self.assertEqual(cloned_obj, obj, "Cloned object should match the original")
        self.assertIsNot(
            cloned_obj,
            obj,
            "Cloned object should not be the same instance as the original",
        )

    def test_deep_copy_handles_list_cycles_and_scalars(self):
        shared = []
        source = [shared, shared]
        shared.append(source)
        cloned = object_impl.deep_copy(source)
        self.assertIsNot(cloned, source)
        self.assertIs(cloned[0], cloned[1])
        self.assertIs(cloned[0][0], cloned)
        self.assertEqual(object_impl.deep_copy(3), 3)

    def test_create(self):
        proto = {"a": 1}
        new_obj = _.create(proto)
        self.assertEqual(
            new_obj["a"], 1, "Should create an object with the prototype properties"
        )

    def test_defaults(self):
        obj = {"a": 1}
        _.defaults(obj, {"a": 0, "b": 2})
        self.assertEqual(obj, {"a": 1, "b": 2})

    def test_defaults_iterable_pairs(self):
        obj = {"a": 1}
        result = _.defaults(obj, [("a", 0), ("b", 2)], {"b": 3, "c": 4})

        self.assertIs(result, obj)
        self.assertEqual(obj, {"a": 1, "b": 2, "c": 4})

    def test_apply_if_not_none(self):
        self.assertEqual(_.apply_if_not_none(10, lambda value: value * 2), 20)
        self.assertIsNone(_.apply_if_not_none(None, lambda value: value * 2))
        self.assertEqual(_.apply_if_not_none(lambda value, inc=1: value + inc, 2, inc=3), 5)

    def test_extend(self):
        obj = {"a": 1}
        source = {"b": 2}
        self.assertEqual(
            _.extend(obj, source),
            {"a": 1, "b": 2},
            "Should extend the object with source properties",
        )

    def test_functions(self):
        obj = {"a": lambda: 1, "b": 2, "c": lambda: 3}
        self.assertEqual(
            _.functions(obj),
            ["a", "c"],
            "Should return names of all functions in the object",
        )

    def test_has(self):
        obj = {"a": 1}
        self.assertTrue(
            _.has(obj, "a"), "Should return True if the object has the key"
        )
        self.assertFalse(
            _.has(obj, "b"),
            "Should return False if the object does not have the key",
        )

    def test_has_supports_sequence_and_attribute_paths(self):
        Pair = namedtuple("Pair", "left right")
        self.assertTrue(_.has({"items": [Pair(1, 2)]}, "items[0].right"))
        self.assertTrue(_.has(Pair(1, 2), "left"))
        self.assertTrue(_.has((10, 20), "-1"))
        self.assertFalse(_.has((10, 20), "3"))

    def test_deep_copy_preserves_cycles(self):
        source = {"items": []}
        source["items"].append(source)
        copied = _.deep_copy(source)
        self.assertIs(copied["items"][0], copied)
        self.assertIsNot(copied, source)

    def test_ordering_reductions_and_transforms(self):
        rows = [{"score": 2}, {"score": 1}, {"score": 3}]
        self.assertEqual([row["score"] for row in _.order_by(rows, ["score"])], [1, 2, 3])
        self.assertEqual([row["score"] for row in _.order_by(rows, ["score"], ["desc"])], [3, 2, 1])
        self.assertEqual(_.reduce_([1, 2, 3], lambda acc, value: acc + value, 0), 6)
        self.assertEqual(_.reduce_right([1, 2, 3], lambda acc, value: acc - value, 0), -6)
        self.assertEqual(_.reductions([1, 2, 3], lambda acc, value: acc + value, 0), [1, 3, 6])
        self.assertEqual(_.reductions_right([1, 2, 3], lambda acc, value: acc + value, 0), [3, 5, 6])
        self.assertEqual(_.transform({"a": 1, "b": 2}, lambda acc, value, key: acc.update({key: value * 2})), {"a": 2, "b": 4})
        self.assertEqual(len(_.sample_size([1, 2, 3], 2)), 2)

    def test_object_collection_primitives_directly(self):
        self.assertEqual(object_impl.at({"a": [10]}, "a[0]"), [10])
        self.assertEqual(object_impl.at({"a": [10]}, "a[bad]"), [None])
        self.assertEqual(object_impl.at({"a": 1}, "a.b"), [None])
        self.assertEqual(object_impl.filter_({"a": 0, "b": 2}), [2])
        self.assertEqual(object_impl.find_last([0, 1, 2], lambda value: value < 2), 1)
        self.assertIsNone(object_impl.find_last([0], lambda value: False))
        self.assertEqual(object_impl.flat_map([1, 2], lambda value: [value, value]), [1, 1, 2, 2])
        self.assertEqual(object_impl.flat_map([1], lambda value: value), [])
        self.assertEqual(object_impl.flat_map_deep([1], lambda value: [[value]]), [1])
        self.assertEqual(object_impl.flat_map_depth([1], lambda value: [[[value]]], 1), [[1]])
        seen = []
        self.assertEqual(object_impl.for_each([1, 2], seen.append), [1, 2])
        self.assertEqual(seen, [1, 2])
        self.assertEqual(object_impl.for_each_right({"a": 1, "b": 2}, seen.append), {"a": 1, "b": 2})
        self.assertTrue(object_impl.includes({"a": 2}, 2))
        self.assertEqual(object_impl.invoke_map(["a", "bb"], "upper"), ["A", "BB"])
        self.assertEqual(object_impl.key_by([{"id": 1}], "id"), {1: {"id": 1}})
        self.assertEqual(object_impl.map_([{"id": 1}], "id"), [1])

    def test_map_values_deep_and_find_helpers(self):
        source = {"a": 1, "nested": {"b": 2}}
        mapped = _.map_values_deep(source, lambda value: value * 10)
        self.assertEqual(mapped, {"a": 10, "nested": {"b": 20}})
        self.assertEqual(_.find_key({"a": 0, "b": 2}), "b")
        self.assertEqual(_.find_last_key({"a": 1, "b": 2}, lambda value: value > 0), "b")

    def test_deep_defaults_merge_and_assignment_customizers(self):
        source = {"a": {"value": 1}, "items": [1, 2]}
        cloned = _.clone_deep_with(source, lambda value: value * 10 if isinstance(value, int) else None)
        self.assertEqual(cloned, {"a": {"value": 10}, "items": [10, 20]})

        target = {"a": {"x": 1}, "empty": None}
        self.assertIs(_.defaults_deep(target, {"a": {"y": 2}, "empty": {"z": 3}}), target)
        self.assertEqual(target, {"a": {"x": 1, "y": 2}, "empty": {"z": 3}})

        merged = _.merge({"a": {"x": 1}, "items": [{"x": 1}, 2]}, {"a": {"y": 2}, "items": [{"y": 3}, 4, 5]})
        self.assertEqual(merged["a"], {"x": 1, "y": 2})
        self.assertEqual(merged["items"], [{"x": 1, "y": 3}, 4, 5])

        assigned = _.assign_with({"a": 1}, {"a": 2, "b": 3}, lambda old, new: old if old is not None else new)
        self.assertEqual(assigned, {"a": 1, "b": 3})

    def test_object_validation_and_fallback_branches(self):
        with self.assertRaises(TypeError):
            object_impl.create([])
        with self.assertRaises(TypeError):
            object_impl.defaults([], {"a": 1})
        with self.assertRaises(TypeError):
            object_impl.defaults({}, ["invalid-pair"])

        self.assertIsNone(object_impl.invoke({}, "missing"))
        self.assertIsNone(object_impl.invoke({}, []))
        self.assertEqual(object_impl.to_array(iter([1, 2])), [1, 2])
        self.assertEqual(object_impl.to_dict(object()), {})
        self.assertEqual(object_impl.keys(42), [])
        self.assertEqual(object_impl.values(42), [])

    def test_object_scalar_and_sequence_validation_edges(self):
        self.assertFalse(object_impl.has({"a": 1}, []))
        self.assertTrue(object_impl.has({1: "x"}, ["1"]))
        self.assertTrue(object_impl.has({"1": "x"}, [1]))
        self.assertTrue(object_impl.has(("x", "y"), "-1"))
        self.assertFalse(object_impl.has(("x", "y"), "bad"))
        self.assertFalse(object_impl.has(["x"], "bad"))
        Pair = namedtuple("Pair", "left right")
        pair = Pair(1, 2)
        self.assertTrue(object_impl.has(pair, "0"))
        self.assertTrue(object_impl.has(pair, [-1]))
        self.assertTrue(object_impl.has(pair, "right"))
        self.assertFalse(object_impl.has(pair, "missing"))
        self.assertFalse(object_impl.has(pair, "9"))

        class Attributes:
            present = "value"

        self.assertTrue(object_impl.has(Attributes(), "present"))
        self.assertFalse(object_impl.has(Attributes(), "missing"))
        with self.assertRaises(TypeError):
            object_impl.all_keys([])
        with self.assertRaises(TypeError):
            object_impl.functions([])
        self.assertEqual(object_impl.to_array({"a": 1}), [1])
        self.assertEqual(sorted(object_impl.to_array({1, 2})), [1, 2])

    def test_defaults_two_dict_fast_path_assigns_missing_keys(self):
        target = {"shared": 0}
        self.assertEqual(
            object_impl.defaults(target, {"first": 1, "shared": 2}, {"second": 3}),
            {"shared": 0, "first": 1, "second": 3},
        )
        self.assertEqual(object_impl.defaults({}, {"a": 1}, {"a": 2}), {"a": 1})

    def test_defaults_user_mapping_and_to_array_list_fast_path(self):
        target = UserDict({"existing": 1})
        self.assertIs(object_impl.defaults(target, {"added": 2}), target)
        self.assertEqual(dict(target), {"existing": 1, "added": 2})
        values = [1, 2]
        self.assertIs(object_impl.to_array(values), values)

        target = UserDict()
        self.assertIs(object_impl.defaults(target, None), target)
        self.assertEqual(object_impl.defaults(target, [("iterable", 3)]), {"iterable": 3})
        with self.assertRaises(TypeError):
            object_impl.defaults(target, object())

        class BadItems:
            def items(self):
                return [("ok", 1), ("malformed",)]

        with self.assertRaises(TypeError):
            object_impl.defaults(UserDict(), BadItems())

    def test_defaults_and_has_coercion_branches(self):
        target = {"a": 1}
        self.assertIs(object_impl.defaults(target), target)
        self.assertEqual(object_impl.defaults(target, {"b": 2}, {"c": 3}), {"a": 1, "b": 2, "c": 3})
        self.assertEqual(object_impl.defaults({"a": 1}, None, [("b", 2)]), {"a": 1, "b": 2})
        with self.assertRaises(TypeError):
            object_impl.defaults({}, ["not-a-pair"])

        self.assertTrue(object_impl.has({1: {"x": 2}}, "1.x"))
        self.assertTrue(object_impl.has({"1": "value"}, 1))
        self.assertTrue(object_impl.has(["a", "b"], "-1"))
        self.assertFalse(object_impl.has(["a"], "9"))

    def test_mapping_protocol_and_object_attribute_fallbacks(self):
        class MappingLike:
            def items(self):
                return [("x", 7)]

        class Attributes:
            def __init__(self):
                self.x = 7

        target = {}
        self.assertEqual(object_impl.defaults(target, MappingLike()), {"x": 7})
        self.assertEqual(object_impl.to_dict(MappingLike()), {"x": 7})
        attrs = Attributes()
        self.assertEqual(object_impl.keys(attrs), ["x"])
        self.assertEqual(object_impl.values(attrs), [7])
        self.assertEqual(object_impl.to_pairs(attrs), [("x", 7)])
        self.assertEqual(object_impl.invert(attrs), {7: "x"})

    def test_assignment_and_key_transform_functions(self):
        target = {"a": 1}
        self.assertIs(object_impl.assign(target, {"b": 2}), target)
        values = {"first": {"id": 1}, "second": {"id": 2}}
        self.assertEqual(object_impl.map_keys(values, "id"), {1: values["first"], 2: values["second"]})
        self.assertEqual(object_impl.map_values(values, "id"), {"first": 1, "second": 2})
        self.assertEqual(object_impl.rename_keys({"a": 1, "b": 2}, {"a": "A"}), {"A": 1, "b": 2})
        def add_existing(left, right, key, parent):
            if key == "a":
                return left + right
            return None

        self.assertEqual(object_impl.merge_with({"a": 1}, {"a": 2, "b": 3}, add_existing), {"a": 3, "b": 3})

    def test_object_iteration_break_and_last_key_fallbacks(self):
        seen = []

        def stop_after_first(value, key, obj):
            seen.append((key, value))
            return False

        source = {"a": 1, "b": 2}
        self.assertIs(object_impl.for_in(source, stop_after_first), source)
        self.assertEqual(seen, [("a", 1)])
        seen.clear()
        self.assertIs(object_impl.for_in_right(source, lambda value, key, obj: seen.append((key, value))), source)
        self.assertEqual(seen, [("b", 2), ("a", 1)])
        self.assertEqual(object_impl.find_last_key({"a": 0, "b": 2}, lambda value: value > 3), None)

    def test_object_parsing_selection_boolean_and_transform_branches(self):
        self.assertEqual(object_impl.parse_int("12", 8), 10)
        self.assertEqual(object_impl.parse_int("0x10"), 16)
        self.assertIsNone(object_impl.parse_int("invalid"))
        self.assertEqual(object_impl.pick({"a": {"b": 2}, "c": 3}, "a.b", "c"), {"a": {"b": 2}, "c": 3})
        self.assertEqual(object_impl.pick_by({"a": 1, "b": 2}, ["b"]), {"b": 2})
        self.assertEqual(object_impl.pick_by({"a": 1, "b": 2}, "a"), {"a": 1})
        self.assertTrue(object_impl.to_boolean("enabled", ["enable"]))
        self.assertFalse(object_impl.to_boolean("disabled", None, ["disable"]))
        self.assertEqual(object_impl.transform([1, 2, 3], lambda acc, value: (acc.append(value), False)[1]), [1])

    def test_customized_shallow_clone_and_path_aware_mapping(self):
        source = {"a": 1, "nested": {"b": 2}}
        cloned = object_impl.clone_with(source, lambda value, key, parent: value + 1 if isinstance(value, int) else None)
        self.assertEqual(cloned, {"a": 2, "nested": source["nested"]})
        self.assertIs(cloned["nested"], source["nested"])
        self.assertEqual(object_impl.clone_with(2, lambda value: value * 3), 6)

        paths = []
        mapped = object_impl.map_values_deep({"a": 1, "nested": {"b": 2}}, lambda value, path: paths.append(path) or value * 2)
        self.assertEqual(mapped, {"a": 2, "nested": {"b": 4}})
        self.assertIn(["nested", "b"], paths)

    def test_get_set_update_and_application_edge_forms(self):
        class Holder:
            pass

        holder = Holder()
        object_impl.set_(holder, "value", 5)
        self.assertEqual(object_impl.get(holder, "value"), 5)
        self.assertEqual(object_impl.get({"a": 1}, "missing", 9), 9)
        self.assertEqual(object_impl.get({"__globals__": 1}, "__globals__", 9), 9)

        target = {}
        object_impl.update_with(target, "count", 3, dict)
        self.assertEqual(target["count"], 3)
        self.assertEqual(object_impl.apply_if(2, lambda value: value * 2, lambda value: value > 1), 4)
        self.assertEqual(object_impl.apply_if(1, lambda value: value * 2, lambda value: value > 1), 1)
        self.assertEqual(object_impl.apply_catch(lambda: 1 / 0, default="fallback"), "fallback")

    def test_invert(self):
        obj = {"a": 1, "b": 2}
        self.assertEqual(
            _.invert(obj),
            {1: "a", 2: "b"},
            "Should invert the keys and values of the object",
        )

    def test_is_arguments(self):
        def func(*args):
            return _.is_arguments(args)

        self.assertTrue(func(1, 2, 3), "Should return True for arguments object")

    def test_is_array_buffer(self):
        from array import array

        buffer = array("i", [1, 2, 3])
        self.assertTrue(
            _.is_array_buffer(buffer), "Should recognize array buffer"
        )

    def test_is_boolean(self):
        self.assertTrue(
            _.is_boolean(True), "True should be recognized as a boolean"
        )
        self.assertTrue(
            _.is_boolean(False), "False should be recognized as a boolean"
        )
        self.assertFalse(
            _.is_boolean(0), "0 should not be recognized as a boolean"
        )

    def test_is_data_view(self):
        buffer = memoryview(bytearray([1, 2, 3]))
        self.assertTrue(_.is_data_view(buffer), "Should recognize data view")

    def test_is_date(self):
        from datetime import datetime

        self.assertTrue(
            _.is_date(datetime.now()),  # noqa: DTZ005
            "datetime object should be recognized as a date",
        )
        self.assertFalse(
            _.is_date("2024-01-01"), "String should not be recognized as a date"
        )

    def test_is_element(self):
        from xml.etree.ElementTree import Element

        element = Element("test")
        self.assertTrue(_.is_element(element), "Should recognize XML element")

    def test_is_empty(self):
        self.assertTrue(_.is_empty([]))
        self.assertTrue(_.is_empty({}))
        self.assertFalse(_.is_empty([1, 2]))

    def test_is_equal(self):
        obj1 = {"a": 1, "b": {"c": 2}}
        obj2 = {"a": 1, "b": {"c": 2}}
        self.assertTrue(
            _.is_equal(obj1, obj2), "Should recognize deeply equal objects"
        )

    def test_is_error(self):
        try:
            raise ValueError("Test error")
        except ValueError as e:
            self.assertTrue(
                _.is_error(e), "Exception should be recognized as an error"
            )
        self.assertFalse(
            _.is_error("Error"), "String should not be recognized as an error"
        )

    def test_is_finite(self):
        self.assertTrue(_.is_finite(100), "100 should be recognized as finite")
        self.assertFalse(
            _.is_finite(float("inf")),
            "Infinity should not be recognized as finite",
        )

    def test_is_function(self):
        self.assertTrue(
            _.is_function(lambda x: x),
            "Lambda should be recognized as a function",
        )
        self.assertFalse(
            _.is_function(5), "5 should not be recognized as a function"
        )

    def test_is_map(self):
        self.assertTrue(
            _.is_map({}), "Dictionary should be recognized as a map"
        )
        self.assertFalse(_.is_map([]), "List should not be recognized as a map")

    def test_is_match(self):
        self.assertTrue(_.is_match({"a": 1, "b": 2}, {"a": 1}))
        self.assertFalse(_.is_match({"a": 1, "b": 2}, {"a": 2}))

    def test_is_nan(self):
        self.assertTrue(
            _.is_nan(float("nan")), "NaN should be recognized as NaN"
        )
        self.assertFalse(_.is_nan(10), "10 should not be recognized as NaN")

    def test_is_null(self):
        self.assertTrue(_.is_null(None), "None should be recognized as null")
        self.assertFalse(_.is_null(0), "0 should not be recognized as null")

    def test_is_number(self):
        self.assertTrue(_.is_number(5), "5 should be recognized as a number")
        self.assertFalse(
            _.is_number("5"), '"5" should not be recognized as a number'
        )

    def test_is_object(self):
        self.assertTrue(
            _.is_object({}), "Should recognize a dictionary as an object"
        )
        self.assertFalse(
            _.is_object([]), "Should not recognize a list as an object"
        )

    def test_is_reg_exp(self):
        import re

        self.assertTrue(
            _.is_reg_exp(re.compile("abc")),
            "Regex object should be recognized as a regular expression",
        )
        self.assertFalse(
            _.is_reg_exp("abc"),
            "String should not be recognized as a regular expression",
        )

    def test_is_set(self):
        self.assertTrue(_.is_set(set()), "Set should be recognized as a set")
        self.assertFalse(_.is_set([]), "List should not be recognized as a set")

    def test_is_string(self):
        self.assertTrue(_.is_string("hello"))
        self.assertFalse(_.is_string(123))

    def test_is_symbol(self):
        import types

        self.assertTrue(
            _.is_symbol(types.ModuleType),
            "Should recognize module type as a symbol",
        )

    def test_is_typed_array(self):
        import array

        typed_array = array.array("i", [1, 2, 3])
        self.assertTrue(
            _.is_typed_array(typed_array), "Should recognize typed array"
        )

    def test_is_undefined(self):
        try:
            value = getattr(UniCoreFW, "some_nonexistent_variable")  # noqa: B009
        except AttributeError:
            value = None  # Simulate an undefined variable scenario
        self.assertTrue(
            _.is_undefined(value),
            "Simulated undefined variable should be recognized as undefined",
        )
        self.assertFalse(
            _.is_undefined(5), "5 should not be recognized as undefined"
        )

    def test_is_weak_map(self):
        from weakref import WeakKeyDictionary

        weak_map = WeakKeyDictionary()
        self.assertTrue(_.is_weak_map(weak_map), "Should recognize WeakMap")

    def test_is_weak_set(self):
        from weakref import WeakSet

        weak_set = WeakSet()
        self.assertTrue(_.is_weak_set(weak_set), "Should recognize WeakSet")

    def test_keys(self):
        result = _.keys({"a": 1, "b": 2})
        self.assertEqual(result, ["a", "b"])

    def test_map_object(self):
        result = _.map_object({"a": 1, "b": 2}, lambda x: x * 2)
        self.assertEqual(result, {"a": 2, "b": 4})

    def test_matcher(self):
        matcher_func = _.matcher({"a": 1})
        self.assertTrue(
            matcher_func({"a": 1, "b": 2}),
            "Should match the object with the given attributes",
        )

    def test_pairs(self):
        obj = {"a": 1, "b": 2}
        self.assertEqual(
            _.pairs(obj),
            [("a", 1), ("b", 2)],
            "Should return key-value pairs as tuples",
        )

    def test_property_of(self):
        obj = {"key": "value"}
        prop_of = _.property_of(obj)
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

        returned_array = _.tap(arr, side_effect)
        self.assertEqual(
            result,
            [arr],
            "Should execute side effect and keep the original array intact",
        )
        self.assertEqual(
            returned_array, arr, "Should return the original array unaltered"
        )

    def test_values(self):
        result = _.values({"a": 1, "b": 2})
        self.assertEqual(result, [1, 2])

    def test_collection_conversion_and_selection_helpers(self):
        self.assertEqual(_.size({"a": 1, "b": 2}), 2)
        self.assertEqual(_.size(iter([1, 2, 3])), 3)
        self.assertEqual(_.to_array({"a": 1, "b": 2}), [1, 2])
        self.assertEqual(_.to_array(4), [4])
        self.assertEqual(_.where([{"a": 1}, {"a": 2}], {"a": 1}), [{"a": 1}])
        self.assertEqual(_.object(["a", "b"], [1, 2]), {"a": 1, "b": 2})
        with self.assertRaises(ValueError):
            _.object(["a"], [1, 2])
        self.assertEqual(_.at({"a": {"b": 2}}, "a.b", "a.c"), [2, None])

    def test_collection_iteration_and_key_helpers(self):
        seen = []
        self.assertEqual(_.for_each({"a": 1, "b": 2}, seen.append), {"a": 1, "b": 2})
        self.assertEqual(seen, [1, 2])
        seen.clear()
        self.assertEqual(_.for_each_right([1, 2, 3], seen.append), [1, 2, 3])
        self.assertEqual(seen, [3, 2, 1])
        self.assertTrue(_.includes({"a": 1}, 1))
        self.assertEqual(_.key_by([{"id": 1}, {"id": 2}], "id")[2], {"id": 2})
        self.assertEqual(_.map_([{"id": 1}], "id"), [1])

    def test_conversion_inversion_selection_and_safe_apply_helpers(self):
        self.assertEqual(_.to_integer("3.9"), 3)
        self.assertEqual(_.to_integer("bad"), 0)
        self.assertEqual(_.to_string(None), "")
        self.assertEqual(_.to_list(None), [])
        self.assertEqual(_.to_list((1, 2)), [1, 2])
        self.assertEqual(_.to_dict(["a", "b"]), {0: "a", 1: "b"})
        self.assertEqual(_.invert({"a": 1, "b": 2}), {1: "a", 2: "b"})
        self.assertEqual(_.invert_by({"a": 1, "b": 3}, lambda value: value % 2), {1: ["a", "b"]})
        self.assertEqual(_.callables({"a": 1, "b": lambda: None}), ["b"])
        self.assertEqual(_.omit({"a": 1, "b": 2}, "b"), {"a": 1})
        self.assertEqual(_.pick({"a": 1, "b": 2}, "a"), {"a": 1})
        self.assertEqual(_.omit_by({"a": 1, "b": 2}, lambda value, key: key == "b"), {"a": 1})
        self.assertEqual(_.pick_by({"a": 1, "b": 2}, lambda value, key: key == "b"), {"b": 2})
        self.assertEqual(_.apply(lambda a, b: a + b, 2, 3), 5)
        self.assertIsNone(_.apply_if_not_none(lambda a: a, None))
        self.assertEqual(_.to_boolean("yes"), True)
        self.assertIsNone(_.to_boolean(""))
        self.assertEqual(_.to_number("1.25", 1), 1.2)
        self.assertIsNone(_.to_number("bad"))

    def test_nested_invoke_and_mutation_helpers(self):
        class Greeter:
            def greet(self, prefix="hi"):
                return f"{prefix} there"

        self.assertEqual(_.invoke(Greeter(), "greet", "hello"), "hello there")
        self.assertEqual(_.invoke([Greeter(), object()], "greet"), ["hi there", None])

        value = {"a": {"b": 1}}
        self.assertEqual(_.update(value, "a.b", lambda current: current + 1), value)
        self.assertEqual(value["a"]["b"], 2)
        self.assertTrue(_.unset(value, "a.b"))
        self.assertFalse(_.unset(value, "a.b"))

        target = {}
        _.set_with(target, "a.b", 3, dict)
        self.assertEqual(target, {"a": {"b": 3}})
        _.update_with(target, "a.c", 4, dict)
        self.assertEqual(target["a"]["c"], 4)

    def test_invoke_path_resolution_fallbacks(self):
        class Calculator:
            def add(self, value):
                return value + 1

            def fail(self):
                raise RuntimeError("hidden")

        self.assertEqual(object_impl.invoke({"1": Calculator()}, 1), None)
        self.assertEqual(object_impl.invoke({1: Calculator()}, "1"), None)
        self.assertEqual(object_impl.invoke([Calculator()], 0), None)
        self.assertEqual(object_impl.invoke([Calculator()], "add", 4), [5])
        self.assertIsNone(object_impl.invoke({"nested": [Calculator()]}, "nested.0.fail"))
        self.assertIsNone(object_impl.invoke({"nested": [Calculator()]}, "nested.4.add", 1))

        class Holder:
            def __init__(self):
                self.child = Calculator()

        self.assertEqual(object_impl.invoke({"nested": {1: Calculator()}}, "nested.1.add", 2), 3)
        self.assertEqual(object_impl.invoke({"nested": {1: Calculator()}}, ["nested", "1", "add"], 2), 3)
        self.assertEqual(object_impl.invoke({"nested": {"1": Calculator()}}, ["nested", 1, "add"], 2), 3)
        self.assertEqual(object_impl.invoke(Holder(), "child.add", 2), 3)
        self.assertIsNone(object_impl.invoke({"nested": None}, "nested.add"))
        self.assertIsNone(object_impl.invoke({"nested": None}, "nested.deep.add"))
        self.assertIsNone(object_impl.invoke({"nested": {}}, ["nested", "missing", "add"], 2))

    def test_order_by_callable_and_mismatched_orders(self):
        rows = [{"score": 2}, {"score": 1}, {"score": 3}]
        self.assertEqual(
            [row["score"] for row in object_impl.order_by(rows, [lambda row: row["score"]])],
            [1, 2, 3],
        )
        self.assertEqual(
            [row["score"] for row in object_impl.order_by(rows, ["score", "missing"], ["desc"])],
            [3, 2, 1],
        )

    def test_object_collection_and_conversion_edge_paths(self):
        self.assertTrue(object_impl.includes([1, 2], 2))
        self.assertEqual(object_impl.invoke_map([1, 2], lambda value, offset=0: value + offset, offset=3), [4, 5])
        rows = [{"id": 1}, {"id": 2}]
        self.assertEqual(object_impl.key_by(rows, lambda row: row["id"]), {1: rows[0], 2: rows[1]})
        self.assertEqual(object_impl.nest(rows, ["id"]), {1: [rows[0]], 2: [rows[1]]})
        sampled = object_impl.sample_size([1, 2], None)
        self.assertEqual(len(sampled), 1)
        self.assertIn(sampled[0], [1, 2])
        self.assertEqual(object_impl.map_keys({"a": 1}, lambda key, value: value), {1: 1})
        values = [1, 2]
        self.assertIs(object_impl.to_list(values), values)

        class Keyed:
            def keys(self):
                return ["x"]

            def values(self):
                return [9]

        self.assertEqual(object_impl.keys(Keyed()), ["x"])
        self.assertEqual(object_impl.values(Keyed()), [9])
        target = {"items": [1, 2]}
        self.assertTrue(object_impl.unset(target, "items[0]"))
        self.assertFalse(object_impl.unset(target, "items[9]"))
        self.assertEqual(object_impl.clone(3), 3)
        self.assertEqual(object_impl.defaults_deep({}, {"nested": {"x": 1}}), {"nested": {"x": 1}})
        self.assertEqual(object_impl.defaults_deep({"nested": None}, {"nested": {"x": 1}}), {"nested": {"x": 1}})

    def test_object_nested_copy_and_unset_edge_paths(self):
        rows = [
            {"kind": "fruit", "color": "red", "name": "apple"},
            {"kind": "fruit", "color": "yellow", "name": "banana"},
        ]
        self.assertEqual(
            object_impl.nest(rows, ["kind", "color"]),
            {"fruit": {"red": [rows[0]], "yellow": [rows[1]]}},
        )
        self.assertEqual(object_impl.to_list(3), [3])
        self.assertEqual(object_impl.to_list({"x": 1}), [{"x": 1}])

        cyclic = []
        cyclic.append(cyclic)
        copied = object_impl.clone_deep(cyclic)
        self.assertIs(copied[0], copied)

        self.assertFalse(object_impl.unset({}, "missing.value"))
        self.assertFalse(object_impl.unset({"items": []}, "items[0]"))
        self.assertFalse(object_impl.unset({"items": [1]}, "items[-1]"))
        self.assertFalse(object_impl.unset({"items": [1]}, ["items", -1]))
        self.assertFalse(object_impl.unset({}, ""))

        class Holder:
            def __init__(self):
                self.value = 1

        holder = Holder()
        self.assertTrue(object_impl.unset(holder, "value"))
        self.assertFalse(object_impl.unset(holder, "value"))

        self.assertEqual(object_impl.defaults_deep({"x": 1}, "invalid"), {"x": 1})
        self.assertEqual(
            object_impl.defaults_deep({"items": [{"a": 1}]}, {"items": [{"b": 2}]}),
            {"items": [{"a": 1, "b": 2}]},
        )

    def test_assign_with_and_apply_if_not_none_arity_paths(self):
        target = {"a": 1}
        self.assertEqual(
            object_impl.assign_with(target, {"a": 2}, lambda old, new: old + new),
            {"a": 3},
        )
        target = {}
        object_impl.assign_with(target, [("b", 2)], lambda value: value * 2)
        self.assertEqual(target, {"b": 4})
        object_impl.assign_with(target, object(), lambda value: value)
        self.assertEqual(target, {"b": 4})
        with self.assertRaises(TypeError):
            object_impl.assign_with({}, {"a": 1})

        self.assertEqual(object_impl.apply_if_not_none(lambda: 4), 4)
        self.assertEqual(object_impl.apply_if_not_none(lambda value: value + 1, 2), 3)
        self.assertIsNone(object_impl.apply_if_not_none(lambda value: value, None))
        self.assertIsNone(object_impl.apply_if_not_none(None, lambda value: value + 1, 2))
        self.assertIsNone(object_impl.apply_if_not_none(None, lambda value: value, None))

    def test_object_mapping_clone_and_get_edge_paths(self):
        self.assertEqual(object_impl.map_values_deep(3, lambda value: value + 1), 4)
        self.assertEqual(object_impl.map_values_deep(3, lambda value, path: value + len(path)), 3)
        cyclic = {}
        cyclic["self"] = cyclic
        mapped = object_impl.map_values_deep(cyclic, lambda value, path: value)
        self.assertIs(mapped["self"], mapped)

        self.assertEqual(object_impl.clone_with([1, 2], lambda value: value * 2), [2, 4])
        self.assertEqual(object_impl.clone_with(2, lambda value: value + 1), 3)
        self.assertEqual(object_impl.clone_with({"a": 1}, lambda value: None), {"a": 1})

        self.assertEqual(object_impl.get(range(3), "1"), 1)
        self.assertEqual(object_impl.get((1, 2), "9", "fallback"), "fallback")
        Point = namedtuple("Point", "x y")
        self.assertEqual(object_impl.get(Point(4, 5), "x"), 4)
        self.assertEqual(object_impl.get(Point(4, 5), "9", "fallback"), "fallback")
        self.assertEqual(object_impl.find_key({"a": 0}), None)

    def test_object_merge_transform_and_apply_variants(self):
        self.assertEqual(object_impl.merge_with(), {})
        self.assertEqual(object_impl.merge_with({"a": 1}, {"b": 2}), {"a": 1, "b": 2})
        self.assertEqual(
            object_impl.merge_with(
                {"a": 1}, {"a": 2},
                lambda old, new, key, parent: old + new if key == "a" else None,
            ),
            {"a": 3},
        )
        self.assertEqual(
            object_impl.merge_with({"a": [1]}, {"a": [2, 3]}, lambda value: None),
            {"a": [2, 3]},
        )

        self.assertEqual(object_impl.transform({"a": 1}, None), {})
        self.assertEqual(object_impl.transform({"a": 1}, None, {"seed": 1}), {"seed": 1})
        self.assertEqual(
            object_impl.transform([1, 2], lambda acc, value: acc.append(value * 2)),
            [2, 4],
        )
        self.assertEqual(
            object_impl.transform({"a": 1, "b": 2}, lambda acc, value, key: False if key == "a" else None),
            {},
        )
        self.assertEqual(object_impl.to_number("2.5", None), 2.5)
        self.assertEqual(object_impl.to_number("25", -1), 20)

        obj = {}
        object_impl.set_with(obj, "[0][0]", 3, list)
        self.assertEqual(obj, {0: [3]})
        self.assertEqual(object_impl.update_with({}, "a", lambda: 4, dict), {"a": 4})
        self.assertEqual(object_impl.set_with({}, "", 4, dict), {})
        self.assertEqual(object_impl.apply_if(2, lambda value: value + 1, lambda value: value > 1), 3)
        self.assertEqual(object_impl.apply_if(1, lambda value: value + 1, lambda value: False), 1)
        self.assertIsNone(object_impl.apply_if(lambda value: value + 1, lambda value: False, 1))
        self.assertEqual(object_impl.apply_catch(2, lambda value: value + 1), 3)
        self.assertEqual(object_impl.apply_catch(2, lambda value: 1 / 0, default=9), 9)
        self.assertEqual(
            object_impl.apply_catch(lambda: 1 / 0, exceptions=[ZeroDivisionError], default=7),
            7,
        )
        self.assertEqual(
            object_impl.apply_catch(2, lambda value: 1 / 0, exceptions={ZeroDivisionError}),
            2,
        )
        self.assertEqual(
            object_impl.apply_catch(lambda: 1 / 0, exceptions=object(), default=8),
            8,
        )

    def test_object_merge_list_and_parse_paths(self):
        self.assertEqual(
            object_impl.merge_with([{"a": 1}], [{"b": 2}], lambda *args: None),
            [{"a": 1, "b": 2}],
        )
        self.assertEqual(object_impl.merge_with({"a": 1}, [2], lambda *args: None), [2])
        self.assertEqual(object_impl.parse_int(True), 1)
        self.assertEqual(object_impl.parse_int(4.9), 4)
        self.assertEqual(object_impl.parse_int("0x10"), 16)
        self.assertIsNone(object_impl.parse_int("not-a-number"))

        class BrokenInt(int):
            def __int__(self):
                raise ValueError("broken conversion")

        self.assertIsNone(object_impl.parse_int(BrokenInt(3)))
        self.assertEqual(object_impl.defaults({"a": 1}, {"a": 2, "b": 3}), {"a": 1, "b": 3})

    def test_object_path_coercion_and_custom_clone_edges(self):
        self.assertEqual(object_impl.get({1: "one"}, "1"), "one")
        self.assertEqual(object_impl.get({"1": "one"}, 1), "one")
        self.assertEqual(object_impl.get(["zero", "one"], "-1"), "one")
        self.assertEqual(object_impl.get(("zero", "one"), 1), "one")
        self.assertEqual(object_impl.get(range(2), 4, "fallback"), "fallback")

        cyclic = {}
        cyclic["self"] = cyclic
        cloned = object_impl.clone_deep_with(cyclic, lambda value, *args: None)
        self.assertIs(cloned["self"], cloned)

        self.assertEqual(object_impl.merge(), {})
        self.assertEqual(object_impl.merge({"a": 1}, None), {"a": 1})
        self.assertEqual(object_impl.merge({}, None), {})

    def test_object_selection_mutation_and_boolean_edges(self):
        source = {"a": 1, "nested": {"value": 2}, "b": 3}
        self.assertEqual(object_impl.pick(source, "a", "nested.value"), {"a": 1, "nested": {"value": 2}})
        self.assertEqual(object_impl.pick(source, "missing.path"), {})
        self.assertEqual(object_impl.pick_by(source, ["a", "b"]), {"a": 1, "b": 3})
        self.assertEqual(object_impl.pick_by(source, "a"), {"a": 1})
        self.assertEqual(object_impl.pick_by(source), source)

        unchanged = {"a": 1}
        self.assertIs(object_impl.set_(unchanged, "", 2), unchanged)
        self.assertEqual(object_impl.set_({}, "items[1]", "x"), {"items": [None, "x"]})

        self.assertTrue(object_impl.to_boolean("yes"))
        self.assertFalse(object_impl.to_boolean("off"))
        self.assertTrue(object_impl.to_boolean("enabled", ["enabled"]))
        self.assertFalse(object_impl.to_boolean("disabled", false_patterns=["disabled"]))


if __name__ == "__main__":
    unittest.main()
