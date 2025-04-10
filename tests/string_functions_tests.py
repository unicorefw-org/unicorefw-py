#!/usr/bin/env python3
#########################################################################################
# /tests/string_functions_tests.py - Tests for UniCoreFW string utilities               #
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

from unicorefw import _, UniCoreFW  # Import UniCoreFW as usual


class TestUniCoreFWStrings(unittest.TestCase):
    # -------------------- Basic String Utilities -------------------- #
    def test_reverse(self):
        self.assertEqual(UniCoreFW.reverse("abc"), "cba")
        self.assertEqual(UniCoreFW.reverse(""), "")
        self.assertEqual(UniCoreFW.reverse("12345"), "54321")

    def test_camel_case(self):
        self.assertEqual(
            UniCoreFW.camel_case("Hello world example"), "helloWorldExample"
        )
        self.assertEqual(UniCoreFW.camel_case("  multiple   spaces "), "multipleSpaces")

    def test_snake_case(self):
        self.assertEqual(UniCoreFW.snake_case("Hello world"), "hello_world")
        self.assertEqual(
            UniCoreFW.snake_case("Already__snake_case"), "already__snake_case"
        )

    def test_kebab_case(self):
        self.assertEqual(UniCoreFW.kebab_case("Hello world"), "hello-world")
        self.assertEqual(UniCoreFW.kebab_case("Some_Var-name"), "some-var-name")

    def test_truncate(self):
        self.assertEqual(UniCoreFW.truncate("Hello world", 5), "Hello...")
        self.assertEqual(UniCoreFW.truncate("Short", 10), "Short")
        self.assertEqual(
            UniCoreFW.truncate("This is a long string", 7, "..."), "This is..."
        )

    def test_starts_with(self):
        self.assertTrue(UniCoreFW.starts_with("Hello world", "Hell"))
        self.assertFalse(UniCoreFW.starts_with("Hello", "hello"))

    def test_ends_with(self):
        self.assertTrue(UniCoreFW.ends_with("Hello world", "world"))
        self.assertFalse(UniCoreFW.ends_with("Testing", "ing "))

    def test_words(self):
        self.assertEqual(UniCoreFW.words("Hello, world!"), ["Hello,", "world!"])
        self.assertEqual(UniCoreFW.words("Hello  world", r"\W+"), ["Hello", "world"])
        self.assertEqual(UniCoreFW.words(""), [])

    def test_humanize(self):
        self.assertEqual(
            UniCoreFW.humanize("hello_world_example"), "Hello world example"
        )
        self.assertEqual(UniCoreFW.humanize("  multiple---dashes  "), "Multiple dashes")

    def test_slice(self):
        self.assertEqual(UniCoreFW.slice("Hello world", 1, 5), "ello")
        self.assertEqual(UniCoreFW.slice("Hello world", 6), "world")
        self.assertEqual(UniCoreFW.slice("Python", 0, 3), "Pyt")

    def test_replace_all(self):
        self.assertEqual(UniCoreFW.replace_all("banana", "a", "o"), "bonono")
        self.assertEqual(UniCoreFW.replace_all("xxxx", "x", ""), "")

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
        matches = UniCoreFW.regex_find_all("abc123xyz456", r"\d+")
        self.assertEqual(matches, ["123", "456"])
        self.assertEqual(UniCoreFW.regex_find_all("No digits", r"\d+"), [])

    def test_regex_test(self):
        self.assertTrue(UniCoreFW.regex_test("Hello123", r"\d+"))
        self.assertFalse(UniCoreFW.regex_test("Just letters", r"\d+"))

    def test_regex_replace(self):
        # Replace digits with '#'
        result = UniCoreFW.regex_replace("abc123xyz", r"\d", "#")
        self.assertEqual(result, "abc###xyz")

        # Using a callable replacement
        def to_upper(m):
            return m.group(0).upper()

        result = UniCoreFW.regex_replace("abc123", r"[a-z]", to_upper)
        self.assertEqual(result, "ABC123")

    def test_regex_extract(self):
        text = "Order ID: AB-12345, Date: 2025-04-01"
        match = UniCoreFW.regex_extract(text, r"Order ID:\s+(\w+-\d+)", 1)
        self.assertEqual(match, "AB-12345")
        no_match = UniCoreFW.regex_extract("No ID here", r"ID:\s+(\w+)")
        self.assertIsNone(no_match)

    def test_regex_extract_all(self):
        text = "Name: Alice, Name: Bob, Name: Charlie"
        matches = UniCoreFW.regex_extract_all(text, r"Name:\s+(\w+)", 1)
        self.assertEqual(matches, ["Alice", "Bob", "Charlie"])
        self.assertEqual(UniCoreFW.regex_extract_all("Nothing here", r"(\d+)"), [])

    # -------------------- Practical Utility Methods -------------------- #
    def test_strip_html_tags(self):
        html = "<p>Hello <b>John</b>!</p>"
        self.assertEqual(UniCoreFW.strip_html_tags(html), "Hello John!")

    def test_slugify(self):
        self.assertEqual(UniCoreFW.slugify("Hello, World!"), "hello-world")
        self.assertEqual(UniCoreFW.slugify("  multi   spaces  "), "multi-spaces")

    def test_mask_sensitive(self):
        text = "Card: 1234-5678-9012-3456"
        masked = UniCoreFW.mask_sensitive(text, r"\d")
        self.assertEqual(masked, "Card: ****-****-****-****")

    def test_highlight_matches(self):
        text = "Hello, world!"
        highlighted = UniCoreFW.highlight_matches(text, "o", "[", "]")
        self.assertEqual(highlighted, "Hell[o], w[o]rld!")

    def test_normalize_whitespace(self):
        text = "Too   many \n spaces \t here"
        result = UniCoreFW.normalize_whitespace(text)
        self.assertEqual(result, "Too many spaces here")

    def test_dedent_text(self):
        text = """\
            def function():
                return True
        """
        dedented = UniCoreFW.dedent_text(text)
        # 'dedented' should start at column 0
        self.assertTrue(dedented.startswith("def function():"))
        self.assertIn("return True", dedented)

    # -------------- Example for Encryption (if using cryptography) -------------- #
    # If you implemented encrypt_string / decrypt_string with cryptography:
    #
    # def test_encrypt_decrypt_string(self):
    #     try:
    #         key = UniCoreFW.generate_key()
    #         original = "my secret"
    #         encrypted = UniCoreFW.encrypt_string(original, key)
    #         decrypted = UniCoreFW.decrypt_string(encrypted, key)
    #         self.assertEqual(decrypted, original)
    #     except RuntimeError:
    #         # If cryptography is not installed, skip
    #         self.skipTest("cryptography library not installed")


if __name__ == "__main__":
    unittest.main()
