"""Bounded policy for caller-supplied regular expressions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Pattern, Union

from .security import (
    InputValidationError,
    ResourceLimitError,
    SecurityError,
    _validate_resource_limit,
)

_HARD_MAX_REGEX_INPUT_LENGTH = 1_000_000
_HARD_MAX_REGEX_PATTERN_LENGTH = 4_096
_HARD_MAX_REGEX_GROUPS = 256
_HARD_MAX_REGEX_QUANTIFIERS = 256
_HARD_MAX_REGEX_REPEAT = 1_000_000


@dataclass(frozen=True)
class RegexLimits:
    """Resource budgets for one caller-supplied regular expression."""

    max_input_length: int = 10_000
    max_pattern_length: int = 512
    max_groups: int = 64
    max_quantifiers: int = 64
    max_repeat: int = 100_000

    def __post_init__(self) -> None:
        _validate_resource_limit(
            self.max_input_length,
            "max_input_length",
            _HARD_MAX_REGEX_INPUT_LENGTH,
        )
        _validate_resource_limit(
            self.max_pattern_length,
            "max_pattern_length",
            _HARD_MAX_REGEX_PATTERN_LENGTH,
        )
        _validate_resource_limit(
            self.max_groups,
            "max_groups",
            _HARD_MAX_REGEX_GROUPS,
        )
        _validate_resource_limit(
            self.max_quantifiers,
            "max_quantifiers",
            _HARD_MAX_REGEX_QUANTIFIERS,
        )
        _validate_resource_limit(
            self.max_repeat,
            "max_repeat",
            _HARD_MAX_REGEX_REPEAT,
        )


_DEFAULT_REGEX_LIMITS = RegexLimits()


class UnsafeRegex:
    """Explicit marker for a reviewed pattern that bypasses structural checks."""

    __slots__ = ("_pattern",)

    def __init__(self, pattern: Union[str, Pattern[str]]):
        if not isinstance(pattern, (str, re.Pattern)):
            raise InputValidationError(
                "unsafe regex must be text or a compiled pattern"
            )
        self._pattern = pattern

    @property
    def pattern(self) -> Union[str, Pattern[str]]:
        return self._pattern

    def __repr__(self) -> str:
        return "UnsafeRegex(<trusted pattern>)"


def unsafe_raw_regex(pattern: Union[str, Pattern[str]]) -> UnsafeRegex:
    """Mark one reviewed complex pattern as trusted."""
    return UnsafeRegex(pattern)


def _resolve_regex_limits(limits: Optional[RegexLimits]) -> RegexLimits:
    if limits is None:
        return _DEFAULT_REGEX_LIMITS
    if not isinstance(limits, RegexLimits):
        raise TypeError("limits must be a RegexLimits instance")
    return limits


def _validate_pattern_structure(pattern: str, limits: RegexLimits) -> None:
    """Reject backtracking-prone constructs from the default regex subset."""
    stack = [
        {
            "alternation": False,
            "quantifiers": 0,
            "follows_quantifier": False,
        }
    ]
    groups = 0
    quantifiers = 0
    last_atom_is_risky = False
    last_was_quantifier = False
    previous_atom_was_quantified = False
    atom_follows_quantifier = False
    index = 0

    while index < len(pattern):
        character = pattern[index]

        if character == "\\":
            if index + 1 < len(pattern) and pattern[index + 1] in "123456789":
                raise SecurityError(
                    "Backreferences require unsafe_raw_regex() and trusted input"
                )
            index += 2
            atom_follows_quantifier = previous_atom_was_quantified
            previous_atom_was_quantified = False
            last_atom_is_risky = False
            last_was_quantifier = False
            continue

        if character == "[":
            index += 1
            while index < len(pattern):
                if pattern[index] == "\\":
                    index += 2
                    continue
                if pattern[index] == "]":
                    index += 1
                    break
                index += 1
            atom_follows_quantifier = previous_atom_was_quantified
            previous_atom_was_quantified = False
            last_atom_is_risky = False
            last_was_quantifier = False
            continue

        if character == "(":
            if pattern.startswith("(?:", index):
                index += 3
            elif index + 1 < len(pattern) and pattern[index + 1] == "?":
                raise SecurityError(
                    "Lookarounds, inline flags, and special groups require "
                    "unsafe_raw_regex()"
                )
            else:
                index += 1
            groups += 1
            if groups > limits.max_groups:
                raise ResourceLimitError("regex group count", limits.max_groups, groups)
            stack.append(
                {
                    "alternation": False,
                    "quantifiers": 0,
                    "follows_quantifier": previous_atom_was_quantified,
                }
            )
            previous_atom_was_quantified = False
            atom_follows_quantifier = False
            last_atom_is_risky = False
            last_was_quantifier = False
            continue

        if character == ")":
            if len(stack) > 1:
                group = stack.pop()
                last_atom_is_risky = bool(group["alternation"] or group["quantifiers"])
                atom_follows_quantifier = bool(group["follows_quantifier"])
                previous_atom_was_quantified = False
                stack[-1]["alternation"] = bool(
                    stack[-1]["alternation"] or group["alternation"]
                )
                stack[-1]["quantifiers"] += group["quantifiers"]
            index += 1
            last_was_quantifier = False
            continue

        if character == "|":
            stack[-1]["alternation"] = True
            index += 1
            previous_atom_was_quantified = False
            atom_follows_quantifier = False
            last_atom_is_risky = False
            last_was_quantifier = False
            continue

        is_quantifier = character in "*+?"
        repeat_upper = None
        if character == "{":
            repeat_match = re.match(r"\{(\d+)(?:,(\d*)?)?\}", pattern[index:])
            if repeat_match is not None:
                is_quantifier = True
                lower = int(repeat_match.group(1))
                upper_text = repeat_match.group(2)
                repeat_upper = (
                    lower
                    if upper_text is None
                    else (None if upper_text == "" else int(upper_text))
                )
                index += len(repeat_match.group(0)) - 1

        if is_quantifier:
            if character == "?" and last_was_quantifier:
                index += 1
                last_was_quantifier = False
                continue
            if last_atom_is_risky:
                raise SecurityError(
                    "Nested or ambiguous repetition requires unsafe_raw_regex()"
                )
            if atom_follows_quantifier:
                raise SecurityError(
                    "Adjacent repetition requires unsafe_raw_regex() and review"
                )
            quantifiers += 1
            stack[-1]["quantifiers"] += 1
            if quantifiers > limits.max_quantifiers:
                raise ResourceLimitError(
                    "regex quantifier count",
                    limits.max_quantifiers,
                    quantifiers,
                )
            if repeat_upper is not None and repeat_upper > limits.max_repeat:
                raise ResourceLimitError(
                    "regex repeat bound",
                    limits.max_repeat,
                    repeat_upper,
                )
            last_was_quantifier = True
            last_atom_is_risky = False
            previous_atom_was_quantified = True
            atom_follows_quantifier = False
            index += 1
            continue

        index += 1
        atom_follows_quantifier = previous_atom_was_quantified
        previous_atom_was_quantified = False
        last_atom_is_risky = False
        last_was_quantifier = False


def compile_bounded_regex(
    pattern: Union[str, Pattern[str], UnsafeRegex],
    text: str,
    *,
    flags: int = 0,
    limits: Optional[RegexLimits] = None,
) -> Pattern[str]:
    """Validate workload budgets and compile one pattern under the safe policy."""
    resolved_limits = _resolve_regex_limits(limits)
    if not isinstance(text, str):
        raise TypeError("regex input must be text")
    if len(text) > resolved_limits.max_input_length:
        raise ResourceLimitError(
            "regex input length",
            resolved_limits.max_input_length,
            len(text),
        )

    trusted = isinstance(pattern, UnsafeRegex)
    raw_pattern = pattern.pattern if trusted else pattern
    if isinstance(raw_pattern, re.Pattern):
        pattern_text = raw_pattern.pattern
        if flags:
            raise ValueError("flags cannot be supplied with a compiled pattern")
    elif isinstance(raw_pattern, str):
        pattern_text = raw_pattern
    else:
        raise TypeError("pattern must be text, a compiled pattern, or UnsafeRegex")

    if len(pattern_text) > resolved_limits.max_pattern_length:
        raise ResourceLimitError(
            "regex pattern length",
            resolved_limits.max_pattern_length,
            len(pattern_text),
        )
    if not trusted:
        _validate_pattern_structure(pattern_text, resolved_limits)
    if isinstance(raw_pattern, re.Pattern):
        return raw_pattern
    return re.compile(raw_pattern, flags=flags)
