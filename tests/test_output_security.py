"""Regression tests for context-specific output encoding."""

from __future__ import annotations

import csv
import json
import logging
import os
import stat
from pathlib import Path

import pytest

from unicorefw.db import (
    Database,
    DataExporter,
    ExportError,
    unsafe_raw_css,
    unsafe_raw_sql,
)
from unicorefw.security import AuditLogger, SecurityError
from unicorefw.template import html_template, template


def _create_output_database() -> Database:
    db = Database(engine="sqlite", database=":memory:")
    db.create_table(
        "records",
        {
            "id": "INTEGER PRIMARY KEY",
            "payload": "TEXT",
            "formula": "TEXT",
        },
    )
    db.insert(
        "records",
        {
            "id": 1,
            "payload": '<img src=x onerror="alert(1)">',
            "formula": '  =HYPERLINK("https://example.invalid")',
        },
    )
    db.commit()
    return db


def test_html_export_escapes_headers_and_cells(tmp_path: Path):
    db = _create_output_database()
    output_path = tmp_path / "records.html"
    try:
        DataExporter(db).to_html(
            unsafe_raw_sql('SELECT payload AS "<header>", formula FROM records'),
            str(output_path),
        )

        rendered = output_path.read_text(encoding="utf-8")
        assert "<header>" not in rendered
        assert "&lt;header&gt;" in rendered
        assert '<img src=x onerror="alert(1)">' not in rendered
        assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" in rendered
    finally:
        db.close()


def test_html_export_requires_explicit_trust_for_custom_css(tmp_path: Path):
    db = _create_output_database()
    output_path = tmp_path / "records.html"
    try:
        with pytest.raises(ExportError, match="unsafe_raw_css"):
            DataExporter(db).to_html(
                "records",
                str(output_path),
                css_style="body { color: red; }",  # type: ignore[arg-type]
            )

        DataExporter(db).to_html(
            "records",
            str(output_path),
            css_style=unsafe_raw_css("body { color: red; }"),
        )
        assert "body { color: red; }" in output_path.read_text(encoding="utf-8")
    finally:
        db.close()


def test_csv_export_neutralizes_formula_cells_by_default(tmp_path: Path):
    db = _create_output_database()
    safe_path = tmp_path / "safe.csv"
    raw_path = tmp_path / "raw.csv"
    try:
        exporter = DataExporter(db)
        exporter.to_csv("records", str(safe_path))
        exporter.to_csv("records", str(raw_path), spreadsheet_safe=False)

        with safe_path.open(encoding="utf-8", newline="") as stream:
            safe_rows = list(csv.DictReader(stream))
        with raw_path.open(encoding="utf-8", newline="") as stream:
            raw_rows = list(csv.DictReader(stream))

        assert safe_rows[0]["formula"].startswith("'  =HYPERLINK")
        assert raw_rows[0]["formula"].startswith("  =HYPERLINK")
    finally:
        db.close()


def test_excel_export_writes_formula_cells_as_text(tmp_path: Path):
    pytest.importorskip("pandas")
    openpyxl = pytest.importorskip("openpyxl")
    db = _create_output_database()
    output_path = tmp_path / "records.xlsx"
    try:
        DataExporter(db).to_excel("records", str(output_path))
        workbook = openpyxl.load_workbook(output_path, data_only=False)
        formula_cell = workbook["Sheet1"]["C2"]

        assert formula_cell.value.startswith("'  =HYPERLINK")
        assert formula_cell.data_type == "s"
        workbook.close()
    finally:
        db.close()


def test_html_template_escapes_values_and_text_template_remains_plain():
    value = '<script data-value="x">alert(1)</script>'

    assert template("Value: <%= value %>", {"value": value}) == f"Value: {value}"
    assert html_template("<p><%= value %></p>", {"value": value}) == (
        "<p>&lt;script data-value=&quot;x&quot;&gt;alert(1)&lt;/script&gt;</p>"
    )


@pytest.mark.parametrize(
    "template_source",
    [
        '<a href="<%= value %>">link</a>',
        "<script><%= value %></script>",
        "<style><%= value %></style>",
        "<script><style></style><%= value %></script>",
        "<style><script></script><%= value %></style>",
    ],
)
def test_html_template_rejects_non_text_interpolation_contexts(template_source):
    with pytest.raises(SecurityError):
        html_template(template_source, {"value": "javascript:alert(1)"})


def test_audit_logger_emits_one_structured_event_for_multiline_input(
    tmp_path: Path,
):
    output_path = tmp_path / "audit.jsonl"
    event_type = "LOGIN\r\nFORGED_EVENT"
    details = "first line\nsecond line"

    with AuditLogger(log_file=str(output_path)) as logger:
        logger.log(event_type, details)

    physical_lines = output_path.read_text(encoding="utf-8").splitlines()
    assert len(physical_lines) == 1
    event = json.loads(physical_lines[0])
    assert event["event_type"] == event_type
    assert event["details"] == details
    if os.name == "posix":
        assert stat.S_IMODE(output_path.stat().st_mode) == 0o600


def test_audit_logger_can_route_through_standard_logging():
    records = []

    class ListHandler(logging.Handler):
        def emit(self, record):
            records.append(record)

    standard_logger = logging.getLogger("unicorefw.tests.audit")
    standard_logger.handlers.clear()
    standard_logger.propagate = False
    standard_logger.setLevel(logging.INFO)
    handler = ListHandler()
    standard_logger.addHandler(handler)
    try:
        AuditLogger(logger=standard_logger).log("ACCESS_DENIED", {"user": "42"})

        assert len(records) == 1
        assert json.loads(records[0].getMessage())["event_type"] == "ACCESS_DENIED"
        assert records[0].audit_event["details"] == {"user": "42"}
    finally:
        standard_logger.removeHandler(handler)
        handler.close()


@pytest.mark.skipif(not hasattr(os, "O_NOFOLLOW"), reason="O_NOFOLLOW unavailable")
def test_audit_logger_refuses_symbolic_link_destinations(tmp_path: Path):
    target_path = tmp_path / "target.log"
    link_path = tmp_path / "audit.log"
    target_path.write_text("original\n", encoding="utf-8")
    link_path.symlink_to(target_path)

    with pytest.raises(SecurityError):
        AuditLogger(log_file=str(link_path)).log("LOGIN", "user=42")

    assert target_path.read_text(encoding="utf-8") == "original\n"
