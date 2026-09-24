#!/usr/bin/env python3
"""Independent validation for the SouthNorth V3 PMDO project.

This is a binary/asset/install check.  It is deliberately not described as a
PMDO runtime, GPU, editor, collision-motion, or warp test.
"""
from __future__ import annotations

import hashlib
import importlib.util
import io
import sys

sys.dont_write_bytecode = True
import json
import shutil
import struct
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "exports/zones_south_north_v3_pmdo"
GRID = 8


def read_varint_string(data: bytes, offset: int) -> tuple[str, int]:
    length = 0
    shift = 0
    while True:
        if offset >= len(data) or shift > 35:
            raise AssertionError("varint .NET invalide")
        byte = data[offset]
        offset += 1
        length |= (byte & 127) << shift
        if byte < 128:
            break
        shift += 7
    end = offset + length
    if end > len(data):
        raise AssertionError("chaine index tronquee")
    return data[offset:end].decode("utf-8"), end


def read_index(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if len(data) < 4:
        raise AssertionError("index trop court")
    count, = struct.unpack_from("<i", data)
    if count < 0:
        raise AssertionError("nombre de nodes invalide")
    offset = 4
    nodes = {}
    for _ in range(count):
        name, offset = read_varint_string(data, offset)
        if offset + 8 > len(data):
            raise AssertionError("node index tronque")
        tile_size, records = struct.unpack_from("<ii", data, offset)
        if tile_size != GRID or records < 0:
            raise AssertionError(f"node invalide: {name}")
        end = offset + 8 + records * 16
        if end > len(data):
            raise AssertionError(f"node tronque: {name}")
        nodes[name] = data[offset:end]
        offset = end
    if offset != len(data):
        raise AssertionError("octets inattendus dans index.idx")
    return nodes


def read_tile(path: Path) -> dict[tuple[int, int], np.ndarray]:
    data = path.read_bytes()
    if len(data) < 8:
        raise AssertionError(f".tile trop court: {path.name}")
    tile_size, count = struct.unpack_from("<ii", data)
    if tile_size != GRID or count <= 0:
        raise AssertionError(f"en-tete .tile invalide: {path.name}")
    result = {}
    cache = {}
    for index in range(count):
        x, y, address = struct.unpack_from("<iiq", data, 8 + index * 16)
        if (x, y) in result:
            raise AssertionError(f"TexLoc duplique: {path.name} {(x, y)}")
        if address < 8 + count * 16 or address + 8 > len(data):
            raise AssertionError(f"offset .tile invalide: {path.name}")
        length, = struct.unpack_from("<q", data, address)
        end = address + 8 + length
        if length <= 0 or end > len(data):
            raise AssertionError(f"PNG .tile invalide: {path.name}")
        if address not in cache:
            image = Image.open(io.BytesIO(data[address + 8 : end])).convert("RGBA")
            if image.size != (GRID, GRID):
                raise AssertionError(f"tuile non 8x8: {path.name}")
            rgba = np.array(image)
            if not np.all(rgba[:, :, :3] <= rgba[:, :, 3:4]):
                raise AssertionError(f"alpha non prémultiplié: {path.name}")
            cache[address] = rgba
        result[(x, y)] = cache[address]
    return result


def render_layer(layer: dict, banks: dict[str, dict[tuple[int, int], np.ndarray]], size: tuple[int, int]) -> np.ndarray:
    width, height = size
    image = np.zeros((height, width, 4), dtype=np.uint8)
    if len(layer["Tiles"]) != width // GRID:
        raise AssertionError(f"largeur de layer invalide: {layer['Name']}")
    for x, column in enumerate(layer["Tiles"]):
        if len(column) != height // GRID:
            raise AssertionError(f"hauteur de layer invalide: {layer['Name']}")
        for y, cell in enumerate(column):
            if cell["AutoTileset"] != "" or cell["Associates"] != []:
                raise AssertionError(f"cellule autotile inattendue: {layer['Name']}")
            animations = cell["Layers"]
            if len(animations) > 1:
                raise AssertionError(f"animation inattendue: {layer['Name']}")
            if not animations:
                continue
            animation = animations[0]
            if animation["FrameLength"] != 60 or len(animation["Frames"]) != 1:
                raise AssertionError(f"frame statique invalide: {layer['Name']}")
            frame = animation["Frames"][0]
            sheet = frame["Sheet"]
            loc = (frame["TexLoc"]["X"], frame["TexLoc"]["Y"])
            if sheet not in banks or loc not in banks[sheet]:
                raise AssertionError(f"référence non résolue: {sheet} {loc}")
            image[y * GRID : (y + 1) * GRID, x * GRID : (x + 1) * GRID] = banks[sheet][loc]
    return image


def import_installer():
    spec = importlib.util.spec_from_file_location("southnorth_installer", OUT / "INSTALLER.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def installer_check(tile_paths: list[Path]) -> None:
    installer = import_installer()
    with tempfile.TemporaryDirectory(prefix="southnorth_pmdo_verify_") as temp:
        target = Path(temp) / "mod"
        target.mkdir(parents=True)
        (target / "Mod.xml").write_text(
            "<Header><Name>verify</Name><Namespace>verify_mod</Namespace></Header>",
            encoding="utf-8",
        )
        existing_tile = target / "Content/Tile/Existing.tile"
        existing_tile.parent.mkdir(parents=True)
        shutil.copyfile(tile_paths[0], existing_tile)
        existing_bytes = existing_tile.read_bytes()
        node_size, node_count = struct.unpack_from("<ii", existing_bytes)
        existing_node = existing_bytes[: 8 + 16 * node_count]
        (existing_tile.parent / "index.idx").write_bytes(
            installer.encode_index({"Existing": existing_node})
        )
        installer.install(OUT, target, dry_run=True)
        assert not (target / "Data").exists(), "dry-run a écrit des fichiers"
        installer.install(OUT, target)
        index = installer.read_index(target / "Content/Tile/index.idx")
        assert "Existing" in index and len(index) == len(tile_paths) + 1
        before = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
        installer.install(OUT, target)
        after = {p.relative_to(target): p.read_bytes() for p in target.rglob("*") if p.is_file()}
        assert before == after, "installation non idempotente"
        ground = next((target / "Data/Ground").glob("*.rsground"))
        ground.write_text("modified by user", encoding="utf-8")
        try:
            installer.install(OUT, target)
        except ValueError as exc:
            assert "Conflits" in str(exc)
        else:
            raise AssertionError("une carte modifiée a été écrasée")
        assert ground.read_text(encoding="utf-8") == "modified by user"


def verify() -> dict:
    assert OUT.is_dir(), f"sortie absente: {OUT}"
    manifest = json.loads((OUT / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["target"] == "PMDO 0.8.12"
    assert manifest["runtime_pmdo_tested"] is False
    assert manifest["warp_destinations"] == "NOT CONFIGURED"
    root = ET.parse(OUT / "Mod.xml").getroot()
    assert root.findtext("Namespace") == "zones_south_north_v3_pmdo"
    assert root.findtext("GameVersion") == "0.8.12.0"

    tile_paths = sorted((OUT / "Content/Tile").glob("*.tile"))
    assert len(tile_paths) == sum(len(m["source_layers"]) for m in manifest["maps"])
    index = read_index(OUT / "Content/Tile/index.idx")
    assert set(index) == {p.stem for p in tile_paths}
    banks = {p.stem: read_tile(p) for p in tile_paths}

    report = {
        "result": "PASS",
        "project": manifest["project"],
        "checks": [
            "all .tile records are 8x8 PNGs with premultiplied alpha",
            "complete index resolves every delivered tile bank",
            "Ground references reconstruct every source layer with zero pixel differences",
            "8px grid, separate layers, markers and conservative path collision scaffold",
            "installer dry-run, index merge, idempotence and edited-map conflict refusal",
        ],
        "zones": [],
        "runtime_pmdo_tested": False,
        "render_gpu_tested": False,
        "gameplay_tested": False,
    }
    for record in manifest["maps"]:
        asset = record["asset"]
        doc = json.loads((OUT / "Data/Ground" / f"{asset}.rsground").read_text(encoding="utf-8"))
        assert doc["Version"] == "0.8.12.0"
        obj = doc["Object"]
        assert obj["$type"] == "RogueEssence.Ground.GroundMap, RogueEssence"
        assert obj["TexSize"] == 1 and obj["AssetName"] == asset
        width, height = record["size_px"]
        assert width % GRID == 0 and height % GRID == 0
        assert len(obj["Layers"]) == len(record["source_layers"])
        assert len(obj["obstacles"]) == width // GRID
        assert all(len(column) == height // GRID for column in obj["obstacles"])
        assert obj["Layers"][-1]["Layer"] == 4
        markers = {m["EntName"]: m for m in obj["Entities"][0]["Markers"]}
        assert set(markers) == {"entrance", "donjon_seuil"}
        assert not obj["Entities"][0]["MapChars"]
        assert not obj["Entities"][0]["GroundObjects"]
        assert not obj["Entities"][0]["Spawners"]
        rendered = []
        source_dir = ROOT / "exports/zones_south_north_v3" / record["id"]
        for layer, source_record in zip(obj["Layers"], record["source_layers"]):
            image = render_layer(layer, banks, (width, height))
            source = np.array(Image.open(source_dir / source_record["file"]).convert("RGBA"))
            assert np.array_equal(image, source), f"pixels différents: {record['id']} {layer['Name']}"
            rendered.append(image)
        # The review composite is a straight alpha composition of the source
        # layers.  All delivered layers use binary alpha, so this is exact.
        composite = np.zeros((height, width, 4), dtype=np.uint8)
        from PIL import Image as PILImage
        composed = PILImage.new("RGBA", (width, height))
        for image in rendered:
            composed.alpha_composite(PILImage.fromarray(image, "RGBA"))
        expected = np.array(PILImage.open(source_dir / "composite.png").convert("RGBA"))
        assert np.array_equal(np.array(composed), expected), f"composite différente: {record['id']}"

        mask = np.array(Image.open(source_dir / "path_connectivity_mask.png").convert("L")) > 0
        collision = record["collision"]
        free = sum(1 for column in obj["obstacles"] for cell in column if cell["Tags"] == 0)
        assert free == collision["free_cells"]
        assert free > 0
        # A free collision cell must be fully covered by the reviewed path mask.
        for x, column in enumerate(obj["obstacles"]):
            for y, cell in enumerate(column):
                if cell["Tags"] == 0:
                    assert mask[y * GRID : (y + 1) * GRID, x * GRID : (x + 1) * GRID].all()
        report["zones"].append({
            "asset": asset,
            "size_px": [width, height],
            "layers": len(rendered),
            "tilesets": len(record["tilesets"]),
            "free_collision_cells": free,
            "pixel_differences": 0,
        })

    for source in manifest["source_records"]:
        actual = hashlib.sha256((ROOT / source["file"]).read_bytes()).hexdigest()
        assert actual == source["sha256"] == source["sha256_at_build"]
    installer_check(tile_paths)
    (OUT / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report


if __name__ == "__main__":
    verify()
