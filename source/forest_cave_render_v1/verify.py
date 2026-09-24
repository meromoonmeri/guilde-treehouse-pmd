#!/usr/bin/env python3
"""Verify the generated final composition and its five aligned PMDO layers."""
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
from scipy import ndimage as nd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exports/forest_cave_render_v1_pmdo"
SOURCE = ROOT / "source/forest_cave_render_v1/generation/forest_cave_final_generated_v3.png"
WIDTH, HEIGHT, GRID = 512, 640, 8
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from source.zones_south_north_v3.pmdo_verify import read_index, read_tile, render_layer  # noqa: E402


def read_installer():
    spec = importlib.util.spec_from_file_location("render_installer", OUT / "INSTALLER.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def install_check(tile_paths):
    installer = read_installer()
    with tempfile.TemporaryDirectory(prefix="forest_render_verify_") as tmp:
        target = Path(tmp) / "mod"
        target.mkdir(parents=True)
        (target / "Mod.xml").write_text("<Header><Namespace>verify_mod</Namespace></Header>")
        existing = target / "Content/Tile/Existing.tile"
        existing.parent.mkdir(parents=True)
        shutil.copyfile(tile_paths[0], existing)
        data = existing.read_bytes(); count = int.from_bytes(data[4:8], "little", signed=True)
        (existing.parent / "index.idx").write_bytes(installer.encode_index({"Existing": data[:8 + count * 16]}))
        installer.install(OUT, target, dry_run=True)
        assert not (target / "Data").exists()
        installer.install(OUT, target)
        nodes = installer.read_index(existing.parent / "index.idx")
        assert set(nodes) == {"Existing", *(p.stem for p in tile_paths)}
        before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
        installer.install(OUT, target)
        after = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
        assert before == after
        ground = next((target / "Data/Ground").glob("*.rsground")); ground.write_text("edited")
        try:
            installer.install(OUT, target)
        except ValueError as exc:
            assert "Conflits" in str(exc)
        else:
            raise AssertionError("edited map was overwritten")


def verify():
    manifest = json.loads((OUT / "manifest.json").read_text())
    assert manifest["workflow"].startswith("final generated composition on magenta")
    assert manifest["final_pixels_are_generated"] is True
    assert manifest["canonical_references_are_style_guides"] is True
    assert manifest["layer_count"] == 5
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == manifest["composition_source"]["sha256"]

    guide = np.array(Image.open(OUT / "provenance/generation/forest_cave_final_composition_magenta.png").convert("RGBA"))
    assert guide.shape[:2] == (HEIGHT, WIDTH)
    r, g, b = (guide[:, :, i].astype(int) for i in range(3))
    candidate = (r >= 200) & (g <= 120) & (b >= 180) & (r - g >= 100) & (b - g >= 90)
    edge = np.zeros(candidate.shape, dtype=bool)
    edge[0, :] = candidate[0, :]
    edge[-1, :] = candidate[-1, :]
    edge[:, 0] |= candidate[:, 0]
    edge[:, -1] |= candidate[:, -1]
    key = nd.binary_propagation(edge, mask=candidate, structure=np.ones((3, 3), dtype=bool))
    assert key[0, 0] and key[0, -1] and key[-1, 0] and key[-1, -1]
    transparent = np.array(Image.open(OUT / "review/composition_final_transparent.png").convert("RGBA"))
    assert np.all(transparent[key, 3] == 0)
    assert np.all(transparent[~key, 3] == 255)

    records = manifest["layers"]
    assert len(records) == 5
    layer_images = []
    covered = np.zeros((HEIGHT, WIDTH), dtype=bool)
    for record in records:
        layer = np.array(Image.open(OUT / "provenance/final_layers" / record["file"]).convert("RGBA"))
        assert layer.shape[:2] == (HEIGHT, WIDTH)
        mask = layer[:, :, 3] > 0
        assert not np.any(covered & mask)
        covered |= mask
        assert int(mask.sum()) == record["pixels"]
        # All visible pixels must be the corresponding pixel of the final guide.
        assert np.array_equal(layer[mask], guide[mask])
        layer_images.append(Image.fromarray(layer, "RGBA"))
    assert np.array_equal(covered, ~key)
    recomposed = Image.new("RGBA", (WIDTH, HEIGHT))
    for layer in layer_images:
        recomposed.alpha_composite(layer)
    assert recomposed.tobytes() == transparent.tobytes()
    assert recomposed.tobytes() == Image.open(OUT / "review/composition_final.png").convert("RGBA").tobytes()

    tiles = sorted((OUT / "Content/Tile").glob("*.tile"))
    assert len(tiles) == 5
    banks = {p.stem: read_tile(p) for p in tiles}
    assert set(read_index(OUT / "Content/Tile/index.idx")) == set(banks)
    doc = json.loads((OUT / "Data/Ground/forest_cave_render_v1.rsground").read_text())
    assert doc["Version"] == "0.8.12.0"
    obj = doc["Object"]
    assert len(obj["Layers"]) == 5 and obj["Layers"][-1]["Layer"] == 4
    for ground_layer, expected in zip(obj["Layers"], layer_images):
        rendered = render_layer(ground_layer, banks, (WIDTH, HEIGHT))
        assert np.array_equal(rendered, np.array(expected)), ground_layer["Name"]
    assert {m["EntName"] for m in obj["Entities"][0]["Markers"]} == {"entrance", "donjon_seuil"}
    free = sum(cell["Tags"] == 0 for col in obj["obstacles"] for cell in col)
    assert free == manifest["map"]["free_collision_cells"] > 0
    install_check(tiles)
    report = {"result": "PASS", "workflow": "magenta final composition -> 5 aligned layers", "layer_count": 5,
              "recomposition_pixel_differences": 0, "tile_banks": 5, "ground_maps": 1,
              "free_collision_cells": free, "runtime_pmdo_tested": False,
              "render_gpu_tested": False, "gameplay_tested": False, "warp_destinations": "NOT CONFIGURED"}
    (OUT / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    verify()
