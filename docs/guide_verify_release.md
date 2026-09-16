# `verify_release.py` guide

Source: [`scripts/verify_release.py`](../scripts/verify_release.py)

## Purpose

Use this script to verify that a proposed Git release tag agrees with package
metadata and the changelog before building or publishing artifacts.

The script reads the package version through AST parsing. It does not import
`unicorefw`, so package import side effects or missing optional dependencies
cannot influence release identity verification.

## Requirements

- Run the command from the repository root.
- Pass exactly one `v`-prefixed semantic version tag.
- Set `VERSION` in `unicorefw/_metadata.py` to the exact version without `v`.
- Add a matching `## [VERSION]` release heading to `CHANGELOG.md`.

## Commands

Verify a stable release:

```bash
python3 scripts/verify_release.py v1.4.0
```

Prerelease and build metadata are accepted when all repository values match:

```bash
python3 scripts/verify_release.py v1.4.0-rc.1+build.7
```

## Options

This script has one positional argument and no optional flags:

| Argument | Default | Contract |
|---|---:|---|
| `vMAJOR.MINOR.PATCH` | required | Exact SemVer tag, with optional prerelease and build identifiers. |

Pass exactly one argument. The command does not implement `-h` or `--help`;
those strings are evaluated as candidate tags and fail validation.

## Output and exit status

Exit status `0` means the tag is valid, its version exactly matches the
literal metadata version, and the changelog contains the release heading. The
script prints `release metadata verified for VERSION`.

An invalid tag, argument-count error, missing or nonliteral `VERSION`, version
mismatch, unreadable file, or missing changelog heading returns nonzero.
Policy failures start with `release verification failed:`.

## Safety and operational notes

Verification is read-only. It does not create a tag, modify files, build
artifacts, or contact a package index.

SemVer components reject leading zeroes where SemVer forbids them. The
comparison is exact, including prerelease and build metadata. The changelog
heading is matched at the start of a line and must use square brackets.

Run this gate before metadata generation and publication. It proves repository
version consistency, not wheel integrity; use `scripts/verify_wheel.py` for the
built wheel.

## Troubleshooting

For a version mismatch, compare the tag without its leading `v` to the literal
`VERSION` value in `unicorefw/_metadata.py`. Do not derive either value from an
imported package because that package may be an older installation.

For a changelog failure, add the exact heading, for example:

```markdown
## [1.4.0]
```

If a tag with prerelease or build identifiers fails, validate each identifier
against SemVer and confirm the entire string appears in both metadata and the
changelog heading.
