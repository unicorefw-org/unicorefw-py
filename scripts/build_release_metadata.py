#!/usr/bin/env python3
"""Generate deterministic checksums, a manifest, and a minimal CycloneDX SBOM."""

from __future__ import annotations

import argparse
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, NoReturn

PACKAGE_NAME = "unicorefw"


def fail(message: str) -> NoReturn:
    raise SystemExit(f"release metadata generation failed: {message}")


def sha256_file(file_path: Path) -> str:
    digest = hashlib.sha256()
    with file_path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_artifacts(dist_dir: Path) -> List[Dict[str, Any]]:
    artifact_paths = sorted(
        path
        for path in dist_dir.iterdir()
        if path.is_file() and (path.suffix == ".whl" or path.name.endswith(".tar.gz"))
    )
    wheels = [path for path in artifact_paths if path.suffix == ".whl"]
    source_distributions = [
        path for path in artifact_paths if path.name.endswith(".tar.gz")
    ]
    if len(wheels) != 1 or len(source_distributions) != 1:
        fail("dist must contain exactly one wheel and one .tar.gz source archive")

    return [
        {
            "filename": path.name,
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in artifact_paths
    ]


def write_json(file_path: Path, payload: Dict[str, Any]) -> None:
    with file_path.open("w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")


def write_utf8_text(file_path: Path, content: str) -> None:
    """Write deterministic LF text on every supported Python version."""
    with file_path.open("w", encoding="utf-8", newline="\n") as stream:
        stream.write(content)


def build_metadata(dist_dir: Path, output_dir: Path, version_tag: str) -> None:
    if not version_tag.startswith("v") or len(version_tag) == 1:
        fail("version must be supplied as a v-prefixed release tag")
    version = version_tag[1:]
    artifacts = collect_artifacts(dist_dir)
    output_dir.mkdir(parents=True, exist_ok=False)

    checksum_lines = [
        f"{artifact['sha256']}  {artifact['filename']}" for artifact in artifacts
    ]
    write_utf8_text(
        output_dir / "SHA256SUMS",
        "\n".join(checksum_lines) + "\n",
    )

    manifest = {
        "schema_version": 1,
        "package": PACKAGE_NAME,
        "version": version,
        "artifacts": artifacts,
    }
    write_json(output_dir / "release-manifest.json", manifest)

    component_ref = f"pkg:pypi/{PACKAGE_NAME}@{version}"
    serial_seed = "|".join(
        [component_ref] + [artifact["sha256"] for artifact in artifacts]
    )
    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "serialNumber": f"urn:uuid:{uuid.uuid5(uuid.NAMESPACE_URL, serial_seed)}",
        "version": 1,
        "metadata": {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": {
                "type": "library",
                "bom-ref": component_ref,
                "name": PACKAGE_NAME,
                "version": version,
                "purl": component_ref,
                "licenses": [{"license": {"id": "BSD-3-Clause"}}],
                "properties": [
                    {
                        "name": (
                            "unicorefw:release-artifact:"
                            f"{artifact['filename']}:sha256"
                        ),
                        "value": artifact["sha256"],
                    }
                    for artifact in artifacts
                ],
            },
        },
        "components": [],
        "dependencies": [{"ref": component_ref, "dependsOn": []}],
    }
    write_json(output_dir / "sbom.cdx.json", sbom)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dist-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--version", required=True)
    return parser.parse_args()


def main() -> int:
    arguments = parse_args()
    build_metadata(
        arguments.dist_dir.resolve(),
        arguments.output_dir.resolve(),
        arguments.version,
    )
    print(f"release metadata written to {arguments.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
