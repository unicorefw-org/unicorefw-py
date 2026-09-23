"""Tests for static-analysis suppression and SARIF enforcement policy."""

from __future__ import annotations

import json
import os
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from scripts.verify_security_policy import (
    SecurityPolicyError,
    main,
    verify_sarif,
    verify_suppressions,
)

TODAY = date(2026, 7, 28)
FUTURE = "2027-07-28"


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _registry(path: Path, suppressions=None) -> Path:
    return _write(
        path,
        json.dumps(
            {
                "version": 1,
                "suppressions": suppressions or [],
            }
        ),
    )


def _sarif(
    path: Path,
    *,
    severity="3.9",
    level="warning",
    fingerprint="stable-fingerprint",
) -> Path:
    return _write(
        path,
        json.dumps(
            {
                "version": "2.1.0",
                "runs": [
                    {
                        "tool": {
                            "driver": {
                                "name": "CodeQL",
                                "rules": [
                                    {
                                        "id": "py/example",
                                        "properties": {
                                            "security-severity": severity,
                                        },
                                    }
                                ],
                            }
                        },
                        "results": [
                            {
                                "ruleId": "py/example",
                                "level": level,
                                "partialFingerprints": {
                                    "primaryLocationLineHash": fingerprint,
                                },
                                "locations": [
                                    {
                                        "physicalLocation": {
                                            "artifactLocation": {
                                                "uri": "unicorefw/example.py"
                                            },
                                            "region": {"startLine": 12},
                                        }
                                    }
                                ],
                            }
                        ],
                    }
                ],
            }
        ),
    )


def test_suppression_policy_accepts_scoped_future_exceptions(tmp_path):
    _write(
        tmp_path / "package.py",
        (
            "# Security suppression: codes=B608; "
            f"expires={FUTURE}; "
            "rationale=Identifier validation and binding were reviewed.\n"
            'query = f"SELECT {table}"  # nosec B608\n'
            'password = "fixture"  # pragma: allowlist secret; '
            f"expires={FUTURE}; "
            "rationale=Non-secret fixture exercises credential handling.\n"
        ),
    )

    assert verify_suppressions(tmp_path, current_date=TODAY) == 2


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ('query = "SELECT 1"  # nosec\n', "blanket"),
        ('query = "SELECT 1"  # nosec B608\n', "requires adjacent"),
        (
            "# Security suppression: codes=B607; "
            f"expires={FUTURE}; rationale=Documented narrow test exception.\n"
            'query = "SELECT 1"  # nosec B608\n',
            "codes do not match",
        ),
        (
            "# Security suppression: codes=B608; expires=2026-07-28; "
            "rationale=Documented narrow test exception.\n"
            'query = "SELECT 1"  # nosec B608\n',
            "expired",
        ),
        (
            "# Security suppression: codes=B608; "
            f"expires={FUTURE}; rationale=too short\n"
            'query = "SELECT 1"  # nosec B608\n',
            "at least 20",
        ),
        (
            'password = "fixture"  # pragma: allowlist secret\n',
            "requires expiry",
        ),
    ],
)
def test_suppression_policy_rejects_unbounded_exceptions(
    tmp_path,
    source,
    message,
):
    _write(tmp_path / "package.py", source)

    with pytest.raises(SecurityPolicyError, match=message):
        verify_suppressions(tmp_path, current_date=TODAY)


def test_suppression_policy_reports_unparseable_python(tmp_path):
    _write(tmp_path / "broken.py", '"""unterminated')

    with pytest.raises(SecurityPolicyError, match="unable to parse"):
        verify_suppressions(tmp_path, current_date=TODAY)


def test_suppression_policy_rejects_missing_root(tmp_path):
    with pytest.raises(SecurityPolicyError, match="must be a directory"):
        verify_suppressions(tmp_path / "missing", current_date=TODAY)


def test_suppression_policy_rejects_reused_metadata(tmp_path):
    _write(
        tmp_path / "package.py",
        (
            "# Security suppression: codes=B608; "
            f"expires={FUTURE}; "
            "rationale=Identifier construction received a security review.\n"
            'first = "SELECT 1"  # nosec B608\n'
            'second = "SELECT 2"  # nosec B608\n'
        ),
    )

    with pytest.raises(SecurityPolicyError, match="cannot be reused"):
        verify_suppressions(tmp_path, current_date=TODAY)


def test_sarif_policy_accepts_low_findings(tmp_path):
    sarif_path = _sarif(tmp_path / "results" / "python.sarif")
    registry = _registry(tmp_path / "suppressions.json")

    assert (
        verify_sarif(
            sarif_path.parent,
            registry,
            current_date=TODAY,
        )
        == 1
    )


def test_sarif_policy_rejects_unsuppressed_medium_finding(tmp_path):
    sarif_path = _sarif(
        tmp_path / "python.sarif",
        severity="4.0",
    )
    registry = _registry(tmp_path / "suppressions.json")

    with pytest.raises(SecurityPolicyError, match="py/example") as caught:
        verify_sarif(sarif_path, registry, current_date=TODAY)
    assert "stable-fingerprint" in str(caught.value)
    assert "unicorefw/example.py:12" in str(caught.value)


def test_sarif_policy_accepts_active_exact_suppression(tmp_path):
    sarif_path = _sarif(
        tmp_path / "python.sarif",
        severity="7.5",
    )
    registry = _registry(
        tmp_path / "suppressions.json",
        [
            {
                "tool": "codeql",
                "rule_id": "py/example",
                "fingerprint": "primaryLocationLineHash=stable-fingerprint",
                "expires": FUTURE,
                "rationale": "Reviewed false positive with constrained data flow.",
            }
        ],
    )

    assert verify_sarif(sarif_path, registry, current_date=TODAY) == 1


def test_sarif_policy_rejects_expired_or_duplicate_registry_entries(tmp_path):
    sarif_path = _sarif(tmp_path / "python.sarif")
    expired_entry = {
        "tool": "codeql",
        "rule_id": "py/example",
        "fingerprint": "primaryLocationLineHash=stable-fingerprint",
        "expires": "2026-07-28",
        "rationale": "Reviewed false positive with constrained data flow.",
    }
    expired_registry = _registry(
        tmp_path / "expired.json",
        [expired_entry],
    )
    with pytest.raises(SecurityPolicyError, match="expired"):
        verify_sarif(sarif_path, expired_registry, current_date=TODAY)

    active_entry = dict(expired_entry, expires=FUTURE)
    duplicate_registry = _registry(
        tmp_path / "duplicate.json",
        [active_entry, active_entry],
    )
    with pytest.raises(SecurityPolicyError, match="duplicate"):
        verify_sarif(sarif_path, duplicate_registry, current_date=TODAY)


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda document: document.update(version="2.0.0"), "version"),
        (lambda document: document.update(runs={}), "runs"),
        (
            lambda document: document["runs"][0].update(results=[{}]),
            "ruleId",
        ),
        (
            lambda document: document["runs"][0]["tool"]["driver"]["rules"][0][
                "properties"
            ].update({"security-severity": "invalid"}),
            "must be numeric",
        ),
    ],
)
def test_sarif_policy_rejects_malformed_security_results(
    tmp_path,
    mutator,
    message,
):
    sarif_path = _sarif(tmp_path / "python.sarif")
    document = json.loads(sarif_path.read_text(encoding="utf-8"))
    mutator(document)
    sarif_path.write_text(json.dumps(document), encoding="utf-8")
    registry = _registry(tmp_path / "suppressions.json")

    with pytest.raises(SecurityPolicyError, match=message):
        verify_sarif(sarif_path, registry, current_date=TODAY)


def test_sarif_policy_requires_results_and_valid_registry(tmp_path):
    registry = _registry(tmp_path / "suppressions.json")
    with pytest.raises(SecurityPolicyError, match="no SARIF"):
        verify_sarif(tmp_path / "missing", registry, current_date=TODAY)

    sarif_path = _sarif(tmp_path / "python.sarif")
    invalid_registry = _write(
        tmp_path / "invalid.json",
        '{"version": 2, "suppressions": []}',
    )
    with pytest.raises(SecurityPolicyError, match="version must be 1"):
        verify_sarif(sarif_path, invalid_registry, current_date=TODAY)


@pytest.mark.parametrize("minimum_severity", [-1, 11, float("nan")])
def test_sarif_policy_rejects_invalid_threshold(tmp_path, minimum_severity):
    sarif_path = _sarif(tmp_path / "python.sarif")
    registry = _registry(tmp_path / "suppressions.json")

    with pytest.raises(SecurityPolicyError, match="between 0 and 10"):
        verify_sarif(
            sarif_path,
            registry,
            minimum_severity=minimum_severity,
            current_date=TODAY,
        )


def test_security_policy_cli_reports_success_and_failure(tmp_path, capsys):
    assert main(["suppressions", "--root", str(tmp_path)]) == 0
    assert "verified 0" in capsys.readouterr().out

    _write(tmp_path / "unsafe.py", 'value = "x"  # nosec\n')
    assert main(["suppressions", "--root", str(tmp_path)]) == 1
    assert "blanket" in capsys.readouterr().err
