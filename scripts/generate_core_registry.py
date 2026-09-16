"""Generate UniCoreFW's deterministic core dispatch registry."""

from __future__ import annotations

import argparse
import ast
import importlib
import inspect
import json
import os
import re
import sys
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from unicorefw._export_policy import (
    APPROVED_PUBLIC_NAME_COLLISIONS,
    CORE_COMPATIBILITY_ALIASES,
    CORE_MODULES_IN_ORDER,
    EXPLICIT_PUBLIC_EXPORTS_BY_MODULE,
    LAZY_CHAIN_MODULES,
    LAZY_STATIC_MODULES,
    PUBLIC_MODULES_IN_ORDER,
    PUBLIC_SUBMODULES,
    SOURCE_DISCOVERY_MODULES,
)

REGISTRY_SCHEMA_VERSION = 1
RUNTIME_REGISTRY_PATH = PROJECT_ROOT / "unicorefw" / "_core_registry.py"
PUBLIC_EXPORTS_PATH = PROJECT_ROOT / "unicorefw" / "_exports.py"
API_METADATA_PATH = PROJECT_ROOT / "docs" / "api" / "core-exports.json"
_PROXY_SIGNATURE = "(*args: Any, **kwargs: Any) -> Any"
_MEMORY_ADDRESS = re.compile(r" at 0x[0-9A-Fa-f]+")


class RegistryGenerationError(RuntimeError):
    """Raised when declared exports cannot produce a safe registry."""


class _StableRepresentation:
    def __init__(self, representation: str):
        self.representation = representation

    def __repr__(self) -> str:
        return self.representation


@dataclass(frozen=True)
class ExportRecord:
    """Build-time metadata for one static compatibility export."""

    public_name: str
    owner_module: str
    target_name: str
    signature: str
    documentation: str
    chainable: bool
    deprecated: bool = False


@dataclass(frozen=True)
class RegistryModel:
    """Complete generated registry model."""

    core_exports: tuple[ExportRecord, ...]
    aliases: tuple[ExportRecord, ...]
    lazy_exports: tuple[ExportRecord, ...]
    public_exports_by_module: tuple[tuple[str, frozenset[str]], ...]

    @property
    def root_exports(self) -> dict[str, str]:
        exports = {}
        for module_name, public_names in self.public_exports_by_module:
            exports.update((name, module_name) for name in public_names)
        return exports

    @property
    def lazy_chain_names(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                export.public_name for export in self.lazy_exports if export.chainable
            )
        )

    @property
    def lazy_static_names(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                export.public_name
                for export in self.lazy_exports
                if not export.chainable
            )
        )

    @property
    def metadata_records(self) -> tuple[ExportRecord, ...]:
        return self.core_exports + self.aliases + self.lazy_exports

    @property
    def static_export_names(self) -> tuple[str, ...]:
        return tuple(sorted(export.public_name for export in self.metadata_records))


def _supports_chain(function: Callable[..., Any]) -> bool:
    parameters = tuple(inspect.signature(function).parameters.values())
    if not parameters:
        return False
    return parameters[0].kind in {
        inspect.Parameter.POSITIONAL_ONLY,
        inspect.Parameter.POSITIONAL_OR_KEYWORD,
        inspect.Parameter.VAR_POSITIONAL,
    }


def _signature_text(function: Callable[..., Any]) -> str:
    signature = inspect.signature(function)
    parameters = []
    for parameter in signature.parameters.values():
        default = parameter.default
        if default is not inspect.Parameter.empty:
            representation = repr(default)
            if representation.startswith("<") and representation.endswith(">"):
                stable_representation = _MEMORY_ADDRESS.sub("", representation)
                if stable_representation != representation:
                    parameter = parameter.replace(
                        default=_StableRepresentation(stable_representation)
                    )
        parameters.append(parameter)
    return str(signature.replace(parameters=parameters))


def _function_record(
    public_name: str,
    owner_module: str,
    target_name: str,
    function: Callable[..., Any],
    *,
    chainable: bool,
) -> ExportRecord:
    return ExportRecord(
        public_name=public_name,
        owner_module=owner_module,
        target_name=target_name,
        signature=_signature_text(function),
        documentation=inspect.getdoc(function) or "",
        chainable=chainable,
    )


def _discover_owned_functions(
    module_name: str,
) -> dict[str, Callable[..., Any]]:
    """Return public functions defined by a trusted implementation module.

    Public aliases are included because ownership follows the callable's
    ``__module__``. Imported functions, private names, classes, and arbitrary
    callable objects are excluded.
    """
    module = importlib.import_module(f"unicorefw.{module_name}")
    return {
        name: value
        for name, value in sorted(vars(module).items())
        if not name.startswith("_")
        and inspect.isfunction(value)
        and value.__module__ == module.__name__
    }


class _BoundNameVisitor(ast.NodeVisitor):
    """Collect names a statement may bind without entering local scopes."""

    def __init__(self) -> None:
        self.names = set()

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, (ast.Store, ast.Del)):
            self.names.add(node.id)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.names.add(node.name)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.names.add(node.name)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.names.add(node.name)

    def visit_Lambda(self, node: ast.Lambda) -> None:
        return None

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.names.add(alias.asname or alias.name.partition(".")[0])

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.names.add(alias.asname or alias.name)


def _bound_names(statement: ast.AST) -> set:
    visitor = _BoundNameVisitor()
    visitor.visit(statement)
    return visitor.names


def _is_known_function_value(value: ast.AST, function_names: set) -> bool:
    if isinstance(value, ast.Lambda):
        return True
    if isinstance(value, ast.Name):
        return value.id in function_names
    if isinstance(value, ast.IfExp):
        return _is_known_function_value(
            value.body, function_names
        ) and _is_known_function_value(value.orelse, function_names)
    return False


def _update_assignment_bindings(
    targets: Sequence[ast.AST],
    value: ast.AST,
    function_names: set,
) -> None:
    value_is_function = _is_known_function_value(value, function_names)
    for target in targets:
        target_names = _bound_names(target)
        function_names.difference_update(target_names)
        if value_is_function and isinstance(target, ast.Name):
            function_names.add(target.id)


def _discover_source_function_names(source_path: Path) -> tuple[str, ...]:
    """Return definite public final function bindings without importing."""
    source = source_path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(source_path))
    except SyntaxError as exc:
        raise RegistryGenerationError(
            f"cannot parse public functions from {source_path.name}"
        ) from exc
    function_names = set()
    for statement in tree.body:
        if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if statement.decorator_list:
                if not statement.name.startswith("_"):
                    raise RegistryGenerationError(
                        "cannot classify decorated public function "
                        f"{source_path.name}.{statement.name}"
                    )
                function_names.discard(statement.name)
            else:
                function_names.add(statement.name)
            continue
        if isinstance(statement, ast.Assign):
            _update_assignment_bindings(
                statement.targets,
                statement.value,
                function_names,
            )
            continue
        if isinstance(statement, ast.AnnAssign):
            if statement.value is not None:
                _update_assignment_bindings(
                    (statement.target,),
                    statement.value,
                    function_names,
                )
            continue
        function_names.difference_update(_bound_names(statement))
    return tuple(sorted(name for name in function_names if not name.startswith("_")))


def _discover_public_function_names(module_name: str) -> tuple[str, ...]:
    if module_name in SOURCE_DISCOVERY_MODULES:
        return _discover_source_function_names(
            PROJECT_ROOT / "unicorefw" / f"{module_name}.py"
        )
    return tuple(_discover_owned_functions(module_name))


def _validate_public_name_collisions(
    exports_by_module: tuple[tuple[str, frozenset[str]], ...],
    approved_collisions: Mapping[str, tuple[str, ...]],
) -> None:
    owners_by_name: dict[str, list[str]] = {}
    for module_name, public_names in exports_by_module:
        for public_name in public_names:
            owners_by_name.setdefault(public_name, []).append(module_name)

    actual_collisions = {
        public_name: tuple(owners)
        for public_name, owners in owners_by_name.items()
        if len(owners) > 1
    }
    for public_name, owners in sorted(actual_collisions.items()):
        if approved_collisions.get(public_name) != owners:
            raise RegistryGenerationError(
                "unapproved public export collision for "
                f"{public_name!r}: {', '.join(owners)}"
            )

    absent_approvals = sorted(set(approved_collisions) - set(actual_collisions))
    if absent_approvals:
        raise RegistryGenerationError(
            "approved public export collision is absent: " + ", ".join(absent_approvals)
        )


def _build_public_exports() -> tuple[tuple[str, frozenset[str]], ...]:
    unknown_modules = sorted(
        set(EXPLICIT_PUBLIC_EXPORTS_BY_MODULE) - set(PUBLIC_MODULES_IN_ORDER)
    )
    if unknown_modules:
        raise RegistryGenerationError(
            "explicit public exports configured for unknown modules: "
            + ", ".join(unknown_modules)
        )

    groups = []
    for module_name in PUBLIC_MODULES_IN_ORDER:
        public_names = set(_discover_public_function_names(module_name))
        public_names.update(
            EXPLICIT_PUBLIC_EXPORTS_BY_MODULE.get(module_name, frozenset())
        )
        if public_names:
            groups.append((module_name, frozenset(public_names)))
    exports_by_module = tuple(groups)
    _validate_public_name_collisions(
        exports_by_module,
        APPROVED_PUBLIC_NAME_COLLISIONS,
    )
    return exports_by_module


def _load_owned_function(
    module_name: str,
    function_name: str,
) -> Callable[..., Any]:
    module = importlib.import_module(f"unicorefw.{module_name}")
    try:
        function = getattr(module, function_name)
    except AttributeError as exc:
        raise RegistryGenerationError(
            f"declared export {module_name}.{function_name} is unavailable"
        ) from exc
    if not inspect.isfunction(function):
        raise RegistryGenerationError(
            f"declared export {module_name}.{function_name} is not a function"
        )
    if function.__module__ != module.__name__:
        raise RegistryGenerationError(
            f"declared export {module_name}.{function_name} is not owned "
            f"by {module.__name__}"
        )
    return function


def _build_core_exports() -> tuple[ExportRecord, ...]:
    records: list[ExportRecord] = []
    seen_names = set()
    for module_name in CORE_MODULES_IN_ORDER:
        for function_name, function in _discover_owned_functions(module_name).items():
            if function_name in seen_names:
                continue
            seen_names.add(function_name)
            records.append(
                _function_record(
                    function_name,
                    module_name,
                    function_name,
                    function,
                    chainable=_supports_chain(function),
                )
            )
    return tuple(records)


def _build_aliases() -> tuple[ExportRecord, ...]:
    records = []
    for public_name, module_name, target_name, chainable in CORE_COMPATIBILITY_ALIASES:
        function = _load_owned_function(module_name, target_name)
        records.append(
            _function_record(
                public_name,
                module_name,
                target_name,
                function,
                chainable=chainable,
            )
        )
    return tuple(records)


def _build_lazy_exports() -> tuple[ExportRecord, ...]:
    records = []
    for module_name in LAZY_CHAIN_MODULES:
        for function_name, function in _discover_owned_functions(module_name).items():
            records.append(
                _function_record(
                    function_name,
                    module_name,
                    function_name,
                    function,
                    chainable=_supports_chain(function),
                )
            )
    for module_name in LAZY_STATIC_MODULES:
        for function_name in _discover_source_function_names(
            PROJECT_ROOT / "unicorefw" / f"{module_name}.py"
        ):
            records.append(
                ExportRecord(
                    public_name=function_name,
                    owner_module=module_name,
                    target_name=function_name,
                    signature=_PROXY_SIGNATURE,
                    documentation=(
                        "Lazy compatibility proxy for "
                        f"``unicorefw.{module_name}.{function_name}``."
                    ),
                    chainable=False,
                )
            )
    return tuple(records)


def build_registry() -> RegistryModel:
    """Return the reviewed static and chainable export model."""
    model = RegistryModel(
        core_exports=_build_core_exports(),
        aliases=_build_aliases(),
        lazy_exports=_build_lazy_exports(),
        public_exports_by_module=_build_public_exports(),
    )
    names = model.static_export_names
    if len(names) != len(set(names)):
        raise RegistryGenerationError("generated static export names are not unique")
    return model


def _quote(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_public_exports(model: RegistryModel) -> str:
    """Return the dependency-free package-root export declaration."""
    lines = [
        '"""Generated public export declarations. Do not edit manually."""',
        "",
        "# Generated by scripts/generate_core_registry.py.",
        "PUBLIC_EXPORTS_BY_MODULE = (",
    ]
    for module_name, public_names in model.public_exports_by_module:
        packed_names = " ".join(sorted(public_names))
        lines.extend(["    (", f"        {_quote(module_name)},"])
        names_line = f"        frozenset({_quote(packed_names)}.split()),"
        if len(names_line) <= 88:
            lines.append(names_line)
        else:
            lines.extend(
                [
                    "        frozenset(",
                    f"            {_quote(packed_names)}.split()",
                    "        ),",
                ]
            )
        lines.append("    ),")
    lines.extend(
        [
            ")",
            "",
            "PUBLIC_SUBMODULES = frozenset(",
            f"    {_quote(' '.join(sorted(PUBLIC_SUBMODULES)))}.split()",
            ")",
            "",
            "# Later modules preserve historical wildcard collision order.",
            "ROOT_EXPORTS = {",
            "    _export_name: _module_name",
            "    for _module_name, _module_exports in PUBLIC_EXPORTS_BY_MODULE",
            "    for _export_name in _module_exports",
            "}",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_core_groups(model: RegistryModel) -> list[str]:
    lines = ["CORE_EXPORTS_BY_MODULE = ("]
    for module_name in CORE_MODULES_IN_ORDER:
        records = tuple(
            record
            for record in model.core_exports
            if record.owner_module == module_name
        )
        if not records:
            continue
        function_names = " ".join(record.public_name for record in records)
        static_only_names = " ".join(
            record.public_name for record in records if not record.chainable
        )
        lines.extend(
            [
                "    (",
                f"        {_quote(module_name)},",
                f"        {_quote(function_names)},",
                f"        {_quote(static_only_names)},",
                "    ),",
            ]
        )
    lines.append(")")
    return lines


def _render_aliases(model: RegistryModel) -> list[str]:
    lines = ["COMPATIBILITY_ALIASES = ("]
    lines.extend(
        "    ("
        f"{_quote(record.public_name)}, "
        f"{_quote(record.owner_module)}, "
        f"{_quote(record.target_name)}, "
        f"{record.chainable!r}"
        "),"
        for record in model.aliases
    )
    lines.append(")")
    return lines


def _group_lazy_exports(
    records: tuple[ExportRecord, ...],
    *,
    chainable: bool,
) -> tuple[tuple[str, tuple[str, ...]], ...]:
    names_by_module: dict[str, list[str]] = {}
    for record in records:
        if record.chainable != chainable:
            continue
        names_by_module.setdefault(record.owner_module, []).append(record.public_name)
    return tuple(
        (module_name, tuple(sorted(function_names)))
        for module_name, function_names in names_by_module.items()
    )


def _render_lazy_groups(
    constant_name: str,
    groups: tuple[tuple[str, tuple[str, ...]], ...],
) -> list[str]:
    lines = [f"{constant_name} = ("]
    for module_name, function_names in groups:
        lines.extend(
            [
                "    (",
                f"        {_quote(module_name)},",
                f"        {_quote(' '.join(function_names))},",
                "    ),",
            ]
        )
    lines.append(")")
    return lines


def _render_static_names(model: RegistryModel) -> list[str]:
    packed_names = " ".join(model.static_export_names)
    return [
        "STATIC_EXPORT_NAMES = tuple(",
        f"    {_quote(packed_names)}.split()",
        ")",
    ]


def render_runtime_registry(model: RegistryModel) -> str:
    """Return the dependency-free runtime registry source."""
    sections = [
        [
            '"""Generated core dispatch declarations. Do not edit manually."""',
            "",
            "# Generated by scripts/generate_core_registry.py.",
            f"REGISTRY_SCHEMA_VERSION = {REGISTRY_SCHEMA_VERSION}",
        ],
        _render_core_groups(model),
        _render_aliases(model),
        _render_lazy_groups(
            "LAZY_CHAIN_EXPORTS",
            _group_lazy_exports(model.lazy_exports, chainable=True),
        ),
        _render_lazy_groups(
            "LAZY_STATIC_EXPORTS",
            _group_lazy_exports(model.lazy_exports, chainable=False),
        ),
        _render_static_names(model),
    ]
    return "\n\n".join("\n".join(section) for section in sections) + "\n"


def render_api_metadata(model: RegistryModel) -> str:
    """Return deterministic build-time API metadata as JSON."""
    exports = []
    for record in sorted(
        model.metadata_records,
        key=lambda item: item.public_name,
    ):
        exports.append(
            {
                "chainable": record.chainable,
                "deprecated": record.deprecated,
                "documentation": record.documentation,
                "name": record.public_name,
                "owner_module": record.owner_module,
                "registry_schema_version": REGISTRY_SCHEMA_VERSION,
                "signature": record.signature,
                "target_name": record.target_name,
            }
        )
    return (
        json.dumps(
            {
                "exports": exports,
                "schema_version": REGISTRY_SCHEMA_VERSION,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )


def _write_atomic(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        text=True,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(
            descriptor,
            "w",
            encoding="utf-8",
            newline="\n",
        ) as temporary_file:
            temporary_file.write(content)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.chmod(temporary_path, 0o644)
        os.replace(temporary_path, path)
    finally:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass


def synchronize_generated_files(*, check: bool) -> list[Path]:
    """Check or update fixed generated artifacts and return drifted paths."""
    model = build_registry()
    outputs = (
        (PUBLIC_EXPORTS_PATH, render_public_exports(model)),
        (RUNTIME_REGISTRY_PATH, render_runtime_registry(model)),
        (API_METADATA_PATH, render_api_metadata(model)),
    )
    changed = []
    for path, expected_content in outputs:
        try:
            current_content = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            current_content = None
        if current_content == expected_content:
            continue
        changed.append(path)
        if not check:
            _write_atomic(path, expected_content)
    return changed


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report generated artifact drift without writing files",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        changed = synchronize_generated_files(check=args.check)
    except (OSError, RegistryGenerationError) as exc:
        print(f"core registry generation failed: {exc}", file=sys.stderr)
        return 1
    if args.check and changed:
        for path in changed:
            try:
                display_path = path.relative_to(PROJECT_ROOT)
            except ValueError:
                display_path = path
            print(
                f"generated core registry is stale: {display_path}",
                file=sys.stderr,
            )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
