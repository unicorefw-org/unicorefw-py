#!/usr/bin/env python3
##############################################################################
# /tests/test_template.py - Tests for Unicore utilities            #
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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from unicorefw import _, SecurityError

class TestTemplateEdgeCases(unittest.TestCase):
    def test_template_invalid_tag(self):
        template_str = "Hello <% unknown %> World"
        context = {}
        with self.assertRaises(ValueError):
            _.template(template_str, context)

    def test_template_unclosed_if(self):
        template_str = "Hello <% if condition %>Condition is true"
        context = {"condition": True}
        with self.assertRaises(ValueError) as ctx:
            _.template(template_str, context)
        self.assertIn("Unclosed 'if' statement", str(ctx.exception))

    def test_template_unmatched_endif(self):
        template_str = "Hello <% endif %>"
        context = {}
        with self.assertRaises(ValueError) as ctx:
            _.template(template_str, context)
        self.assertIn("Unmatched 'endif'", str(ctx.exception))

    def test_template_dangerous_pattern(self):
        # Pattern suspicious for __class__ or __globals__, etc.
        template_str = "Danger <%= something.__class__.__dict__ %>"
        context = {"something": "test"}
        with self.assertRaises(SecurityError):
            _.template(template_str, context)


if __name__ == "__main__":
    unittest.main()
