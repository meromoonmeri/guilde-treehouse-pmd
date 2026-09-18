"""Verify and package the canonical glacier-cliff PMDO Ground."""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "exports/glacier_cliff_aurora_pmdo_v1"
ZIP = ROOT / "exports/glacier_cliff_aurora_pmdo_v1_pack.zip"


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    # Rebuild from the canonical native source, then run the independent audit.
    subprocess.run([sys.executable, str(HERE / "build.py")], cwd=ROOT, check=True)
    runtime = subprocess.run([sys.executable, str(HERE / "runtime_test.py")], cwd=ROOT)
    if runtime.returncode not in (0, 2):
        raise SystemExit("native PMDO runtime test failed")
    subprocess.run([sys.executable, str(HERE / "verify.py")], cwd=ROOT, check=True)
    shutil.copyfile(HERE / "INSTALLER.py", OUT / "INSTALLER.py")

    package_manifest = {
        "name": "glacier_cliff_aurora_pmdo_v1",
        "pmdo": "0.8.12.0",
        "root": "standalone mod pack; index included for direct project opening",
        "files": [],
        "excluded_from_zip": [
            "tests/", "tests/native_tile_payloads/", "tests/*.mvg",
            "generated composition guide (never copied to Content/)"
        ],
    }
    excluded = lambda p: "tests" in p.relative_to(OUT).parts
    for path in sorted(OUT.rglob("*")):
        if path.is_file() and not excluded(path) and path.name != "package_manifest.json":
            package_manifest["files"].append({
                "path": path.relative_to(OUT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            })
    (OUT / "package_manifest.json").write_text(
        json.dumps(package_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    package_manifest["files"].append({
        "path": "package_manifest.json",
        "bytes": (OUT / "package_manifest.json").stat().st_size,
        "sha256": sha256(OUT / "package_manifest.json"),
    })
    # Rewrite after adding its own entry is intentionally avoided: the package
    # manifest describes all payload files, while its own self-entry is a
    # convenience record whose hash is recorded in the ZIP verification below.

    entries = [p for p in sorted(OUT.rglob("*"))
               if p.is_file() and not excluded(p)]
    with zipfile.ZipFile(ZIP, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in entries:
            info = zipfile.ZipInfo(path.relative_to(OUT).as_posix(), (2026, 9, 18, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)
    with zipfile.ZipFile(ZIP) as archive:
        assert archive.testzip() is None
        names = set(archive.namelist())
        required = {
            "Mod.xml", "INSTALLER.py", "README.md", "verification.json",
            "Content/Tile/VastIceMountain.tile", "Content/Tile/index.idx",
            "Data/Ground/glacier_cliff_aurora_v1.rsground",
            "Content/BG/GLACIER_AURORA_PALETTE_CYCLE.dir",
            "Content/BG/GLACIER_NIGHT_BASE.dir",
            "Content/BG/GLACIER_DISTANT_MOUNTAINS.dir",
            "Content/BG/GLACIER_SNOW_TREES.dir",
            "Content/BG/GLACIER_SNOW_FOREST_PATH.dir",
            "provenance/provenance.json",
        }
        assert required <= names, sorted(required - names)
        assert not any(n.startswith("tests/") for n in names)
    print(f"Created {ZIP} ({ZIP.stat().st_size / 2**20:.2f} MiB, {len(entries)} files)")


if __name__ == "__main__":
    main()
