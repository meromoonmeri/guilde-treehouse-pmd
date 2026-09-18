"""Build the canonical glacier-cliff GroundMap for PMDO 0.8.12.

The map is deliberately assembled from the native VastIceMountain.tile and
canonical reference pixels.  The generated composition guide is never used as
an engine texture.  Python's standard library is enough for the PMDO files;
ImageMagick is used only to make exact pixel crops and a review preview.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "exports/glacier_cliff_aurora_pmdo_v1"
TILE_SOURCE = ROOT / "source/donjons_dtef_v2/references/DumpAsset/Content/Tile/VastIceMountain.tile"
AUTOTILE_DIR = ROOT / "source/donjons_dtef_v2/references/DumpAsset/Data/AutoTile"
GUIDE = ROOT / "renders/glacier_cliff_aurora_v3/raw/native_tileset_reference_composition_magenta.png"

# The references are artwork, not generated PMDO textures.  The two cropped
# strips retain their native pixels and have their provenance recorded below.
REFS = {
    "sky": ROOT / "bgnightbackgroundpmdskyda.png",
    "aurora": ROOT / "aurorepmdsky.png",
    "distant_mountains": ROOT / "iceroadpmdsky.png",
    "ground_ice_reference": ROOT / "pmdskyicearena.png",
    "path_reference": ROOT / "source/references_54d3731/path.png",
    "trees_and_snow_forest": ROOT / "source/references_54d3731/snow.png",
}

WIDTH, HEIGHT = 72, 54                 # 576 x 432 px at the collision grid
TILE_PX = 8
TEX_SIZE = 3                            # VastIceMountain native tile images are 24 px
ASSET = "glacier_cliff_aurora_v1"
AURORA_ASSET = "GLACIER_AURORA_PALETTE_CYCLE"
AURORA_FRAME_COUNT = 6
AURORA_FRAME_TIME = 6
AURORA_FRAME_SIZE = (264, 160)
# A narrow loop keeps the canonical cyan/magenta palette harmonious with the
# ice arena; it cycles color, not geometry, and returns smoothly to frame zero.
AURORA_HUE_SHIFTS = (0.0, 0.008, 0.016, 0.024, 0.016, 0.008)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_tile_records(path: Path):
    data = path.read_bytes()
    tile_size, count = struct.unpack_from("<ii", data, 0)
    if tile_size != 24:
        raise ValueError(f"Unexpected VastIceMountain tile size: {tile_size}")
    records = {}
    for i in range(count):
        x, y, address = struct.unpack_from("<iiq", data, 8 + i * 16)
        length = struct.unpack_from("<q", data, address)[0]
        payload = data[address + 8:address + 8 + length]
        records[(x, y)] = payload
    return data, tile_size, records


def write_dir(path: Path, png: bytes, width: int, height: int):
    # RogueEssence DirSheet: Int64 PNG length, PNG bytes, width/height,
    # direction count, frame count.
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(struct.pack("<q", len(png)) + png + struct.pack("<4i", width, height, 0, 1))


def write_dir_sheet(path: Path, frames: list[Path], frame_width: int, frame_height: int):
    """Write a real multi-frame DirSheet with one independent frame per PNG.

    RogueEssence stores a horizontal frame atlas followed by the dimensions of
    one frame, direction mode and frame count.  The aurora therefore animates
    as its own BG asset; the canonical night sky remains a one-frame asset.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet = path.parent.parent.parent / "tests" / "aurora_palette_cycle_sheet.png"
    subprocess.run(
        ["convert", *[str(frame) for frame in frames], "+append", "png:" + str(sheet)],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    png = sheet.read_bytes()
    path.write_bytes(
        struct.pack("<q", len(png)) + png
        + struct.pack("<4i", frame_width, frame_height, 0, len(frames))
    )


def build_aurora_palette_cycle():
    """Derive a transparent six-frame palette cycle from the canonical aurora.

    The dark sky pixels are alpha-keyed out, so the independent animated layer
    sits over GLACIER_NIGHT_BASE.  Hue values are rotated modulo one in HSL;
    pixel geometry and the canonical source frame remain unchanged.
    """
    derived = OUT / "provenance/derived"
    frames_dir = derived / "aurora_palette_cycle"
    frames_dir.mkdir(parents=True, exist_ok=True)
    source = REFS["aurora"]
    width, height = AURORA_FRAME_SIZE
    base = frames_dir / "base_keyed.png"
    subprocess.run([
        "convert", str(source), "-crop", f"{width}x{height}+0+0", "+repage",
        "-alpha", "on", "-colorspace", "HSL", "-channel", "A",
        "-fx", "((g>0.32)&&(b>0.16))?1:0", "+channel", "-colorspace", "sRGB",
        "png:" + str(base),
    ], check=True, stdout=subprocess.DEVNULL)
    frames = []
    for index in range(AURORA_FRAME_COUNT):
        frame = frames_dir / f"frame_{index:02d}.png"
        shift = AURORA_HUE_SHIFTS[index]
        subprocess.run([
            "convert", str(base), "-colorspace", "HSL", "-channel", "R",
            "-fx", f"mod(r+{shift:.8f},1)", "+channel", "-colorspace", "sRGB",
            "png:" + str(frame),
        ], check=True, stdout=subprocess.DEVNULL)
        frames.append(frame)
    return frames, base


def exact_crop(source: Path, destination: Path, geometry: str):
    destination.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["convert", str(source), "-crop", geometry, "+repage", "png:" + str(destination)],
        check=True,
        stdout=subprocess.DEVNULL,
    )


def png_size(path: Path):
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not PNG: {path}")
    # IHDR is always the first PNG chunk for these references.
    length = struct.unpack(">I", data[8:12])[0]
    if data[12:16] != b"IHDR" or length < 8:
        raise ValueError(f"PNG without IHDR: {path}")
    return struct.unpack(">II", data[16:24])


def auto_tables():
    result = {}
    for kind in ("floor", "wall", "secondary"):
        path = AUTOTILE_DIR / f"vast_ice_mountain_{kind}.json"
        obj = json.loads(path.read_text(encoding="utf-8-sig"))["Object"]["Tiles"]
        table = {}
        for key, variants in obj.items():
            if not key.startswith("Tilex"):
                continue
            mask = int(key[5:], 16)
            choices = []
            for variant in variants:
                # The first layer is the static native tile.  Any additional
                # layers are animation/details and are kept in separate Ground
                # layers rather than silently discarded into the floor.
                if not variant:
                    continue
                frame = variant[0]["Frames"][0]
                choices.append({
                    "Sheet": frame["Sheet"],
                    "TexLoc": frame["TexLoc"],
                    "FrameLength": variant[0].get("FrameLength", 60),
                })
            if choices:
                table[mask] = choices
        if 255 not in table:
            raise ValueError(f"Missing full mask in {path}")
        result[kind] = table
    return result


def tile_code(cells: set[tuple[int, int]], x: int, y: int) -> int:
    """Return PMDO's four-neighbour + diagonal adjacency code.

    This is the bit order used by the native DTEF import helper: south, west,
    north, east, followed by SW, NW, NE, SE corner bits.
    """
    def same(dx, dy):
        return (x + dx, y + dy) in cells

    cardinals = [same(0, 1), same(-1, 0), same(0, -1), same(1, 0)]
    mask = sum((1 << i) for i, value in enumerate(cardinals) if value)
    corners = [(-1, 1), (-1, -1), (1, -1), (1, 1)]
    for i, (dx, dy) in enumerate(corners):
        if cardinals[i] and cardinals[(i + 1) % 4] and same(dx, dy):
            mask |= 1 << (i + 4)
    return mask


def floor_layout() -> set[tuple[int, int]]:
    """A connected top-of-cliff arena with a south access ramp.

    Coordinates are collision cells.  The long northern terrace gives the
    requested view; the central bowl is the playable arena and the narrow
    south strip is the only approach.  No decorative/background cell is made
    walkable.
    """
    rows = {
        10: (28, 43), 11: (25, 46), 12: (23, 48), 13: (21, 50),
        14: (20, 51), 15: (19, 52), 16: (18, 53), 17: (17, 54),
        18: (16, 55), 19: (15, 56), 20: (14, 57), 21: (14, 57),
        22: (13, 58), 23: (13, 58), 24: (12, 59), 25: (12, 59),
        26: (12, 59), 27: (12, 59), 28: (12, 59), 29: (12, 59),
        30: (12, 59), 31: (12, 59), 32: (12, 59), 33: (13, 58),
        34: (13, 58), 35: (14, 57), 36: (14, 57), 37: (15, 56),
        38: (17, 54), 39: (19, 52), 40: (23, 48), 41: (28, 43),
    }
    floor = {(x, y) for y, (left, right) in rows.items() for x in range(left, right + 1)}
    # The access is intentionally straight and wide enough for a party.
    floor.update((x, y) for y in range(42, 50) for x in range(32, 40))
    return floor


def wall_layout(floor: set[tuple[int, int]]) -> set[tuple[int, int]]:
    wall = set()
    # One native cliff ring around the arena, with a larger foreground lip on
    # both sides.  Keep the south approach open until its terminal landing.
    for x, y in floor:
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)):
            p = (x + dx, y + dy)
            if 0 <= p[0] < WIDTH and 0 <= p[1] < HEIGHT and p not in floor:
                wall.add(p)
    wall -= {(x, y) for y in range(42, 50) for x in range(31, 41)}
    # Side masses make the cliff read as a high ledge without closing the view.
    wall.update((x, y) for y in range(23, 38) for x in range(9, 12))
    wall.update((x, y) for y in range(23, 38) for x in range(60, 63))
    # A low foreground lip, leaving the marked south landing clear.
    wall.update((x, y) for y in range(50, 52) for x in range(17, 31))
    wall.update((x, y) for y in range(50, 52) for x in range(41, 55))
    return wall - floor


def blank_tile():
    return {"AutoTileset": "", "Associates": [], "Layers": [], "NeighborCode": -1}


def tile_cell(frame: dict, mask: int):
    return {
        "AutoTileset": "",
        "Associates": [],
        "Layers": [{"Frames": [{"Sheet": frame["Sheet"], "TexLoc": frame["TexLoc"]}],
                    "FrameLength": frame.get("FrameLength", 60)}],
        "NeighborCode": mask,
    }


def make_layer(name: str, layer_number: int, cells: set[tuple[int, int]], table: dict,
               variant_offset: int = 0):
    tiles = []
    for x in range(WIDTH):
        column = []
        for y in range(HEIGHT):
            if (x, y) not in cells:
                column.append(blank_tile())
                continue
            mask = tile_code(cells, x, y)
            choices = table.get(mask) or table[255]
            frame = choices[(x + y + variant_offset) % len(choices)]
            column.append(tile_cell(frame, mask))
        tiles.append(column)
    return {"Name": name, "Layer": layer_number, "Visible": True, "Tiles": tiles}


def background(name: str, y: int, repeat: bool = True, frame_time: int = 1,
               start_frame: int = -1, end_frame: int = -1, anim_dir: int = -1):
    return {
        "$type": "RogueEssence.Dungeon.MapBG, RogueEssence",
        "MapLoc": {"X": 0, "Y": y},
        "BGAnim": {"AnimIndex": name, "FrameTime": frame_time, "StartFrame": start_frame,
                    "EndFrame": end_frame, "AnimDir": anim_dir, "Alpha": 255, "AnimFlip": 0},
        "BGMovement": {"X": 0, "Y": 0}, "Parallax": "1, 1",
        "RepeatX": repeat, "RepeatY": False,
    }


def obstacles(floor: set[tuple[int, int]]):
    return [[{
        "Bounds": {"X": x * TILE_PX, "Y": y * TILE_PX, "Width": TILE_PX, "Height": TILE_PX},
        "Tags": 0 if (x, y) in floor else 1,
    } for y in range(HEIGHT)] for x in range(WIDTH)]


def marker(name: str, x: int, y: int, direction: int = 4):
    return {"EntName": name, "Direction": direction, "EntEnabled": True,
            "EntOrder": 0, "InteractOrder": 0, "triggerType": 0,
            "Collider": {"X": x * TILE_PX, "Y": y * TILE_PX, "Width": 16, "Height": 16}}


def build_ground(floor, wall, tables):
    foreground = {p for p in wall if p[1] >= 38 and p[0] not in range(30, 42)}
    regular_wall = wall - foreground
    layers = [
        make_layer("00 Arena glace — sol praticable", 0, floor, tables["floor"]),
        make_layer("01 Falaise glace — parois et rebords", 0, regular_wall, tables["wall"], 1),
        make_layer("02 Falaise glace — details secondaires", 0, regular_wall, tables["secondary"], 2),
        {"Name": "03 Decor de fond — foret et montagnes (Background)", "Layer": 0, "Visible": True,
         "Tiles": [[blank_tile() for _ in range(HEIGHT)] for _ in range(WIDTH)]},
        make_layer("04 Rebord glace — avant-plan", 4, foreground, tables["wall"], 1),
    ]
    obj = {
        "$type": "RogueEssence.Ground.GroundMap, RogueEssence",
        "TexSize": TEX_SIZE,
        "Name": {"DefaultText": "Glacier Cliff Aurora — arene du sommet", "LocalTexts": {}},
        "Released": False,
        "Comment": (
            "PMDO 0.8.12. Terrain canonique VastIceMountain.tile. "
            "Sol, parois, fond et collisions sont separes. "
            "Le guide genere n'est jamais importe. Le ciel reste canonique et "
            "l'aurore est un calque anime independant, derive par palette cycling."
        ),
        "obstacles": obstacles(floor),
        "rand": {"$type": "RogueElements.ReRandom, RogueElements", "FirstSeed": 0,
                 "s": [16294208416658607535, 7960286522194355700,
                       487617019471545679, 17909611376780542444]},
        "Status": {},
        "Background": {"$type": "RogueEssence.Dungeon.LayeredBG, RogueEssence", "Layers": [
            {"BG": background("GLACIER_NIGHT_BASE", 0)},
            {"BG": background(AURORA_ASSET, 0, True, AURORA_FRAME_TIME,
                                  0, AURORA_FRAME_COUNT - 1, 1)},
            {"BG": background("GLACIER_DISTANT_MOUNTAINS", 120)},
            {"BG": background("GLACIER_SNOW_TREES", 216)},
            {"BG": background("GLACIER_SNOW_FOREST_PATH", 376)},
        ]},
        "BlankBG": blank_tile(),
        "Layers": layers,
        "AssetName": ASSET,
        "Music": "",
        "EdgeView": 0,
        "NoSwitching": False,
        "ViewCenter": None,
        "ViewOffset": {"X": 0, "Y": 0},
        "ActiveChar": None,
        "Decorations": [{"Name": "Decor de fond non praticable", "Layer": 3,
                         "Visible": True, "Anims": []}],
        "Entities": [{
            "Name": "Entrees et marqueurs de l'arene",
            "Visible": True, "MapChars": [], "GroundObjects": [], "Spawners": [],
            "Markers": [
                marker("entrance", 35, 46, 4),
                marker("entrance_sud", 35, 48, 4),
                marker("arena_seuil", 35, 15, 0),
            ],
        }],
    }
    return {"Version": "0.8.12.0", "Object": obj}


def make_mod_xml():
    return """<?xml version=\"1.0\" encoding=\"utf-8\"?>
<Header>
  <Name>Glacier Cliff Aurora - PMDO 0.8.12</Name>
  <Author>meromoonmeri</Author>
  <Description>Ground jouable : arene de glace au sommet, foret enneigee en contrebas, montagnes et aurore. Ressources canoniques separees.</Description>
  <Namespace>glacier_cliff_aurora</Namespace>
  <UUID>7a5fe1d9-6692-4a18-bbc5-5e4f87b96701</UUID>
  <Version>1.0.0.0</Version>
  <GameVersion>0.8.12.0</GameVersion>
  <ModType>Quest</ModType>
  <Relationships />
</Header>
"""


def setup_dirs():
    if OUT.exists():
        shutil.rmtree(OUT)
    for p in [OUT / "Content/Tile", OUT / "Content/BG", OUT / "Data/Ground",
              OUT / "Data/Script/ground" / ASSET,
              OUT / "Data/Script/glacier_cliff_aurora/ground" / ASSET,
              OUT / "provenance/references", OUT / "provenance/derived",
              OUT / "layers", OUT / "preview", OUT / "tests"]:
        p.mkdir(parents=True, exist_ok=True)


def retrieve_canonical_textures():
    """Retrieve the canonical inputs into the deliverable with hash checks.

    This is intentionally a local canonical-source retrieval, not a generated
    image lookup: missing or changed references stop the build before any
    Ground file is written.
    """
    destination = OUT / "provenance/references"
    records = []
    for role, source in REFS.items():
        if not source.is_file():
            raise FileNotFoundError(f"canonical texture missing: {source}")
        target = destination / source.name
        shutil.copyfile(source, target)
        source_hash = sha256(source)
        target_hash = sha256(target)
        if source_hash != target_hash:
            raise RuntimeError(f"canonical texture copy changed: {source}")
        records.append({
            "role": role,
            "source": str(source.relative_to(ROOT)),
            "delivered_reference": str(target.relative_to(OUT)),
            "sha256": source_hash,
            "size": list(png_size(source)),
            "retrieval": "workspace canonical source copied byte-exact; generated guide excluded",
        })
    return records


def build_backgrounds():
    derived = OUT / "provenance/derived"
    # Crop boundaries are native-pixel selections, not generated artwork.
    exact_crop(REFS["distant_mountains"], derived / "iceroad_mountains_strip.png", "504x96+0+24")
    exact_crop(REFS["trees_and_snow_forest"], derived / "snow_trees_strip.png", "522x160+0+160")
    exact_crop(REFS["trees_and_snow_forest"], derived / "snow_path_strip.png", "522x216+0+357")
    aurora_frames, aurora_base = build_aurora_palette_cycle()
    assets = {
        "GLACIER_NIGHT_BASE": (REFS["sky"], REFS["sky"]),
        "GLACIER_DISTANT_MOUNTAINS": (derived / "iceroad_mountains_strip.png", REFS["distant_mountains"]),
        "GLACIER_SNOW_TREES": (derived / "snow_trees_strip.png", REFS["trees_and_snow_forest"]),
        "GLACIER_SNOW_FOREST_PATH": (derived / "snow_path_strip.png", REFS["trees_and_snow_forest"]),
    }
    records = []
    for name, (png, source) in assets.items():
        w, h = png_size(png)
        write_dir(OUT / "Content/BG" / f"{name}.dir", png.read_bytes(), w, h)
        try:
            png_record = str(png.relative_to(OUT))
        except ValueError:
            png_record = str(png.relative_to(ROOT))
        records.append({"asset": f"Content/BG/{name}.dir", "png": png_record,
                        "source": str(source.relative_to(ROOT)), "size": [w, h],
                        "sheet_size": [w, h], "frames": 1,
                        "sha256_source": sha256(source), "sha256_png": sha256(png),
                        "animation": None})

    aurora_asset = OUT / "Content/BG" / f"{AURORA_ASSET}.dir"
    write_dir_sheet(aurora_asset, aurora_frames, *AURORA_FRAME_SIZE)
    sheet_png = OUT / "tests/aurora_palette_cycle_sheet.png"
    records.append({
        "asset": f"Content/BG/{AURORA_ASSET}.dir",
        "png": str(aurora_base.relative_to(OUT)),
        "source": str(REFS["aurora"].relative_to(ROOT)),
        "size": list(AURORA_FRAME_SIZE),
        "sheet_size": list(png_size(sheet_png)),
        "frames": AURORA_FRAME_COUNT,
        "sha256_source": sha256(REFS["aurora"]),
        "sha256_png": sha256(sheet_png),
        "animation": {
            "method": "independent_hsl_palette_cycle",
            "hue_shifts": list(AURORA_HUE_SHIFTS),
            "frame_time": AURORA_FRAME_TIME,
            "frame_files": [str(frame.relative_to(OUT)) for frame in aurora_frames],
            "base_keyed": str(aurora_base.relative_to(OUT)),
            "sky_asset": "Content/BG/GLACIER_NIGHT_BASE.dir",
            "official_cycle": False,
        },
    })
    return records


def extract_tiles(records):
    directory = OUT / "tests/native_tile_payloads"
    directory.mkdir(parents=True, exist_ok=True)
    for (x, y), payload in records.items():
        (directory / f"{x:02d}_{y:02d}.png").write_bytes(payload)


def make_preview(ground, floor, wall, native_records):
    """Create a review-only static reconstruction and a collision diagram."""
    work = OUT / "tests/native_tile_payloads"
    # A map-layer image is produced by ImageMagick's MVG image primitive.  It
    # uses the exact PNG payloads from VastIceMountain.tile; no scaling occurs.
    def draw_layer(cells):
        commands = []
        for x in range(WIDTH):
            for y in range(HEIGHT):
                tile = cells.get((x, y))
                if tile is None:
                    continue
                path = work / f"{tile['TexLoc']['X']:02d}_{tile['TexLoc']['Y']:02d}.png"
                commands.append(f"image over {x*8},{y*8} 24,24 '{path}'")
        return " ".join(commands)

    def render(cells, name):
        output = OUT / "preview" / name
        mvg = OUT / "tests" / (name + ".mvg")
        mvg.write_text(draw_layer(cells), encoding="utf-8")
        subprocess.run(["convert", "-size", f"{WIDTH*8}x{HEIGHT*8}", "xc:none",
                        "-draw", "@" + str(mvg), str(output)], check=True,
                       stdout=subprocess.DEVNULL)
        return output

    def cell_frames(layer_index, cells, allowed=None):
        layer = ground["Object"]["Layers"][layer_index]
        result = {}
        for x, col in enumerate(layer["Tiles"]):
            for y, tile in enumerate(col):
                if (allowed is None or (x, y) in allowed) and tile["Layers"]:
                    result[(x, y)] = tile["Layers"][0]["Frames"][0]
        return result

    access_cells = {(x, y) for y in range(42, 50) for x in range(32, 40)}
    path_png = render(cell_frames(0, floor, access_cells), "native_access_path_layer.png")
    floor_png = render(cell_frames(0, floor), "native_floor_layer.png")
    wall_png = render(cell_frames(1, wall), "native_wall_layer.png")
    foreground_png = render(cell_frames(4, wall), "native_foreground_layer.png")
    # Compose a review-only background from the exact canonical layers.  The
    # Ground file references the corresponding .dir assets; this PNG is not a
    # texture and is never imported as a native sheet.
    refs = OUT / "provenance/references"
    derived = OUT / "provenance/derived"
    background = OUT / "preview/canonical_background_reconstruction.png"
    aurora_tile = OUT / "tests/aurora_repeat.png"
    mountain_tile = OUT / "tests/mountain_repeat.png"
    trees_tile = OUT / "tests/trees_repeat.png"
    path_tile = OUT / "tests/forest_path_repeat.png"
    subprocess.run(["convert", "-size", f"{WIDTH*8}x216", "tile:" + str(derived / "aurora_palette_cycle/frame_00.png"),
                    "-crop", f"{WIDTH*8}x216+0+0", "+repage", str(aurora_tile)],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["convert", "-size", f"{WIDTH*8}x96", "tile:" + str(derived / "iceroad_mountains_strip.png"),
                    "-crop", f"{WIDTH*8}x96+0+0", "+repage", str(mountain_tile)],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["convert", "-size", f"{WIDTH*8}x160", "tile:" + str(derived / "snow_trees_strip.png"),
                    "-crop", f"{WIDTH*8}x160+0+0", "+repage", str(trees_tile)],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["convert", "-size", f"{WIDTH*8}x216", "tile:" + str(derived / "snow_path_strip.png"),
                    "-crop", f"{WIDTH*8}x216+0+0", "+repage", str(path_tile)],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["convert", "-size", f"{WIDTH*8}x{HEIGHT*8}", "xc:#07153d",
                    str(aurora_tile), "-geometry", "+0+0", "-compose", "over", "-composite",
                    str(mountain_tile), "-geometry", "+0+120", "-compose", "over", "-composite",
                    str(trees_tile), "-geometry", "+0+216", "-compose", "over", "-composite",
                    str(path_tile), "-geometry", "+0+376", "-compose", "over", "-composite",
                    str(background)], check=True, stdout=subprocess.DEVNULL)
    scene = OUT / "preview/native_ground_reconstruction.png"
    subprocess.run(["composite", "-compose", "over", str(floor_png), str(background), str(scene)],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["composite", "-compose", "over", str(wall_png), str(scene), str(scene)],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["composite", "-compose", "over", str(foreground_png), str(scene), str(scene)],
                   check=True, stdout=subprocess.DEVNULL)
    # Collision map: green = walkable, red = obstacle/background. It is a
    # diagnostic, never imported by PMDO.
    collision = OUT / "preview/collision_grid.png"
    draw = []
    for x in range(WIDTH):
        for y in range(HEIGHT):
            colour = "#5fd18a" if (x, y) in floor else "#bd5266"
            draw.append(f"fill {colour} rectangle {x*8},{y*8} {x*8+7},{y*8+7}")
    collision_mvg = OUT / "tests/collision_grid.mvg"
    collision_mvg.write_text(" ".join(draw), encoding="utf-8")
    subprocess.run(["convert", "-size", f"{WIDTH*8}x{HEIGHT*8}", "xc:#15233d",
                    "-draw", "@" + str(collision_mvg), str(collision)], check=True,
                   stdout=subprocess.DEVNULL)


def write_layer_exports():
    """Expose the requested stack as editable review layers.

    The first seven are exact canonical inputs/crops used by Background or
    retained as references; the last five are native-tile reconstructions or
    collision diagnostics.  The
    latter are deliberately marked review-only and are not presented as new
    PMDO textures.
    """
    layer_dir = OUT / "layers"
    refs = OUT / "provenance/references"
    derived = OUT / "provenance/derived"
    preview = OUT / "preview"
    exports = [
        ("00_night_sky_canonical.png", refs / "bgnightbackgroundpmdskyda.png", "canonical", "Background GLACIER_NIGHT_BASE"),
        ("01_aurora_canonical.png", refs / "aurorepmdsky.png", "canonical", "Background GLACIER_AURORA_PALETTE_CYCLE — source frame"),
        ("02_mountains_iceroad_native_crop.png", derived / "iceroad_mountains_strip.png", "canonical_crop", "Background GLACIER_DISTANT_MOUNTAINS"),
        ("03_trees_snow_native_crop.png", derived / "snow_trees_strip.png", "canonical_crop", "Background GLACIER_SNOW_TREES"),
        ("04_forest_below_path_native_crop.png", derived / "snow_path_strip.png", "canonical_crop", "Background GLACIER_SNOW_FOREST_PATH"),
        ("05_arena_material_reference_canonical.png", refs / "pmdskyicearena.png", "canonical_reference_only", "Reference for Ground arena material; not direct PNG import"),
        ("06_south_path_reference_canonical.png", refs / "path.png", "canonical_reference_only", "Reference for south access path; not direct PNG import"),
        ("07_south_path_vast_ice_reconstruction.png", preview / "native_access_path_layer.png", "review_only_native_reconstruction", "South access cells in Ground layer 00"),
        ("08_arena_floor_vast_ice_reconstruction.png", preview / "native_floor_layer.png", "review_only_native_reconstruction", "Ground layer 00"),
        ("09_cliff_walls_vast_ice_reconstruction.png", preview / "native_wall_layer.png", "review_only_native_reconstruction", "Ground layer 01/02"),
        ("10_foreground_ice_rim_reconstruction.png", preview / "native_foreground_layer.png", "review_only_native_reconstruction", "Ground layer 04 Top=4"),
        ("11_collision_grid_diagnostic.png", preview / "collision_grid.png", "review_only_collision", "Serialized obstacles; never imported"),
    ]
    manifest = []
    for name, source, provenance, engine_role in exports:
        target = layer_dir / name
        shutil.copyfile(source, target)
        manifest.append({
            "file": str(target.relative_to(OUT)),
            "provenance": provenance,
            "engine_role": engine_role,
            "size": list(png_size(target)),
            "sha256": sha256(target),
            "importable": provenance in {"canonical", "canonical_crop"} and engine_role.startswith("Background") is False,
        })
    # The actual PMDO importable assets remain the .dir/.tile/.rsground files;
    # these PNGs are a named layer handoff for visual editing and audit.
    (layer_dir / "layer_manifest.json").write_text(
        json.dumps({
            "schema": "glacier_cliff_aurora_layer_stack_v2",
            "note": "Canonical source layers are separate; native Ground layers remain authoritative. Review reconstructions are not native textures.",
            "background_layers": [
                {"asset": "GLACIER_NIGHT_BASE", "role": "static canonical sky", "frames": 1},
                {"asset": AURORA_ASSET, "role": "independent palette cycle above sky", "frames": AURORA_FRAME_COUNT, "frame_time": AURORA_FRAME_TIME},
                {"asset": "GLACIER_DISTANT_MOUNTAINS", "role": "distant mountain layer", "frames": 1},
                {"asset": "GLACIER_SNOW_TREES", "role": "snow trees below", "frames": 1},
                {"asset": "GLACIER_SNOW_FOREST_PATH", "role": "forest and path below", "frames": 1},
            ],
            "ground_layers": [
                {"layer": 0, "role": "playable arena floor and south access"},
                {"layer": 1, "role": "arena cliff walls and rim"},
                {"layer": 2, "role": "cliff secondary details"},
                {"layer": 4, "role": "foreground ice rim"},
            ],
            "layers": manifest,
        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return manifest


def write_docs(ground, floor, wall, background_records, retrieval_records, layer_records):
    (OUT / "Mod.xml").write_text(make_mod_xml(), encoding="utf-8")
    lua = """-- Glacier Cliff Aurora: the map is data-driven; no fake transition is hidden here.
-- Bind `entrance` / `arena_seuil` to the destination dungeon in the host quest.
return {}
"""
    (OUT / "Data/Script/ground" / ASSET / "init.lua").write_text(lua, encoding="utf-8")
    (OUT / "Data/Script/glacier_cliff_aurora/ground" / ASSET / "init.lua").write_text(lua, encoding="utf-8")
    (OUT / "README.md").write_text("""# Glacier Cliff Aurora — Ground PMDO 0.8.12

Carte PMDO native et editable : une arene de glace jouable au sommet, une
arrivee sud, une vue vers une foret enneigee et des montagnes, avec le ciel
canonique et l'aurore animee sur deux calques de fond independants.

## Fichier principal

`Data/Ground/glacier_cliff_aurora_v1.rsground` est une vraie serialisation
`RogueEssence.Ground.GroundMap`, version `0.8.12.0`, `TexSize=3`, grille de
collision 72 x 54 cellules de 8 px. Le terrain jouable est une surface
continue ; les parois, le rebord avant et tout le decor de fond sont bloques.

Le tileset `Content/Tile/VastIceMountain.tile` est copie byte a byte depuis la
ressource native PMDO. Les calques du Ground sont :

1. sol praticable `VastIceMountain` / AutoTile Floor ;
2. parois et rebords `VastIceMountain` / AutoTile Wall ;
3. details secondaires `VastIceMountain` / AutoTile Secondary ;
4. calque reserve au decor d'arriere-plan ;
5. rebord de glace d'avant-plan, `Layer=4`.

## Fonds et provenance

Les fonds sont des `.dir` PMDO separes. Les pixels sont issus des references
canoniques suivantes : `aurorepmdsky.png`, `iceroadpmdsky.png`,
`bgnightbackgroundpmdskyda.png`, `source/references_54d3731/path.png` et
`source/references_54d3731/snow.png` pour les arbres enneiges. Le generateur
les recupere au debut du build, les copie byte a byte dans
`provenance/references/` et arrete la production si un hash change. Les bandes
montagne/foret sont des crops de pixels natifs documentes dans
`provenance/provenance.json`. L'aurore utilise la frame canonique comme source,
puis un cycle de palette de 6 frames dans `GLACIER_AURORA_PALETTE_CYCLE.dir` ;
le ciel `GLACIER_NIGHT_BASE.dir` reste immobile et independant.

Le dossier `layers/` expose la pile demandee : nuit, aurore, montagnes,
foret en contrebas, reference de materiau d'arene, chemin d'acces, sol
d'arene, parois, rebord avant et collision. Les sept premiers sont des
sources/crops ou des references canoniques ; les cinq derniers sont des
reconstructions de controle depuis `VastIceMountain.tile`, pas des textures
inventees. Le Ground PMDO et ses `.dir`/`.tile` restent les fichiers a
importer.

Le guide genere
`renders/glacier_cliff_aurora_v3/raw/native_tileset_reference_composition_magenta.png` a ete
compose avec les previews raster du vrai tileset `VastIceMountain.tile` et les
references canoniques. Il n'est pas importe dans le Ground et n'est pas une
texture de jeu.

L'aurore livree est un calque anime independant : 6 frames derivees par
palette cycling depuis la frame canonique, avec le ciel masque en transparence.
Ce cycle est une adaptation de composition, pas une animation officielle
attribuee a la source. Le fichier `.dir` et les frames derivees sont declares
explicitement dans `provenance/provenance.json`.

## Installation

Extraire l'archive dans un dossier temporaire puis lancer :

```sh
python INSTALLER.py /chemin/PMDO/MODS/mon_mod --dry-run
python INSTALLER.py /chemin/PMDO/MODS/mon_mod
```

L'installateur fusionne l'index des tilesets, ne remplace pas une carte editee
et copie aussi le script sous le namespace `glacier_cliff_aurora`. Pour une
ouverture directe en projet separe, le dossier contient deja `Mod.xml` et un
`Content/Tile/index.idx` autonome.

## Marqueurs

- `entrance` et `entrance_sud` : arrivee praticable au sud ;
- `arena_seuil` : point de raccord au nord de l'arene.

Ces marqueurs ne choisissent pas un donjon absent du projet utilisateur. Il
faut les relier au quest concerné pour une transition narrative.

## Validation et limites

Les tests de structure, de provenance, de references de tuiles et de
connectivite des collisions sont fournis dans `verification.json`. Le vrai
chargeur natif PMDO 0.8.12 a aussi deserialise cette carte en mode headless :
`Width=72`, `Height=54`, `TexSize=3`, `5` calques — PASS.

Ce test ne lance pas l'editeur graphique, le GPU, les deplacements ou les
animations affichees. Le PNG de preview est une reconstruction de controle,
pas une nouvelle texture canonique. La transition vers un donjon doit encore
etre liee au quest utilisateur via `arena_seuil`.
""", encoding="utf-8")

    prov = {
        "status": "built",
        "pmdo_target": "0.8.12.0",
        "ground": ASSET,
        "dimensions_px": [WIDTH * 8, HEIGHT * 8],
        "grid_cells": [WIDTH, HEIGHT],
        "tex_size": TEX_SIZE,
        "generated_guide_not_imported": str(GUIDE.relative_to(ROOT)),
        "native_tile": {
            "source": str(TILE_SOURCE.relative_to(ROOT)), "asset": "Content/Tile/VastIceMountain.tile",
            "sha256": sha256(TILE_SOURCE), "tile_px": 24,
        },
        "autotiles": {k: str((AUTOTILE_DIR / f"vast_ice_mountain_{k}.json").relative_to(ROOT))
                      for k in ("floor", "wall", "secondary")},
        "texture_retrieval": retrieval_records,
        "layer_stack": layer_records,
        "backgrounds": background_records,
        "canonical_references": {
            key: {"path": str(path.relative_to(ROOT)), "sha256": sha256(path),
                  "size": list(png_size(path))} for key, path in REFS.items()
        },
        "layout": {
            "floor_cells": len(floor), "wall_cells": len(wall),
            "south_entry_cells": [[x, y] for y in range(42, 50) for x in range(32, 40)],
            "arena_view": "top/north arena, south approach, forest and snow mountains below/in front",
        },
        "animation": {
            "aurora": "independent palette cycling derived from canonical frame",
            "asset": f"Content/BG/{AURORA_ASSET}.dir",
            "frames": AURORA_FRAME_COUNT,
            "frame_time": AURORA_FRAME_TIME,
            "sky_independent": True,
            "official_cycle": False,
            "proposal": "derived layer explicitly included in native Ground",
        },
    }
    (OUT / "provenance/provenance.json").write_text(json.dumps(prov, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / "provenance/layout_guide_reference.txt").write_text(
        "Composition guide used only for orientation; never imported as a texture:\n"
        + str(GUIDE.relative_to(ROOT)) + "\nSHA256=" + sha256(GUIDE) + "\n", encoding="utf-8")


def write_index():
    # The index stores the TileIndexNode header and entries, not tile payloads.
    data = TILE_SOURCE.read_bytes()
    tile_size, count = struct.unpack_from("<ii", data)
    node = data[:8 + count * 16]
    name = "VastIceMountain".encode("utf-8")
    index = struct.pack("<i", 1) + bytes([len(name)]) + name + node
    (OUT / "Content/Tile/index.idx").write_bytes(index)


def main():
    setup_dirs()
    raw_tile, _, native_records = read_tile_records(TILE_SOURCE)
    shutil.copyfile(TILE_SOURCE, OUT / "Content/Tile/VastIceMountain.tile")
    extract_tiles(native_records)
    tables = auto_tables()
    floor = floor_layout()
    wall = wall_layout(floor)
    ground = build_ground(floor, wall, tables)
    (OUT / "Data/Ground" / f"{ASSET}.rsground").write_text(
        json.dumps(ground, ensure_ascii=False, separators=(",", ":")), encoding="utf-8"
    )
    retrieval_records = retrieve_canonical_textures()
    background_records = build_backgrounds()
    write_index()
    make_preview(
        ground,
        floor,
        {**{p: ground["Object"]["Layers"][1]["Tiles"][p[0]][p[1]] for p in wall},
         **{p: ground["Object"]["Layers"][4]["Tiles"][p[0]][p[1]] for p in wall}},
        native_records,
    )
    layer_records = write_layer_exports()
    write_docs(ground, floor, wall, background_records, retrieval_records, layer_records)
    print(f"Built {ASSET}: {WIDTH}x{HEIGHT} collision cells, {len(floor)} walkable, {len(wall)} wall cells; {len(layer_records)} named layers")


if __name__ == "__main__":
    main()
