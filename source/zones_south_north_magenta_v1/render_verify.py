#!/usr/bin/env python3
"""Verify the generated-final-render forest pack."""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exports/forest_cave_render_v1_pmdo"
WIDTH, HEIGHT, GRID = 512, 640, 8
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT))
from source.zones_south_north_v3.pmdo_verify import read_index, read_tile, render_layer  # noqa: E402


def key_mask(rgb: np.ndarray) -> np.ndarray:
    r, g, b = rgb.astype(np.int16).transpose(2, 0, 1)
    exact = (r >= 220) & (g <= 80) & (b >= 200)
    softened = (r > 100) & (b > 80) & (r - g > 40) & (b - g > 35)
    return exact | softened


def read_installer():
    spec = importlib.util.spec_from_file_location("forest_render_installer", OUT / "INSTALLER.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def installer_check(tile_paths: list[Path]) -> None:
    installer = read_installer()
    with tempfile.TemporaryDirectory(prefix="forest_render_verify_") as tmp:
        target = Path(tmp) / "mod"
        target.mkdir(parents=True)
        (target / "Mod.xml").write_text("<Header><Namespace>verify_mod</Namespace></Header>")
        existing = target / "Content/Tile/Existing.tile"
        existing.parent.mkdir(parents=True)
        shutil.copyfile(tile_paths[0], existing)
        data = existing.read_bytes()
        count = int.from_bytes(data[4:8], "little", signed=True)
        existing.parent.joinpath("index.idx").write_bytes(installer.encode_index({"Existing": data[:8 + count * 16]}))
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


def verify() -> dict:
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["material_status"].startswith("generated final render")
    assert manifest["guide"]["generated_final"] is True
    assert manifest["guide"]["canonical_pixels_in_final"] is False
    assert len(manifest["layers"]) == 5

    guide = np.array(Image.open(OUT / "provenance/guide/forest_cave_layout_magenta.png").convert("RGBA"))
    key = key_mask(guide[:, :, :3])
    assert guide.shape[:2] == (HEIGHT, WIDTH)
    assert key[0, 0] and key[0, -1] and key[-1, 0] and key[-1, -1]
    clean = np.array(Image.open(OUT / "provenance/guide/forest_cave_layout_alpha_clean.png").convert("RGBA"))
    assert np.all(clean[key, 3] == 0) and np.all(clean[~key, 3] == 255)
    assert np.all(clean[key, :3] == 0)

    final_layers = []
    for record in manifest["layers"]:
        assert record["generated_final"] is True and record["canonical_pixels"] is False
        image = Image.open(OUT / "review/layers" / record["file"]).convert("RGBA")
        assert image.size == (WIDTH, HEIGHT)
        final_layers.append(image)
    composition = Image.new("RGBA", (WIDTH, HEIGHT))
    for image in final_layers:
        composition.alpha_composite(image)
    saved = np.array(Image.open(OUT / "review/composition_final.png").convert("RGBA"))
    assert np.array_equal(np.array(composition), saved)
    assert np.array_equal(saved, clean)
    assert np.all(np.isin(saved[:, :, 3], [0, 255]))
    assert np.all(saved[~key, 3] == 255) and np.all(saved[key, 3] == 0)
    visible_magenta = key_mask(saved[:, :, :3]) & (saved[:, :, 3] > 0)
    assert not np.any(visible_magenta)
    # Every non-key pixel of the final render is the generated source pixel.
    assert np.array_equal(saved[~key, :3], guide[~key, :3])

    tile_paths = sorted((OUT / "Content/Tile").glob("*.tile"))
    assert len(tile_paths) == 5
    banks = {p.stem: read_tile(p) for p in tile_paths}
    index = read_index(OUT / "Content/Tile/index.idx")
    assert set(index) == {p.stem for p in tile_paths}
    doc = json.loads((OUT / "Data/Ground/forest_render_v1.rsground").read_text())
    obj = doc["Object"]
    assert doc["Version"] == "0.8.12.0" and len(obj["Layers"]) == 5
    assert obj["Layers"][-1]["Layer"] == 4
    for layer, expected in zip(obj["Layers"], final_layers):
        rendered = render_layer(layer, banks, (WIDTH, HEIGHT))
        assert np.array_equal(rendered, np.array(expected)), layer["Name"]
    markers = {m["EntName"] for m in obj["Entities"][0]["Markers"]}
    assert markers == {"entrance", "donjon_seuil"}
    assert not obj["Entities"][0]["MapChars"] and not obj["Entities"][0]["GroundObjects"] and not obj["Entities"][0]["Spawners"]
    path = np.array(Image.open(OUT / "review/generated_path_mask.png").convert("L")) > 0
    free = 0
    for x, column in enumerate(obj["obstacles"]):
        for y, cell in enumerate(column):
            if cell["Tags"] == 0:
                free += 1
                assert path[y * GRID : (y + 1) * GRID, x * GRID : (x + 1) * GRID].all()
    assert free == manifest["ground"]["free_collision_cells"] > 0
    installer_check(tile_paths)
    report = {
        "result": "PASS",
        "workflow": "magenta final composition -> chroma cleanup -> generated five layers -> PMDO Ground",
        "layer_count": 5,
        "generated_pixels_preserved_outside_key": True,
        "magenta_residual_pixels": int(visible_magenta.sum()),
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
