# `generate_core_registry.py` guide

Source: [`scripts/generate_core_registry.py`](../scripts/generate_core_registry.py)

## Purpose

Use this script to discover public functions and generate the static export
and dispatch metadata used by UniCoreFW. A function defined by a managed module
is public when its name does not start with `_`, subject to the ownership and
module policies in `unicorefw/_export_policy.py`.

Generation keeps runtime dispatch free of reflection while avoiding a manual
export entry for each ordinary public function.

## Requirements

- Run the command from the repository root with the project's supported Python
  environment.
- Ensure dependencies required to import trusted implementation modules are
  available.
- Review public-name collisions and compatibility aliases in
  `unicorefw/_export_policy.py`.
- Do not edit generated artifacts by hand.

## Commands

Regenerate all artifacts after adding, renaming, or removing a public
function:

```bash
python3 scripts/generate_core_registry.py
```

Check for drift without modifying files:

```bash
python3 scripts/generate_core_registry.py --check
```

The wheel and source-distribution build hook runs generation automatically,
but `--check` remains useful in local validation and CI.

## Options

| Option | Default | Contract |
|---|---:|---|
| `--check` | off | Compare generated content with tracked artifacts and return nonzero on drift without writing. |
| `-h`, `--help` | n/a | Print command help and exit. |

The output paths are fixed:

- `unicorefw/_exports.py`;
- `unicorefw/_core_registry.py`;
- `docs/api/core-exports.json`.

## Output and exit status

Normal mode writes changed artifacts and is quiet on success. Check mode is
also quiet when every artifact is current. It prints each stale path to
standard error when drift exists.

Exit status `0` means generation succeeded or check mode found no drift. Check
mode returns `1` for stale or missing artifacts. Discovery errors, unsafe
definitions, unapproved public-name collisions, import failures, and write
errors return nonzero.

## Safety and operational notes

Trusted implementation modules are imported at generation time so function
ownership, signatures, and documentation can be inspected. Source-discovery
modules such as database and ORM code use AST analysis to avoid importing
optional or stateful backends. Decorated public definitions in those modules
are rejected because static analysis cannot prove the final binding safely.

Generation is deterministic for a fixed source tree and interpreter. Each
changed file is written to a temporary file, flushed, set to mode `0644`, and
atomically replaced. A failure between files can still leave a mixed artifact
set, so rerun generation after resolving the error.

Only module-owned functions become automatic exports. Imported functions,
classes, callable instances, and names beginning with `_` are excluded.
Approved collisions and explicit compatibility behavior stay centralized in
`unicorefw/_export_policy.py`.

## Troubleshooting

For drift, run normal generation and inspect the diff. Do not copy generated
records manually.

If a new function is absent, confirm that it is defined in a managed module,
does not start with `_`, and has that module as its `__module__`. Then inspect
the applicable discovery policy.

If generation reports a collision, either rename the new API or add a reviewed
ownership decision to the collision policy. Do not let import order decide
which implementation wins.

If a source-discovered function is decorated, move behavior into an undecorated
public definition or define an explicit safe policy. The generator fails
closed instead of guessing the decorated binding.
