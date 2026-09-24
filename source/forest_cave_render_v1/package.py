#!/usr/bin/env python3
"""Build, verify and package the one generated forest map."""
from __future__ import annotations

import argparse
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "exports/forest_cave_render_v1_pmdo"
DEFAULT_ZIP = ROOT / "exports/forest_cave_render_v1_pmdo_pack.zip"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_ZIP)
    args = parser.parse_args()
    subprocess.run([sys.executable, str(Path(__file__).with_name("build.py"))], cwd=ROOT, check=True)
    subprocess.run([sys.executable, str(Path(__file__).with_name("verify.py"))], cwd=ROOT, check=True)
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in PROJECT.rglob("*") if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc")
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in files:
            info = zipfile.ZipInfo(path.relative_to(PROJECT).as_posix(), (2026, 9, 24, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes(), compresslevel=9)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert len([name for name in archive.namelist() if name.endswith(".rsground")]) == 1
        assert "Content/Tile/index.idx" in archive.namelist()
    print(f"Archive generated render valide : {output} ({output.stat().st_size / 2**20:.2f} MiB)")


if __name__ == "__main__":
    main()
