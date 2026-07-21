"""Adversarial tests for content-expansion and import resource budgets."""

from __future__ import annotations

import importlib
import json
import threading
import time
import zipfile
from pathlib import Path

import pytest

from unicorefw.db import CacheManager, Database, DataImporter, _validate_zip_expansion
from unicorefw.function import debounce
from unicorefw.object import get, set_
from unicorefw.regex_policy import RegexLimits, unsafe_raw_regex
from unicorefw.security import InputValidationError, ResourceLimitError, SecurityError
from unicorefw.string import regex_find_all, regex_replace, regex_test
from unicorefw.supporter import PathLimits, _ensure_container, _ensure_len
from unicorefw.template import TemplateLimits, html_template, template
from unicorefw.utils import decompress, memoize


def _database_with_items_table() -> Database:
    db = Database(engine="sqlite", database=":memory:")
    db.create_table("items", {"name": "TEXT"})
    return db


def test_decompress_enforces_output_and_ratio_limits_before_allocation():
    assert decompress("2a3b") == "aabbb"

    with pytest.raises(ResourceLimitError, match="decompressed output") as error:
        decompress("1000000000a")
    assert error.value.resource == "decompressed output length"
    assert error.value.limit == 1_000_000

    with pytest.raises(ResourceLimitError, match="compression ratio"):
        decompress("100a", max_compression_ratio=10)


def test_decompress_rejects_unsafe_limit_overrides():
    with pytest.raises(InputValidationError, match="max_output_length"):
        decompress("1a", max_output_length=100_000_000)

    with pytest.raises(InputValidationError, match="max_compression_ratio"):
        decompress("1a", max_compression_ratio=10_000)

    with pytest.raises(InputValidationError, match="finite"):
        decompress("1a", max_compression_ratio=float("nan"))


def test_template_enforces_token_and_nesting_limits():
    with pytest.raises(ResourceLimitError, match="template token count"):
        template(
            "<%= a %><%= b %><%= c %>",
            {"a": 1, "b": 2, "c": 3},
            limits=TemplateLimits(max_tokens=2),
        )

    nested = "<% if ok %>" * 3 + "value" + "<% endif %>" * 3
    with pytest.raises(ResourceLimitError, match="template nesting depth"):
        template(
            nested,
            {"ok": True},
            limits=TemplateLimits(max_nesting_depth=2),
        )


def test_template_enforces_output_limit_for_static_and_interpolated_text():
    limits = TemplateLimits(max_output_length=8)

    with pytest.raises(ResourceLimitError, match="template output length"):
        template("123456789", {}, limits=limits)

    with pytest.raises(ResourceLimitError, match="template output length"):
        html_template("<p><%= value %></p>", {"value": "<script>"}, limits=limits)


def test_template_limit_configuration_has_hard_upper_bounds():
    with pytest.raises(InputValidationError, match="max_template_length"):
        TemplateLimits(max_template_length=2_000_000)


def test_template_enforces_context_item_limit():
    with pytest.raises(ResourceLimitError, match="template context items"):
        template(
            "<%= first %>",
            {"first": "one", "second": "two"},
            limits=TemplateLimits(max_context_items=1),
        )


def test_memoize_enforces_lru_entry_limit_and_ttl():
    current_time = [0.0]
    calls = []

    def calculate(value):
        calls.append(value)
        return value * 2

    cached = memoize(
        calculate,
        max_entries=2,
        max_weight_bytes=4_096,
        ttl_seconds=10,
        clock=lambda: current_time[0],
    )

    assert cached(1) == 2
    assert cached(2) == 4
    assert cached(1) == 2
    assert cached(3) == 6
    assert cached(2) == 4
    assert calls == [1, 2, 3, 2]
    assert cached.cache_info()["entries"] == 2

    current_time[0] = 11
    assert cached(2) == 4
    assert calls == [1, 2, 3, 2, 2]
    cached.cache_clear()
    assert cached.cache_info()["entries"] == 0


def test_memoize_skips_entries_over_weight_budget_and_validates_settings():
    calls = []

    def calculate(value):
        calls.append(value)
        return "x" * 1_000

    cached = memoize(calculate, max_weight_bytes=128)
    assert cached(1) == "x" * 1_000
    assert cached(1) == "x" * 1_000
    assert calls == [1, 1]

    with pytest.raises(InputValidationError, match="max_entries"):
        memoize(calculate, max_entries=0)
    with pytest.raises(InputValidationError, match="clock"):
        memoize(calculate, clock=None)  # type: ignore[arg-type]
    with pytest.raises(InputValidationError, match="func"):
        memoize(None)  # type: ignore[arg-type]

    key_too_large = memoize(calculate, max_weight_bytes=1)
    assert key_too_large(2) == "x" * 1_000
    assert key_too_large(2) == "x" * 1_000


def test_memoize_resolves_concurrent_duplicate_insertions():
    barrier = threading.Barrier(2)
    call_count = 0
    call_lock = threading.Lock()

    def calculate(value):
        nonlocal call_count
        with call_lock:
            call_count += 1
        barrier.wait(timeout=2)
        return value * 2

    cached = memoize(calculate)
    results = []
    threads = [
        threading.Thread(target=lambda: results.append(cached(2))) for _ in range(2)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=2)

    assert not any(thread.is_alive() for thread in threads)
    assert results == [4, 4]
    assert call_count == 2
    assert cached.cache_info()["entries"] == 1


def test_query_cache_is_bounded_expires_and_isolates_mutable_results():
    current_time = [0.0]
    db = Database(engine="sqlite", database=":memory:")
    cache = CacheManager(
        db,
        ttl=10,
        max_entries=1,
        max_weight_bytes=4_096,
        clock=lambda: current_time[0],
    )
    try:
        source = [{"value": [1]}]
        cache.set("SELECT 1", source)
        source[0]["value"].append(2)
        first = cache.get("SELECT 1")
        assert first == [{"value": [1]}]
        first[0]["value"].append(3)  # type: ignore[index]
        assert cache.get("SELECT 1") == [{"value": [1]}]

        cache.set("SELECT 2", [{"value": 2}])
        assert cache.get("SELECT 1") is None
        assert cache.cache_info()["entries"] == 1

        current_time[0] = 11
        assert cache.get("SELECT 2") is None
        assert cache.cache_info()["entries"] == 0
    finally:
        db.close()


def test_query_cache_skips_overweight_results_and_validates_settings():
    db = Database(engine="sqlite", database=":memory:")
    try:
        cache = CacheManager(db, max_weight_bytes=128)
        cache.set("SELECT payload", [{"payload": "x" * 1_000}])
        assert cache.get("SELECT payload") is None

        with pytest.raises(InputValidationError, match="ttl"):
            CacheManager(db, ttl=0)
        with pytest.raises(InputValidationError, match="max_entries"):
            CacheManager(db, max_entries=0)
        with pytest.raises(InputValidationError, match="clock"):
            CacheManager(db, clock=None)  # type: ignore[arg-type]

        with pytest.raises(InputValidationError, match="query"):
            cache.get(1)  # type: ignore[arg-type]
    finally:
        db.close()


def test_query_cache_handles_copy_failures_replacement_clear_and_fetch():
    class NeverCopy:
        def __deepcopy__(self, memo):
            raise RuntimeError("copy blocked")

    class CopyOnce:
        def __init__(self):
            self.calls = 0

        def __deepcopy__(self, memo):
            self.calls += 1
            if self.calls > 1:
                raise RuntimeError("copy blocked")
            return self

    db = _database_with_items_table()
    try:
        db.insert("items", {"name": "alpha"})
        cache = CacheManager(db)

        cache.set("SELECT never", [{"value": NeverCopy()}])
        assert cache.get("SELECT never") is None

        copy_once = CopyOnce()
        cache.set("SELECT once", [{"value": copy_once}])
        assert cache.get("SELECT once") is None

        cache.set("SELECT constant", [{"value": 1}])
        cache.set("SELECT constant", [{"value": 2}])
        assert cache.get("SELECT constant") == [{"value": 2}]

        assert cache.fetch_with_cache("SELECT name FROM items") == [{"name": "alpha"}]
        db.execute("UPDATE items SET name = ?", ("beta",))
        assert cache.fetch_with_cache("SELECT name FROM items") == [{"name": "alpha"}]

        cache.clear()
        assert cache.cache_info()["entries"] == 0
    finally:
        db.close()


def test_debounce_rejects_timer_thread_flood(monkeypatch):
    function_module = importlib.import_module("unicorefw.function")
    monkeypatch.setattr(
        function_module._BudgetedTimer,
        "start",
        lambda self: None,
    )
    wrapped = debounce(lambda: None, 1_000, max_pending_timers=1)
    wrapped()

    with pytest.raises(ResourceLimitError, match="pending debounce timers"):
        wrapped()

    assert wrapped.pending_timer_count() == 1
    wrapped.cancel()


def test_debounce_validates_timer_budgets():
    with pytest.raises(InputValidationError, match="max_pending_timers"):
        debounce(lambda: None, 1, max_pending_timers=0)
    with pytest.raises(InputValidationError, match="wait"):
        debounce(lambda: None, float("nan"))


def test_debounce_releases_budget_after_start_and_callback_failures(monkeypatch):
    function_module = importlib.import_module("unicorefw.function")

    def fail_start(self):
        raise RuntimeError("thread start blocked")

    monkeypatch.setattr(function_module._BudgetedTimer, "start", fail_start)
    wrapped = debounce(lambda: None, 1)
    with pytest.raises(RuntimeError, match="thread start blocked"):
        wrapped()
    assert wrapped.pending_timer_count() == 0

    monkeypatch.undo()
    called = threading.Event()

    def fail_callback():
        called.set()
        raise RuntimeError("callback failed")

    wrapped = debounce(fail_callback, 0)
    wrapped()
    assert called.wait(timeout=2)
    for _ in range(100):
        if wrapped.pending_timer_count() == 0:
            break
        time.sleep(0.01)
    assert wrapped.pending_timer_count() == 0
    wrapped.cancel()


def test_nested_path_limits_preflight_depth_and_list_growth():
    target = {}
    with pytest.raises(ResourceLimitError, match="nested path depth"):
        set_(
            target,
            ["a", "b", "c"],
            1,
            limits=PathLimits(max_depth=2),
        )
    assert target == {}

    with pytest.raises(ResourceLimitError, match="auto-created list length"):
        set_(
            target,
            ["items", 3],
            "value",
            limits=PathLimits(max_list_length=3),
        )
    assert target == {}

    limits = PathLimits(max_depth=2, max_list_length=3)
    assert set_(target, ["items", 2], "value", limits=limits) == {
        "items": [None, None, "value"]
    }
    assert get(target, ["items", 2], limits=limits) == "value"


def test_nested_path_limits_reject_source_and_unsafe_overrides():
    with pytest.raises(ResourceLimitError, match="nested path source length"):
        get({}, "abcd", limits=PathLimits(max_path_length=3))
    with pytest.raises(InputValidationError, match="max_depth"):
        PathLimits(max_depth=1_000)
    with pytest.raises(TypeError, match="PathLimits"):
        get({}, "value", limits=object())  # type: ignore[arg-type]

    with pytest.raises(ResourceLimitError, match="auto-created list length"):
        _ensure_container([], 3, max_list_length=3)
    with pytest.raises(ResourceLimitError, match="auto-created list length"):
        _ensure_len([], 4, max_list_length=3)


def test_regex_policy_rejects_backtracking_and_resource_exhaustion():
    with pytest.raises(SecurityError, match="Nested or ambiguous repetition"):
        regex_test("a" * 100 + "!", r"(a+)+$")
    with pytest.raises(SecurityError, match="special groups"):
        regex_test("admin", r"(?=admin)")
    with pytest.raises(ResourceLimitError, match="regex input length"):
        regex_test("12345", r"\d+", limits=RegexLimits(max_input_length=4))
    with pytest.raises(ResourceLimitError, match="regex pattern length"):
        regex_test("a", "a" * 5, limits=RegexLimits(max_pattern_length=4))
    with pytest.raises(ResourceLimitError, match="regex quantifier count"):
        regex_test("axbb", "a+xb+", limits=RegexLimits(max_quantifiers=1))
    with pytest.raises(ResourceLimitError, match="regex repeat bound"):
        regex_test("a", "a{100001}")


def test_regex_policy_supports_safe_helpers_and_explicit_trust():
    assert regex_find_all("a1b22", r"\d+") == ["1", "22"]
    assert regex_replace("a1b2", r"\d", "#") == "a#b#"
    assert regex_test("aaaa", unsafe_raw_regex(r"(a+)+$"))


def test_json_import_rejects_byte_limit_before_database_mutation(tmp_path: Path):
    input_path = tmp_path / "items.json"
    input_path.write_text(json.dumps([{"name": "alpha"}]), encoding="utf-8")
    db = Database(engine="sqlite", database=":memory:")
    try:
        with pytest.raises(ResourceLimitError, match="JSON import bytes"):
            DataImporter(db).from_json(
                str(input_path),
                "items",
                max_bytes=4,
            )

        assert (
            db.fetch_one(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='items'"
            )
            is None
        )
    finally:
        db.close()


def test_json_import_rejects_row_limit_before_database_mutation(tmp_path: Path):
    input_path = tmp_path / "items.json"
    input_path.write_text(
        json.dumps([{"name": "alpha"}, {"name": "beta"}]),
        encoding="utf-8",
    )
    db = Database(engine="sqlite", database=":memory:")
    try:
        with pytest.raises(ResourceLimitError, match="JSON import rows"):
            DataImporter(db).from_json(
                str(input_path),
                "items",
                max_rows=1,
            )

        assert (
            db.fetch_one(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='items'"
            )
            is None
        )
    finally:
        db.close()


def test_json_import_rejects_column_limit_before_database_mutation(tmp_path: Path):
    input_path = tmp_path / "items.json"
    input_path.write_text(
        json.dumps([{"name": "alpha", "description": "item"}]),
        encoding="utf-8",
    )
    db = Database(engine="sqlite", database=":memory:")
    try:
        with pytest.raises(ResourceLimitError, match="JSON import columns"):
            DataImporter(db).from_json(
                str(input_path),
                "items",
                max_columns=1,
            )

        assert (
            db.fetch_one(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='items'"
            )
            is None
        )
    finally:
        db.close()


def test_json_import_accepts_content_at_exact_byte_and_row_limits(tmp_path: Path):
    input_path = tmp_path / "items.json"
    encoded = json.dumps([{"name": "alpha"}]).encode("utf-8")
    input_path.write_bytes(encoded)
    db = Database(engine="sqlite", database=":memory:")
    try:
        inserted = DataImporter(db).from_json(
            str(input_path),
            "items",
            max_bytes=len(encoded),
            max_rows=1,
        )

        assert inserted == 1
        assert db.fetch_one("SELECT name FROM items") == {"name": "alpha"}
    finally:
        db.close()


def test_csv_import_rolls_back_when_stream_exceeds_row_limit(tmp_path: Path):
    input_path = tmp_path / "items.csv"
    input_path.write_text("name\nalpha\nbeta\n", encoding="utf-8")
    db = _database_with_items_table()
    try:
        with pytest.raises(ResourceLimitError, match="CSV import rows"):
            DataImporter(db).from_csv(
                str(input_path),
                "items",
                create_table=False,
                max_rows=1,
            )

        assert db.fetch_one("SELECT COUNT(*) AS count FROM items") == {"count": 0}
    finally:
        db.close()


def test_csv_import_accepts_content_at_exact_byte_and_row_limits(tmp_path: Path):
    input_path = tmp_path / "items.csv"
    encoded = b"name\nalpha\n"
    input_path.write_bytes(encoded)
    db = _database_with_items_table()
    try:
        inserted = DataImporter(db).from_csv(
            str(input_path),
            "items",
            create_table=False,
            max_bytes=len(encoded),
            max_rows=1,
        )

        assert inserted == 1
        assert db.fetch_one("SELECT name FROM items") == {"name": "alpha"}
    finally:
        db.close()


def test_csv_import_enforces_streamed_byte_limit(tmp_path: Path):
    input_path = tmp_path / "items.csv"
    input_path.write_text("name\nalpha\n", encoding="utf-8")
    db = _database_with_items_table()
    try:
        with pytest.raises(ResourceLimitError, match="CSV import bytes"):
            DataImporter(db).from_csv(
                str(input_path),
                "items",
                create_table=False,
                max_bytes=5,
            )
        assert db.fetch_one("SELECT COUNT(*) AS count FROM items") == {"count": 0}
    finally:
        db.close()


def test_csv_import_counts_duplicate_header_columns(tmp_path: Path):
    input_path = tmp_path / "items.csv"
    input_path.write_text("name,name\nalpha,beta\n", encoding="utf-8")
    db = Database(engine="sqlite", database=":memory:")
    try:
        with pytest.raises(ResourceLimitError, match="CSV import columns"):
            DataImporter(db).from_csv(
                str(input_path),
                "items",
                max_columns=1,
            )
        assert (
            db.fetch_one(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='items'"
            )
            is None
        )
    finally:
        db.close()


def test_import_rejects_unsafe_batch_and_row_limit_overrides(tmp_path: Path):
    input_path = tmp_path / "items.json"
    input_path.write_text("[]", encoding="utf-8")
    db = Database(engine="sqlite", database=":memory:")
    try:
        with pytest.raises(InputValidationError, match="batch_size"):
            DataImporter(db).from_json(str(input_path), "items", batch_size=0)

        with pytest.raises(InputValidationError, match="max_rows"):
            DataImporter(db).from_json(
                str(input_path),
                "items",
                max_rows=100_000_000,
            )
    finally:
        db.close()


def test_dict_import_enforces_row_limit_before_database_mutation():
    db = Database(engine="sqlite", database=":memory:")
    try:
        with pytest.raises(ResourceLimitError, match="dictionary import rows"):
            DataImporter(db).from_dict(
                [{"name": "alpha"}, {"name": "beta"}],
                "items",
                max_rows=1,
            )
        assert (
            db.fetch_one(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='items'"
            )
            is None
        )
    finally:
        db.close()


def test_zip_expansion_preflight_rejects_compression_bomb_ratio(tmp_path: Path):
    archive_path = tmp_path / "workbook.xlsx"
    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        archive.writestr("xl/worksheets/sheet1.xml", "A" * 100_000)

    with pytest.raises(ResourceLimitError, match="Excel ZIP expansion ratio"):
        _validate_zip_expansion(
            str(archive_path),
            max_uncompressed_bytes=1_000_000,
            max_compression_ratio=2,
        )


def test_zip_expansion_preflight_rejects_expanded_byte_limit(tmp_path: Path):
    archive_path = tmp_path / "workbook.xlsx"
    with zipfile.ZipFile(
        archive_path, "w", compression=zipfile.ZIP_DEFLATED
    ) as archive:
        archive.writestr("xl/worksheets/sheet1.xml", "A" * 1_000)

    with pytest.raises(ResourceLimitError, match="Excel ZIP expanded bytes"):
        _validate_zip_expansion(
            str(archive_path),
            max_uncompressed_bytes=999,
            max_compression_ratio=1_000,
        )


def test_excel_import_enforces_row_limit(tmp_path: Path):
    pandas = pytest.importorskip("pandas")
    pytest.importorskip("openpyxl")
    input_path = tmp_path / "items.xlsx"
    pandas.DataFrame([{"name": "alpha"}, {"name": "beta"}]).to_excel(
        input_path,
        index=False,
    )
    db = Database(engine="sqlite", database=":memory:")
    try:
        with pytest.raises(ResourceLimitError, match="Excel import rows"):
            DataImporter(db).from_excel(
                str(input_path),
                table="items",
                max_rows=1,
            )
        assert (
            db.fetch_one(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='items'"
            )
            is None
        )
    finally:
        db.close()
