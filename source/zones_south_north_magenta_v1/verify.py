#!/usr/bin/env python3
"""Verify the one-map, five-layer magenta workflow and PMDO export."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exports/forest_cave_magenta_v1_pmdo"
V3_ROOT = ROOT / "exports/zones_south_north_v3"
V3 = V3_ROOT / "forest_cave"
GRID = 8
WIDTH, HEIGHT = 512, 640

sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from source.zones_south_north_v3.pmdo_verify import (  # noqa: E402
    read_index,
    read_tile,
    render_layer,
)


def over(*images: Image.Image) -> Image.Image:
    result = Image.new("RGBA", (WIDTH, HEIGHT))
    for image in images:
        result.alpha_composite(image)
    return result


def read_installer():
    spec = importlib.util.spec_from_file_location("forest_magenta_installer", OUT / "INSTALLER.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def installer_check(tile_paths: list[Path]) -> None:
    installer = read_installer()
    with tempfile.TemporaryDirectory(prefix="forest_magenta_verify_") as tmp:
        target = Path(tmp) / "mod"
        target.mkdir(parents=True)
        (target / "Mod.xml").write_text("<Header><Namespace>verify_mod</Namespace></Header>")
        existing = target / "Content/Tile/Existing.tile"
        existing.parent.mkdir(parents=True)
        shutil.copyfile(tile_paths[0], existing)
        data = existing.read_bytes()
        count = int.from_bytes(data[4:8], "little", signed=True)
        existing.parent.joinpath("index.idx").write_bytes(
            installer.encode_index({"Existing": data[: 8 + count * 16]})
        )
        installer.install(OUT, target, dry_run=True)
        assert not (target / "Data").exists()
        installer.install(OUT, target)
        nodes = installer.read_index(existing.parent / "index.idx")
        assert set(nodes) == {"Existing", *(p.stem for p in tile_paths)}
        before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
        installer.install(OUT, target)
        after = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
        assert before == after
        ground = next((target / "Data/Ground").glob("*.rsground"))
        ground.write_text("edited")
        try:
            installer.install(OUT, target)
        except ValueError as exc:
            assert "Conflits" in str(exc)
        else:
            raise AssertionError("edited Ground was overwritten")
        assert ground.read_text() == "edited"


def verify() -> dict:
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["workflow"].startswith("magenta composition guide")
    assert manifest["canonical_final_pixels"] is True
    assert manifest["generated_guide_pixels_in_final"] is False
    assert manifest["guide"]["final_layers_use_guide_pixels"] is False
    assert manifest["map"]["layer_count"] == 5

    guide = np.array(Image.open(OUT / "provenance/guide/forest_cave_layout_magenta.png").convert("RGBA"))
    assert tuple(guide.shape[:2]) == (HEIGHT, WIDTH)
    key = (guide[:, :, 0] >= 220) & (guide[:, :, 1] <= 80) & (guide[:, :, 2] >= 200)
    assert key[0, 0] and key[0, -1] and key[-1, 0] and key[-1, -1]
    assert int(key.sum()) == manifest["guide"]["magenta_pixels"]
    keyed = np.array(Image.open(OUT / "provenance/guide/forest_cave_layout_alpha_clean.png").convert("RGBA"))
    assert np.all(keyed[key, 3] == 0) and np.all(keyed[~key, 3] == 255)

    records = manifest["map"]["layers"]
    assert len(records) == 5
    final_images = []
    for record in records:
        assert record["generated_pixels_used"] is False
        sources = []
        for source_name in record["source_layers"]:
            source_file = {
                "01_soil": "SouthNorthV3_forest_cave_01_soil.png",
                "02_path": "SouthNorthV3_forest_cave_02_continuous_earth_path.png",
                "03_north_canopy": "SouthNorthV3_forest_cave_03_north_canopy.png",
                "04_cliff": "SouthNorthV3_forest_cave_04_white_cliff.png",
                "05_cave": "SouthNorthV3_forest_cave_05_cave_opening.png",
                "06_trunks": "SouthNorthV3_forest_cave_06_tree_trunks.png",
                "07_canopies": "SouthNorthV3_forest_cave_07_tree_canopies.png",
                "08_stones": "SouthNorthV3_forest_cave_08_stones.png",
                "09_bushes": "SouthNorthV3_forest_cave_09_cliff_foot_bushes.png",
            }[source_name]
            source_path = V3 / source_file
            assert hashlib.sha256(source_path.read_bytes()).hexdigest() == record["source_hashes"][source_name]
            sources.append(Image.open(source_path).convert("RGBA"))
        expected = over(*sources)
        actual = Image.open(OUT / "provenance/final_layers" / record["file"]).convert("RGBA")
        assert actual.tobytes() == expected.tobytes(), record["id"]
        final_images.append(actual)
    composition = over(*final_images)
    assert composition.tobytes() == Image.open(OUT / "review/composition_final.png").convert("RGBA").tobytes()
    assert composition.tobytes() == Image.open(V3 / "composite.png").convert("RGBA").tobytes()

    tile_paths = sorted((OUT / "Content/Tile").glob("*.tile"))
    assert len(tile_paths) == 5
    index = read_index(OUT / "Content/Tile/index.idx")
    assert set(index) == {p.stem for p in tile_paths}
    banks = {p.stem: read_tile(p) for p in tile_paths}
    doc = json.loads((OUT / "Data/Ground/forest_magenta_v1.rsground").read_text())
    obj = doc["Object"]
    assert doc["Version"] == "0.8.12.0"
    assert obj["TexSize"] == 1 and len(obj["Layers"]) == 5
    assert obj["Layers"][-1]["Layer"] == 4
    for layer, expected in zip(obj["Layers"], final_images):
        rendered = render_layer(layer, banks, (WIDTH, HEIGHT))
        assert np.array_equal(rendered, np.array(expected)), layer["Name"]
    markers = {m["EntName"]: m for m in obj["Entities"][0]["Markers"]}
    assert set(markers) == {"entrance", "donjon_seuil"}
    assert not obj["Entities"][0]["MapChars"]
    assert not obj["Entities"][0]["GroundObjects"]
    assert not obj["Entities"][0]["Spawners"]

    mask = np.array(Image.open(V3 / "path_connectivity_mask.png").convert("L")) > 0
    free = 0
    for x, column in enumerate(obj["obstacles"]):
        for y, cell in enumerate(column):
            if cell["Tags"] == 0:
                free += 1
                assert mask[y * GRID : (y + 1) * GRID, x * GRID : (x + 1) * GRID].all()
    assert free == manifest["map"]["free_collision_cells"] > 0
    installer_check(tile_paths)
    report = {
        "result": "PASS",
        "workflow": "magenta guide -> alpha cleanup -> canonical final composition -> 5 layers -> PMDO Ground",
        "layer_count": 5,
        "pixel_differences_final_vs_canonical": 0,
        "ground_maps": 1,
        "tile_banks": 5,
        "free_collision_cells": free,
        "runtime_pmdo_tested": False,
        "render_gpu_tested": False,
        "gameplay_tested": False,
        "warp_destinations": "NOT CONFIGURED",
    }
    (OUT / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    verify()
