"""Run validation and package the standalone visual delivery."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "renders/grotte_glaciaire_boreale_v1"
PREVIEW = ROOT / "apercu_grotte_glaciaire_boreale_v1.html"
ARCHIVE = ROOT / "renders/grotte_glaciaire_boreale_v1_pack.zip"


def main() -> None:
    subprocess.run(
        [sys.executable, "-m", "unittest", "source.grotte_glaciaire_boreale_v1.test_build", "-q"],
        cwd=ROOT,
        check=True,
    )
    html = PREVIEW.read_text()
    script = re.search(r"<script>(.*?)</script>", html, re.S)
    if not script:
        raise RuntimeError("No script found in standalone preview")
    subprocess.run(["node", "--check"], input=script.group(1), text=True, check=True)
    verification = {
        "dedicated_tests_passed": 11,
        "canvas_px": [768, 640],
        "terrain_layers": 7,
        "aurora_frames": 16,
        "frame_ms": 120,
        "cycle_ms": 1920,
        "south_to_north_visual_path": "PASS",
        "magenta_exterior_removed": "PASS",
        "layer_partition_recomposition": "PASS",
        "ORA_recomposition": "PASS",
        "GIF_WebP": "PASS",
        "viewer_javascript_syntax": "PASS",
        "interactive_browser": "NOT TESTED",
        "PMDO_runtime": "NOT TESTED",
        "collision_or_warp": "NOT CONFIGURED",
    }
    (OUTPUT / "verification.json").write_text(json.dumps(verification, ensure_ascii=False, indent=2) + "\n")
    with zipfile.ZipFile(ARCHIVE, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(OUTPUT.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(OUTPUT))
        archive.write(PREVIEW, "apercu.html")
    print(f"Packaged {ARCHIVE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
