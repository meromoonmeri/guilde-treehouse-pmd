"""Tests d'intégration légers pour le build Zone glaciale / grotte boréale V1."""
from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "renders" / "zone_glaciale_grotte_boreale_v1"


class ZoneGlacialeBuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run([sys.executable, str(HERE / "build.py")], check=True)
        subprocess.run([sys.executable, str(HERE / "verify.py")], check=True)
        cls.report = json.loads((OUT / "verification.json").read_text(encoding="utf-8"))

    def test_verification_passes(self) -> None:
        self.assertEqual(self.report["status"], "PASS")
        self.assertTrue(all(item["pass"] for item in self.report["checks"]))

    def test_canvas_and_animation_contract(self) -> None:
        self.assertEqual(self.report["canvas_px"], [1264, 1008])
        self.assertEqual(self.report["grid_px"], 8)
        self.assertEqual(self.report["animation"], {"frames": 16, "frame_ms": 100, "duration_s": 1.6})

    def test_deliverable_files_exist(self) -> None:
        for relative in (
            "COMPOSITION.png",
            "zone_glaciale_grotte_boreale_v1.ora",
            "animation/aurore_indexee.png",
            "animation/aurore_alpha.png",
            "animation/aurore_16frames.webp",
            "review/animation_complete.gif",
            "masques/09_corridor_geometrique_sud_nord.png",
        ):
            self.assertTrue((OUT / relative).is_file(), relative)


if __name__ == "__main__":
    unittest.main()
