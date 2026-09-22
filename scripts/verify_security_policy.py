"""Verify scoped security suppressions and fail on material SARIF findings."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import sys
import tokenize
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

_MAX_POLICY_FILE_BYTES = 64 * 1024 * 1024
_RATIONALE_MIN_LENGTH = 20
_SKIPPED_DIRECTORIES = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
}
_TEXT_COMMENT_SUFFIXES = {
    ".bash",
    ".cfg",
    ".ini",
    ".js",
    ".jsx",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".yaml",
    ".yml",
}
_NOSEC_RE = re.compile(
    r"#\s*nosec(?:\s+(?P<codes>[A-Z]\d{3}(?:\s*,\s*[A-Z]\d{3})*))?\s*$"
)
_NOSEC_POLICY_RE = re.compile(
    r"#\s*Security suppression:\s*"
    r"codes=(?P<codes>[A-Z]\d{3}(?:\s*,\s*[A-Z]\d{3})*);\s*"
    r"expires=(?P<expires>\d{4}-\d{2}-\d{2});\s*"
    r"rationale=(?P<rationale>.+)$"
)
_SECRET_ALLOWLIST_RE = re.compile(
    r"#\s*pragma:\s*allowlist(?:\s+nextline)?\s+secret"
    r"(?:;\s*expires=(?P<expires>\d{4}-\d{2}-\d{2});\s*"
    r"rationale=(?P<rationale>.+))?$",
    re.IGNORECASE,
)


class SecurityPolicyError(ValueError):
    """Raised when a security gate cannot establish the required policy."""


def _parse_expiry(
    raw_value: str,
    *,
    current_date: date,
    location: str,
) -> date:
    try:
        expiry = date.fromisoformat(raw_value)
    except ValueError as exc:
        raise SecurityPolicyError(
            f"{location}: expiry must use a valid YYYY-MM-DD date"
        ) from exc
    if expiry <= current_date:
        raise SecurityPolicyError(
            f"{location}: suppression expired on {expiry.isoformat()}"
        )
    return expiry


def _validate_rationale(value: str, location: str) -> str:
    rationale = value.strip()
    if len(rationale) < _RATIONALE_MIN_LENGTH:
        raise SecurityPolicyError(
            f"{location}: suppression rationale must contain at least "
            f"{_RATIONALE_MIN_LENGTH} characters"
        )
    return rationale


def _iter_source_paths(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            relative_parts = path.relative_to(root).parts
        except ValueError:
            continue
        if any(part in _SKIPPED_DIRECTORIES for part in relative_parts):
            continue
        if path.suffix == ".py" or path.suffix in _TEXT_COMMENT_SUFFIXES:
            yield path


def _python_comments(path: Path) -> list[tuple[int, str]]:
    try:
        source = path.read_bytes()
        return [
            (token.start[0], token.string)
            for token in tokenize.tokenize(io.BytesIO(source).readline)
            if token.type == tokenize.COMMENT
        ]
    except (OSError, SyntaxError, tokenize.TokenError) as exc:
        raise SecurityPolicyError(f"{path}: unable to parse Python comments") from exc


def _text_comments(path: Path) -> list[tuple[int, str]]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        raise SecurityPolicyError(f"{path}: unable to read policy comments") from exc
    comments = []
    for line_number, line in enumerate(lines, start=1):
        comment_start = line.find("#")
        if comment_start >= 0:
            comments.append((line_number, line[comment_start:]))
    return comments


def verify_suppressions(
    root: Path,
    *,
    current_date: date | None = None,
) -> int:
    """Require every inline security suppression to have scope and an expiry."""
    root = root.resolve()
    if not root.is_dir():
        raise SecurityPolicyError(f"{root}: suppression root must be a directory")
    today = current_date or datetime.now(timezone.utc).date()
    errors: list[str] = []
    suppression_count = 0
    used_policy_locations = set()

    for path in _iter_source_paths(root):
        try:
            comments = (
                _python_comments(path)
                if path.suffix == ".py"
                else _text_comments(path)
            )
        except SecurityPolicyError as exc:
            errors.append(str(exc))
            continue
        comments_by_line = {line_number: comment for line_number, comment in comments}
        relative_path = path.relative_to(root)

        for line_number, comment in comments:
            nosec_match = _NOSEC_RE.fullmatch(comment.strip())
            if nosec_match:
                suppression_count += 1
                location = f"{relative_path}:{line_number}"
                raw_codes = nosec_match.group("codes")
                if not raw_codes:
                    errors.append(f"{location}: blanket # nosec is forbidden")
                    continue
                codes = {
                    code.strip() for code in raw_codes.split(",") if code.strip()
                }
                policy_match = None
                policy_location = None
                for policy_line in range(max(1, line_number - 2), line_number):
                    candidate = comments_by_line.get(policy_line, "").strip()
                    candidate_match = _NOSEC_POLICY_RE.fullmatch(candidate)
                    if candidate_match:
                        policy_match = candidate_match
                        policy_location = (path, policy_line)
                        break
                if policy_match is None:
                    errors.append(
                        f"{location}: # nosec requires adjacent scope, expiry, "
                        "and rationale metadata"
                    )
                    continue
                if policy_location in used_policy_locations:
                    errors.append(
                        f"{location}: suppression policy metadata cannot be reused"
                    )
                    continue
                used_policy_locations.add(policy_location)
                policy_codes = {
                    code.strip()
                    for code in policy_match.group("codes").split(",")
                    if code.strip()
                }
                if codes != policy_codes:
                    errors.append(
                        f"{location}: suppression codes do not match policy metadata"
                    )
                try:
                    _parse_expiry(
                        policy_match.group("expires"),
                        current_date=today,
                        location=location,
                    )
                    _validate_rationale(policy_match.group("rationale"), location)
                except SecurityPolicyError as exc:
                    errors.append(str(exc))
                continue

            allowlist_match = _SECRET_ALLOWLIST_RE.search(comment.strip())
            if allowlist_match:
                suppression_count += 1
                location = f"{relative_path}:{line_number}"
                expiry = allowlist_match.group("expires")
                rationale = allowlist_match.group("rationale")
                if expiry is None or rationale is None:
                    errors.append(
                        f"{location}: secret allowlist requires expiry and rationale"
                    )
                    continue
                try:
                    _parse_expiry(
                        expiry,
                        current_date=today,
                        location=location,
                    )
                    _validate_rationale(rationale, location)
                except SecurityPolicyError as exc:
                    errors.append(str(exc))

    if errors:
        raise SecurityPolicyError("\n".join(errors))
    return suppression_count


def _read_json(path: Path) -> Any:
    try:
        file_size = path.stat().st_size
    except OSError as exc:
        raise SecurityPolicyError(f"{path}: unable to inspect JSON input") from exc
    if file_size > _MAX_POLICY_FILE_BYTES:
        raise SecurityPolicyError(
            f"{path}: JSON input exceeds {_MAX_POLICY_FILE_BYTES} bytes"
        )
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SecurityPolicyError(f"{path}: invalid JSON input") from exc


def _load_sarif_suppressions(
    path: Path,
    *,
    current_date: date,
) -> dict[tuple[str, str, str], Mapping[str, Any]]:
    document = _read_json(path)
    if not isinstance(document, dict) or document.get("version") != 1:
        raise SecurityPolicyError(f"{path}: suppression registry version must be 1")
    entries = document.get("suppressions")
    if not isinstance(entries, list):
        raise SecurityPolicyError(f"{path}: suppressions must be a list")

    suppressions: dict[tuple[str, str, str], Mapping[str, Any]] = {}
    for index, entry in enumerate(entries):
        location = f"{path}:suppressions[{index}]"
        if not isinstance(entry, dict):
            raise SecurityPolicyError(f"{location}: entry must be an object")
        tool = entry.get("tool")
        rule_id = entry.get("rule_id")
        fingerprint = entry.get("fingerprint")
        if not all(
            isinstance(value, str) and value.strip()
            for value in (tool, rule_id, fingerprint)
        ):
            raise SecurityPolicyError(
                f"{location}: tool, rule_id, and fingerprint must be non-empty text"
            )
        raw_expiry = entry.get("expires")
        rationale = entry.get("rationale")
        if not isinstance(raw_expiry, str) or not isinstance(rationale, str):
            raise SecurityPolicyError(
                f"{location}: expires and rationale must be text"
            )
        _parse_expiry(
            raw_expiry,
            current_date=current_date,
            location=location,
        )
        _validate_rationale(rationale, location)
        key = (tool.lower(), rule_id, fingerprint) # type: ignore
        if key in suppressions:
            raise SecurityPolicyError(f"{location}: duplicate suppression entry")
        suppressions[key] = entry # type: ignore
    return suppressions


def _result_fingerprint(result: Mapping[str, Any]) -> str:
    partial_fingerprints = result.get("partialFingerprints")
    if isinstance(partial_fingerprints, dict) and partial_fingerprints:
        preferred_name = "primaryLocationLineHash"
        if preferred_name in partial_fingerprints:
            value = partial_fingerprints[preferred_name]
            if isinstance(value, str) and value:
                return f"{preferred_name}={value}"
        name = sorted(partial_fingerprints)[0]  # noqa: FURB192
        value = partial_fingerprints[name]
        if isinstance(value, str) and value:
            return f"{name}={value}"

    locations = result.get("locations")
    location_payload: Any = locations[0] if isinstance(locations, list) and locations else {}
    payload = json.dumps(
        {
            "ruleId": result.get("ruleId"),
            "location": location_payload,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256={hashlib.sha256(payload).hexdigest()}"


def _result_location(result: Mapping[str, Any]) -> str:
    try:
        physical = result["locations"][0]["physicalLocation"]
        uri = physical["artifactLocation"]["uri"]
        line = physical.get("region", {}).get("startLine", "?")
        return f"{uri}:{line}"
    except (KeyError, IndexError, TypeError):
        return "<unknown>"


def _security_severity(
    result: Mapping[str, Any],
    rule: Mapping[str, Any],
) -> float:
    for properties in (result.get("properties"), rule.get("properties")):
        if isinstance(properties, dict):
            raw_value = properties.get("security-severity")
            if raw_value is not None:
                try:
                    value = float(raw_value)
                except (TypeError, ValueError) as exc:
                    raise SecurityPolicyError(
                        "SARIF security-severity must be numeric"
                    ) from exc
                if not 0 <= value <= 10:
                    raise SecurityPolicyError(
                        "SARIF security-severity must be between 0 and 10"
                    )
                return value

    default_configuration = rule.get("defaultConfiguration")
    default_level = (
        default_configuration.get("level")
        if isinstance(default_configuration, dict)
        else None
    )
    level = result.get("level", default_level)
    if level is not None and not isinstance(level, str):
        raise SecurityPolicyError("SARIF result level must be text")
    return {"error": 7.0, "warning": 4.0, "note": 0.0, "none": 0.0}.get(
        level, # type: ignore
        7.0,
    ) # type: ignore


def verify_sarif(
    sarif_input: Path,
    suppression_registry: Path,
    *,
    minimum_severity: float = 4.0,
    current_date: date | None = None,
) -> int:
    """Fail when SARIF contains unsuppressed medium-or-higher findings."""
    if not math.isfinite(minimum_severity) or not 0 <= minimum_severity <= 10:
        raise SecurityPolicyError("minimum severity must be between 0 and 10")
    today = current_date or datetime.now(timezone.utc).date()
    suppressions = _load_sarif_suppressions(
        suppression_registry,
        current_date=today,
    )
    if sarif_input.is_dir():
        sarif_paths = sorted(sarif_input.rglob("*.sarif"))
    elif sarif_input.is_file():
        sarif_paths = [sarif_input]
    else:
        sarif_paths = []
    if not sarif_paths:
        raise SecurityPolicyError(f"{sarif_input}: no SARIF files found")

    result_count = 0
    violations = []
    for sarif_path in sarif_paths:
        document = _read_json(sarif_path)
        if not isinstance(document, dict) or document.get("version") != "2.1.0":
            raise SecurityPolicyError(f"{sarif_path}: SARIF version must be 2.1.0")
        runs = document.get("runs")
        if not isinstance(runs, list):
            raise SecurityPolicyError(f"{sarif_path}: SARIF runs must be a list")
        for run in runs:
            if not isinstance(run, dict):
                raise SecurityPolicyError(f"{sarif_path}: SARIF run must be an object")
            tool = run.get("tool")
            if not isinstance(tool, dict):
                raise SecurityPolicyError(
                    f"{sarif_path}: SARIF tool must be an object"
                )
            driver = tool.get("driver", {})
            if not isinstance(driver, dict):
                raise SecurityPolicyError(
                    f"{sarif_path}: SARIF tool driver must be an object"
                )
            raw_tool_name = driver.get("name")
            if not isinstance(raw_tool_name, str) or not raw_tool_name.strip():
                raise SecurityPolicyError(
                    f"{sarif_path}: SARIF tool driver requires a name"
                )
            tool_name = raw_tool_name.lower()
            rules = driver.get("rules", [])
            if not isinstance(rules, list):
                raise SecurityPolicyError(f"{sarif_path}: SARIF rules must be a list")
            rules_by_id = {
                rule.get("id"): rule
                for rule in rules
                if isinstance(rule, dict) and isinstance(rule.get("id"), str)
            }
            results = run.get("results", [])
            if not isinstance(results, list):
                raise SecurityPolicyError(
                    f"{sarif_path}: SARIF results must be a list"
                )
            for result in results:
                if not isinstance(result, dict):
                    raise SecurityPolicyError(
                        f"{sarif_path}: SARIF result must be an object"
                    )
                result_count += 1
                rule_id = result.get("ruleId")
                if not isinstance(rule_id, str) or not rule_id:
                    raise SecurityPolicyError(
                        f"{sarif_path}: SARIF result requires ruleId"
                    )
                rule = rules_by_id.get(rule_id, {})
                severity = _security_severity(result, rule)
                if severity < minimum_severity:
                    continue
                fingerprint = _result_fingerprint(result)
                key = (tool_name, rule_id, fingerprint)
                if key in suppressions:
                    continue
                violations.append(
                    f"{rule_id} severity={severity:g} "
                    f"fingerprint={fingerprint} location={_result_location(result)}"
                )

    if violations:
        raise SecurityPolicyError(
            "unsuppressed medium-or-higher SARIF findings:\n"
            + "\n".join(violations)
        )
    return result_count


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    suppression_parser = subparsers.add_parser(
        "suppressions",
        help="verify inline suppression scope, rationale, and expiry",
    )
    suppression_parser.add_argument("--root", type=Path, default=Path("."))

    sarif_parser = subparsers.add_parser(
        "sarif",
        help="reject unsuppressed medium-or-higher SARIF results",
    )
    sarif_parser.add_argument("--input", type=Path, required=True)
    sarif_parser.add_argument(
        "--suppressions",
        type=Path,
        default=Path("security/suppressions.json"),
    )
    sarif_parser.add_argument(
        "--minimum-severity",
        type=float,
        default=4.0,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        if args.command == "suppressions":
            count = verify_suppressions(args.root)
            print(f"verified {count} scoped security suppressions")
        else:
            count = verify_sarif(
                args.input,
                args.suppressions,
                minimum_severity=args.minimum_severity,
            )
            print(f"verified {count} SARIF results")
    except SecurityPolicyError as exc:
        print(f"security policy verification failed:\n{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
