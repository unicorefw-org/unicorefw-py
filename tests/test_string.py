#!/usr/bin/env python3
#########################################################################################
# /tests/test_string.py - Tests for UniCoreFW string utilities               #
# Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.Info                           #
#                                                                                       #
# This file is part of UniCoreFW. You can redistribute it and/or modify                 #
# it under the terms of the [BSD-3-Clause] as published by                              #
# the Free Software Foundation.                                                         #
# You should have received a copy of the [BSD-3-Clause] license                         #
# along with UniCoreFW. If not, see https://www.gnu.org/licenses/.                      #
#########################################################################################

import unittest
import sys
import os

# Add the src directory to the Python path (adjust if needed)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from unicorefw import _  # Import UniCoreFW as usual

class TestUniCoreFWStrings(unittest.TestCase):
    # -------------------- Basic String Utilities -------------------- #
    def test_reverse(self):
        self.assertEqual(_.reverse("abc"), "cba")
        self.assertEqual(_.reverse(""), "")
        self.assertEqual(_.reverse("12345"), "54321")

    def test_camel_case(self):
        self.assertEqual(
            _.camel_case("Hello world example"), "helloWorldExample"
        )
        self.assertEqual(_.camel_case("  multiple   spaces "), "multipleSpaces")

    def test_snake_case(self):
        self.assertEqual(_.snake_case("Hello world"), "hello_world")
        self.assertEqual(
            _.snake_case("Already__snake_case"), "already__snake_case"
        )

    def test_kebab_case(self):
        self.assertEqual(_.kebab_case("Hello world"), "hello-world")
        self.assertEqual(_.kebab_case("Some_Var-name"), "some-var-name")

    def test_truncate(self):
        self.assertEqual(_.truncate("Hello world", 10, separator=" "), "Hello...")
        self.assertEqual(_.truncate("Short", 10), "Short")
        self.assertEqual(
            _.truncate("This is a long string", 10, "..."), "This is..."
        )

    def test_starts_with(self):
        self.assertTrue(_.starts_with("Hello world", "Hell"))
        self.assertFalse(_.starts_with("Hello", "hello"))

    def test_ends_with(self):
        self.assertTrue(_.ends_with("Hello world", "world"))
        self.assertFalse(_.ends_with("Testing", "ing "))

    def test_words(self):
        self.assertEqual(_.words("Hello, world!"), ["Hello", "world"])
        self.assertEqual(_.words("Hello  world", r"\W+"), ["Hello", "world"])
        self.assertEqual(_.words(""), [])

    def test_humanize(self):
        self.assertEqual(
            _.humanize("hello_world_example"), "Hello world example"
        )
        self.assertEqual(_.humanize("  multiple---dashes  "), "Multiple dashes")

    def test_slice(self):
        self.assertEqual(_.slice("Hello world", 1, 5), "ello")
        self.assertEqual(_.slice("Hello world", 6), "world")
        self.assertEqual(_.slice("Python", 0, 3), "Pyt")

    def test_replace_all(self):
        self.assertEqual(_.replace_all("banana", "a", "o"), "bonono")
        self.assertEqual(_.replace_all("xxxx", "x", ""), "")

    def test_chain_usage(self):
        result = (
            _("Hello world")
            .snake_case()  # "hello_world"
            .regex_replace(r"_", "-", 0)  # "hello-world"
            .reverse()  # "dlrow-olleh"
            .value()
        )
        self.assertEqual(result, "dlrow-olleh")

    # -------------------- Advanced Regex Methods -------------------- #
    def test_regex_find_all(self):
        matches = _.regex_find_all("abc123xyz456", r"\d+")
        self.assertEqual(matches, ["123", "456"])
        self.assertEqual(_.regex_find_all("No digits", r"\d+"), [])

    def test_regex_test(self):
        self.assertTrue(_.regex_test("Hello123", r"\d+"))
        self.assertFalse(_.regex_test("Just letters", r"\d+"))

    def test_regex_replace(self):
        # Replace digits with '#'
        result = _.regex_replace("abc123xyz", r"\d", "#")
        self.assertEqual(result, "abc###xyz")

        # Using a callable replacement
        def to_upper(m):
            return m.group(0).upper()

        result = _.regex_replace("abc123", r"[a-z]", to_upper)
        self.assertEqual(result, "ABC123")

    def test_regex_extract(self):
        text = "Order ID: AB-12345, Date: 2025-04-01"
        match = _.regex_extract(text, r"Order ID:\s+(\w+-\d+)", 1)
        self.assertEqual(match, "AB-12345")
        no_match = _.regex_extract("No ID here", r"ID:\s+(\w+)")
        self.assertIsNone(no_match)

    def test_regex_extract_all(self):
        text = "Name: Alice, Name: Bob, Name: Charlie"
        matches = _.regex_extract_all(text, r"Name:\s+(\w+)", 1)
        self.assertEqual(matches, ["Alice", "Bob", "Charlie"])
        self.assertEqual(_.regex_extract_all("Nothing here", r"(\d+)"), [])

    # -------------------- Practical Utility Methods -------------------- #
    def test_strip_html_tags(self):
        html = "<p>Hello <b>John</b>!</p>"
        self.assertEqual(_.strip_html_tags(html), "Hello John!")

    def test_slugify(self):
        self.assertEqual(_.slugify("Hello, World!"), "hello-world")
        self.assertEqual(_.slugify("  multi   spaces  "), "multi-spaces")

    def test_mask_sensitive(self):
        text = "Card: 1234-5678-9012-3456"
        masked = _.mask_sensitive(text, r"\d")
        self.assertEqual(masked, "Card: ****-****-****-****")

    def test_highlight_matches(self):
        text = "Hello, world!"
        highlighted = _.highlight_matches(text, "o", "[", "]")
        self.assertEqual(highlighted, "Hell[o], w[o]rld!")

    def test_normalize_whitespace(self):
        text = "Too   many \n spaces \t here"
        result = _.normalize_whitespace(text)
        self.assertEqual(result, "Too many spaces here")

    def test_dedent_text(self):
        text = """\
            def function():
                return True
        """
        dedented = _.dedent_text(text)
        # 'dedented' should start at column 0
        self.assertTrue(dedented.startswith("def function():"))
        self.assertIn("return True", dedented)

    # -------------- Example for Encryption (if using cryptography) -------------- #
    # If you implemented encrypt_string / decrypt_string with cryptography:
    #
    # def test_encrypt_decrypt_string(self):
    #     try:
    #         key = _.generate_key()
    #         original = "my secret"
    #         encrypted = _.encrypt_string(original, key)
    #         decrypted = _.decrypt_string(encrypted, key)
    #         self.assertEqual(decrypted, original)
    #     except RuntimeError:
    #         # If cryptography is not installed, skip
    #         self.skipTest("cryptography library not installed")


if __name__ == "__main__":
    unittest.main()
