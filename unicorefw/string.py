"""
File: unicorefw/string.py
String manipulation functions for UniCoreFW.

This module contains advanced, chainable methods for working with strings,
mirroring the style and approach used across UniCoreFW. Functions here allow
you to transform strings into various casing styles, slice or truncate them,
split them into arrays of words, and more.

Copyright (C) 2024 Kenny Ngo / UniCoreFW.Org / IIPTech.info

This file is part of UniCoreFW. You can redistribute it and/or modify
it under the terms of the [BSD-3-Clause] as published by
the Free Software Foundation.
You should have received a copy of the [BSD-3-Clause] license
along with UniCoreFW. If not, see https://www.gnu.org/licenses/.
"""
from .supporter import (
    _deburr_latin_only,
    _parse_js_regex,
    _to_str
)
import math
import re
import string as _st
import textwrap
from typing import Any, List, Optional, Union, Callable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


# Mapping for Latin-1 Supplement block (U+00C0–U+00FF)
_DEBURR_MAP = {
    'À':'A','Á':'A','Â':'A','Ã':'A','Ä':'A','Å':'A','Æ':'Ae','Ç':'C',
    'È':'E','É':'E','Ê':'E','Ë':'E','Ì':'I','Í':'I','Î':'I','Ï':'I',
    'Ð':'D','Ñ':'N','Ò':'O','Ó':'O','Ô':'O','Õ':'O','Ö':'O','×':' ',
    'Ø':'O','Ù':'U','Ú':'U','Û':'U','Ü':'U','Ý':'Y','Þ':'Th','ß':'ss',
    'à':'a','á':'a','â':'a','ã':'a','ä':'a','å':'a','æ':'ae','ç':'c',
    'è':'e','é':'e','ê':'e','ë':'e','ì':'i','í':'i','î':'i','ï':'i',
    'ð':'d','ñ':'n','ò':'o','ó':'o','ô':'o','õ':'o','ö':'o','÷':' ',
    'ø':'o','ù':'u','ú':'u','û':'u','ü':'u','ý':'y','þ':'th','ÿ':'y'
}
_HTML_ESCAPE_MAP = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#39;",
    "`": "&#96;"
}


def reverse(string: str) -> str:
    """
    Return the reverse of the given string.

    Args:
        string: The string to reverse

    Returns:
        The reversed string

    Examples:
        >>> reverse("Hello")
        "olleH"
    """
    return string[::-1]

def humanize(string: str) -> str:
    """
    Convert a snake_case, kebab-case, or underscored string into a human-readable form.
    For instance, it replaces underscores/dashes with spaces and capitalizes the first letter.

    Args:
        string: The string to humanize

    Returns:
        A human-readable version of the string

    Examples:
        >>> humanize("hello_world_example")
        "Hello world example"
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

    Examples:
        >>> slice("Hello world", 1, 5)
        "ello"
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

    Examples:
        >>> replace_all("banana", "a", "o")
        "bonono"
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

    Examples:
        >>> regex_find_all("abc123xyz456", r"\\d+")
        ["123", "456"]
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

    Examples:
        >>> regex_test("Hello123", r"\\d+", 0)
        True
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

    Examples:
        >>> regex_replace("abc123", r"\\d+", "#", 0)
        "abc#"
        >>> regex_replace("abc123", r"[a-z]", |m| m.as_str().to_uppercase().into(), 0)
        "ABC123"
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

    Examples:
        >>> regex_extract("Name: Alice, Age: 30", r"Name:\\s+(\\w+)", 1, 0)
        "Alice"
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

    Examples:
        >>> regex_extract_all("Name: Alice, Name: Bob, Name: Charlie", r"Name:\\s+(\\w+)", 1)
        ["Alice", "Bob", "Charlie"]
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

    Examples:
        >>> strip_html_tags("<h1>Hello, world!</h1>")
        "Hello, world!"
    """
    # This pattern finds anything of the form <...>
    # Note: This is a simplistic approach; for complex HTML parsing,
    #       consider a dedicated HTML parser.
    return re.sub(r"<[^>]*>", "", string)

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

    Examples:
        // Hide digits with a simple pattern (all digits)
        >>> mask_sensitive("Card: 1234-5678-9012-3456", r"\\d", "*")
        "Card: ****-****-****-****"
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

    Examples:
        >>> highlight_matches("Hello, HELLO, hello!", "hello", "<<", ">>", 2)
        "<<Hello>>, <<HELLO>>, <<hello>>!"
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

    Examples:
        >>> normalize_whitespace("  Too   many  spaces\n  here\t.")
        "Too many spaces here ."
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

    Examples:
        >>> dedent_text("  First line\n  Second line\n  Third line")
        "First line\nSecond line\nThird line"
    """
    return textwrap.dedent(string)


####################################################################################
#  Extended String Functions
####################################################################################

def decapitalize(s: Any) -> str:
    """
    Convert the first character of `s` to lowercase, leaving the rest unchanged.

    Args:
        s: The string or value to transform.

    Returns:
        A new string with first letter lowercase, rest as in original.

    Examples:
        >>> decapitalize("Foo")
        "foo"
        >>> decapitalize("FOO")
        "fOO"
        >>> decapitalize("fOO")
        "fOO"
        >>> decapitalize(None)
        ""
    """
    s = _to_str(s)
    if not s:
        return ""
    return s[0].lower() + s[1:]


def pascal_case(s: Any) -> str:
    """
    Convert `s` to PascalCase (also known as UpperCamelCase): each word capitalized, concatenated.

    Args:
        s: The string or value to transform.

    Returns:
        PascalCased string.

    Examples:
        >>> pascal_case("foo bar")
        "FooBar"
        >>> pascal_case("FOO BAR")
        "FOO BAR"
        >>> pascal_case(None)
        ""
    """
    s = _to_str(s)
    words = re.split(r'[^0-9A-Za-z]+', s)
    return ''.join(capitalize(w) for w in words if w)

def lower_first(s: Any) -> str:
    """
    Lowercase the first character of `s`, leaving the rest of the string untouched.

    Args:
        s: The string or value to transform.

    Returns:
        String with first character lowercased.

    Examples:
        >>> lower_first("Hello")
        "hello"
        >>> lower_first("Hello WORLD")
        "hello WORLD"
        >>> lower_first(None)

    """
    return decapitalize(s)

def upper_first(s: Any) -> str:
    """
    Uppercase the first character of `s`, leaving the rest untouched.

    Args:
        s: The string or value to transform.

    Returns:
        String with first character uppercased.

    Examples:
        >>> upper_first("hello")
        "Hello"
        >>> upper_first("hello world")
        "Hello world"
        >>> upper_first(None)
    """
    return capitalize(s)

def chop(s: Any, size: int) -> List[str]:
    """
    Split the string into chunks of length `size`, starting from the front.
    The last chunk may be shorter if the string length isn’t a multiple of `size`.

    Args:
        s: The string (or other value) to chop.
        size: The chunk length. If size ≤ 0, returns the whole string as a single chunk.

    Returns:
        A list of chunks. Returns [] if the input is None or empty.

    Examples:
        >>> chop("foobarbaz", 3)
        ["foo", "bar", "baz"]
        >>> chop("foobarbazaa", 3)
        ["foo", "bar", "baz", "aa"]
        >>> chop("foo", 4)
        ["foo"]
        >>> chop(None, 3)
        []
    """
    text = _to_str(s)
    if not text or size <= 0:
        return [] if not text else [text]
    result: List[str] = []
    for i in range(0, len(text), size):
        result.append(text[i : i + size])
    return result

def chop_right(s: Any, size: int) -> List[str]:
    """
    Split the string into chunks of length `size`, starting from the right.
    The first chunk may be shorter if the string length isn’t a multiple of `size`.

    Args:
        s: The string (or other value) to chop from the right.
        size: The chunk length. If size ≤ 0, returns the whole string as a single chunk.

    Returns:
        A list of chunks. Returns [] if the input is None or empty.

    Examples:
        >>> chop_right("foobarbaz", 3)
        ["foo", "bar", "baz"]
        >>> chop_right("foobarbazaa", 3)
        ["foo", "bar", "baz", "aa"]
        >>> chop_right("foo", 4)
        ["foo"]
        >>> chop_right(None, 3)
    """
    text = _to_str(s)
    if not text or size <= 0:
        return [] if not text else [text]
    n = len(text)
    rem = n % size
    chunks: List[str] = []
    # first chunk handles the remainder
    start = 0
    if rem:
        chunks.append(text[0:rem])
        start = rem
    # remaining full-size chunks
    for i in range(start, n, size):
        chunks.append(text[i : i + size])
    return chunks

def clean(s: Any) -> str:
    """
    Collapse all whitespace (spaces, tabs, line breaks) to single spaces,
    and trim leading/trailing whitespace.

    Args:
        s: The string (or other value) to clean.

    Returns:
        A cleaned string with no extra spaces. None → "".

    Examples:
        >>> clean("  Too   many  spaces\n  here\t.")
        "Too many spaces here ."
        >>> clean(None)
        ""
    """
    text = _to_str(s)
    # collapse any run of whitespace into a single space, then trim
    return re.sub(r"\s+", " ", text).strip()

def chars(s: Any) -> List[str]:
    """
    Return a list of the individual characters in the string.

    Args:
        s: The string (or other value) to split into chars.

    Returns:
        A list of single-character strings. None or "" → [].

    Examples:
        >>> chars("foobarbaz")
        ["f", "o", "o", "b", "a", "r", "b", "a", "z"]
        >>> chars(-5.6)
        ["-", "5", ".", "6"]
        >>> chars(None)
        []
        >>> chars("")
        []
    """
    text = _to_str(s)
    return list(text) if text else []

def substr_left(s: Any, sep: Any) -> str:
    """
    Return the substring before the first occurrence of `sep`.

    Args:
        s: The string (or value) to inspect.
        sep: The separator to look for.

    Returns:
        The portion of `s` before the first `sep`. If `sep` is empty or None,
        returns the entire string. If `s` is None, returns an empty string.

    Examples:
        >>> substr_left("a_b_c", "_")
        "a"
        >>> substr_left(None, "_")
        ""
    """
    s = "" if s is None else str(s)
    if not sep:
        return s
    sep = str(sep)
    idx = s.find(sep)
    return s if idx == -1 else s[:idx]

def substr_left_end(s: Any, sep: Any) -> str:
    """
    Return the substring before the last occurrence of `sep`.

    Args:
        s: The string (or value) to inspect.
        sep: The separator to look for.

    Returns:
        The portion of `s` up to (but not including) the last `sep`. If `sep`
        is empty or None, returns the entire string. If `s` is None, returns
        an empty string.

    Examples:
        >>> substr_left_end("a_b_c", "_")
        "a_b"
        >>> substr_left_end(None, "_")
        ""
    """
    s = "" if s is None else str(s)
    if not sep:
        return s
    sep = str(sep)
    idx = s.rfind(sep)
    return s if idx == -1 else s[:idx]

def substr_right(s: Any, sep: Any) -> str:
    """
    Return the substring after the first occurrence of `sep`.

    Args:
        s: The string (or value) to inspect.
        sep: The separator to look for.

    Returns:
        The portion of `s` after the first `sep`. If `sep` is empty or None,
        returns the entire string. If `s` is None, returns an empty string.

    Examples:
        >>> substr_right("a_b_c", "_")
        "b_c"
    """
    s = "" if s is None else str(s)
    if not sep:
        return s
    sep = str(sep)
    idx = s.find(sep)
    return s if idx == -1 else s[idx + len(sep):]

def substr_right_end(s: Any, sep: Any) -> str:
    """
    Return the substring after the last occurrence of `sep`.

    Args:
        s: The string (or value) to inspect.
        sep: The separator to look for.

    Returns:
        The portion of `s` after the last `sep`. If `sep` is empty or None,
        returns the entire string. If `s` is None, returns an empty string.

    Examples:
        >>> substr_right_end("a_b_c", "_")
        "c"
    """
    s = "" if s is None else str(s)
    if not sep:
        return s
    sep = str(sep)
    idx = s.rfind(sep)
    return s if idx == -1 else s[idx + len(sep):]

def strip_tags(s: Any) -> str:
    """
    Remove all HTML tags from the string.

    Args:
        s: The string (or value) to clean.

    Returns:
        The string with all `<...>` tags stripped out. If `s` is None or
        empty, returns an empty string.

    Examples:
        >>> strip_tags("<h1>Hello, world!</h1>")
        "Hello, world!"
    """
    from .string import strip_html_tags  # existing helper
    s = "" if s is None else str(s)
    return strip_html_tags(s)


def predecessor(s: Any) -> str:
    """
    Return the character immediately preceding the first character of `s` in Unicode.

    Args:
        s: A one-character string (or value).

    Returns:
        The predecessor character. If `s` is None or empty, returns an empty string.

    Examples:
        >>> predecessor("a")
        "Z"
    """
    s = "" if s is None else str(s)
    if not s:
        return ""
    return chr(ord(s[0]) - 1)

def successor(s: Any) -> str:
    """
    Return the character immediately following the first character of `s` in Unicode.

    Args:
        s: A one-character string (or value).

    Returns:
        The successor character. If `s` is None or empty, returns an empty string.

    Examples:
        >>> successor("a")
        "b"
    """
    s = "" if s is None else str(s)
    if not s:
        return ""
    return chr(ord(s[0]) + 1)

def surround(value: Any, wrapper: Any) -> str:
    """
    Surround `value` with `wrapper` on both sides.

    Args:
        value: The inner content (any type).
        wrapper: The string (or value) to wrap around.

    Returns:
        A new string: wrapper + value + wrapper. If `wrapper` is None,
        returns only the stringified `value`. If `value` is None, treats
        as empty string.

    Examples:
        >>> surround("foo", "**")
        '**foo**'
    """
    val = "" if value is None else str(value)
    if wrapper is None:
        return val
    wrap = str(wrapper)
    return f"{wrap}{val}{wrap}"


def swap_case(s: Any) -> str:
    """
    Swap the case of each letter in `s`.

    Args:
        s: The string (or value) to transform.

    Returns:
        A new string where lowercase letters are uppercased and vice versa.
        Non-letter characters are unchanged. If `s` is None, returns "".

    Examples:
        >>> swap_case("Hello World")
        "hELLO wORLD"
    """
    s = "" if s is None else str(s)
    return "".join(
        ch.lower() if ch.isupper() else ch.upper() if ch.islower() else ch
        for ch in s
    )

def title_case(s: Any) -> str:
    """
    Convert `s` to Title Case (capitalize first letter of each word, rest lowercase).

    Args:
        s: The string (or value) to transform.

    Returns:
        A title-cased string. If `s` is None, returns "".

    Examples:
        >>> title_case("hello world")
        "Hello World"
    """
    s = "" if s is None else str(s)
    def cap(word: str) -> str:
        return word[0].upper() + word[1:].lower() if word else ""
    return " ".join(cap(w) for w in s.split(" "))

def to_lower(s: Any) -> str:
    """
    Convert `s` to all lowercase.

    Args:
        s: The string (or value) to transform.

    Returns:
        Lowercased string. If `s` is None, returns "".

    Examples:
        >>> to_lower("FooBar")
        "foobar"
    """
    return "" if s is None else str(s).lower()

def to_upper(s: Any) -> str:
    """
    Convert `s` to all uppercase.

    Args:
        s: The string (or value) to transform.

    Returns:
        Uppercased string. If `s` is None, returns "".

    Examples:
        >>> to_upper("FooBar")
        "FOOBAR"
    """
    return "" if s is None else str(s).upper()


def has_substr(s: Any, substr: Any, pos: int = 0) -> bool:
    """
    Check whether `substr` occurs in `s`, starting the search at index `pos`.

    Args:
        s:       The string or value to search (None→"").
        substr:  The substring to look for (None or "" → always True).
        pos:     The index to begin searching from.

    Returns:
        True if `substr` is found in `s` at or after `pos`, otherwise False.

    Examples:
        >>> has_substr("abc", "b")
        True
        >>> has_substr("abc", "d")
        False
        >>> has_substr("abc", "")
        True
        >>> has_substr("abc", None)
        False
    """
    text = "" if s is None else str(s)
    needle = "" if substr is None else str(substr)
    if needle == "":
        return True
    try:
        return text.find(needle, pos) != -1
    except Exception:
        return False

def pad(
    string: Optional[str],
    length: int,
    chars: str = " "
) -> str:
    """
    Pad `string` on both sides to reach the given total `length`, using `chars` cyclically.

    Args:
        string: The original string (None treated as "").
        length: Desired total length of the output string.
        chars: Characters to cycle for padding.

    Returns:
        The padded string. If `string` is longer than `length`, returns it unchanged.

    Examples:
        >>> pad("abc", 9, "12")
        "1abc1"
        >>> pad("abc", 10, "12")
        "1abc12"
        >>> pad("abc", 11, "12")
        "12abc12"
        >>> pad("abc", 12, "12")
        "12abc12"
        >>> pad("abc", 8, "_-")  #:contentReference[oaicite:7]{index=7}
        "_-abc_-_"  
    """
    s = string or ""
    if len(s) >= length:
        return s
    pad_total = length - len(s)
    left = pad_total // 2
    right = pad_total - left
    # build a long enough pad string and slice
    def build(n):
        cycle = chars or " "
        times = (n + len(cycle) - 1) // len(cycle)
        return (cycle * times)[:n]
    return build(left) + s + build(right)

def pad_start(
    string: Optional[str],
    length: int,
    chars: str = " "
) -> str:
    """
    Pad `string` on the left side to reach `length`, using `chars` cyclically
    (taking characters from the end of the cycle when truncating).

    Args:
        string: The original string (None treated as "").
        length: Desired total length.
        chars: Characters to cycle for padding.

    Returns:
        The left-padded string.

    Examples:
        >>> pad_start("a", 8, "12")
        "121212a"
    """
    s = string or ""
    if len(s) >= length:
        return s
    pad_count = length - len(s)
    cycle = chars or " "
    times = (pad_count + len(cycle) - 1) // len(cycle)
    big = cycle * times
    # take last pad_count chars
    return big[-pad_count:] + s

def pad_end(
    string: Optional[str],
    length: int,
    chars: str = " "
) -> str:
    """
    Pad `string` on the right side to reach `length`, using `chars` cyclically.

    Args:
        string: The original string (None treated as "").
        length: Desired total length.
        chars: Characters to cycle for padding.

    Returns:
        The right-padded string.

    Examples:
        >>> pad_end("a", 9, "12")
        "a12121212"
    """
    s = string or ""
    if len(s) >= length:
        return s
    pad_count = length - len(s)
    cycle = chars or " "
    times = (pad_count + len(cycle) - 1) // len(cycle)
    big = cycle * times
    return s + big[:pad_count]

def quote(
    value: Any,
    wrapper: Optional[Any] = '"'
) -> str:
    """
    Wrap `value` (converted to string) with `wrapper` on both sides.
    If `wrapper` is None, returns the raw string (or "" for None).

    Args:
        value: The value to quote.
        wrapper: Character or string to wrap around `value`.

    Returns:
        The quoted string.

    Examples:
        >>> quote("foo")
        '"foo"'
        >>> quote("foo", "'")
        "'foo'"
    """
    text = "" if value is None else str(value)
    if wrapper is None:
        return text
    w = str(wrapper)
    if not w:
        return text
    return f"{w}{text}{w}"

def capitalize(s: Any, lower: bool = True) -> str:
    """
    Uppercase the first character of `s`, with optional lowercasing of the rest.

    Args:
        s:     The string or value to transform (None → "").
        lower: If True (default), the remainder of the string is lowercased;
               if False, the remainder is left as-is.

    Returns:
        A string with its first character uppercased, and the rest
        handled per the `lower` flag.

    Examples:
        >>> capitalize("hello")
        "Hello"
        >>> capitalize("heLLo", lower=False)
        "HeLLo"
        >>> capitalize("hello", lower=True)
        "Hello"
    """
    text = "" if s is None else str(s)
    if not text:
        return ""
    first = text[0].upper()
    rest = text[1:].lower() if lower else text[1:]
    return first + rest


def count_substr(s: Any, substr: Any) -> int:
    """
    Count non-overlapping occurrences of `substr` in `s`.

    Args:
        s:      The haystack (None → "").
        substr: The needle (None → always 0). An empty string → len(haystack)+1.

    Returns:
        The number of occurrences of `substr` within `s`.

    Examples:
        >>> count_substr("foobar", "o")
        2
        >>> count_substr("foobar", "oo")
        1
        >>> count_substr("", "")
        1
        >>> count_substr("1", "")
        2
        >>> count_substr(1.4, "")
        4
        >>> count_substr(None, "x")
        0
        >>> count_substr("xyz", None) 
        0
    """
    text = "" if s is None else str(s)
    if substr is None:
        return 0
    sub = str(substr)
    if sub == "":
        return len(text) + 1
    return text.count(sub)
def replace(
    string: Any,
    pattern: Optional[Union[str, re.Pattern]],
    replacement: Any,
    ignore_case: bool = False,
    count: int = 0
) -> str:
    """
    Replace up to `count` occurrences of `pattern` in `string` with `replacement`.
    If `count` is 0 (default), replaces all occurrences.
    If `ignore_case` is True, matching is case-insensitive.
    `pattern` may be a plain string or a compiled regex.

    Args:
        string:      The input text (None→"").
        pattern:     Substring or regex to replace (None or ""→no-op).
        replacement: Replacement text (None→"").
        ignore_case: Case-insensitive match if True.
        count:       Max replacements; 0 → unlimited.

    Returns:
        The resulting string.

    Examples:
        >>> replace("foo", "o", "a")
        "faa"
        >>> replace("foo", "o", "a", count=1)
        "fao"
        >>> replace("fOO", "o", "a")
        "fOO"
        >>> replace("fOO", "o", "a", True)
        "faa"
        >>> replace("foo", "", "x")
        "foo"
        >>> replace(54.7,  "5", "6")
        "64.7"
    """
    text = "" if string is None else str(string)
    # no pattern → return original
    if pattern is None:
        return text
    # coerce replacement
    repl = "" if replacement is None else str(replacement)
    # empty pattern → no-op
    if isinstance(pattern, str) and pattern == "":
        return text
    # build regex
    if isinstance(pattern, re.Pattern):
        regex = pattern
    else:
        pat = str(pattern)
        flags = re.IGNORECASE if ignore_case else 0
        regex = re.compile(re.escape(pat), flags)
    # do replace
    return regex.sub(repl, text, count)


def replace_start(
    string: Any,
    pattern: Any,
    replacement: Any
) -> str:
    """
    Replace `pattern` at the start of `string` with `replacement`, once.

    Args:
        string:      The input text (None→"").
        pattern:     Substring or regex (first match only).
        replacement: Replacement text (None→"").

    Returns:
        The resulting string.

    Examples:
        >>> replace_start("foo", "f", "a")
        "aoo"
        >>> replace_start("foo", "o", "a")
        "foo"
    """
    text = "" if string is None else str(string)
    if pattern is None or replacement is None and replacement is not False:
        repl = "" if replacement is None else str(replacement)
    else:
        repl = str(replacement)
    # compile regex for start
    if isinstance(pattern, re.Pattern):
        regex = re.compile(rf'^(?:{pattern.pattern})')
    else:
        pat = re.escape(str(pattern)) if pattern is not None else ""
        regex = re.compile(rf'^{pat}')
    return regex.sub(repl, text, 1)


def replace_end(
    string: Any,
    pattern: Any,
    replacement: Any
) -> str:
    """
    Replace `pattern` at the end of `string` with `replacement`, once.

    Args:
        string:      The input text (None→"").
        pattern:     Substring or regex (last match only).
        replacement: Replacement text (None→"").

    Returns:
        The resulting string.

    Examples:
        >>> replace_end("foo", "o", "a")
        "foa"
        >>> replace_end("foo", "f", "a")
        "foo"
    """
    text = "" if string is None else str(string)
    if pattern is None:
        return text
    repl = "" if replacement is None else str(replacement)
    # compile regex for end
    if isinstance(pattern, re.Pattern):
        regex = re.compile(rf'(?:{pattern.pattern})$')
    else:
        pat = re.escape(str(pattern))
        regex = re.compile(rf'{pat}$')
    return regex.sub(repl, text, 1)


def separator_case(
    string: Any,
    sep: Any = '-'
) -> str:
    """
    Normalize `string` into lowercase “words” joined by `sep`. Splits on any
    non-alphanumeric chars, collapses empties, lowercases.

    Args:
        string: The input text (None→"").
        sep:    Separator to join (None→"").

    Returns:
        The normalized string.

    Examples:
        >>> separator_case("Foo Bar", "-")
        "foo-bar"
        >>> separator_case("foo__bar_baz", "_")
        "foo_bar_baz"
        >>> separator_case(None, "_")
        ""
    """
    text = "" if string is None else str(string)
    sep_str = "" if sep is None else str(sep)
    # split on any non-alphanumeric
    parts = re.split(r'[^0-9A-Za-z]+', text)
    words = [w.lower() for w in parts if w]
    return sep_str.join(words)



# --- 1. Escaping & Unescaping ---

def escape_reg_exp(string: Any) -> str:
    """
    Escape the characters that have special meaning in regular expressions.

    Args:
        string: The input to escape.

    Returns:
        A string with all RegExp metacharacters escaped.

    Examples:
        >>> escape_reg_exp("[test](1.2)")
        "\\[test\\]\\(1\\.2\\)"
    """
    s = "" if string is None else str(string)
    return re.escape(s)

# --- 2. Ensuring prefix/suffix & Trimming ---

def ensure_starts_with(string: Any, prefix: Any) -> str:
    """
    Ensure that `string` begins with `prefix`, adding it if missing.

    Args:
        string: The original text.
        prefix: The prefix to enforce.

    Returns:
        The string guaranteed to start with prefix.

    Examples:
        >>> ensure_starts_with("world", "hello ")
        "hello world"
    """
    s = "" if string is None else str(string)
    p = "" if prefix is None else str(prefix)
    return s if (not p or s.startswith(p)) else p + s


def ensure_ends_with(string: Any, suffix: Any) -> str:
    """
    Ensure that `string` ends with `suffix`, adding it if missing.

    Args:
        string: The original text.
        suffix: The suffix to enforce.

    Returns:
        The string guaranteed to end with suffix.

    Examples:
        >>> ensure_ends_with("hello", "!")
        "hello!"
    """
    s = "" if string is None else str(string)
    suf = "" if suffix is None else str(suffix)
    return s if (not suf or s.endswith(suf)) else s + suf


def trim_start(string: Any, chars: Optional[str] = None) -> str:
    """
    Trim whitespace or specified characters from the start of the string.

    Args:
        string: The string to trim.
        chars: Optional set of characters to remove; defaults to whitespace.

    Returns:
        The trimmed string.

    Examples:
        >>> trim_start("  abc  ")
        "abc  "
    """
    s = "" if string is None else str(string)
    return s.lstrip() if chars is None else s.lstrip(chars)


def trim_end(string: Any, chars: Optional[str] = None) -> str:
    """
    Trim whitespace or specified characters from the end of the string.

    Args:
        string: The string to trim.
        chars: Optional set of characters to remove; defaults to whitespace.

    Returns:
        The trimmed string.

    Examples:
        >>> trim_end("  abc  ")
        "  abc"
    """
    s = "" if string is None else str(string)
    return s.rstrip() if chars is None else s.rstrip(chars)


def trim(string: Any, chars: Optional[str] = None) -> str:
    """
    Trim whitespace or specified characters from both ends of the string.

    Args:
        string: The string to trim.
        chars: Optional set of characters to remove; defaults to whitespace.

    Returns:
        The trimmed string.

    Examples:
        >>> trim("  abc  ")
        "abc"
    """
    return trim_end(trim_start(string, chars), chars)


def insert_substr(string: Any, index: int, substring: Any) -> str:
    """
    Insert `substring` into `string` at position `index`.

    Args:
        string: The original text.
        index: The zero-based insertion point.
        substring: The text to insert.

    Returns:
        Modified string.

    Examples:
        >>> insert_substr("hello", 2, "X")
        "heXllo"
    """
    s = "" if string is None else str(string)
    sub = "" if substring is None else str(substring)
    try:
        idx = int(index)
    except (TypeError, ValueError):
        idx = 0
    if idx < 0:
        idx = 0
    if idx > len(s):
        idx = len(s)
    return s[:idx] + sub + s[idx:]


def unquote(string: Any, quote_char: Optional[str] = None) -> str:
    """
    Remove matching surrounding quotes from a string.

    Args:
        string: The possibly-quoted text.
        quote_char: If given, only strips that character; otherwise strips matching ' or ".

    Returns:
        Unquoted string.

    Examples:
        >>> unquote('"hello"')
        "hello"
        >>> unquote("`hey`", "`")
        "hey"
    """
    s = "" if string is None else str(string)
    if quote_char:
        qc = str(quote_char)
        if s.startswith(qc) and s.endswith(qc) and len(s) >= 2:
            return s[1:-1]
        return s
    if len(s) >= 2 and s[0] == s[-1] and s[0] in {"'", '"', "`"}:
        return s[1:-1]
    return s


def reg_exp_js_match(text: Any, js_literal: Any) -> List[str]:
    """
    Match JS-style regex literal against text, returning list of matches.
    Non-global returns at most one; global returns all.
    """
    s = "" if text is None else str(text)
    pat, flags, is_global = _parse_js_regex("" if js_literal is None else str(js_literal))
    try:
        regex = re.compile(pat, flags)
    except re.error:
        return []
    if is_global:
        return [m.group(0) for m in regex.finditer(s)]
    m = regex.search(s)
    return [m.group(0)] if m else []

def reg_exp_js_replace(
    text: Any,
    js_literal: Any,
    replacement: Any
) -> str:
    """
    Replace via JS‐style regex literal.  
    - 'g' flag → replace all, otherwise only first.  
    - 'i' flag → case‐insensitive.  

    Args:
        text:        The input text (None→"").
        js_literal:  JS regex literal (None or ""→no-op).
        replacement: Replacement text (None→"").

    Returns:
        The resulting string.

    Examples:
        >>> reg_exp_js_replace("abc", "/a/i", "X")
        "Xbc"
    """
    s = "" if text is None else str(text)
    rep = "" if replacement is None else str(replacement)
    pat, flags, is_global = _parse_js_regex("" if js_literal is None else str(js_literal))
    try:
        regex = re.compile(pat, flags)
    except re.error:
        return s
    count = 0 if is_global else 1
    return regex.sub(rep, s, count)

def starts_with(string: Any, prefix: Any, position: Optional[int] = 0) -> bool:
    """
    Check if `string` starts with `prefix` at `position`.

    Args:
        string:  The input (None → "").
        prefix:  The search prefix (None → "").
        position: Index in `string` to begin matching (clamped to [0, len(string)]).

    Returns:
        True if `string[position:]` begins with `prefix`.

    Examples:
        >>> starts_with("abc", "a")
        True
        >>> starts_with("abc", "b")
        False
        >>> starts_with("abc", "a", 0)
        rue
        >>> starts_with("abc", "a", 1)
        False
        >>> starts_with(5.78, 5)
        True
        >>> starts_with(None, None)
        True
    """
    s = "" if string is None else str(string)
    p = "" if prefix is None else str(prefix)

    try:
        # Ensure position is not None before calling int()
        pos = int(position) if position is not None else 0
    except (TypeError, ValueError):
        pos = 0

    # clamp to [0, len(s)]
    pos = max(0, min(pos, len(s)))
    return s.startswith(p, pos)

def ends_with(string: Any, suffix: Any, position: Optional[int] = None) -> bool:
    """
    Check if `string` ends with `suffix` at `position`.

    Args:
        string:  The input (None → "").
        suffix:  The search suffix (None → "").
        position: Length of string to consider; effectively tests
                  `string[:position].endswith(suffix)`. If None,
                  uses full length.

    Returns:
        True if `string[:position]` ends with `suffix`.

    Examples:
        >>> ends_with("abc", "c")
        True
        >>> ends_with("abc", "b")
        False
        >>> ends_with("abc", "c", 3)
        True
        >>> ends_with("abc", "c", 2)
        False
        >>> ends_with(6.34, 4)
        True  # "6.34"[:len]=="6.34".endswith("4")
        >>> ends_with(None, None)
        True
    """
    s = "" if string is None else str(string)
    suf = "" if suffix is None else str(suffix)
    if position is None:
        pos = len(s)
    else:
        try:
            pos = int(position)
        except (TypeError, ValueError):
            pos = len(s)
    # clamp to [0, len(s)]
    pos = max(0, min(pos, len(s)))
    return s[:pos].endswith(suf)

def camel_case(value: Any) -> str:
    """
    Convert `value` to camelCase by stripping Latin accents,
    dropping apostrophes, and splitting on punctuation and whitespace.

    Args:
        value: Input (None → "").

    Returns:
        camelCased string.

    Examples:
        >>> camel_case("Foo!#Bar's")
        "fooBars"
        >>> camel_case("J'peux..., ça m'fa pas mal.")
        "jpeuxCaMfaPasMal"
    """
    if value is None:
        return ""

    value = "" if value is None else str(value)
    value = _deburr_latin_only(value)


    # Drop apostrophes explicitly
    value = value.replace("'", "")

    # Split on punctuation (except apostrophes) and whitespace
    punctuations = _st.punctuation.replace("'", "")
    words = re.split(rf"[{re.escape(punctuations)}\s]+", value.strip())

    # Filter out empty strings resulting from split
    words = [word for word in words if word]

    if not words:
        return ""

    # Build camelCase
    first_word = words[0].lower()
    other_words = [word.capitalize() for word in words[1:]]

    return first_word + "".join(other_words)


# --- 2. Accents & HTML ---

def deburr(string: Any) -> str:
    """
    Remove Latin-1 Supplement accents (U+00C0–U+00FF), leaving other scripts untouched.

    Args:
        string: The input text (None → "").

    Returns:
        A new string where each accented Latin-1 character is replaced
        by its ASCII equivalent (e.g. “Æ”→“AE”, “ß”→“ss”), “×”/“÷” → space.

    Examples:
        >>> deburr("déjà vu")
        "deja vu"
        >>> deburr("\xc0\xc1\xc6\xdf")
        "AAAEss"
    """
    s = "" if string is None else str(string)
    # Direct map for U+00C0–U+00FF
    return "".join(_DEBURR_MAP.get(ch, ch) for ch in s)

def lines(string: Optional[str]) -> List[str]:
    """
    Split a string into lines, handling Unix (\\n), Windows (\\r\\n) and old Mac (\\r) breaks.

    Drops a trailing empty line if one is produced (so "foo\\n" → ["foo"], not ["foo", ""]).

    Args:
        string: The string to split, or None.

    Returns:
        A list of lines.

    Examples:
        >>> lines("foo\\nbar")
        ["foo", "bar"]
        >>> lines("foo\\rbar")
        ["foo", "bar"]
        >>> lines("foo\\r\\nbar")
        ["foo", "bar"]
        >>> lines("foo\\n")
        ["foo"]
        >>> lines("\\nfoo")
        ["", "foo"]
        >>> lines("")
        []
        >>> lines(None)
        []
    """
    if string is None:
        return []
    # Normalize all CRLF or CR to LF
    text = string.replace('\r\n', '\n').replace('\r', '\n')
    parts = text.split('\n')
    # Drop trailing empty line if present
    if parts and parts[-1] == "":
        parts.pop()
    return parts


def words(string: Optional[str], pattern: Optional[str] = None) -> List[str]:
    """
    Extract “words” (letter‐runs and number‐runs) from a string, including camelCase splits.

    Splits on transitions between lowercase→Uppercase, on digit boundaries, and ignores all other punctuation.

    Args:
        string: The string to parse, or None.

    Returns:
        A list of word fragments or numeric fragments.

    Examples:
        >>> words("hello world!")
        ["hello", "world"]
        >>> words("hello_world")
        ["hello", "world"]
        >>> words("hello!@#world")
        ["hello", "world"]
        >>> words("enable 24h format")
        ["enable", "24", "h", "format"]
        >>> words("tooLegit2Quit")
        ["too", "Legit", "2", "Quit"]
        >>> words("xhr2Request")
        ["xhr", "2", "Request"]
        >>> words(" ") 
        []
        >>> words("")
        []
        >>> words(None)
        []
    """
    if not isinstance(string, str):
        return []
    
    if pattern is not None:
        _pattern = re.compile(pattern)
        return [w for w in re.split(_pattern, string) if w]

    # Match uppercase acronyms, camelCase segments, or numeric runs:
    _pattern = re.compile(r'''
        [A-Z]+(?=[A-Z][a-z])    |  # all-caps before a camelCase start (e.g. "XMLHttp" -> "XML")
        [A-Z]?[a-z]+            |  # uppercase-started words or all-lowercase runs
        \d+                       # digit runs
    ''', re.VERBOSE)
    return _pattern.findall(string)
    
# --- Series & Truncation Helpers ---
def series_phrase(
    items: Any,
    sep: Any = ", ",
    last_sep: Any = " and "
) -> str:
    """
    Join a sequence into a human‐readable series without Oxford comma.

    Args:
        items:     Iterable of values (None→empty list).
        sep:       Delimiter between all but last two items.
        last_sep:  Delimiter between the penultimate and last item.

    Returns:
        A joined string:
          []            → ""
          ["foo"]       → "foo"
          ["foo","bar"] → "foo and bar"
          ["a","b","c"] → "a, b and c"

    Examples:
        >>> series_phrase(["a","b","c"])
        "a, b and c"
        >>> series_phrase(["a","b"], ";", " or ")
        "a; b or c"
        >>> series_phrase([None,5], None, None)
        "5"
    """
    # Normalize inputs
    seq = list(items) if items is not None else []
    sep_str = "" if sep is None else str(sep)
    last_str = "" if last_sep is None else str(last_sep)

    # Filter out None or empty-string
    parts = [str(x) for x in seq if x is not None and str(x) != ""]

    n = len(parts)
    if n == 0:
        return ""
    if n == 1:
        return parts[0]
    if n == 2:
        return parts[0] + last_str + parts[1]
    # n >= 3
    return sep_str.join(parts[:-1]) + last_str + parts[-1]

def prune(
    string: Any,
    length: Optional[int] = None,
    omission: str = "..."
) -> str:
    """
    Prune `string` to exactly `length` characters (default 0) then append `omission`.
    If a custom `omission` is provided that is longer than `length`, returns the original string.
    Truncation always splits at word boundaries (spaces), dropping trailing punctuation.

    Args:
        string:   The input text (None→"").
        length:   Number of characters to keep before omission. Defaults to 0.
        omission: Text to append when pruning. Defaults to "...".

    Returns:
        Possibly‐pruned text.

    Examples:
        >>> prune("Hello, world")
        "..."
        >>> prune("Hello, world", 5)
        "Hello..."
        >>> prune("Hello, world", 8)
        "Hello..."
        >>> prune("Hello, world", 5, " (more)")
        "Hello, world"
    """
    s = "" if string is None else str(string)
    try:
        keep = int(length) if length is not None else 0
    except (TypeError, ValueError):
        keep = 0
    omit = "" if omission is None else omission

    # If custom omission too long, skip pruning
    if omission not in (None, "...") and len(omit) > keep:
        return s

    # If input fits, or length==0, we still proceed:
    if keep <= 0:
        head = ""
    elif len(s) <= keep:
        return s
    else:
        head = s[:keep]

    # If input shorter than or equal keep, no prune
    if len(s) <= keep:
        return s

    # Try break at last space
    idx = head.rfind(" ")
    if idx != -1:
        head = head[:idx]

    # Strip trailing non-alphanumeric
    while head and not head[-1].isalnum():
        head = head[:-1]

    return head + omit


def kebab_case(value: Any) -> str:
    """
    Convert a string to kebab-case.

    This function is an implementation of the `kebabCase` function from
    the Lodash library. It takes a string and converts it to kebab-case,
    inserting hyphens between words and converting the string to lower
    case.
    
    Args:
        value: The string to convert to kebab-case.

    Returns:    
        The kebab-cased version of the string.

    Examples:
        >>> kebab_case("Hello World")
        "hello-world"
        >>> kebab_case("Hello123World")
        "hello-123-world"
        >>> kebab_case("Hello  World")
        "hello-world"
    """
    s = "" if value is None else str(value)
    s = _deburr_latin_only(s).replace("'", "")
    # insert spaces at camelCase and digit/letter boundaries
    s = re.sub(r"([a-z\d])([A-Z])", r"\1 \2", s)
    s = re.sub(r"(\d)([A-Za-z])", r"\1 \2", s)
    s = re.sub(r"([A-Za-z])(\d)", r"\1 \2", s)
    # now split on ASCII punctuation (minus apostrophe) or whitespace
    sep = _st.punctuation.replace("'", "")
    parts = re.split(rf"[{re.escape(sep)}\s]+", s.strip())
    return "-".join(p.lower() for p in parts if p)

def snake_case(string: str, preserve_multiple_underscores: bool = True) -> str:
    """
    Convert a string to snake_case.

    Preserves multiple underscores when `preserve_multiple_underscores` is True.

    Args:
        string: The string to convert.
        preserve_multiple_underscores: If True, underscores in the input are
                                        preserved as-is; otherwise they are normalized.

    Returns:
        Snake_cased version of the string.

    Examples:
        >>> snake_case("Hello World")
        "hello_world"
        >>> snake_case("Already__snake_case")
        "already__snake_case"
        >>> snake_case("Hello123World")
        "hello_123_world"
    """
    s = "" if string is None else str(string)
    s = _deburr_latin_only(s).replace("'", "")
    s = re.sub(r"([a-z\d])([A-Z])", r"\1 \2", s)
    s = re.sub(r"(\d)([A-Za-z])", r"\1 \2", s)
    s = re.sub(r"([A-Za-z])(\d)", r"\1 \2", s)

    sep = _st.punctuation.replace("'", "")
    if preserve_multiple_underscores:
        # Remove underscore from split set so it's preserved in output
        sep = sep.replace("_", "")

    # Split on allowed punctuation (minus underscore) and whitespace
    parts = re.split(rf"[{re.escape(sep)}\s]+", s.strip())

    return "_".join(p.lower() for p in parts if p)


# In string.py

def lower_case(value: Any) -> str:
    """
    Convert a string to lower_case.

    This function is an implementation of the `lowerCase` function from
    the Lodash library. It takes a string and converts it to lower_case,
    inserting spaces between words and converting the string to lower case.
    
    Args:
        value: The string to convert to lower_case.

    Returns:    
        The lower_cased version of the string.

    Examples:
        >>> lower_case("Hello World")
        "hello world"
        >>> lower_case("Hello123World")
        "hello 123 world"
        >>> lower_case("Hello  World")
        "hello world"
    """
    if value is None:
        return ""
    s = str(value)
    # reuse the boundary‐insertion from kebab_case
    s = re.sub(r"([a-z\d])([A-Z])", r"\1 \2", s)
    s = re.sub(r"(\d)([A-Za-z])", r"\1 \2", s)
    s = re.sub(r"([A-Za-z])(\d)", r"\1 \2", s)
    # split on non-alphanumeric
    parts = re.split(r"[^0-9A-Za-z\u0080-\uFFFF]+", s)
    return " ".join(p.lower() for p in parts if p)

def upper_case(value: Any) -> str:
    """
    This function is an implementation of the `upperCase` function from
    the Lodash library. It takes a string and converts it to upper case,
    inserting spaces between words and converting the string to upper case.
    
    Args:
        value: The string to convert to upper_case.

    Returns:    
        The upper_cased version of the string.    
    
    Examples:
        >>> upper_case("Hello World")
        "HELLO WORLD"
        >>> upper_case("Hello123World")
        "HELLO 123 WORLD"
        >>> upper_case("Hello  World")
        "HELLO WORLD"
    """
    if value is None:
        return ""
    s = str(value)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1 \2", s)
    s = re.sub(r"(\d)([A-Za-z])", r"\1 \2", s)
    s = re.sub(r"([A-Za-z])(\d)", r"\1 \2", s)
    parts = re.split(r"[^0-9A-Za-z\u0080-\uFFFF]+", s)
    return " ".join(p.upper() for p in parts if p)

def truncate(
    string: Any,
    length: Optional[int] = None,
    omission: str = "...",
    separator: Union[str, re.Pattern, None] = None
) -> str:
    """
    Truncate `string` to a maximum length and append an omission marker if truncated.

    This function merges the flexible behavior of the extended truncate with the
    shorthand of the simpler version.

    Args:
        string: String to truncate.
        length: Maximum string length (including omission). Defaults to 30.
        omission: String to indicate text is omitted (default "...").
        separator: Optional string or regex pattern. If provided, the cut is moved
                   back to the last occurrence of the separator before the limit.

    Returns:
        The truncated string if longer than `length`; otherwise the original string.

    Examples:
        >>> truncate("hello world", 5)
        'he...'
        >>> truncate("hello world", 5, "..")
        'hel..'
        >>> truncate("hello world", 10)
        'hello w...'
        >>> truncate("hello world", 10, separator=" ")
        'hello...'
        >>> truncate("Short", 10)
        'Short'
    """
    s = "" if string is None else str(string)

    if length is None:
        length = 30
    if length < 0:
        raise ValueError("Length cannot be negative.")

    omission = "" if omission is None else omission

    if len(s) <= length:
        return s

    cut = length - len(omission)
    if cut < 0:
        # Edge case: omission itself longer than allowed length
        return omission[:length]

    head = s[:cut]

    if separator:
        if isinstance(separator, str):
            idx = head.rfind(separator)
            if idx != -1:
                head = head[:idx]
        else:  # regex
            matches = list(re.finditer(separator, head))
            if matches:
                head = head[:matches[-1].start()]
    else:
        # Strip trailing non-alphanumeric characters if present
        while head and not head[-1].isalnum():
            head = head[:-1]

    return head + omission

def repeat(string: Any, n: int = 0) -> str:
    """
    Repeat `string` `n` times.

    Args:
        string: The value to repeat (None→"").
        n:      Number of repetitions. If ≤0, returns "".

    Returns:
        The repeated string.

    Examples:
        >>> repeat("foo", 3)
        "foofoofoo"
        >>> repeat("foo", 1)
        "foo"
        >>> repeat("foo", 0)
        ""
        >>> repeat("", 5)
          ""
        >>> repeat(None, 2)
        ""
    """
    s = "" if string is None else str(string)
    try:
        count = int(n)
    except (TypeError, ValueError):
        return ""
    return s * max(0, count)

def reg_exp_replace(
    text: Any,
    pattern: Any,
    replacement: Any,
    ignore_case: bool = False,
    count: Optional[int] = None
) -> str:
    """
    Replace occurrences of regex `pattern` with `replacement` in `text`. Optionally, ignore case
    when replacing. Optionally, set `count` to limit number of replacements.

    Args:
        text: String to replace.
        pattern: Pattern to find and replace.
        replacement: String to substitute `pattern` with.
        ignore_case: Whether to ignore case when replacing. Defaults to ``False``.
        count: Maximum number of occurrences to replace. Defaults to ``None`` which
            replaces all.

    Returns:
        Replaced string.

    Examples:
        >>> reg_exp_replace("aabbcc", "b", "X")
        'aaXXcc'
        >>> reg_exp_replace("aabbcc", "B", "X", ignore_case=True)
        'aaXXcc'
        >>> reg_exp_replace("aabbcc", "b", "X", count=1)
        'aaXbcc'
        >>> reg_exp_replace("aabbcc", "[ab]", "X")
        'XXXXcc'
    """
    s = "" if text is None else str(text)
    if pattern is None or replacement is None:
        return s
    rep = str(replacement)
    # empty‐pattern special
    pat_str = None
    if not isinstance(pattern, re.Pattern):
        pat_str = str(pattern)
        if pat_str == "":
            # every boundary
            parts = list(s)
            return rep + rep.join(parts) + rep
    flags = re.IGNORECASE if ignore_case else 0
    # compile from string or accept existing pattern
    try:
        regex = re.compile(pat_str if pat_str is not None else pattern, flags)
    except re.error:
        return s
    # count=None → all, else up to count
    return regex.sub(rep, s, 0 if count is None else max(0, int(count)))


def slugify(string: Any, delimiter: str = "-") -> str:
    """
    Convert `string` into a URL-friendly slug.

    1. Lowercases the string
    2. Removes non-alphanumeric characters (except spaces)
    3. Replaces whitespace with the given delimiter

    Args:
        string: The string to slugify.
        delimiter: The delimiter to replace spaces, defaults to '-'.

    Returns:
        A URL-friendly slug string.

    Examples:
        >>> slugify("Hello, World!")
        "hello-world"
    """
    if string is None:
        return ""
    text = _deburr_latin_only(str(string)).lower().strip()
    # remove apostrophes and all non-alphanumeric/spaces
    text = re.sub(r"[’'`]", "", text)
    text = re.sub(r"[^0-9a-z\u0080-\uFFFF ]+", "", text)
    parts = text.split()
    return delimiter.join(parts)

def url(*parts: str, **params: Any) -> str:
    """
    Combine URL parts into a single URL with optional query parameters.

    Args:
        parts: URL components (strings).
        params: Optional query parameters as keyword args.

    Returns:
        Combined URL string.
        
    Examples:
        >>> link = url("a", "b", ["c", "d"], "/", q="X", y="Z")
        >>> path, params = link.split("?")
        >>> path == "a/b/c/d/"
        True
        >>> set(params.split("&")) == set(["q=X", "y=Z"])
        True        
    """
    if not parts:
        return ""

    u = urlsplit(parts[0])
    scheme, netloc, path, query, frag = u.scheme, u.netloc, u.path, u.query, u.fragment
    query_items = parse_qsl(query, keep_blank_values=True)

    for part in parts[1:]:
        p = urlsplit(part)

        # Merge queries
        query_items.extend(parse_qsl(p.query, keep_blank_values=True))

        if frag:
            # Merge into fragment if one exists
            frag_path = p.fragment or p.path.strip("/")
            if frag_path:
                frag += "/" + frag_path
        else:
            # Merge into path if no fragment yet
            if p.fragment:
                frag = p.fragment
            if p.path:
                path = path.rstrip("/") + "/" + p.path.lstrip("/")

    # Ensure trailing slash if last part had it
    if parts[-1].endswith("/") and not path.endswith("/"):
        path += "/"

    # Merge keyword arguments into query string
    for k, v in params.items():
        if isinstance(v, (list, tuple)):
            query_items.extend((k, str(i)) for i in v)
        else:
            query_items.append((k, str(v)))

    return urlunsplit((scheme, netloc, path, urlencode(query_items, doseq=True), frag))

def human_case(string: str) -> str:
    """
    Convert a string into human-readable form:
    - Trims whitespace
    - Drops trailing 'id' suffix (with optional underscore or hyphen)
    - Splits on capitals, underscores, hyphens
    - Lowercases and capitalizes first letter

    Args:
        string: The input string

    Returns:
        A human-cased string

    Examples:
        >>> human_case("helloWorld_test")
        "Hello world test"
    """
    if string is None:
        return ""
    s = str(string).strip()
    if not s:
        return ""
    # drop trailing id
    s = re.sub(r"[_\-\s]*id$", "", s, flags=re.IGNORECASE)
    # split CamelCase (including XMLHttp → XML Http)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
    # replace separators with spaces
    s = re.sub(r"[_\-]+", " ", s)
    s = s.lower().strip()
    if not s:
        return ""
    return s[0].upper() + s[1:]

def join(array, separator=None) -> str:
    """
    Join elements of an array into a string.
    None elements become empty strings.

    Args:
        array: Iterable of elements (or None)
        separator: Separator to insert between elements (defaults to "")

    Returns:
        The joined string
    
    Examples:
        >>> join(["foo", "bar", "baz"], "_")
        "foo_bar_baz"    
    """
    if array is None:
        return ""
    sep = "" if separator is None else str(separator)
    parts = []
    for x in array:
        if x is None:
            parts.append("")
        else:
            parts.append(str(x))
    return sep.join(parts)

def number_format(
    value: Any,
    precision: int = 0,
    decimal_sep: str = ".",
    thousands_sep: str = ","
) -> str:
    """
    Format a number with grouped thousands and fixed decimals.

    Args:
        value: The number to format
        precision: Number of decimal places
        decimal_sep: Character for the decimal point
        thousands_sep: Character for the thousands grouping

    Returns:
        The formatted number string, or "" if invalid
    
    Examples:
        >>> number_format(1234567.89)
        "1,234,567.89"
    """
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        return ""
    # Round to the given precision
    fmt = f"{{:,.{precision}f}}"
    result = fmt.format(value)
    # Python always uses ',' for thousands and '.' for decimal
    if thousands_sep != ",":
        result = result.replace(",", "TMP")
    if decimal_sep != ".":
        result = result.replace(".", decimal_sep)
    if thousands_sep != ",":
        result = result.replace("TMP", thousands_sep)
    return result



def split(*args) -> List[str]:
    """
    Split a string into parts.

    - split(s)           → s.split()  (on whitespace)
    - split(s, "") or (s, None) → list(s) (every char)
    - split(s, sep)      → s.split(sep)

    Args:
        args[0]: the string
        args[1] (optional): the separator

    Returns:
        A list of substrings
    
    Examples:
        >>> split("foo bar baz")
        ["foo", "bar", "baz"]
        >>> split("foo bar baz", "_")
        ["foo", "bar", "baz"]
        >>> split("foo bar baz", None)
        ["f", "o", "o", " ", "b", "a", "r", " ", "b", "a", "z"]
    """
    if not args or args[0] is None:
        return []
    s = str(args[0])
    if len(args) == 1:
        # default: whitespace
        return [w for w in s.split() if w]
    sep = args[1]
    if sep is None or sep == "":
        return list(s) if s else []
    return s.split(sep)


def start_case(string: str) -> str:
    """
    Convert a string into Start Case:
    - Splits on spaces, punctuation, and camelCase
    - Capitalizes each word (preserves ALLCAPS words)
    - Drops apostrophes

    Args:
        string: The input string

    Returns:
        The Start Cased string

    Examples:
        >>> start_case("helloWorld_test")
        "Hello World Test"
    """
    if string is None:
        return ""
    s = str(string).strip()
    if not s:
        return ""
    # camelCase splits
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
    # drop apostrophes
    s = s.replace("'", "")
    # non-alphanumerics → spaces
    s = re.sub(r"[^A-Za-z0-9]+", " ", s)
    words = [w for w in s.split(" ") if w]
    def _cap(w):
        return w.upper() if w.isupper() else w.lower().capitalize()
    return " ".join(_cap(w) for w in words)

def escape(string: Any) -> str:
    """
    Escape HTML characters in a string.

    Args:
        string: The string to escape (None→"").

    Returns:
        An HTML-escaped string, using decimal entities for ' and `.

    Examples:
        >>> escape('abc<> &"\'`efg') 
        "abc&lt;&gt; &amp;&quot;&#39;&#96;efg"
    """
    if string is None:
        return ""
    s = str(string)
    out: list[str] = []
    for ch in s:
        if ch == "&":
            out.append("&amp;")
        elif ch == "<":
            out.append("&lt;")
        elif ch == ">":
            out.append("&gt;")
        elif ch == '"':
            out.append("&quot;")
        elif ch == "'":
            out.append("&#39;")
        elif ch == "`":
            out.append("&#96;")
        else:
            out.append(ch)
    return "".join(out)


def unescape(string: Any) -> str:
    """
    Unescape HTML entities in a string.

    Args:
        string: The escaped HTML (None→"").

    Returns:
        An unescaped string, reversing decimal entities for ' and `.

    Examples:
        >>> unescape("abc&lt;&gt; &amp;&quot;&#39;&#96;efg")"
        '"abc<> &"\'`efg'
    """
    if string is None:
        return ""
    s = str(string)
    # Replace decimal entities first, then &amp;
    s = s.replace("&#39;", "'")
    s = s.replace("&#96;", "`")
    s = s.replace("&quot;", '"')
    s = s.replace("&lt;", "<")
    s = s.replace("&gt;", ">")
    s = s.replace("&amp;", "&")
    return s

def series_phrase_serial(
    items: Any,
    sep: Any = ", ",
    last_sep: Any = ", and "
) -> str:
    """
    Join a sequence into a human-readable series **with** an Oxford comma
    for 3+ items, even if the user supplied a custom `last_sep` without
    the comma.

    Args:
        items:    Iterable of values (None→empty list)
        sep:      Separator between items (e.g. ", " or ";")
        last_sep: Separator before last item (e.g. ", and " or " or ")

    Returns:
        A string like "a, b, c, and d" or with custom separators.

    Examples:
        >>> series_phrase_serial(["foo","bar","baz","qux"],", "," or ")
        "foo, bar, baz, or qux"
    """
    seq = [str(x) for x in (items or []) if x is not None and str(x) != ""]
    n = len(seq)
    if n == 0:
        return ""
    if n == 1:
        return seq[0]
    if n == 2:
        # for two items always use plain " and "
        return seq[0] + " and " + seq[1]

    # n >= 3: enforce Oxford comma
    sep_str = "" if sep is None else str(sep)
    last_str = "" if last_sep is None else str(last_sep)

    # if user‐supplied last_sep doesn’t already start with the sep’s punctuation,
    # prefix it so we get the comma (or semicolon, etc.) back.
    lead = sep_str.rstrip()
    if last_str.strip() and not last_str.lstrip().startswith(lead):
        last_str = lead + last_str

    return sep_str.join(seq[:-1]) + last_str + seq[-1]