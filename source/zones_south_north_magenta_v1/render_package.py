#!/usr/bin/env python3
"""Validate and package the generated-final-render forest deliverable."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exports/forest_cave_render_v1_pmdo"
ARCHIVE = ROOT / "exports/forest_cave_render_v1_pmdo_pack.zip"
PREVIEW = ROOT / "apercu_forest_cave_render_v1.html"
PACKAGE_MANIFEST = OUT / "package_manifest.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def package_files() -> list[Path]:
    # The sidecar package manifest records the archive hash and therefore is
    # deliberately kept outside the archive to avoid a self-referential hash.
    return sorted(p for p in OUT.rglob("*") if p.is_file() and p != PACKAGE_MANIFEST)


def write_archive(files: list[Path]) -> None:
    with zipfile.ZipFile(ARCHIVE, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            archive.write(path, path.relative_to(OUT).as_posix())
        archive.write(PREVIEW, "apercu_forest_cave_render_v1.html")


def main() -> None:
    if not OUT.is_dir():
        raise SystemExit("Build the generated render first: render_build.py")
    subprocess.run([sys.executable, str(Path(__file__).with_name("render_verify.py"))], cwd=ROOT, check=True)
    verification = json.loads((OUT / "verification.json").read_text(encoding="utf-8"))
    if verification.get("result") != "PASS":
        raise SystemExit("render verification did not pass")
    if not PREVIEW.is_file():
        raise SystemExit("Preview is missing: apercu_forest_cave_render_v1.html")

    files = package_files()
    write_archive(files)
    package_manifest = {
        "archive": ARCHIVE.name,
        "archive_sha256": sha256(ARCHIVE),
        "root": OUT.name,
        "preview": PREVIEW.name,
        "file_count": len(files) + 1,
        "generated_final_render": True,
        "canonical_pixels_replace_generated_render": False,
        "verification": verification,
    }
    PACKAGE_MANIFEST.write_text(json.dumps(package_manifest, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "result": "PASS",
        "archive": str(ARCHIVE),
        "archive_sha256": package_manifest["archive_sha256"],
        "files": len(files) + 1,
        "preview": str(PREVIEW),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
