"""Branch coverage for security and template failure contracts."""

from __future__ import annotations

import logging
import os
import re

import pytest

from unicorefw.regex_policy import (
    RegexLimits,
    UnsafeRegex,
    compile_bounded_regex,
    unsafe_raw_regex,
)
from unicorefw.security import (
    AuditLogger,
    InputValidationError,
    ResourceLimitError,
    SanitizationError,
    SecurityError,
    _estimate_resource_weight,
    _SecureAppendFileHandler,
    _validate_resource_duration,
    _validate_resource_ratio,
    sanitize_string,
    validate_callable,
)
from unicorefw.template import TemplateLimits, html_template, template


def _record(message: str = "event") -> logging.LogRecord:
    return logging.LogRecord("audit", logging.INFO, __file__, 1, message, (), None)


def test_resource_validators_cover_type_duration_and_cycle_branches():
    with pytest.raises(InputValidationError, match="greater than or equal"):
        _validate_resource_ratio("1", "ratio", 10)
    with pytest.raises(InputValidationError, match="finite number"):
        _validate_resource_duration("1", "duration", 10)
    with pytest.raises(InputValidationError, match="non-negative"):
        _validate_resource_duration(-1, "duration", 10, allow_zero=True)
    with pytest.raises(InputValidationError, match="positive"):
        _validate_resource_duration(0, "duration", 10)
    with pytest.raises(InputValidationError, match="hard safety maximum"):
        _validate_resource_duration(11, "duration", 10)
    assert _validate_resource_duration(0, "duration", 10, allow_zero=True) == 0

    cyclic = []
    cyclic.append(cyclic)
    assert _estimate_resource_weight(cyclic, 10_000) > 0


def test_secure_handler_covers_optional_os_flag_branches(tmp_path, monkeypatch):
    output = tmp_path / "audit.log"
    monkeypatch.setattr(os, "O_BINARY", 0, raising=False)
    monkeypatch.delattr(os, "O_NOFOLLOW", raising=False)
    monkeypatch.delattr(os, "fchmod", raising=False)

    _SecureAppendFileHandler(str(output)).emit(_record())
    assert output.read_text(encoding="utf-8") == "event\n"


def test_secure_handler_rejects_non_file_and_zero_progress(tmp_path, monkeypatch):
    output = tmp_path / "audit.log"
    handler = _SecureAppendFileHandler(str(output))

    monkeypatch.setattr("unicorefw.security.stat.S_ISREG", lambda mode: False)
    with pytest.raises(SecurityError, match="regular file"):
        handler.emit(_record())

    monkeypatch.undo()
    handler = _SecureAppendFileHandler(str(output))
    monkeypatch.setattr("unicorefw.security.os.write", lambda descriptor, data: 0)
    with pytest.raises(SecurityError, match="append"):
        handler.emit(_record())


def test_secure_handler_wraps_open_failure(tmp_path, monkeypatch):
    handler = _SecureAppendFileHandler(str(tmp_path / "audit.log"))

    def fail_open(*args, **kwargs):
        raise OSError("denied")

    monkeypatch.setattr("unicorefw.security.os.open", fail_open)
    with pytest.raises(SecurityError, match="append"):
        handler.emit(_record())


def test_audit_logger_rejects_invalid_configuration_and_events(tmp_path):
    with pytest.raises(InputValidationError, match="logging.Logger"):
        AuditLogger(logger=object())  # type: ignore[arg-type]

    logger = AuditLogger(log_file=str(tmp_path / "audit.log"))
    try:
        with pytest.raises(InputValidationError, match="non-empty"):
            logger.log("", {})
        with pytest.raises(InputValidationError, match="null bytes"):
            logger.log("LOGIN\x00FORGED", {})
        logger.log("OBJECT", object())
    finally:
        logger.close()
        logger.close()


def test_validate_callable_bound_method_and_sanitize_type():
    class Handler:
        def call(self):
            return None

    method = Handler().call
    assert validate_callable(method) is method
    with pytest.raises(SanitizationError, match="string"):
        sanitize_string(1)


def test_template_rejects_invalid_limit_source_and_context_types():
    with pytest.raises(TypeError, match="TemplateLimits"):
        template("value", {}, limits=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="template_str"):
        template(1, {})  # type: ignore[arg-type]
    with pytest.raises(ResourceLimitError, match="source length"):
        template("abcd", {}, limits=TemplateLimits(max_template_length=3))
    with pytest.raises(TypeError, match="Context"):
        template("value", [])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Context key"):
        template("<%= value %>", {1: "value"})  # type: ignore[dict-item]


def test_template_expression_attribute_method_and_condition_branches():
    class User:
        name = "Alice"

    class MissingUpper(str):
        def __getattribute__(self, name):
            if name == "upper":
                return None
            return super().__getattribute__(name)

    assert template("<%= user.name %>", {"user": User()}) == "Alice"
    assert template("<%= name.upper() %>", {"name": "alice"}) == "ALICE"

    with pytest.raises(ValueError, match="Invalid expression"):
        template("<%= name + other %>", {"name": "a", "other": "b"})
    with pytest.raises(NameError, match="not defined"):
        template("<%= missing %>", {})
    with pytest.raises(AttributeError, match="not found"):
        template("<%= user.missing %>", {"user": User()})
    with pytest.raises(ValueError, match="not allowed"):
        template("<%= value.bit_length() %>", {"value": 1})
    assert template("<%= value.upper() %>", {"value": MissingUpper("a")}) == "None"
    with pytest.raises(ValueError, match="Invalid condition"):
        template("<% if invalid.condition %>x<% endif %>", {})


def test_template_skips_false_blocks_and_accepts_callable_context():
    assert (
        template(
            "before<% if visible %><%= missing %>hidden<% endif %>after",
            {"visible": False, "callable": lambda: None},
        )
        == "beforeafter"
    )


def test_html_template_tracks_closed_raw_blocks_and_tag_scan_branches():
    assert (
        html_template(
            "<script>constant</script><p><%= value %></p>",
            {"value": "safe"},
        )
        == "<script>constant</script><p>safe</p>"
    )
    assert html_template("><%= value %>", {"value": "safe"}) == ">safe"


def test_regex_policy_rejects_invalid_wrapper_limits_input_and_pattern_types():
    with pytest.raises(InputValidationError, match="unsafe regex"):
        UnsafeRegex(1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="RegexLimits"):
        compile_bounded_regex("a", "a", limits=object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="input must be text"):
        compile_bounded_regex("a", 1)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="pattern must be text"):
        compile_bounded_regex(object(), "a")  # type: ignore[arg-type]

    trusted = unsafe_raw_regex("a+")
    assert trusted.pattern == "a+"
    assert repr(trusted) == "UnsafeRegex(<trusted pattern>)"


def test_regex_policy_covers_structural_scanner_branches():
    assert compile_bounded_regex(r"[a\]]+", "a]").fullmatch("a]")
    assert compile_bounded_regex(r"(?:ab)+", "abab").fullmatch("abab")
    assert compile_bounded_regex("a|b", "b").fullmatch("b")
    assert compile_bounded_regex("a{", "a{").fullmatch("a{")
    assert compile_bounded_regex("a{2}", "aa").fullmatch("aa")
    assert compile_bounded_regex("a{1,}", "aaa").fullmatch("aaa")
    assert compile_bounded_regex("a{1,3}?", "aaa").match("aaa").group() == "a"

    with pytest.raises(SecurityError, match="Backreferences"):
        compile_bounded_regex(r"(a)\1", "aa")
    with pytest.raises(SecurityError, match="Adjacent repetition"):
        compile_bounded_regex("a+a+", "aaaa")
    with pytest.raises(SecurityError, match="Adjacent repetition"):
        compile_bounded_regex("(a)+(b)+", "ab")
    with pytest.raises(ResourceLimitError, match="group count"):
        compile_bounded_regex("(a)(b)", "ab", limits=RegexLimits(max_groups=1))
    with pytest.raises(re.error):
        compile_bounded_regex(")", "")
    with pytest.raises(re.error):
        compile_bounded_regex("[ab", "a")


def test_regex_policy_handles_compiled_patterns_flags_and_trusted_bypass():
    compiled = re.compile("a+")
    assert compile_bounded_regex(compiled, "aaa") is compiled
    assert compile_bounded_regex(unsafe_raw_regex(compiled), "aaa") is compiled

    with pytest.raises(ValueError, match="flags cannot be supplied"):
        compile_bounded_regex(compiled, "aaa", flags=re.IGNORECASE)

    case_insensitive = compile_bounded_regex("a", "A", flags=re.IGNORECASE)
    assert case_insensitive.fullmatch("A")
