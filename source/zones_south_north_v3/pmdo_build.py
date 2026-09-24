#!/usr/bin/env python3
"""Build a standalone PMDO Ground project from the reviewed south-to-north layers.

The V3 images are the source of truth for the composition.  This script only
serializes their existing 8 px RGBA pixels into PMDO tile banks and Ground
maps; it never calls an image generator and never edits the V3 layers.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import shutil
import struct
import uuid
from pathlib import Path
from typing import Iterable

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
V3 = ROOT / "exports/zones_south_north_v3"
OUT = ROOT / "exports/zones_south_north_v3_pmdo"
GRID = 8
PROJECT_ID = "zones_south_north_v3_pmdo"
NAMESPACE = "zones_south_north_v3_pmdo"
VERSION = "0.8.12.0"


# ---------------------------------------------------------------------------
# Native PMDO tile/index serialization.  The layout matches the existing
# source/pmdo_cote builder and the RogueEssence TileIndexNode format used by
# PMDO 0.8.x: 8-byte node header, x/y/PNG-offset records, then length-prefixed
# PNG payloads.
# ---------------------------------------------------------------------------


def premultiplied(image: Image.Image) -> Image.Image:
    rgba = np.array(image.convert("RGBA"), dtype=np.uint16)
    rgba[:, :, :3] = rgba[:, :, :3] * rgba[:, :, 3:4] // 255
    return Image.fromarray(rgba.astype(np.uint8), "RGBA")


def png_bytes(image: Image.Image) -> bytes:
    stream = io.BytesIO()
    # Compression is deliberately fixed for deterministic output.  Pixels are
    # decoded by PMDO; the PNG compression level has no visual effect.
    image.save(stream, format="PNG", compress_level=0)
    return stream.getvalue()


class TileBank:
    """One PMDO .tile bank whose TexLocs retain the map-cell coordinates."""

    def __init__(self, name: str):
        self.name = name
        self.entries: dict[tuple[int, int], bytes] = {}

    def add(self, image: Image.Image, x: int, y: int) -> dict | None:
        tile = image.convert("RGBA")
        if tile.getchannel("A").getbbox() is None:
            return None
        raw = premultiplied(tile).tobytes()
        key = (x, y)
        previous = self.entries.get(key)
        if previous is not None and previous != raw:
            raise ValueError(f"collision de TexLoc dans {self.name}: {key}")
        self.entries[key] = raw
        return {"Sheet": self.name, "TexLoc": {"X": x, "Y": y}}

    def write(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        ordered = sorted(self.entries.items(), key=lambda item: (item[0][1], item[0][0]))
        header_size = 8 + 16 * len(ordered)
        payload = bytearray()
        offsets: dict[bytes, int] = {}
        records: list[bytes] = []
        for (x, y), raw in ordered:
            if raw not in offsets:
                tile = Image.frombytes("RGBA", (GRID, GRID), raw)
                encoded = png_bytes(tile)
                offsets[raw] = header_size + len(payload)
                payload.extend(struct.pack("<q", len(encoded)))
                payload.extend(encoded)
            records.append(struct.pack("<iiq", x, y, offsets[raw]))
        path.write_bytes(struct.pack("<ii", GRID, len(records)) + b"".join(records) + payload)


def write_string(value: str) -> bytes:
    raw = value.encode("utf-8")
    length = len(raw)
    header = bytearray()
    while length >= 128:
        header.append((length & 127) | 128)
        length >>= 7
    header.append(length)
    return bytes(header) + raw


def read_node_header(data: bytes) -> bytes:
    if len(data) < 8:
        raise ValueError(".tile trop court")
    tile_size, count = struct.unpack_from("<ii", data)
    if tile_size != GRID or count < 0:
        raise ValueError("en-tête .tile invalide")
    size = 8 + count * 16
    if len(data) < size:
        raise ValueError("index .tile tronqué")
    return data[:size]


def write_index(tile_paths: Iterable[Path], path: Path) -> None:
    nodes = {}
    for tile_path in sorted(tile_paths):
        data = tile_path.read_bytes()
        nodes[tile_path.stem] = read_node_header(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<i", len(nodes)) + b"".join(
        write_string(name) + nodes[name] for name in sorted(nodes)
    ))


# ---------------------------------------------------------------------------
# Ground document helpers
# ---------------------------------------------------------------------------


def empty_auto() -> dict:
    return {"AutoTileset": "", "Associates": [], "Layers": [], "NeighborCode": -1}


def cell_animation(frame: dict | None) -> dict:
    if frame is None:
        return empty_auto()
    return {
        "AutoTileset": "",
        "Associates": [],
        "Layers": [{"Frames": [frame], "FrameLength": 60}],
        "NeighborCode": 0,
    }


def marker(name: str, rect: tuple[int, int, int, int], comment: str) -> dict:
    x, y, width, height = rect
    return {
        "EntName": name,
        "Direction": 0,
        "EntEnabled": True,
        "triggerType": 0,
        "Collider": {"X": x, "Y": y, "Width": width, "Height": height},
        "Comment": comment,
    }


def obstacle_grid(w: int, h: int, free_cells: np.ndarray) -> list[list[dict]]:
    return [
        [
            {
                "Bounds": {"X": x * GRID, "Y": y * GRID, "Width": GRID, "Height": GRID},
                "Tags": 0 if bool(free_cells[y, x]) else 1,
            }
            for y in range(h)
        ]
        for x in range(w)
    ]


def collision_cells(path_mask_path: Path, width: int, height: int) -> tuple[np.ndarray, np.ndarray]:
    """Return (path pixels, free cells) using a conservative 8 px clearance.

    A Ground cell is free only when the complete 8x8 cell is inside the reviewed
    route and at least one full cell away from its mask boundary.  This avoids
    claiming that a painted edge is a walkable collision.  The rest remains
    blocked scaffolding for the editor and can be widened after an in-engine
    review.
    """
    path = np.array(Image.open(path_mask_path).convert("L")) > 0
    path = path[:height, :width]
    # A small, dependency-free erosion by an 8px square.  The masks are modest
    # (512x640 max), and the explicit loops make the collision rule auditable.
    clearance = np.zeros_like(path, dtype=bool)
    for y in range(8, max(8, height - 8)):
        for x in range(8, max(8, width - 8)):
            clearance[y, x] = path[y - 8 : y + 9, x - 8 : x + 9].all()
    free = np.zeros((height // GRID, width // GRID), dtype=bool)
    for cy in range(height // GRID):
        for cx in range(width // GRID):
            block = clearance[cy * GRID : (cy + 1) * GRID, cx * GRID : (cx + 1) * GRID]
            free[cy, cx] = block.shape == (GRID, GRID) and bool(block.all())
    return path, free


def build_tile_layer(image: Image.Image, bank: TileBank, width: int, height: int) -> list[list[dict]]:
    pixels = image.convert("RGBA")
    tiles: list[list[dict]] = []
    for x in range(width):
        column = []
        for y in range(height):
            tile = pixels.crop((x * GRID, y * GRID, (x + 1) * GRID, (y + 1) * GRID))
            column.append(cell_animation(bank.add(tile, x, y)))
        tiles.append(column)
    return tiles


def ground_layer(name: str, tiles: list[list[dict]], draw_layer: int) -> dict:
    return {
        "Name": name,
        "Layer": draw_layer,
        "Visible": True,
        "Tiles": tiles,
    }


def source_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def copy_provenance(v3_manifest: dict, output: Path) -> list[dict]:
    records = []
    p_root = output / "provenance"
    for source in v3_manifest["sources"]:
        src = ROOT / source["file"]
        record = {**source, "sha256_at_build": source_hash(src)}
        if record["sha256"] != record["sha256_at_build"]:
            raise ValueError(f"source modifiée depuis le manifeste: {src}")
        records.append(record)
    for map_record in v3_manifest["maps"]:
        map_dir = V3 / map_record["id"]
        dest = p_root / "layers" / map_record["id"]
        dest.mkdir(parents=True, exist_ok=True)
        for layer in map_record["layers"]:
            for filename in (layer["file"], layer["provenance"]):
                shutil.copyfile(map_dir / filename, dest / filename)
        for filename in ("composite.png", "path_connectivity_mask.png", "access_review_NOT_RUNTIME.png"):
            shutil.copyfile(map_dir / filename, dest / filename)
    shutil.copyfile(V3 / "manifest.json", p_root / "v3_manifest.json")
    shutil.copyfile(ROOT / "source/zones_south_north_v3/STATUS.md", p_root / "V3_STATUS.md")
    return records


def make_map(map_record: dict, output: Path) -> tuple[dict, list[TileBank]]:
    map_id = map_record["id"]
    width, height = map_record["size"]
    w, h = width // GRID, height // GRID
    v3_dir = V3 / map_id
    banks: list[TileBank] = []
    layers = []
    exported_layers = []
    for index, layer_record in enumerate(map_record["layers"]):
        image = Image.open(v3_dir / layer_record["file"]).convert("RGBA")
        if image.size != (width, height):
            raise ValueError(f"taille de couche invalide: {image.filename}")
        bank_name = f"SNV3P_{map_id.upper()}_{index:02d}"
        bank = TileBank(bank_name)
        banks.append(bank)
        # Keep the V3 order.  The last foreground foliage/cover layers are put
        # on Top=4 so the player can pass behind them; the other terrain remains
        # on the normal map plane.
        draw_layer = 4 if index == len(map_record["layers"]) - 1 or (
            map_id == "forest_cave" and index == 6
        ) else 0
        tiles = build_tile_layer(image, bank, w, h)
        layers.append(ground_layer(layer_record["id"], tiles, draw_layer))
        exported_layers.append({
            "id": layer_record["id"],
            "file": layer_record["file"],
            "bank": bank_name,
            "source_provenance": layer_record["provenance"],
            "draw_layer": draw_layer,
        })

    path_mask, free_cells = collision_cells(
        v3_dir / "path_connectivity_mask.png", width, height
    )
    entrance = tuple(map_record["entrance_trigger_candidate"])
    south = tuple(map_record["south_access"])
    asset = f"sn_v3_{map_id}"
    markers = [
        marker("entrance", south, "Arrivée sud; aucun warp automatique n'est configuré."),
        marker("donjon_seuil", entrance, "Seuil nord; destination à raccorder par le projet utilisateur."),
    ]
    obj = {
        "$type": "RogueEssence.Ground.GroundMap, RogueEssence",
        "TexSize": 1,
        "Name": {"DefaultText": map_record["title"], "LocalTexts": {}},
        "Released": False,
        "Comment": (
            "SouthNorth V3 PMDO. Pixels des couches V3 conservés depuis les sources "
            "documentées, sérialisés en banques .tile 8 px. Collision conservatrice "
            "sur le chemin sud-nord uniquement; collisions, warp et rendu moteur à vérifier."
        ),
        "obstacles": obstacle_grid(w, h, free_cells),
        "rand": {
            "$type": "RogueElements.ReRandom, RogueElements",
            "FirstSeed": 0,
            "s": [16294208416658607535, 7960286522194355700, 487617019471545679, 17909611376780542444],
        },
        "Status": {},
        "Background": {
            "$type": "RogueEssence.Dungeon.LayeredBG, RogueEssence",
            "Layers": [],
        },
        "BlankBG": empty_auto(),
        "Layers": layers,
        "AssetName": asset,
        "Music": "",
        "EdgeView": 0,
        "NoSwitching": False,
        "ViewCenter": None,
        "ViewOffset": {"X": 0, "Y": 0},
        "ActiveChar": None,
        "Decorations": [{"Name": "Decorations", "Layer": 2, "Visible": True, "Anims": []}],
        "Entities": [{
            "Name": "Arrivee et seuil",
            "Visible": True,
            "MapChars": [],
            "GroundObjects": [],
            "Spawners": [],
            "Markers": markers,
        }],
    }
    doc = {"Version": VERSION, "Object": obj}
    destination = output / "Data/Ground" / f"{asset}.rsground"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n")
    script = output / "Data/Script/ground" / asset / "init.lua"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(
        "-- SouthNorth V3: empty scaffold. No automatic dungeon warp is defined.\n"
        "return {}\n"
    )
    return {
        "id": map_id,
        "asset": asset,
        "title": map_record["title"],
        "size_px": [width, height],
        "grid": [w, h],
        "orientation": map_record["orientation"],
        "source_layers": exported_layers,
        "tilesets": [bank.name for bank in banks],
        "markers": [
            {"name": "entrance", "rect": list(south), "role": "south_arrival"},
            {"name": "donjon_seuil", "rect": list(entrance), "role": "north_threshold"},
        ],
        "collision": {
            "policy": "free cells are the 8px-cleared reviewed south-to-north path; all other cells blocked scaffold",
            "free_cells": int(free_cells.sum()),
            "total_cells": int(free_cells.size),
            "path_pixels": int(path_mask.sum()),
            "runtime_validated": False,
        },
        "canonical_materials": map_record["notes"],
        "runtime": "NOT TESTED",
        "art_approved": False,
    }, banks


def patch_installer(output: Path) -> None:
    source = (ROOT / "source/pmdo_cote/INSTALLER.py").read_text()
    old = "            relative = src.relative_to(source)\n            # Keep legacy scripts and provide a namespaced copy for recent PMDO.\n"
    new = "            relative = src.relative_to(source)\n            # The standalone project's index is merged, never copied over an\n            # existing project's complete index.\n            if relative.as_posix() == 'Content/Tile/index.idx':\n                continue\n            # Keep legacy scripts and provide a namespaced copy for recent PMDO.\n"
    if old not in source:
        raise RuntimeError("template INSTALLER.py changed; patch refused")
    (output / "INSTALLER.py").write_text(source.replace(old, new))


def write_mod_header(output: Path) -> None:
    ident = uuid.uuid5(uuid.NAMESPACE_URL, "https://github.com/meromoonmeri/guilde-treehouse-pmd/" + PROJECT_ID)
    (output / "Mod.xml").write_text(
        f'''<?xml version="1.0" encoding="utf-8"?>
<Header>
  <Name>SouthNorth V3 — entrées canoniques</Name>
  <Author>meromoonmeri</Author>
  <Description>Deux Ground PMDO 0.8.12, arrivee sud vers seuil nord, couches V3 et pixels sources documentes. Pas de warp automatique.</Description>
  <Namespace>{NAMESPACE}</Namespace>
  <UUID>{ident}</UUID>
  <Version>1.0.0.0</Version>
  <GameVersion>{VERSION}</GameVersion>
  <ModType>Quest</ModType>
  <Relationships />
</Header>
''',
        encoding="utf-8",
    )
    # PMDO versions in the project use both paths; keeping a namespaced copy is
    # harmless and makes the standalone pack editable in recent builds.
    for source in (output / "Data/Script/ground").glob("*/init.lua"):
        target = output / "Data/Script" / NAMESPACE / "ground" / source.parent.name / "init.lua"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)


def write_readme(output: Path) -> None:
    shutil.copyfile(ROOT / "source/zones_south_north_v3/README_PMDO.md", output / "README.md")


def main() -> None:
    if OUT == ROOT or OUT.parent != ROOT / "exports":
        raise RuntimeError("sortie PMDO inattendue")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    v3_manifest = json.loads((V3 / "manifest.json").read_text(encoding="utf-8"))
    records = copy_provenance(v3_manifest, OUT)
    project_maps = []
    banks: list[TileBank] = []
    for map_record in v3_manifest["maps"]:
        project_map, map_banks = make_map(map_record, OUT)
        project_maps.append(project_map)
        banks.extend(map_banks)
        # Review-only images remain visible in the pack, but never enter the
        # Ground tile banks.
        review_dir = OUT / "review"
        review_dir.mkdir(exist_ok=True)
        for filename, target in [
            ("composite.png", f"{map_record['id']}_composite.png"),
            ("access_review_NOT_RUNTIME.png", f"{map_record['id']}_access_NOT_RUNTIME.png"),
            ("path_connectivity_mask.png", f"{map_record['id']}_path_mask.png"),
        ]:
            shutil.copyfile(V3 / map_record["id"] / filename, review_dir / target)
    for bank in banks:
        bank.write(OUT / "Content/Tile" / f"{bank.name}.tile")
    write_index((OUT / "Content/Tile").glob("*.tile"), OUT / "Content/Tile/index.idx")
    write_mod_header(OUT)
    patch_installer(OUT)
    write_readme(OUT)
    manifest = {
        "project": PROJECT_ID,
        "target": "PMDO 0.8.12",
        "serialization_version": VERSION,
        "grid_px": GRID,
        "canonical_claim": "exact documented source RGBA pixels serialized into new 8px PMDO banks; not a claim that the original upstream tile bank was recovered",
        "source_records": records,
        "maps": project_maps,
        "runtime_pmdo_tested": False,
        "render_gpu_tested": False,
        "gameplay_tested": False,
        "warp_destinations": "NOT CONFIGURED",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"{len(project_maps)} Ground PMDO construits dans {OUT}")
    print(f"{len(banks)} banques .tile, index complet et installateur de fusion écrits")


if __name__ == "__main__":
    main()
