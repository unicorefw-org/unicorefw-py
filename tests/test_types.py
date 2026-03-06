#!/usr/bin/env python3
##############################################################################
# /tests/test_types.py - Tests for Unicore utilities            #
# Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.Info                #
#                                                                            #
# This file is part of UniCoreFW. You can redistribute it and/or modify      #
# it under the terms of the [BSD-3-Clause] as published by                   #
# the Free Software Foundation.                                              #
# You should have received a copy of the [BSD-3-Clause] license              #
# along with UniCoreFW. If not, see https://www.gnu.org/licenses/.           #
##############################################################################

import re
import sys
import os
from datetime import date
from array import array
from weakref import WeakKeyDictionary, WeakSet
from xml.etree.ElementTree import Element
import unittest

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from unicorefw import _

class TestTemplateEdgeCases(unittest.TestCase):
    def test_is_string(self):
        assert _.is_string("test")
        assert not _.is_string(123)

    def test_is_number(self):
        assert _.is_number(10)
        assert _.is_number(3.14)
        assert not _.is_number("3.14")

    def test_is_array_and_object(self):
        assert _.is_array([1,2,3])
        assert not _.is_array((1,2,3))
        assert _.is_object({"a":1})
        assert not _.is_object([("a",1)])

    def test_is_function_and_boolean(self):
        assert _.is_function(lambda x: x)
        def foo(): pass
        assert _.is_function(foo)
        assert _.is_boolean(True)
        assert _.is_boolean(False)
        assert not _.is_boolean(0)

    def test_is_date_and_reg_exp(self):
        assert _.is_date(date.today())
        assert not _.is_date("2025-06-30")
        patt = re.compile(r"\d+")
        assert _.is_reg_exp(patt)
        assert not _.is_reg_exp("123")

    def test_is_error_null_undefined(self):
        assert _.is_error(ValueError("error"))
        assert not _.is_error("error")
        assert _.is_null(None)
        assert not _.is_null(0)
        assert _.is_undefined(None)
        assert not _.is_undefined(False)

    def test_is_finite_and_nan(self):
        assert _.is_finite(0)
        assert _.is_finite(1.5)
        assert not _.is_finite(float("inf"))
        assert _.is_nan(float("nan"))
        assert not _.is_nan(123)

    def test_is_map_set_and_arguments(self):
        assert _.is_map({"a":1})
        assert not _.is_map([1,2])
        assert _.is_set({1,2})
        assert not _.is_set([1,2])
        assert _.is_arguments((1,2))
        assert not _.is_arguments([1,2])

    def test_is_array_buffer_and_data_view_and_typed_array(self):
        arr = array('i', [1,2,3])
        assert _.is_array_buffer(arr)
        mv = memoryview(b"abc")
        assert _.is_data_view(mv)
        assert _.is_typed_array(arr)

    def test_is_weak_map_and_weak_set_and_element(self):
        wk = WeakKeyDictionary()
        assert _.is_weak_map(wk)
        assert not _.is_weak_map({})
        ws = WeakSet()
        assert _.is_weak_set(ws)
        assert not _.is_weak_set(set())
        el = Element("tag")
        assert _.is_element(el)
        assert not _.is_element({"tag": None})

    def test_is_empty(self):
        assert _.is_empty(None)
        assert _.is_empty([])
        assert _.is_empty({})
        assert _.is_empty("")
        assert not _.is_empty([0])
        # Test non-len iterable
        def gen(): yield 1
        assert not _.is_empty(gen())
        assert _.is_empty(iter([]))

    def test_is_symbol(self):
        import types as _builtin_types
        assert _.is_symbol(_builtin_types.ModuleType)
        assert _.is_symbol(_builtin_types.FunctionType)
        assert _.is_symbol(_.is_symbol)
        assert not _.is_symbol(123)

    def test_is_equal(self):
        assert _.is_equal(1,1)
        assert not _.is_equal(1,2)
        assert _.is_equal([1,2],[1,2])
        assert not _.is_equal([1,2],[2,1])
        assert _.is_equal({"a":1,"b":[2,3]},{"b":[2,3],"a":1})
        # cyclic
        a = []; a.append(a)
        b = []; b.append(b)
        assert _.is_equal(a,b)
        # different cycle
        c = []; c.append(c); c.append(1)
        d = []; d.append(d); d.append(2)
        assert not _.is_equal(c,d)
