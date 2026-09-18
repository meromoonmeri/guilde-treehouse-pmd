"""Construit, vérifie et archive le rendu Zone glaciale / grotte boréale V1."""
from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(__file__).resolve().parent
RENDER = ROOT / "renders" / "zone_glaciale_grotte_boreale_v1"
ARCHIVE = ROOT / "renders" / "zone_glaciale_grotte_boreale_v1_pack.zip"
VIEWER = ROOT / "apercu_zone_glaciale_grotte_boreale_v1.html"


def main() -> int:
    python = sys.executable
    subprocess.run([python, str(SOURCE / "build.py")], check=True)
    subprocess.run([python, str(SOURCE / "verify.py")], check=True)
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(RENDER.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(ROOT).as_posix())
        archive.write(VIEWER, VIEWER.relative_to(ROOT).as_posix())
        for path in sorted(SOURCE.glob("*.py")):
            archive.write(path, path.relative_to(ROOT).as_posix())
        for name in ("README.md", "STATUS.md", "requirements.txt"):
            path = SOURCE / name
            if path.is_file():
                archive.write(path, path.relative_to(ROOT).as_posix())
    print(f"Archive créée : {ARCHIVE.relative_to(ROOT)} ({ARCHIVE.stat().st_size} octets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
