# `build_release_metadata.py` guide

Source: [`scripts/build_release_metadata.py`](../scripts/build_release_metadata.py)

## Purpose

Use this script to generate integrity and inventory metadata for one release
wheel and one source archive. It creates SHA-256 checksums, a release manifest,
and a minimal CycloneDX software bill of materials.

Run release and wheel verification before generating this metadata. This
script hashes the supplied artifacts but does not validate their contents or
confirm that the version tag matches package metadata.

## Requirements

- Run the command from the repository root.
- Provide a distribution directory containing exactly one `.whl` and one
  `.tar.gz` file. Other file types are ignored.
- Provide an output path that does not exist.
- Supply the version as a `v`-prefixed release tag, such as `v1.4.0`.

## Commands

Verify the release, then generate metadata into a new directory:

```bash
python3 scripts/verify_release.py v1.4.0
python3 scripts/build_release_metadata.py \
  --dist-dir dist \
  --output-dir build/release-metadata-v1.4.0 \
  --version v1.4.0
```

Verify the generated checksums from the artifact directory:

```bash
cd dist
sha256sum --check ../build/release-metadata-v1.4.0/SHA256SUMS
```

## Options

| Option | Default | Contract |
|---|---:|---|
| `--dist-dir PATH` | required | Directory containing exactly one wheel and one `.tar.gz` source archive. |
| `--output-dir PATH` | required | New directory for generated files. Its parents are created, but the directory itself must not exist. |
| `--version TAG` | required | Nonempty `v`-prefixed tag. The leading `v` is removed from metadata versions. |
| `-h`, `--help` | n/a | Print command help and exit. |

## Output and exit status

The output directory contains:

| File | Contents |
|---|---|
| `SHA256SUMS` | GNU-compatible SHA-256 lines for both artifacts. |
| `release-manifest.json` | Schema version 1 manifest with package, version, filename, size, and SHA-256 fields. |
| `sbom.cdx.json` | CycloneDX 1.5 SBOM for the release component and artifact hashes. |

Exit status `0` means all three files were written and the command prints the
output path. Invalid input, an existing output directory, unreadable
artifacts, or a write failure returns a nonzero status. Validation failures
start with `release metadata generation failed:`.

## Safety and operational notes

Artifacts are hashed in 1 MiB chunks, so memory use does not scale with
artifact size. Artifact order and JSON key order are deterministic. The SBOM
serial number is derived from the package URL and artifact hashes; its UTC
timestamp records generation time.

The command refuses to reuse an output directory, preventing stale files from
being mixed into a release. The three files are not published as one atomic
transaction. Generate them in a new staging directory, validate them, then
move or upload the complete set.

The version parser only enforces a leading `v`. Use
`scripts/verify_release.py` first to enforce the repository's SemVer,
metadata, and changelog contract.

## Troubleshooting

If artifact collection fails, remove old wheels and source archives from the
distribution directory or point `--dist-dir` at a clean staging directory.

If the output directory exists after an interrupted attempt, inspect it and
choose a new empty path. Do not merge partial metadata into a release.

If checksum verification cannot find artifacts, run it from the distribution
directory because `SHA256SUMS` contains artifact filenames without directory
prefixes.
