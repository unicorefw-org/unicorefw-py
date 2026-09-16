# `verify_wheel.py` guide

Source: [`scripts/verify_wheel.py`](../scripts/verify_wheel.py)

## Purpose

Use this script to inspect and smoke-test one wheel before release. It rejects
unsafe or incomplete archive layouts, installs the wheel into a temporary
virtual environment, imports it away from the checkout, and checks installed
dependency consistency.

## Requirements

- Run the command with Python's `venv` and bundled `pip` support available.
- Pass exactly one existing file whose name ends in `.whl`.
- Provide enough temporary disk space for a virtual environment and wheel
  installation.
- Build the wheel before running the command.

The wheel is installed with `--no-deps`, so its declared runtime dependencies
must not be needed by the smoke-tested root API.

## Commands

Verify a built wheel:

```bash
python3 scripts/verify_wheel.py dist/unicorefw-1.4.0-py3-none-any.whl
```

For a clean release directory, select the wheel explicitly in automation
rather than passing an unresolved glob.

## Options

This script has one positional argument and no optional flags:

| Argument | Default | Contract |
|---|---:|---|
| `path/to/package.whl` | required | Existing wheel file to inspect, install, and smoke-test. |

Pass exactly one argument. The command does not implement `-h` or `--help`;
those strings are treated as wheel paths and fail validation.

## Output and exit status

Exit status `0` means the archive structure passed, installation succeeded,
`unicorefw` imported from the isolated environment, the package exposed a
version, `uniq([1, 1, 2])` returned `[1, 2]`, and `pip check` passed. The script
prints the verified wheel filename.

An invalid path, unsafe archive, missing required member, installation error,
smoke-test error, or dependency inconsistency returns nonzero. Structural
failures start with `wheel verification failed:`. Subprocess failures include
the failing command through Python's standard subprocess diagnostics.

## Safety and operational notes

Before installation, the archive inspection rejects:

- duplicate member names;
- absolute paths, parent traversal, and NUL-containing names;
- `.pyc`, `.pyo`, and `__pycache__` content;
- a top-level `scripts` directory;
- missing `unicorefw/__init__.py`;
- missing `.dist-info/METADATA`, `RECORD`, or `WHEEL` files.

The temporary virtual environment is created under a unique temporary
directory and removed when verification ends. Installation uses isolated
Python mode, disables pip's version check, installs only the local wheel, and
does not resolve dependencies. The import and `pip check` also use isolated
mode and run outside the source checkout.

This is a release smoke test, not a malware sandbox or complete wheel-record
signature verifier. Only verify artifacts produced by the trusted build
pipeline.

## Troubleshooting

If virtual-environment creation fails, install the interpreter's `venv` or
`ensurepip` component. If installation reports a platform mismatch, build or
select a wheel compatible with the verification interpreter and platform.

If `pip check` reports a missing dependency, inspect wheel metadata. Keep the
dependency when it is required, and run verification in a policy-approved
environment that can satisfy the complete smoke-test contract.

If repository tooling appears inside the wheel, review package discovery and
the build manifest. Do not weaken the verifier to permit release scripts in
the runtime artifact.
