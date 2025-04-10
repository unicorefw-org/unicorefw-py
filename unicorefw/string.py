"""
String manipulation functions for UniCoreFW.

This module contains advanced, chainable methods for working with strings,
mirroring the style and approach used across UniCoreFW. Functions here allow
you to transform strings into various casing styles, slice or truncate them,
split them into arrays of words, and more.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info
"""

import re
import textwrap
from typing import List, Optional, Union, Callable


def reverse(string: str) -> str:
    """
    Return the reverse of the given string.

    Args:
        string: The string to reverse

    Returns:
        The reversed string

    Example:
        reverse("Hello") -> "olleH"
    """
    return string[::-1]


def camel_case(string: str) -> str:
    """
    Convert a string to camelCase.

    Args:
        string: The string to convert

    Returns:
        The camelCased version of the string

    Example:
        camel_case("Hello world example") -> "helloWorldExample"
    """
    # Split the string into words, removing non-alphanumeric except underscores/spaces
    words = re.split(r"[\s_\-]+", string.strip())
    # First word is lowercased, subsequent words have capitalized first letter
    if not words:
        return ""

    first_word = words[0].lower()
    remaining = [w.capitalize() for w in words[1:]]
    return first_word + "".join(remaining)


def snake_case(string: str, flag: bool = True) -> str:
    """
    Convert a string to snake_case.

    Args:
        string: The string to convert
        flag:  False to convert _____ to _

    Returns:
        The snake_cased version of the string

    Example:
        snake_case("Hello world example") -> "hello_world_example"
    """
    # Lowercase everything, replace spaces/punctuation with underscores
    if(flag):
        words = re.split(r"[\s\-]+", string.strip().lower())
    else:
        words = re.split(r"[\s_\-]+", string.strip().lower())
    return "_".join(word for word in words if word)


def kebab_case(string: str) -> str:
    """
    Convert a string to kebab-case.

    Args:
        string: The string to convert

    Returns:
        The kebab-cased version of the string

    Example:
        kebab_case("Hello world example") -> "hello-world-example"
    """
    words = re.split(r"[\s_\-]+", string.strip().lower())
    return "-".join(word for word in words if word)


def truncate(string: str, length: int, ellipsis: str = "...") -> str:
    """
    Truncate a string to the specified length and append an ellipsis (or custom suffix).

    Args:
        string: The string to truncate
        length: Maximum allowed length before truncation
        ellipsis: Optional suffix to indicate truncation

    Returns:
        The truncated string, possibly with ellipsis appended

    Example:
        truncate("Hello, world!", 5) -> "Hello..."
    """
    if length < 0:
        raise ValueError("Length cannot be negative.")
    if len(string) <= length:
        return string

    # Make sure we don't cut in the middle of the ellipsis
    return string[:length] + ellipsis


def starts_with(string: str, prefix: str) -> bool:
    """
    Check if the string starts with the given prefix.

    Args:
        string: The string to check
        prefix: The prefix to look for

    Returns:
        True if the string starts with prefix; otherwise False

    Example:
        starts_with("Hello world", "He") -> True
    """
    return string.startswith(prefix)


def ends_with(string: str, suffix: str) -> bool:
    """
    Check if the string ends with the given suffix.

    Args:
        string: The string to check
        suffix: The suffix to look for

    Returns:
        True if the string ends with suffix; otherwise False

    Example:
        ends_with("Hello world", "world") -> True
    """
    return string.endswith(suffix)


def words(string: str, pattern: Optional[str] = None) -> List[str]:
    """
    Split the string into an array of words based on a regex pattern.
    If no pattern is provided, splits on whitespace.

    Args:
        string: The string to split
        pattern: Optional regex pattern for splitting

    Returns:
        A list of words in the string

    Example:
        words("Hello, world!") -> ["Hello,", "world!"]
    """
    if pattern is None:
        pattern = r"\s+"  # Default splits on whitespace
    return [w for w in re.split(pattern, string) if w]


def humanize(string: str) -> str:
    """
    Convert a snake_case, kebab-case, or underscored string into a human-readable form.
    For instance, it replaces underscores/dashes with spaces and capitalizes the first letter.

    Args:
        string: The string to humanize

    Returns:
        A human-readable version of the string

    Example:
        humanize("hello_world_example") -> "Hello world example"
    """
    # Replace underscores or dashes with spaces
    text = re.sub(r"[_\-]+", " ", string.strip())
    return text.capitalize()


def slice(string: str, start: int = 0, end: Optional[int] = None) -> str:
    """
    Return a substring of 'string' from index 'start' up to, but not including, 'end'.
    If 'end' is None, slices until the end of the string.

    Args:
        string: The string to slice
        start: Starting index
        end: Ending index (non-inclusive), defaults to None

    Returns:
        The sliced substring

    Example:
        slice("Hello world", 1, 5) -> "ello"
    """
    return string[start:end]


def replace_all(string: str, find: str, replacement: str) -> str:
    """
    Replace all occurrences of 'find' in 'string' with 'replacement'.

    Args:
        string: The original string
        find: The substring to find
        replacement: The string to replace 'find' with

    Returns:
        The string with replacements applied

    Example:
        replace_all("banana", "a", "o") -> "bonono"
    """
    return string.replace(find, replacement)


def regex_find_all(string: str, pattern: str, flags: int = 0) -> List[str]:
    """
    Find all non-overlapping matches of a regex pattern in the given string.

    Args:
        string: The string to search.
        pattern: The regular expression pattern to match.
        flags: Optional re.* flags (e.g., re.IGNORECASE, re.MULTILINE).

    Returns:
        A list of all non-overlapping matches in the string.

    Example:
        regex_find_all("abc123xyz456", r"\\d+") -> ["123", "456"]
    """
    return re.findall(pattern, string, flags=flags)


def regex_test(string: str, pattern: str, flags: int = 0) -> bool:
    """
    Test if the string contains at least one match of the regex pattern.

    Args:
        string: The string to test.
        pattern: The regular expression pattern to match.
        flags: Optional re.* flags (e.g., re.IGNORECASE, re.MULTILINE).

    Returns:
        True if there's at least one match; otherwise False.

    Example:
        regex_test("Hello123", r"\\d+") -> True
    """
    return bool(re.search(pattern, string, flags=flags))


def regex_replace(
    string: str,
    pattern: str,
    replacement: Union[str, Callable[[re.Match], str]],
    flags: int = 0
) -> str:
    """
    Replace all matches of the given regex pattern in 'string' with 'replacement'.

    'replacement' can be either a regular string or a callable (match object -> string).
    If it's a callable, each match object is passed for dynamic replacement.

    Args:
        string: The string in which to perform the replacements.
        pattern: The regex pattern to find.
        replacement: A string or callable used to replace each match.
        flags: Optional re.* flags (e.g., re.IGNORECASE, re.MULTILINE).

    Returns:
        A new string with all replacements applied.

    Example:
        regex_replace("abc123", r"\\d+", "#") -> "abc#"
        regex_replace("abc123", r"[a-z]", lambda m: m.group(0).upper()) -> "ABC123"
    """
    return re.sub(pattern, replacement, string, flags=flags)


def regex_extract(
    string: str,
    pattern: str,
    group: int = 0,
    flags: int = 0
) -> Optional[str]:
    """
    Find the first match of 'pattern' in 'string' and return the specified capture group.

    Args:
        string: The string to search.
        pattern: The regex pattern to match.
        group: The capture group index to return (default 0 = entire match).
        flags: Optional re.* flags (e.g., re.IGNORECASE, re.MULTILINE).

    Returns:
        The matched substring if found; otherwise None.

    Example:
        regex_extract("Name: Alice, Age: 30", r"Name:\\s+(\\w+)", 1) -> "Alice"
    """
    match = re.search(pattern, string, flags=flags)
    return match.group(group) if match else None


def regex_extract_all(
    string: str,
    pattern: str,
    group: int = 0,
    flags: int = 0
) -> List[str]:
    """
    Find all non-overlapping matches of 'pattern' in 'string' and return the specified capture group.

    Args:
        string: The string to search.
        pattern: The regex pattern to match.
        group: The capture group index to return (default 0 = entire match).
        flags: Optional re.* flags (e.g., re.IGNORECASE, re.MULTILINE).

    Returns:
        A list of matched substrings, possibly empty if no matches are found.

    Example:
        regex_extract_all("Name: Alice, Name: Bob, Name: Charlie",
                          r"Name:\\s+(\\w+)", 1)
        -> ["Alice", "Bob", "Charlie"]
    """
    matches = re.finditer(pattern, string, flags=flags)
    return [m.group(group) for m in matches]

def strip_html_tags(string: str) -> str:
    """
    Remove all HTML tags from a string.

    Args:
        string: The string to process.

    Returns:
        A copy of the string with all HTML tags removed.

    Example:
        strip_html_tags("<p>Hello <em>world</em>!</p>")
        -> "Hello world!"
    """
    # This pattern finds anything of the form <...>
    # Note: This is a simplistic approach; for complex HTML parsing,
    #       consider a dedicated HTML parser.
    return re.sub(r"<[^>]*>", "", string)


def slugify(string: str, delimiter: str = "-") -> str:
    """
    Convert a string into a URL-friendly slug.

    1. Lowercases the string
    2. Removes non-alphanumeric characters (except spaces)
    3. Replaces whitespace with the given delimiter

    Args:
        string: The string to slugify.
        delimiter: The delimiter to replace spaces, defaults to '-'.

    Returns:
        A URL-friendly slug string.

    Example:
        slugify("Hello, World!") -> "hello-world"
    """
    # Lowercase
    text = string.lower().strip()
    # Remove characters except alphanumerics and spaces
    text = re.sub(r"[^a-z0-9\s]+", "", text)
    # Replace whitespace with the chosen delimiter
    return re.sub(r"\s+", delimiter, text)


def mask_sensitive(string: str, pattern: str, mask_char: str = "*") -> str:
    """
    Mask sensitive information by replacing pattern matches with the specified character(s).
    Great for hiding phone numbers, credit-card details, etc.

    Args:
        string: The string to process.
        pattern: A regex pattern capturing what should be masked.
        mask_char: The character (or string) to replace each matched group with.

    Returns:
        A new string where every match of pattern is replaced by mask_char repeated
        for the length of each match.

    Example:
        # Hide digits with a simple pattern (all digits)
        mask_sensitive("Card: 1234-5678-9012-3456", r"\\d")
        -> "Card: ****-****-****-****"
    """

    def mask_match(m: re.Match) -> str:
        return mask_char * len(m.group(0))

    return re.sub(pattern, mask_match, string)


def highlight_matches(
    string: str,
    pattern: str,
    highlight_start: str = "<<",
    highlight_end: str = ">>",
    flags: int = 0
) -> str:
    """
    Surround each regex match with highlight markers.

    Args:
        string: The input text.
        pattern: The regex pattern to highlight.
        highlight_start: The prefix for each match.
        highlight_end: The suffix for each match.
        flags: Regex flags (e.g., re.IGNORECASE).

    Returns:
        A new string where all matches are wrapped in highlight markers.

    Example:
        highlight_matches("Hello, HELLO, hello!", "hello", "<<", ">>", re.IGNORECASE)
        -> "<<Hello>>, <<HELLO>>, <<hello>>!"
    """

    def wrap_match(m: re.Match) -> str:
        return f"{highlight_start}{m.group(0)}{highlight_end}"

    return re.sub(pattern, wrap_match, string, flags=flags)


def normalize_whitespace(string: str) -> str:
    """
    Replace multiple consecutive whitespace characters (spaces, tabs, newlines)
    with a single space, and trim leading/trailing whitespace.

    Args:
        string: The string to normalize.

    Returns:
        A new string with normalized spacing.

    Example:
        normalize_whitespace("  Too   many  spaces\n  here\t.")
        -> "Too many spaces here ."
    """
    # Collapse consecutive whitespace to a single space
    text = re.sub(r"\s+", " ", string)
    # Strip leading/trailing whitespace
    return text.strip()


def dedent_text(string: str) -> str:
    """
    Remove any common leading whitespace from every line in the string.

    Args:
        string: The string to dedent.

    Returns:
        A new string with shared leading whitespace removed.

    Example:
        text = \"""
            def function():
                pass
        \"""
        dedent_text(text) -> "def function():\n    pass"
    """
    return textwrap.dedent(string)
