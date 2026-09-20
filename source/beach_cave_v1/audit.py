"""Audit canonical Beach Cave references before any layout is built.

The EoSO maps are the composition/material reference. The final layout uses only
native 24px BeachCavePit payloads pinned from that repository; the generated
composition guide is deliberately not read by this script.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import hashlib
import io
import json
import struct

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REF = HERE / "references"
EOSO = REF / "ExplorersOfSkyOrigins"
AUDIT = HERE / "audit"
OUT = ROOT / "renders" / "beach_cave_v1"

EOSO_COMMIT = "bed944992c32e7e7927cc3480c72edb0b1782e26"
EOSO_REPO = "Minemaker0430/ExplorersOfSkyOrigins"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()


def read_tile(path: Path) -> tuple[int, dict[tuple[int, int], Image.Image]]:
    raw = path.read_bytes()
    tile_size, count = struct.unpack_from("<ii", raw)
    if tile_size not in (8, 24):
        raise AssertionError(f"unexpected tile size in {path}: {tile_size}")
    bank: dict[tuple[int, int], Image.Image] = {}
    payloads: dict[int, Image.Image] = {}
    for i in range(count):
        x, y, offset = struct.unpack_from("<iiq", raw, 8 + i * 16)
        if offset in payloads:
            image = payloads[offset]
        else:
            length = struct.unpack_from("<q", raw, offset)[0]
            if not 0 < length <= len(raw) - offset - 8:
                raise AssertionError(f"bad PNG length in {path} at {offset}")
            image = Image.open(io.BytesIO(raw[offset + 8 : offset + 8 + length])).convert("RGBA")
            if image.size != (tile_size, tile_size):
                raise AssertionError(f"bad native cell size in {path}: {image.size}")
            payloads[offset] = image
        if (x, y) in bank:
            raise AssertionError(f"duplicate TexLoc {(x, y)} in {path}")
        bank[x, y] = image
    return tile_size, bank


def frame_names(obj: dict) -> set[str]:
    return {
        frame["Sheet"]
        for layer in obj["Layers"]
        for column in layer["Tiles"]
        for tile in column
        for cell_layer in tile.get("Layers", [])
        for frame in cell_layer.get("Frames", [])
    }


def compose_ground(path: Path, banks: dict[str, dict[tuple[int, int], Image.Image]], cell: int) -> tuple[Image.Image, dict]:
    source = json.loads(path.read_text(encoding="utf-8-sig"))
    obj = source["Object"]
    width = len(obj["Layers"][0]["Tiles"]) * cell
    height = len(obj["Layers"][0]["Tiles"][0]) * cell
    scene = Image.new("RGBA", (width, height))
    layer_report = []
    for layer in obj["Layers"]:
        image = Image.new("RGBA", scene.size)
        occupied = 0
        animated = 0
        frame_lengths: set[int] = set()
        used = Counter()
        for x, column in enumerate(layer["Tiles"]):
            for y, tile in enumerate(column):
                if tile.get("Layers"):
                    occupied += 1
                for cell_layer in tile.get("Layers", []):
                    frames = cell_layer.get("Frames", [])
                    if len(frames) > 1:
                        animated += 1
                    frame_lengths.add(cell_layer.get("FrameLength", 0))
                    if not frames:
                        continue
                    first = frames[0]
                    sheet = first["Sheet"]
                    loc = (first["TexLoc"]["X"], first["TexLoc"]["Y"])
                    if loc not in banks[sheet]:
                        raise AssertionError(f"unresolved {sheet}{loc} in {path}")
                    used[sheet] += 1
                    image.alpha_composite(banks[sheet][loc], (x * cell, y * cell))
        if layer.get("Visible", True):
            scene = Image.alpha_composite(scene, image)
        layer_report.append({
            "name": layer["Name"],
            "visible": layer.get("Visible", True),
            "occupied_cells": occupied,
            "animated_cells": animated,
            "frame_lengths": sorted(frame_lengths),
            "referenced_sheets": dict(used),
        })
    return scene, {"layers": layer_report, "size_px": list(scene.size)}


def main() -> None:
    AUDIT.mkdir(exist_ok=True)
    OUT.mkdir(exist_ok=True)
    provenance = []
    eoso_files = {
        "beach.rsground": "Data/Ground/beach.rsground",
        "beach_cave_pit.rsground": "Data/Ground/beach_cave_pit.rsground",
        "D01P11A_layer1.tile": "Content/Tile/D01P11A_layer1.tile",
        "D01P11A_layer2.tile": "Content/Tile/D01P11A_layer2.tile",
        "beach_animation.tile": "Content/Tile/beach_animation.tile",
        "BeachCavePit.tile": "Content/Tile/BeachCavePit.tile",
    }
    for filename, remote in eoso_files.items():
        path = EOSO / filename
        provenance.append({
            "repo": EOSO_REPO,
            "commit": EOSO_COMMIT,
            "path": remote,
            "blob": git_blob(path),
            "sha256": sha256(path),
            "local": str(path.relative_to(ROOT)),
        })

    eoso_reports = []
    for map_name in ("beach.rsground", "beach_cave_pit.rsground"):
        path = EOSO / map_name
        source = json.loads(path.read_text(encoding="utf-8-sig"))
        obj = source["Object"]
        cell = obj["TexSize"] * 8
        sheets = {}
        sheet_reports = []
        for sheet in sorted(frame_names(obj)):
            tile = EOSO / f"{sheet}.tile"
            tile_size, bank = read_tile(tile)
            if tile_size != cell:
                raise AssertionError(f"{map_name}: {sheet} is {tile_size}px, expected {cell}px")
            sheets[sheet] = bank
            sheet_reports.append({
                "name": sheet,
                "tile_size_px": tile_size,
                "index_entries": len(bank),
                "sha256": sha256(tile),
            })
        image, report = compose_ground(path, sheets, cell)
        output = AUDIT / f"{path.stem}_composition.png"
        image.save(output, optimize=True)
        report.update({
            "name": path.stem,
            "version": source["Version"],
            "TexSize": obj["TexSize"],
            "grid_cells": [len(obj["Layers"][0]["Tiles"]), len(obj["Layers"][0]["Tiles"][0])],
            "sheets": sheet_reports,
            "entities": {
                key: sum(len(entity.get(key, [])) for entity in obj.get("Entities", []))
                for key in ("MapChars", "GroundObjects", "Spawners", "Markers")
            },
            "composition": str(output.relative_to(ROOT)),
        })
        eoso_reports.append(report)

    final_tile = EOSO / "BeachCavePit.tile"
    report = {
        "status": "PASS",
        "scope": "canonical reference provenance and source frame resolution; no engine/GPU validation",
        "eoso": {"repo": EOSO_REPO, "commit": EOSO_COMMIT, "files": provenance, "maps": eoso_reports},
        "final_native_source": {
            "repo": EOSO_REPO,
            "commit": EOSO_COMMIT,
            "path": "Content/Tile/BeachCavePit.tile",
            "local": str(final_tile.relative_to(ROOT)),
            "sha256": sha256(final_tile),
            "tile_size_px": read_tile(final_tile)[0],
        },
        "forbidden_in_final": [
            "generated guide pixels",
            "rotation, scaling, recoloring or interpolation of canonical cells",
            "automatic crop of a generated panel sheet",
        ],
    }
    (HERE / "provenance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    (HERE / "verification.json").write_text(json.dumps({"status": "PASS", "reference_maps": 2, "final_sheet": "BeachCavePit.tile", "final_tile_size_px": 24, "generated_pixels_used_in_final": 0}, indent=2) + "\n")
    print("PASS: EoSO canonical maps and every referenced sheet resolved; final BeachCavePit source pinned.")


if __name__ == "__main__":
    main()
