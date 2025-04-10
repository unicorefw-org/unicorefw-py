# tests/utility_functions_tests.py or tests/template_functions_tests.py

import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from unicorefw import UniCoreFW, SecurityError


class TestTemplateEdgeCases(unittest.TestCase):
    def test_template_invalid_tag(self):
        template_str = "Hello <% unknown %> World"
        context = {}
        with self.assertRaises(ValueError):
            UniCoreFW.template(template_str, context)

    def test_template_unclosed_if(self):
        template_str = "Hello <% if condition %>Condition is true"
        context = {"condition": True}
        with self.assertRaises(ValueError) as ctx:
            UniCoreFW.template(template_str, context)
        self.assertIn("Unclosed 'if' statement", str(ctx.exception))

    def test_template_unmatched_endif(self):
        template_str = "Hello <% endif %>"
        context = {}
        with self.assertRaises(ValueError) as ctx:
            UniCoreFW.template(template_str, context)
        self.assertIn("Unmatched 'endif'", str(ctx.exception))

    def test_template_dangerous_pattern(self):
        # Pattern suspicious for __class__ or __globals__, etc.
        template_str = "Danger <%= something.__class__.__dict__ %>"
        context = {"something": "test"}
        with self.assertRaises(SecurityError):
            UniCoreFW.template(template_str, context)


if __name__ == "__main__":
    unittest.main()
