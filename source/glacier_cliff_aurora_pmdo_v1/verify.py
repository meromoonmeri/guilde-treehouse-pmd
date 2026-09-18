"""Independent structural/provenance/collision checks for the glacier Ground.

This verifier does not claim to be the PMDO executable.  It validates the
serialized schema, native tile references, backgrounds, collision geometry,
marker reachability, provenance hashes, and installer conflict safety.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import struct
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "exports/glacier_cliff_aurora_pmdo_v1"
ASSET = "glacier_cliff_aurora_v1"
MAP_PATH = OUT / "Data/Ground" / f"{ASSET}.rsground"
TILE_PATH = OUT / "Content/Tile/VastIceMountain.tile"
SOURCE_TILE = ROOT / "source/donjons_dtef_v2/references/DumpAsset/Content/Tile/VastIceMountain.tile"


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def png_size(data: bytes):
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert data[12:16] == b"IHDR"
    return struct.unpack(">II", data[16:24])


def tile_node(path: Path):
    data = path.read_bytes()
    tile_size, count = struct.unpack_from("<ii", data)
    assert tile_size == 24 and count > 0
    coords = {}
    payloads = {}
    for i in range(count):
        x, y, address = struct.unpack_from("<iiq", data, 8 + i * 16)
        assert (x, y) not in coords
        assert 0 <= address < len(data)
        length = struct.unpack_from("<q", data, address)[0]
        raw = data[address + 8:address + 8 + length]
        assert png_size(raw) == (24, 24)
        coords[(x, y)] = raw
        payloads[address] = raw
    return data, coords, payloads


def dir_payload(path: Path):
    data = path.read_bytes()
    n = struct.unpack_from("<q", data, 0)[0]
    png = data[8:8 + n]
    width, height, directions, frames = struct.unpack_from("<4i", data, 8 + n)
    assert len(data) == 8 + n + 16
    assert directions == 0 and frames > 0
    assert png_size(png) == (width * frames, height)
    return png, (width, height), (directions, frames)


def layer_cells(layer):
    cells = set()
    for x, column in enumerate(layer["Tiles"]):
        for y, tile in enumerate(column):
            if tile["Layers"]:
                cells.add((x, y))
    return cells


def walkable_path(floor, start, goal):
    todo = [start]
    seen = {start}
    while todo:
        x, y = todo.pop(0)
        if (x, y) == goal:
            return True
        for p in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if p in floor and p not in seen:
                seen.add(p)
                todo.append(p)
    return False


def check_installer():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import INSTALLER

    with tempfile.TemporaryDirectory(prefix="glacier_install_") as temp:
        target = Path(temp)
        (target / "Mod.xml").write_text(
            "<Header><Namespace>existing_mod</Namespace></Header>", encoding="utf-8"
        )
        tile_dir = target / "Content/Tile"
        tile_dir.mkdir(parents=True)
        existing_tile = tile_dir / "EXISTING.tile"
        shutil.copyfile(TILE_PATH, existing_tile)
        _, node, _ = tile_node(existing_tile)
        # Reuse the binary node header/entries through the installer reader.
        with existing_tile.open("rb") as f:
            existing_node = INSTALLER.read_node(f)
        (tile_dir / "index.idx").write_bytes(INSTALLER.encode_index({"EXISTING": existing_node}))

        INSTALLER.install(OUT, target, dry_run=True)
        assert not (target / "Data/Ground").exists()
        INSTALLER.install(OUT, target)
        idx = INSTALLER.read_index(tile_dir / "index.idx")
        assert set(idx) == {"EXISTING", "VastIceMountain"}
        assert (target / "Data/Script/existing_mod/ground" / ASSET / "init.lua").is_file()
        first = (target / "Data/Ground" / f"{ASSET}.rsground")
        before = first.read_bytes()
        INSTALLER.install(OUT, target)
        assert first.read_bytes() == before
        first.write_text("user edited", encoding="utf-8")
        try:
            INSTALLER.install(OUT, target)
        except ValueError:
            pass
        else:
            raise AssertionError("installer overwrote an edited Ground")
        assert first.read_text(encoding="utf-8") == "user edited"


def main():
    assert MAP_PATH.is_file()
    doc = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    obj = doc["Object"]
    assert doc["Version"] == "0.8.12.0"
    assert obj["$type"] == "RogueEssence.Ground.GroundMap, RogueEssence"
    assert obj["TexSize"] == 3 and obj["AssetName"] == ASSET
    assert len(obj["Layers"]) == 5
    assert all(len(layer["Tiles"]) == 72 for layer in obj["Layers"])
    assert all(len(column) == 54 for layer in obj["Layers"] for column in layer["Tiles"])
    assert len(obj["obstacles"]) == 72 and all(len(c) == 54 for c in obj["obstacles"])
    bg_layers = obj["Background"]["Layers"]
    bg_names = [entry["BG"]["BGAnim"]["AnimIndex"] for entry in bg_layers]
    assert bg_names == [
        "GLACIER_NIGHT_BASE", "GLACIER_AURORA_PALETTE_CYCLE",
        "GLACIER_DISTANT_MOUNTAINS", "GLACIER_SNOW_TREES",
        "GLACIER_SNOW_FOREST_PATH",
    ]
    assert bg_layers[0]["BG"]["BGAnim"]["StartFrame"] == -1
    aurora_anim = bg_layers[1]["BG"]["BGAnim"]
    assert aurora_anim["FrameTime"] == 6
    assert aurora_anim["StartFrame"] == 0 and aurora_anim["EndFrame"] == 5
    assert aurora_anim["AnimDir"] == 1

    source_bytes, native, payloads = tile_node(SOURCE_TILE)
    delivered_bytes, delivered, delivered_payloads = tile_node(TILE_PATH)
    assert source_bytes == delivered_bytes
    assert sha256(TILE_PATH) == sha256(SOURCE_TILE)
    assert len(native) == 158 and len(payloads) == 135

    floor = layer_cells(obj["Layers"][0])
    wall = layer_cells(obj["Layers"][1]) | layer_cells(obj["Layers"][4])
    secondary = layer_cells(obj["Layers"][2])
    assert len(floor) == 1328 and len(wall) == 288 and len(secondary) == 196
    assert floor.isdisjoint(wall)
    assert floor.isdisjoint(secondary)
    assert layer_cells(obj["Layers"][3]) == set()

    # Every map reference resolves directly in the canonical native tile bank.
    references = 0
    for layer in obj["Layers"]:
        for column in layer["Tiles"]:
            for tile in column:
                assert tile["AutoTileset"] == "" and tile["Associates"] == []
                assert len(tile["Layers"]) <= 1
                for anim in tile["Layers"]:
                    assert anim["FrameLength"] > 0
                    for frame in anim["Frames"]:
                        assert frame["Sheet"] == "VastIceMountain"
                        loc = (frame["TexLoc"]["X"], frame["TexLoc"]["Y"])
                        assert loc in native
                        references += 1
    assert references > 1500

    # The collision grid is 8 px even though the native texture stamps are
    # 24 px (TexSize=3), as in PMDO's TexSize=3 Ground examples.
    for x, column in enumerate(obj["obstacles"]):
        for y, cell in enumerate(column):
            assert cell["Bounds"] == {"X": x * 8, "Y": y * 8, "Width": 8, "Height": 8}
            assert cell["Tags"] == (0 if (x, y) in floor else 1)
    assert all(obj["obstacles"][x][y]["Tags"] == 1 for x, y in wall)
    assert walkable_path(floor, (35, 46), (35, 15))
    assert all((x, y) in floor for x, y in ((35, 46), (35, 48), (35, 15)))

    markers = {m["EntName"]: m for m in obj["Entities"][0]["Markers"]}
    assert {"entrance", "entrance_sud", "arena_seuil"} <= set(markers)
    assert markers["entrance"]["Collider"] == {"X": 280, "Y": 368, "Width": 16, "Height": 16}
    assert markers["arena_seuil"]["Collider"] == {"X": 280, "Y": 120, "Width": 16, "Height": 16}
    assert obj["Entities"][0]["MapChars"] == []
    assert obj["Entities"][0]["GroundObjects"] == []
    assert obj["Entities"][0]["Spawners"] == []

    # Check the five .dir headers and their canonical/source relations.
    prov = json.loads((OUT / "provenance/provenance.json").read_text(encoding="utf-8"))
    for record in prov["backgrounds"]:
        png, size, sheet = dir_payload(OUT / record["asset"])
        assert list(size) == record["size"]
        assert list(png_size(png)) == record["sheet_size"]
        assert sheet[1] == record["frames"]
        assert sha256(OUT / record["asset"]) != ""
        source_path = ROOT / record["source"]
        assert sha256(source_path) == record["sha256_source"]
        if record["asset"].endswith("NIGHT_BASE.dir"):
            assert png == source_path.read_bytes()
            assert sheet == (0, 1)
        if record["asset"].endswith("AURORA_PALETTE_CYCLE.dir"):
            assert sheet == (0, 6)
            assert record["animation"]["sky_asset"].endswith("GLACIER_NIGHT_BASE.dir")
            assert record["animation"]["official_cycle"] is False
            frame_paths = [OUT / frame for frame in record["animation"]["frame_files"]]
            assert all(path.is_file() for path in frame_paths)
            assert len({sha256(path) for path in frame_paths}) > 1

    retrieval = prov["texture_retrieval"]
    assert {r["role"] for r in retrieval} == {
        "sky", "aurora", "distant_mountains", "ground_ice_reference",
        "path_reference", "trees_and_snow_forest",
    }
    for record in retrieval:
        source = ROOT / record["source"]
        delivered = OUT / record["delivered_reference"]
        assert source.is_file() and delivered.is_file()
        assert sha256(source) == record["sha256"] == sha256(delivered)
    for key, record in prov["canonical_references"].items():
        assert sha256(ROOT / record["path"]) == record["sha256"]
    layer_manifest = json.loads((OUT / "layers/layer_manifest.json").read_text(encoding="utf-8"))
    assert len(layer_manifest["layers"]) == 12
    assert [item["file"] for item in layer_manifest["layers"][:7]] == [
        "layers/00_night_sky_canonical.png",
        "layers/01_aurora_canonical.png",
        "layers/02_mountains_iceroad_native_crop.png",
        "layers/03_trees_snow_native_crop.png",
        "layers/04_forest_below_path_native_crop.png",
        "layers/05_arena_material_reference_canonical.png",
        "layers/06_south_path_reference_canonical.png",
    ]
    assert all((OUT / item["file"]).is_file() for item in layer_manifest["layers"])
    assert not any(p.suffix.lower() in {".png", ".jpg", ".webp"} and "guide" in p.name.lower()
                   for p in (OUT / "Content").rglob("*"))
    assert (OUT / "Content/Tile/index.idx").is_file()

    check_installer()
    runtime_results = HERE / "runtime_results.tsv"
    if runtime_results.is_file() and runtime_results.read_text(encoding="utf-8").strip() == "glacier_cliff_aurora_v1\t72\t54\t3\t5\tPASS":
        native_runtime = "PASS"
    else:
        native_runtime = "NOT RUN IN THIS CHECKOUT"
    report = {
        "status": "PASS",
        "target": "PMDO 0.8.12.0",
        "ground": ASSET,
        "serialized_ground": True,
        "native_tile_byte_exact": True,
        "native_tile_references_resolved": references,
        "grid_cells": [72, 54],
        "dimensions_px": [576, 432],
        "tex_size": 3,
        "walkable_cells": len(floor),
        "blocked_cells": 72 * 54 - len(floor),
        "wall_cells": len(wall),
        "markers": sorted(markers),
        "entry_to_arena_path": True,
        "canonical_backgrounds": 5,
        "named_layer_exports": 12,
        "canonical_reference_hashes": True,
        "aurora_palette_cycle": {
            "asset": "Content/BG/GLACIER_AURORA_PALETTE_CYCLE.dir",
            "frames": 6,
            "frame_time": 6,
            "independent_from_sky": True,
            "derived_from_canonical_reference": True,
        },
        "installer_merge_idempotence_and_conflict_protection": True,
        "runtime": {
            "pmdo_binary_deserialization": native_runtime,
            "graphics_editor": "NOT RUN",
            "gpu_render": "NOT RUN",
            "collision_and_connectivity": "PASS (serialized-grid audit)",
        },
        "limits": [
            "The report proves file/schema/reference/collision integrity, not a graphical PMDO session.",
            "The aurora palette cycle is a derived six-frame layer, not an official source animation claim.",
            "Dungeon destination is intentionally not bound; connect arena_seuil in the host quest.",
        ],
    }
    for path in (OUT / "verification.json", HERE / "verification.json"):
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
