"""Tests for deterministic core-registry generation."""

from __future__ import annotations

import ast
import importlib
import json
import os
import runpy
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.dont_write_bytecode = True

from scripts import generate_core_registry


def test_chain_classification_requires_a_positional_input():
    generator = importlib.import_module("scripts.generate_core_registry")

    def accepts_value(value):
        return value

    def accepts_positional_only(value, /):
        return value

    def accepts_variadic(*values):
        return values

    def accepts_keyword_only(*, value):
        return value

    def accepts_nothing():
        return None

    assert generator._supports_chain(accepts_value)
    assert generator._supports_chain(accepts_positional_only)
    assert generator._supports_chain(accepts_variadic)
    assert not generator._supports_chain(accepts_keyword_only)
    assert not generator._supports_chain(accepts_nothing)


def test_registry_model_matches_the_reviewed_compatibility_surface():
    generator = importlib.import_module("scripts.generate_core_registry")

    model = generator.build_registry()

    assert len(model.core_exports) == 350
    assert sum(export.chainable for export in model.core_exports) == 348
    assert model.lazy_chain_names == ("decrypt_string", "encrypt_string")
    assert "generate_key" in model.lazy_static_names
    assert len(model.static_export_names) == 365
    assert len(model.metadata_records) == 365
    assert sum(len(names) for _, names in model.public_exports_by_module) == 452
    assert len(model.root_exports) == 444


def test_rendered_registry_and_metadata_are_deterministic():
    model = generate_core_registry.build_registry()

    runtime_first = generate_core_registry.render_runtime_registry(model)
    runtime_second = generate_core_registry.render_runtime_registry(model)
    metadata_first = generate_core_registry.render_api_metadata(model)
    metadata_second = generate_core_registry.render_api_metadata(model)
    exports_first = generate_core_registry.render_public_exports(model)
    exports_second = generate_core_registry.render_public_exports(model)

    assert runtime_first == runtime_second
    assert metadata_first == metadata_second
    assert exports_first == exports_second
    assert "REGISTRY_SCHEMA_VERSION = 1" in runtime_first
    assert "CORE_EXPORTS_BY_MODULE" in runtime_first
    assert "STATIC_EXPORT_NAMES" in runtime_first

    payload = json.loads(metadata_first)
    assert payload["schema_version"] == 1
    assert len(payload["exports"]) == 365
    assert "PUBLIC_EXPORTS_BY_MODULE" in exports_first
    assert "ROOT_EXPORTS" in exports_first


def test_runtime_registry_stays_compact_for_import_performance():
    runtime_source = generate_core_registry.render_runtime_registry(
        generate_core_registry.build_registry()
    )

    assert len(runtime_source.encode("utf-8")) < 10_000
    assert len(runtime_source.splitlines()) < 100


def test_metadata_is_deterministic_across_python_processes():
    source = (
        "from scripts.generate_core_registry import "
        "build_registry, render_api_metadata; "
        "print(render_api_metadata(build_registry()), end='')"
    )
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    # Metadata intentionally preserves Unicode documentation.  Force the
    # child interpreter and the parent pipe to use the same portable encoding
    # instead of the Windows console code page.
    environment["PYTHONIOENCODING"] = "utf-8"

    outputs = [
        subprocess.run(
            [sys.executable, "-c", source],
            capture_output=True,
            check=True,
            cwd=generate_core_registry.PROJECT_ROOT,
            env=environment,
            text=True,
            encoding="utf-8",
            timeout=30,
        ).stdout
        for _run in range(2)
    ]

    assert outputs[0] == outputs[1]
    assert " at 0x" not in outputs[0]


def test_metadata_preserves_chainability_and_collision_owners():
    payload = json.loads(
        generate_core_registry.render_api_metadata(
            generate_core_registry.build_registry()
        )
    )
    records = {record["name"]: record for record in payload["exports"]}

    assert records["now"]["owner_module"] == "function"
    assert records["now"]["chainable"] is False
    assert records["noop"]["chainable"] is False
    assert records["generate_key"]["chainable"] is False
    assert records["invoke"]["owner_module"] == "object"
    assert records["max_value"]["owner_module"] == "array"
    assert records["encrypt_string"]["chainable"] is True


def test_owned_function_loader_rejects_missing_export(monkeypatch):
    module = SimpleNamespace(__name__="unicorefw.fixture")
    monkeypatch.setattr(
        generate_core_registry.importlib,
        "import_module",
        lambda name: module,
    )

    with pytest.raises(
        generate_core_registry.RegistryGenerationError,
        match="fixture.missing is unavailable",
    ):
        generate_core_registry._load_owned_function("fixture", "missing")


def test_owned_function_loader_rejects_non_function(monkeypatch):
    module = SimpleNamespace(
        __name__="unicorefw.fixture",
        invalid=object(),
    )
    monkeypatch.setattr(
        generate_core_registry.importlib,
        "import_module",
        lambda name: module,
    )

    with pytest.raises(
        generate_core_registry.RegistryGenerationError,
        match="fixture.invalid is not a function",
    ):
        generate_core_registry._load_owned_function("fixture", "invalid")


def test_owned_function_loader_rejects_foreign_function(monkeypatch):
    def foreign():
        return None

    module = SimpleNamespace(
        __name__="unicorefw.fixture",
        foreign=foreign,
    )
    monkeypatch.setattr(
        generate_core_registry.importlib,
        "import_module",
        lambda name: module,
    )

    with pytest.raises(
        generate_core_registry.RegistryGenerationError,
        match="fixture.foreign is not owned",
    ):
        generate_core_registry._load_owned_function("fixture", "foreign")


def test_registry_rejects_duplicate_static_names(monkeypatch):
    record = generate_core_registry.ExportRecord(
        public_name="duplicate",
        owner_module="fixture",
        target_name="duplicate",
        signature="()",
        documentation="",
        chainable=False,
    )
    monkeypatch.setattr(
        generate_core_registry,
        "_build_core_exports",
        lambda: (record,),
    )
    monkeypatch.setattr(
        generate_core_registry,
        "_build_aliases",
        lambda: (record,),
    )
    monkeypatch.setattr(
        generate_core_registry,
        "_build_lazy_exports",
        lambda: (),
    )

    with pytest.raises(
        generate_core_registry.RegistryGenerationError,
        match="not unique",
    ):
        generate_core_registry.build_registry()


def test_owned_function_discovery_includes_public_aliases_only(monkeypatch):
    def public_function():
        return None

    def foreign_function():
        return None

    public_function.__module__ = "unicorefw.fixture"
    module = SimpleNamespace(
        __name__="unicorefw.fixture",
        _private=public_function,
        alias=public_function,
        foreign=foreign_function,
        public_function=public_function,
        public_value=object(),
    )
    monkeypatch.setattr(
        generate_core_registry.importlib,
        "import_module",
        lambda name: module,
    )

    discovered = generate_core_registry._discover_owned_functions("fixture")

    assert tuple(discovered) == ("alias", "public_function")


def test_source_discovery_includes_top_level_public_functions_only(tmp_path):
    source_path = tmp_path / "optional.py"
    source_path.write_text(
        """
def public_function():
    def nested():
        return None

public_alias = public_function
public_annotated_alias: object = public_alias
annotation_only: object
public_conditional_alias = public_function if runtime_condition else public_alias
public_lambda = lambda value: value
_private_alias = public_function
(lambda: None)

async def public_async_function():
    return None

def _private_function():
    return None

@unknown_decorator
def _decorated_private_function():
    return None

public_private_alias = _private_function

def overwritten_function():
    return None

overwritten_function = object()

def deleted_function():
    return None

del deleted_function

def conditionally_rebound():
    return None

if runtime_condition:
    conditionally_rebound = object()

if runtime_condition:
    async def conditional_async_function():
        return None

class PublicClass:
    def method(self):
        return None
""",
        encoding="utf-8",
    )

    assert generate_core_registry._discover_source_function_names(source_path) == (
        "public_alias",
        "public_annotated_alias",
        "public_async_function",
        "public_conditional_alias",
        "public_function",
        "public_lambda",
        "public_private_alias",
    )

    conditional_value = ast.parse(
        "public_function if condition else unknown",
        mode="eval",
    ).body
    assert not generate_core_registry._is_known_function_value(
        conditional_value,
        {"public_function"},
    )


def test_every_public_utility_submodule_participates_in_function_discovery():
    assert set(generate_core_registry.PUBLIC_MODULES_IN_ORDER) == (
        set(generate_core_registry.PUBLIC_SUBMODULES) - {"core"}
    )


def test_source_discovery_rejects_invalid_python(tmp_path):
    source_path = tmp_path / "invalid.py"
    source_path.write_text("def broken(:\n", encoding="utf-8")

    with pytest.raises(
        generate_core_registry.RegistryGenerationError,
        match="cannot parse public functions from invalid.py",
    ):
        generate_core_registry._discover_source_function_names(source_path)


def test_source_discovery_rejects_decorated_public_function(tmp_path):
    source_path = tmp_path / "decorated.py"
    source_path.write_text(
        """
@unknown_decorator
def public_function():
    return None
""",
        encoding="utf-8",
    )

    with pytest.raises(
        generate_core_registry.RegistryGenerationError,
        match="cannot classify decorated public function decorated.py.public_function",
    ):
        generate_core_registry._discover_source_function_names(source_path)


def test_public_export_builder_automatically_includes_new_function(monkeypatch):
    monkeypatch.setattr(
        generate_core_registry,
        "PUBLIC_MODULES_IN_ORDER",
        ("array",),
    )
    monkeypatch.setattr(generate_core_registry, "SOURCE_DISCOVERY_MODULES", frozenset())
    monkeypatch.setattr(
        generate_core_registry,
        "EXPLICIT_PUBLIC_EXPORTS_BY_MODULE",
        {},
    )
    monkeypatch.setattr(
        generate_core_registry,
        "APPROVED_PUBLIC_NAME_COLLISIONS",
        {},
    )
    monkeypatch.setattr(
        generate_core_registry,
        "_discover_owned_functions",
        lambda module_name: {"map": object(), "reduce_top": object()},
    )

    exports = generate_core_registry._build_public_exports()

    assert exports == (("array", frozenset(("map", "reduce_top"))),)


def test_core_export_builder_automatically_includes_new_function(monkeypatch):
    def reduce_top(values):
        return values

    monkeypatch.setattr(generate_core_registry, "CORE_MODULES_IN_ORDER", ("array",))
    monkeypatch.setattr(
        generate_core_registry,
        "_discover_owned_functions",
        lambda module_name: {"reduce_top": reduce_top},
    )

    records = generate_core_registry._build_core_exports()

    assert tuple(record.public_name for record in records) == ("reduce_top",)
    assert records[0].chainable is True


def test_public_export_builder_rejects_unknown_explicit_module(monkeypatch):
    monkeypatch.setattr(generate_core_registry, "PUBLIC_MODULES_IN_ORDER", ())
    monkeypatch.setattr(
        generate_core_registry,
        "EXPLICIT_PUBLIC_EXPORTS_BY_MODULE",
        {"unknown": frozenset(("value",))},
    )

    with pytest.raises(
        generate_core_registry.RegistryGenerationError,
        match="explicit public exports configured for unknown modules: unknown",
    ):
        generate_core_registry._build_public_exports()


def test_public_export_builder_omits_modules_without_exports(monkeypatch):
    monkeypatch.setattr(
        generate_core_registry,
        "PUBLIC_MODULES_IN_ORDER",
        ("empty",),
    )
    monkeypatch.setattr(
        generate_core_registry,
        "EXPLICIT_PUBLIC_EXPORTS_BY_MODULE",
        {},
    )
    monkeypatch.setattr(
        generate_core_registry,
        "APPROVED_PUBLIC_NAME_COLLISIONS",
        {},
    )
    monkeypatch.setattr(
        generate_core_registry,
        "_discover_public_function_names",
        lambda module_name: (),
    )

    assert generate_core_registry._build_public_exports() == ()


def test_unapproved_public_name_collision_fails_closed():
    exports = (
        ("array", frozenset(("duplicate",))),
        ("object", frozenset(("duplicate",))),
    )

    with pytest.raises(
        generate_core_registry.RegistryGenerationError,
        match="unapproved public export collision.*duplicate",
    ):
        generate_core_registry._validate_public_name_collisions(exports, {})


def test_approved_public_name_collision_requires_exact_owners():
    exports = (
        ("array", frozenset(("duplicate",))),
        ("object", frozenset(("duplicate",))),
    )

    generate_core_registry._validate_public_name_collisions(
        exports,
        {"duplicate": ("array", "object")},
    )

    with pytest.raises(
        generate_core_registry.RegistryGenerationError,
        match="approved public export collision.*missing",
    ):
        generate_core_registry._validate_public_name_collisions(
            exports,
            {
                "duplicate": ("array", "object"),
                "missing": ("array", "object"),
            },
        )


def test_registry_generation_does_not_import_database_or_orm_modules():
    source = (
        "import json, sys; "
        "from scripts.generate_core_registry import build_registry; "
        "build_registry(); "
        "print(json.dumps(sorted(name for name in sys.modules "
        "if name in {'unicorefw.db', 'unicorefw.orm'})))"
    )
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONIOENCODING"] = "utf-8"

    completed = subprocess.run(
        [sys.executable, "-c", source],
        capture_output=True,
        check=True,
        cwd=generate_core_registry.PROJECT_ROOT,
        env=environment,
        text=True,
        encoding="utf-8",
        timeout=30,
    )

    assert json.loads(completed.stdout) == []


def test_runtime_renderer_supports_an_empty_model():
    model = generate_core_registry.RegistryModel(
        core_exports=(),
        aliases=(),
        lazy_exports=(),
        public_exports_by_module=(),
    )

    source = generate_core_registry.render_runtime_registry(model)
    public_source = generate_core_registry.render_public_exports(model)
    public_namespace = {}
    exec(public_source, public_namespace)  # noqa: S102

    assert "CORE_EXPORTS_BY_MODULE = (\n)" in source
    assert "COMPATIBILITY_ALIASES = (\n)" in source
    assert 'STATIC_EXPORT_NAMES = tuple(\n    "".split()\n)' in source
    assert public_namespace["PUBLIC_EXPORTS_BY_MODULE"] == ()
    assert public_namespace["ROOT_EXPORTS"] == {}


def test_synchronization_checks_and_writes_only_changed_fixed_paths(
    monkeypatch,
    tmp_path,
):
    runtime_path = tmp_path / "unicorefw" / "_core_registry.py"
    exports_path = tmp_path / "unicorefw" / "_exports.py"
    metadata_path = tmp_path / "docs" / "api" / "core-exports.json"
    monkeypatch.setattr(
        generate_core_registry,
        "RUNTIME_REGISTRY_PATH",
        runtime_path,
    )
    monkeypatch.setattr(
        generate_core_registry,
        "PUBLIC_EXPORTS_PATH",
        exports_path,
    )
    monkeypatch.setattr(
        generate_core_registry,
        "API_METADATA_PATH",
        metadata_path,
    )

    assert generate_core_registry.synchronize_generated_files(check=True) == [
        exports_path,
        runtime_path,
        metadata_path,
    ]
    assert not exports_path.exists()
    assert not runtime_path.exists()
    assert not metadata_path.exists()

    assert generate_core_registry.synchronize_generated_files(check=False) == [
        exports_path,
        runtime_path,
        metadata_path,
    ]
    expected_exports = generate_core_registry.render_public_exports(
        generate_core_registry.build_registry()
    )
    expected_runtime = generate_core_registry.render_runtime_registry(
        generate_core_registry.build_registry()
    )
    expected_metadata = generate_core_registry.render_api_metadata(
        generate_core_registry.build_registry()
    )
    assert exports_path.read_text(encoding="utf-8") == expected_exports
    assert runtime_path.read_text(encoding="utf-8") == expected_runtime
    assert metadata_path.read_text(encoding="utf-8") == expected_metadata
    assert generate_core_registry.synchronize_generated_files(check=True) == []
    assert generate_core_registry.synchronize_generated_files(check=False) == []

    runtime_path.write_text("stale\n", encoding="utf-8")
    assert generate_core_registry.synchronize_generated_files(check=True) == [
        runtime_path
    ]
    assert runtime_path.read_text(encoding="utf-8") == "stale\n"


def test_generator_cli_reports_drift_without_writing(
    monkeypatch,
    capsys,
):
    drifted = Path("/fixed/_core_registry.py")
    monkeypatch.setattr(
        generate_core_registry,
        "synchronize_generated_files",
        lambda *, check: [drifted] if check else [],
    )

    assert generate_core_registry.main(["--check"]) == 1
    assert "_core_registry.py" in capsys.readouterr().err


def test_generator_cli_succeeds_for_current_or_written_files(
    monkeypatch,
    capsys,
):
    monkeypatch.setattr(
        generate_core_registry,
        "synchronize_generated_files",
        lambda *, check: [],
    )

    assert generate_core_registry.main(["--check"]) == 0
    assert generate_core_registry.main([]) == 0
    assert capsys.readouterr().err == ""


def test_generator_cli_reports_generation_failure(monkeypatch, capsys):
    def fail_generation(*, check):
        raise generate_core_registry.RegistryGenerationError("fixture failure")

    monkeypatch.setattr(
        generate_core_registry,
        "synchronize_generated_files",
        fail_generation,
    )

    assert generate_core_registry.main([]) == 1
    assert (
        capsys.readouterr().err == "core registry generation failed: fixture failure\n"
    )


def test_generator_script_entry_point(monkeypatch):
    script_path = Path(generate_core_registry.__file__).resolve()
    monkeypatch.setattr(sys, "argv", [str(script_path), "--check"])

    with pytest.raises(SystemExit) as caught:
        runpy.run_path(str(script_path), run_name="__main__")

    assert caught.value.code == 0


def test_committed_generated_artifacts_are_current():
    assert generate_core_registry.synchronize_generated_files(check=True) == []
