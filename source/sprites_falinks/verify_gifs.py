"""Validate Falinks GIF previews and their timing archive."""
from __future__ import annotations

import json
import zipfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "gifs" / "0870" / "0002"
ARCHIVE = ROOT / "gifs-0870-0002.zip"
ALIAS = ROOT / "gifs-0870.zip"


def fail(message: str) -> None:
    raise SystemExit("FAIL: " + message)


def main() -> None:
    timing_path = OUT / "timing.json"
    if not timing_path.is_file():
        fail("missing gifs/0870/0002/timing.json")
    timing = json.loads(timing_path.read_text(encoding="utf-8"))
    records = timing.get("animations")
    if not isinstance(records, list) or len(records) != 35:
        fail("timing.json must describe exactly 35 animations")
    if timing.get("direction") != 0 or timing.get("game_ticks_per_second") != 60:
        fail("GIF metadata must identify direction 0 and the PMD 60 Hz clock")

    expected_files = {"README.md", "timing.json"}
    for record in records:
        name = record.get("name")
        filename = record.get("file")
        if not isinstance(name, str) or filename != f"{name}.gif":
            fail(f"invalid GIF record for {name!r}")
        path = OUT / filename
        if not path.is_file():
            fail(f"missing {path.relative_to(ROOT)}")
        expected_files.add(filename)
        with Image.open(path) as gif:
            if gif.mode != "P":
                fail(f"{filename}: expected indexed GIF")
            durations = []
            for frame_index in range(gif.n_frames):
                gif.seek(frame_index)
                durations.append(int(gif.info.get("duration", 0)))
            if gif.info.get("loop") != 0:
                fail(f"{filename}: expected infinite loop")
            if gif.size != tuple(record["frame_size"]):
                fail(f"{filename}: frame size differs from timing.json")
            if gif.n_frames != record["frames"]:
                fail(f"{filename}: frame count differs from timing.json")
            if durations != record["duration_gif_ms"]:
                fail(f"{filename}: frame durations differ from timing.json")
            if sum(durations) != record["loop_gif_ms"]:
                fail(f"{filename}: loop duration is inconsistent")

    actual_files = {path.name for path in OUT.iterdir() if path.is_file()}
    if actual_files != expected_files:
        fail("unexpected or missing GIF files: " + ", ".join(sorted(actual_files ^ expected_files)))
    if not ARCHIVE.is_file() or not ALIAS.is_file():
        fail("missing GIF archive or compatibility alias")
    with zipfile.ZipFile(ARCHIVE) as archive:
        if set(archive.namelist()) != expected_files:
            fail("gifs-0870-0002.zip does not match the GIF folder")
    if ARCHIVE.read_bytes() != ALIAS.read_bytes():
        fail("gifs-0870.zip is not byte-for-byte identical to the variant archive")

    print("PASS: 35 direction-0 GIF previews have indexed palettes and valid loops")
    print("PASS: GIF durations match timing.json and PMD 60 Hz metadata")
    print("PASS: gifs-0870-0002.zip and gifs-0870.zip match the preview folder")


if __name__ == "__main__":
    main()
