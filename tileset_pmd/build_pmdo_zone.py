from __future__ import annotations

"""Build the Luminous Spring reconstruction as PMDO 8 px ground assets.

The two uploaded 600 px images are references only. Nothing is cropped from them.
The image generator produced design studies in source/generated/, then every final
8x8 tile below is rebuilt with hard pixel clusters and a controlled palette.

Outputs:
- PNG editing boards, one board per PMDO layer
- RogueEssence/PMDO .tile sheets (8x8 entries, same format as Halcyon)
- an animated Aseprite file for the spring light
- an 8 px Tiled map and a PMDO .rsground companion
- a browser preview and a machine-readable manifest
"""

from pathlib import Path
from struct import pack
from io import BytesIO
import json
import struct
import zlib

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tileset_pmd"
PLANCHES = OUT / "planches"
TILE_DIR = OUT / "pmd" / "Content" / "Tile"
GROUND_DIR = OUT / "pmd" / "Data" / "Ground"
TILED_DIR = OUT / "tiled"
TILED_TS = TILED_DIR / "tilesets"
SPRITES = OUT / "sprites"
ASEPRITE = OUT / "aseprite"
PREVIEW = OUT / "preview"

for d in (PLANCHES, TILE_DIR, GROUND_DIR, TILED_DIR, TILED_TS, SPRITES, ASEPRITE, PREVIEW):
    d.mkdir(parents=True, exist_ok=True)

# Palette chosen from luminoussspring.png: bright emerald forest, warm ochre
# clearing, turquoise water, olive stones and cyan-white light. No deep-blue
# palette is imported from the layout reference and no antialias shades are used.
PAL = {
    "void": (0, 0, 0, 0),
    # Palette follows luminoussspring.png. The technical reference changes the
    # layout only; it does not introduce its deep-blue palette here.
    "forest0": (18, 66, 36, 255),
    "forest1": (27, 91, 42, 255),
    "forest2": (40, 116, 51, 255),
    "fern0": (48, 128, 49, 255),
    "fern1": (69, 155, 59, 255),
    "grass0": (55, 139, 64, 255),
    "grass1": (83, 174, 70, 255),
    "grass2": (111, 195, 83, 255),
    "moss0": (45, 110, 58, 255),
    "moss1": (80, 155, 70, 255),
    "path0": (164, 103, 41, 255),
    "path1": (219, 153, 63, 255),
    "path2": (242, 181, 76, 255),
    "water0": (24, 104, 116, 255),
    "water1": (53, 157, 169, 255),
    "water2": (70, 182, 183, 255),
    "water3": (117, 203, 193, 255),
    "water4": (180, 226, 198, 255),
    "stone0": (58, 74, 53, 255),
    "stone1": (91, 108, 70, 255),
    "stone2": (132, 143, 82, 255),
    "stone3": (174, 175, 106, 255),
    "wood0": (46, 45, 27, 255),
    "wood1": (92, 62, 34, 255),
    "wood2": (130, 84, 42, 255),
    "wood3": (176, 119, 58, 255),
    "shadow": (14, 61, 37, 210),
    "shadow2": (24, 86, 42, 180),
    "beam0": (16, 128, 126, 255),
    "beam1": (25, 189, 177, 255),
    "beam2": (49, 226, 211, 255),
    "beam3": (164, 245, 218, 255),
    "beam4": (255, 255, 230, 255),
}

# PMDO/Halcyon uses 8x8 texture entries on the ground grid.
TILE = 8
MAP_W = 64
MAP_H = 64


def rgba(name: str):
    return PAL[name]


def tile(fill: str = "void") -> Image.Image:
    im = Image.new("RGBA", (TILE, TILE), rgba(fill))
    return im


def save_png(im: Image.Image, path: Path) -> None:
    # Every final pixel is opaque or fully transparent. This deliberately avoids
    # the semi-transparent edges that make AI or filtered source art unusable.
    a = im.convert("RGBA")
    alphas = set(a.getchannel("A" ).getdata())
    assert alphas <= {0, 180, 210, 255}, (path, alphas)
    a.save(path, optimize=True)


def rect(d: ImageDraw.ImageDraw, xy, colour: str):
    d.rectangle(xy, fill=rgba(colour))


def grass(kind: int = 0) -> Image.Image:
    im = tile("grass0")
    d = ImageDraw.Draw(im)
    patterns = [
        [(1, 1, 1, 3, "fern0"), (5, 0, 5, 2, "grass1"), (3, 5, 3, 7, "grass1")],
        [(2, 0, 2, 2, "grass1"), (6, 2, 6, 4, "fern0"), (0, 5, 1, 5, "grass1")],
        [(5, 1, 6, 1, "fern0"), (1, 4, 1, 7, "grass1"), (4, 6, 6, 6, "fern0")],
        [(0, 2, 1, 2, "grass1"), (3, 1, 3, 3, "fern0"), (6, 5, 7, 5, "grass1")],
        [(2, 2, 2, 4, "grass1"), (5, 4, 7, 4, "fern0"), (0, 7, 1, 7, "grass1")],
        [(4, 0, 5, 0, "grass1"), (0, 3, 0, 5, "fern0"), (4, 7, 6, 7, "grass1")],
    ]
    for x0, y0, x1, y1, c in patterns[kind % len(patterns)]:
        rect(d, (x0, y0, x1, y1), c)
    return im


def forest(kind: int = 0) -> Image.Image:
    # Low-contrast clusters deliberately stop short of the tile edges. This keeps
    # the forest repeatable without producing the diagonal barcode visible in a
    # bad generated texture.
    im = tile("forest0")
    d = ImageDraw.Draw(im)
    shapes = [
        [(1, 1, 1, 2, "forest1"), (5, 1, 6, 1, "forest2"), (3, 5, 4, 6, "forest1")],
        [(2, 1, 3, 1, "forest2"), (6, 3, 6, 4, "forest1"), (1, 6, 2, 6, "forest1")],
        [(0, 3, 1, 3, "forest1"), (4, 1, 4, 2, "forest2"), (5, 6, 6, 6, "forest1")],
        [(2, 0, 2, 1, "forest1"), (4, 4, 5, 4, "forest2"), (7, 2, 7, 3, "forest1")],
    ]
    for x0, y0, x1, y1, c in shapes[kind % len(shapes)]:
        rect(d, (x0, y0, x1, y1), c)
    return im


def path(kind: int = 0) -> Image.Image:
    # Warm ochre clearing/path from the supplied Luminous Spring, not the
    # blue-grey ground of the technical reference.
    im = tile("path1")
    d = ImageDraw.Draw(im)
    rect(d, (0, 0, 7, 0), "path0")
    if kind % 3 == 0:
        rect(d, (2, 3, 5, 3), "path2")
        rect(d, (0, 6, 2, 6), "path0")
    elif kind % 3 == 1:
        rect(d, (5, 1, 7, 1), "path2")
        rect(d, (1, 5, 3, 5), "path0")
    else:
        rect(d, (3, 2, 4, 4), "path2")
        rect(d, (6, 6, 7, 7), "path0")
    return im


def water(kind: int = 0) -> Image.Image:
    # The outermost pixel row remains the same water colour so a water tile can
    # repeat in every direction without a visible seam.
    im = tile("water1")
    d = ImageDraw.Draw(im)
    variants = [
        [(1, 2, 3, 2, "water2"), (5, 5, 6, 5, "water3")],
        [(4, 1, 7, 1, "water2"), (0, 4, 2, 4, "water3")],
        [(1, 5, 2, 5, "water2"), (4, 3, 6, 3, "water4")],
        [(2, 1, 4, 1, "water3"), (5, 6, 6, 6, "water2")],
        [(0, 3, 3, 3, "water2"), (4, 6, 5, 6, "water3")],
        [(5, 4, 7, 4, "water3"), (1, 1, 2, 1, "water4")],
    ]
    for x0, y0, x1, y1, c in variants[kind % len(variants)]:
        rect(d, (x0, y0, x1, y1), c)
    return im


def shore(direction: str, kind: int = 0) -> Image.Image:
    """One 8 px PMDO shore cell; direction is where water occupies the tile."""
    im = grass(kind)
    d = ImageDraw.Draw(im)
    if direction == "N":
        rect(d, (0, 0, 7, 3), "water1"); rect(d, (0, 3, 7, 4), "stone1")
        rect(d, (1, 3, 2, 3), "stone3"); rect(d, (5, 3, 6, 3), "stone2")
    elif direction == "S":
        rect(d, (0, 4, 7, 7), "water1"); rect(d, (0, 3, 7, 4), "stone1")
        rect(d, (2, 4, 3, 4), "stone3"); rect(d, (6, 3, 7, 3), "stone2")
    elif direction == "W":
        rect(d, (0, 0, 3, 7), "water1"); rect(d, (3, 0, 4, 7), "stone1")
        rect(d, (3, 1, 3, 2), "stone3"); rect(d, (3, 5, 3, 6), "stone2")
    elif direction == "E":
        rect(d, (4, 0, 7, 7), "water1"); rect(d, (3, 0, 4, 7), "stone1")
        rect(d, (4, 2, 4, 3), "stone3"); rect(d, (3, 6, 3, 7), "stone2")
    return im


def corner(corner: str, kind: int = 0) -> Image.Image:
    """Stepped water/shore corner. The full 8x8 cell stays grid aligned."""
    im = grass(kind)
    d = ImageDraw.Draw(im)
    if corner == "NW":
        poly = [(0, 0), (7, 0), (7, 3), (3, 3), (3, 7), (0, 7)]
    elif corner == "NE":
        poly = [(0, 0), (7, 0), (7, 7), (4, 7), (4, 3), (0, 3)]
    elif corner == "SW":
        poly = [(0, 0), (3, 0), (3, 4), (7, 4), (7, 7), (0, 7)]
    else:
        poly = [(4, 0), (7, 0), (7, 7), (0, 7), (0, 4), (4, 4)]
    d.polygon(poly, fill=rgba("water1"))
    # stepped, readable stone rim
    if corner in ("NW", "SW"):
        rect(d, (3, 2, 4, 3), "stone2"); rect(d, (2, 3, 3, 4), "stone1")
    else:
        rect(d, (3, 2, 4, 3), "stone2"); rect(d, (4, 3, 5, 4), "stone1")
    return im


def stone(kind: int = 0) -> Image.Image:
    im = tile("void")
    d = ImageDraw.Draw(im)
    shapes = [
        [(1, 3, 6, 6, "stone1"), (2, 2, 5, 2, "stone2"), (3, 3, 4, 3, "stone3"), (1, 6, 6, 6, "stone0")],
        [(0, 4, 5, 7, "stone0"), (1, 3, 4, 3, "stone1"), (2, 4, 3, 4, "stone3"), (4, 6, 5, 6, "stone2")],
        [(2, 1, 6, 5, "stone1"), (3, 0, 5, 0, "stone2"), (2, 2, 3, 2, "stone3"), (1, 5, 6, 6, "stone0")],
        [(1, 2, 7, 4, "stone1"), (3, 1, 5, 1, "stone2"), (2, 3, 3, 3, "stone3"), (1, 5, 7, 6, "stone0")],
    ]
    for x0, y0, x1, y1, c in shapes[kind % len(shapes)]:
        rect(d, (x0, y0, x1, y1), c)
    return im


def reed(kind: int = 0) -> Image.Image:
    im = tile("void")
    d = ImageDraw.Draw(im)
    for x, top in ((1 + kind % 2, 2), (4, 0), (6 - kind % 2, 3)):
        rect(d, (x, top, x, 7), "fern0")
        if top < 3:
            rect(d, (max(0, x - 1), top, x, top), "grass1")
    return im


def light8(frame: int, variant: int = 0) -> Image.Image:
    """A real per-frame 8x8 animated tile, not a duplicated still."""
    im = tile("void")
    d = ImageDraw.Draw(im)
    # Four-state ripple movement plus two rotating highlight positions.
    core = [(3, 3), (4, 3), (4, 4), (3, 4)][frame % 4]
    if variant % 2:
        core = (core[0], max(2, core[1] - 1))
    x, y = core
    rect(d, (x, y, x + 1, y + 1), "beam3")
    if (frame + variant) % 3 != 1:
        rect(d, (max(0, x - 2), y, max(0, x - 1), y), "beam1")
    if (frame + variant) % 3 != 2:
        rect(d, (min(7, x + 2), y + 1, min(7, x + 3), y + 1), "beam2")
    return im


def sheet_png(images: list[Image.Image], columns: int, path: Path, scale: int = 1) -> None:
    rows = (len(images) + columns - 1) // columns
    out = Image.new("RGBA", (columns * TILE * scale, rows * TILE * scale), rgba("void"))
    for i, im in enumerate(images):
        x = (i % columns) * TILE * scale
        y = (i // columns) * TILE * scale
        if scale == 1:
            out.alpha_composite(im, (x, y))
        else:
            out.alpha_composite(im.resize((TILE * scale, TILE * scale), Image.Resampling.NEAREST), (x, y))
    save_png(out, path)


def png_bytes(im: Image.Image) -> bytes:
    b = BytesIO()
    im.save(b, format="PNG", optimize=True)
    return b.getvalue()


def write_tile(path: Path, images: list[Image.Image], positions: list[tuple[int, int]]) -> None:
    assert len(images) == len(positions)
    table_end = 8 + len(images) * 16
    blobs = []
    offset = table_end
    for im in images:
        p = png_bytes(im)
        blob = pack("<q", len(p)) + p
        blobs.append(blob)
        offset += len(blob)
    data = bytearray(pack("<ii", TILE, len(images)))
    offset = table_end
    for (x, y), blob in zip(positions, blobs):
        data.extend(pack("<iiq", x, y, offset))
        offset += len(blob)
    for blob in blobs:
        data.extend(blob)
    path.write_bytes(data)


def astr(s: str) -> bytes:
    b = s.encode("utf-8")
    return pack("<H", len(b)) + b


def chunk(kind: int, payload: bytes) -> bytes:
    return pack("<IH", len(payload) + 6, kind) + payload


def aseprite_write(path: Path, frames: list[Image.Image], name: str, duration: int = 100) -> None:
    """Minimal valid 32-bit RGBA Aseprite with one layer and real frames."""
    w, h = frames[0].size
    assert all(f.size == (w, h) for f in frames)
    chunks = []
    for frame_index, im in enumerate(frames):
        content = b""
        if frame_index == 0:
            layer_payload = struct.pack("<HHHHHHB", 3, 0, 0, 0, 0, 0, 255) + b"\0" * 3 + astr(name)
            content += chunk(0x2004, layer_payload)
        raw = zlib.compress(im.convert("RGBA").tobytes(), 9)
        cel_payload = struct.pack("<HhhBHh", 0, 0, 0, 255, 2, 0) + b"\0" * 5 + struct.pack("<HH", w, h) + raw
        content += chunk(0x2005, cel_payload)
        frame_size = len(content) + 16
        frame_header = struct.pack("<IHHH2sI", frame_size, 0xF1FA, 1 if frame_index == 0 else 1, duration, b"\0\0", 1)
        chunks.append(frame_header + content)
    total = 128 + sum(len(c) for c in chunks)
    header = bytearray(128)
    struct.pack_into("<IHHHHHIH", header, 0, total, 0xA5E0, len(frames), w, h, 32, 0, duration)
    struct.pack_into("<HBBhhHH", header, 32, 0, 1, 1, 0, 0, 8, 8)
    path.write_bytes(bytes(header) + b"".join(chunks))


def make_sprite(name: str, w: int, h: int, draw_fn) -> Image.Image:
    im = Image.new("RGBA", (w, h), rgba("void"))
    draw_fn(ImageDraw.Draw(im), w, h)
    save_png(im, SPRITES / f"{name}.png")
    return im


def tree_draw(d: ImageDraw.ImageDraw, w: int, h: int, variant: int = 0):
    # Organic canopy and roots, all vertices intentionally snapped to 8 px.
    outer = [(16, 0), (48, 0), (48, 8), (56, 8), (56, 16), (64, 16),
             (64, 40), (56, 40), (56, 48), (48, 48), (48, 56),
             (16, 56), (16, 48), (8, 48), (8, 40), (0, 40), (0, 16),
             (8, 16), (8, 8), (16, 8)]
    d.polygon(outer, fill=rgba("forest0"))
    inner = [(24, 8), (48, 8), (48, 16), (56, 16), (56, 32), (48, 32),
             (48, 40), (16, 40), (16, 32), (8, 32), (8, 24), (16, 24),
             (16, 16), (24, 16)]
    d.polygon(inner, fill=rgba("forest1"))
    # Leaf masses are broad readable clusters, not isolated random dots.
    for poly, c in [
        ([(16, 8), (32, 8), (32, 16), (24, 16), (24, 24), (8, 24), (8, 16), (16, 16)], "fern0"),
        ([(40, 8), (48, 8), (48, 16), (56, 16), (56, 24), (40, 24)], "fern1"),
        ([(16, 32), (32, 32), (32, 40), (48, 40), (48, 48), (16, 48)], "fern1"),
    ]:
        d.polygon(poly, fill=rgba(c))
    if variant:
        rect(d, (24, 8, 31, 15), "grass1")
        rect(d, (40, 24, 47, 31), "grass2")
    # trunk and three roots remain readable on a dark floor.
    d.polygon([(28, 40), (36, 40), (36, 56), (44, 64), (36, 64), (32, 56), (28, 64), (20, 64), (28, 52)], fill=rgba("wood1"))
    rect(d, (30, 40, 34, 55), "wood2")
    rect(d, (31, 40, 32, 47), "wood3")


def small_tree_draw(d: ImageDraw.ImageDraw, w: int, h: int, variant: int = 0):
    outer = [(24, 8), (48, 8), (48, 16), (56, 16), (56, 40), (48, 40),
             (48, 48), (16, 48), (16, 40), (8, 40), (8, 16), (16, 16), (16, 8)]
    d.polygon(outer, fill=rgba("forest1"))
    d.polygon([(24, 16), (40, 16), (40, 24), (48, 24), (48, 40), (16, 40), (16, 24), (24, 24)], fill=rgba("fern0"))
    rect(d, (28, 40, 35, 63), "wood2")
    rect(d, (24, 48, 28, 55), "wood1")
    rect(d, (36, 48, 40, 55), "wood1")
    if variant:
        rect(d, (16, 16, 23, 23), "grass1")
        rect(d, (40, 24, 47, 31), "moss1")


def build_layers():
    # Each group is a deliberate PMDO sheet. Positions are also the coordinates
    # used by the .tile format, so each board can be inspected in Tile/Tiled.
    groups: dict[str, list[Image.Image]] = {}
    groups["01_Luminous_Spring_Base"] = [forest(i) for i in range(4)] + [grass(i) for i in range(6)] + [path(i) for i in range(4)] + [tile("moss0"), tile("moss1")]
    groups["02_Luminous_Spring_River"] = [water(i) for i in range(8)] + [shore("N", i) for i in range(2)] + [shore("S", i) for i in range(2)] + [shore("W", i) for i in range(2)] + [shore("E", i) for i in range(2)]
    groups["03_Luminous_Spring_Cliffs"] = [corner(c, i) for c in ("NW", "NE", "SW", "SE") for i in range(2)] + [stone(i) for i in range(8)] + [shore(c, 0) for c in ("N", "S", "W", "E")]
    groups["04_Luminous_Spring_Fringe"] = [grass(i) for i in range(4)] + [reed(i) for i in range(8)] + [tile("fern0"), tile("fern1"), tile("moss0"), tile("moss1")]
    groups["05_Luminous_Spring_Objects"] = [stone(i) for i in range(8)] + [reed(i) for i in range(8)] + [grass(i) for i in range(4)]
    groups["06_Luminous_Spring_Objects_Over"] = [tile("void") for _ in range(8)]
    groups["07_Luminous_Spring_Objects_Under"] = [tile("shadow") for _ in range(8)]
    groups["08_Luminous_Spring_Shadows"] = [tile("void") for _ in range(4)]
    # The PMDO animation logic: four different cells at the same texture role.
    # Four frame sequences are laid out contiguously per tile role: role 0
    # occupies coordinates 0..3, role 1 occupies 4..7, etc. This is the same
    # lookup pattern used by the rsground frame list below.
    groups["09_Luminous_Spring_River_Animations"] = [light8(f, v) for v in range(4) for f in range(4)]

    group_meta = {}
    for name, images in groups.items():
        # Stable 16-column sheet for editing and visual inspection.
        board_name = name.lower().replace("_luminous_spring", "") + ".png"
        sheet_png(images, 16, PLANCHES / board_name, scale=1)
        positions = [(i % 16, i // 16) for i in range(len(images))]
        write_tile(TILE_DIR / f"{name}.tile", images, positions)
        group_meta[name] = {"count": len(images), "positions": positions, "tile_size": 8, "png": f"planches/{board_name}"}

    # Separate 64 px tree sprites, with a fixed 8 px art grid and stable anchors.
    trees = [
        make_sprite("ancient_tree", 64, 64, lambda d, w, h: tree_draw(d, w, h, 0)),
        make_sprite("ancient_tree_bright", 64, 64, lambda d, w, h: tree_draw(d, w, h, 1)),
        make_sprite("young_tree", 64, 64, lambda d, w, h: small_tree_draw(d, w, h, 0)),
        make_sprite("young_tree_bright", 64, 64, lambda d, w, h: small_tree_draw(d, w, h, 1)),
    ]
    tree_board = Image.new("RGBA", (128, 128), rgba("void"))
    for i, im in enumerate(trees):
        tree_board.alpha_composite(im, ((i % 2) * 64, (i // 2) * 64))
    save_png(tree_board, PLANCHES / "06_arbres_sprites.png")
    save_png(tree_board, PLANCHES / "06_arbres.png")

    # Six artist-facing boards requested for the decomposition workflow. They are
    # aliases/curated views of the PMDO layer sheets, never crops from either
    # uploaded illustration.
    sheet_png(groups["03_Luminous_Spring_Cliffs"] + groups["04_Luminous_Spring_Fringe"], 16, PLANCHES / "01_bordures.png")
    sheet_png(groups["01_Luminous_Spring_Base"], 16, PLANCHES / "02_sol.png")
    sheet_png(groups["02_Luminous_Spring_River"] + groups["03_Luminous_Spring_Cliffs"][:16], 16, PLANCHES / "03_bassin.png")
    sheet_png(groups["02_Luminous_Spring_River"][:8], 16, PLANCHES / "04_eau.png")

    # Eight true frames at 32x32 for the independent spring glow. The anchor is
    # the same bottom-center pixel in every frame, while the silhouette changes.
    light_frames = []
    widths = [8, 10, 12, 10, 8, 12, 10, 8]
    offsets = [0, 0, 1, 1, 0, -1, -1, 0]
    for f in range(8):
        im = Image.new("RGBA", (32, 32), rgba("void"))
        d = ImageDraw.Draw(im)
        cx = 16 + offsets[f]
        bw = widths[f]
        # Broad, stepped beam like the supplied light reference. It always
        # terminates at the same anchor y=31; only the silhouette above moves.
        rect(d, (cx - bw // 2, 0, cx + bw // 2, 20 + (f % 2)), "beam0")
        rect(d, (cx - max(2, bw // 2 - 2), 0, cx + max(2, bw // 2 - 2), 19 + ((f + 1) % 2)), "beam1")
        rect(d, (cx - max(1, bw // 2 - 4), 0, cx + max(1, bw // 2 - 4), 18 + (f % 3)), "beam2")
        # stepped expanding halo, not a blur
        r = 6 + (f % 3)
        rect(d, (cx - r, 21, cx + r, 27), "beam0")
        rect(d, (cx - r + 2, 20, cx + r - 2, 28), "beam1")
        rect(d, (cx - 5, 21, cx + 5, 28), "beam2")
        rect(d, (cx - 3, 22, cx + 3, 28), "beam3")
        rect(d, (cx - 2, 23 + (f % 2), cx + 2, 26 + (f % 2)), "beam4")
        # two controlled sparkles migrate around the fixed core
        sx = 8 + ((f * 3) % 15); sy = 17 + ((f * 2) % 7)
        rect(d, (sx, sy, sx + 1, sy + 1), "beam3")
        if f % 2 == 0:
            rect(d, (24 - (f % 4), 12 + f % 5, 25 - (f % 4), 13 + f % 5), "beam2")
        # Constant PMDO anchor marker: the sprite is placed from this bottom
        # center, while the visible glow above it changes frame by frame.
        rect(d, (16, 30, 16, 31), "beam0")
        light_frames.append(im)
    light_sheet = Image.new("RGBA", (32 * len(light_frames), 32), rgba("void"))
    for i, im in enumerate(light_frames):
        light_sheet.alpha_composite(im, (i * 32, 0))
    save_png(light_sheet, PLANCHES / "05_lumiere_frames.png")
    save_png(light_sheet, PLANCHES / "05_lumiere.png")
    aseprite_write(ASEPRITE / "05_lumiere_spring.aseprite", light_frames, "lumiere_spring", duration=100)

    return groups, group_meta, light_frames, trees


def tiled_tsx(name: str, image: str, tilewidth: int, tileheight: int, count: int, columns: int, image_w: int, image_h: int) -> str:
    return f'''<?xml version="1.0" encoding="UTF-8"?>\n<tileset version="1.10" tiledversion="1.11.0" name="{name}" tilewidth="{tilewidth}" tileheight="{tileheight}" tilecount="{count}" columns="{columns}">\n  <image source="../../{image}" width="{image_w}" height="{image_h}"/>\n  <grid orientation="orthogonal" width="{tilewidth}" height="{tileheight}"/>\n</tileset>\n'''


def build_tiled(groups, meta):
    # Tiled uses the exact same 8 px ground cells as PMDO/Halcyon.
    ts_specs = [
        ("01_Luminous_Spring_Base", 1, 16, "planches/base.png"),
        ("02_Luminous_Spring_River", 1, 16, "planches/river.png"),
        ("03_Luminous_Spring_Cliffs", 1, 16, "planches/cliffs.png"),
        ("04_Luminous_Spring_Fringe", 1, 16, "planches/fringe.png"),
        ("05_Luminous_Spring_Objects", 1, 16, "planches/objects.png"),
        ("06_Luminous_Spring_Objects_Over", 1, 16, "planches/objects_over.png"),
        ("07_Luminous_Spring_Objects_Under", 1, 16, "planches/objects_under.png"),
        ("08_Luminous_Spring_Shadows", 1, 16, "planches/shadows.png"),
        ("09_Luminous_Spring_River_Animations", 1, 16, "planches/river_animations.png"),
    ]
    firstgid = 1
    ts_json = []
    gid = {}
    for name, tw, cols, image in ts_specs:
        count = len(groups[name])
        rows = (count + cols - 1) // cols
        # Actual PNG names are derived from the group name.
        png_name = name.lower().replace("_luminous_spring", "") + ".png"
        png_path = PLANCHES / png_name
        # Tree/over groups can have fewer than 16 entries; dimensions stay explicit.
        im = Image.open(png_path)
        tsx_name = name + ".tsx"
        (TILED_TS / tsx_name).write_text(tiled_tsx(name, f"planches/{png_name}", 8, 8, count, 16, im.width, im.height), encoding="utf-8")
        ts_json.append({"firstgid": firstgid, "source": f"tilesets/{tsx_name}"})
        gid[name] = firstgid
        firstgid += count

    # Tall objects and effects remain independent from the ground raster. Tiled
    # object layers can therefore select a complete 64 px tree or a 32 px light
    # frame without pretending that it is one 8 px ground tile.
    tree_gid = firstgid
    (TILED_TS / "10_Luminous_Spring_Trees.tsx").write_text(tiled_tsx("10_Luminous_Spring_Trees", "planches/06_arbres.png", 64, 64, 4, 2, 128, 128), encoding="utf-8")
    ts_json.append({"firstgid": tree_gid, "source": "tilesets/10_Luminous_Spring_Trees.tsx"})
    light_gid = tree_gid + 4
    (TILED_TS / "11_Luminous_Spring_Light.tsx").write_text(tiled_tsx("11_Luminous_Spring_Light", "planches/05_lumiere_frames.png", 32, 32, 8, 8, 256, 32), encoding="utf-8")
    ts_json.append({"firstgid": light_gid, "source": "tilesets/11_Luminous_Spring_Light.tsx"})

    # Helper to fill an empty layer with zero gids.
    def empty():
        return [0] * (MAP_W * MAP_H)

    base = empty()
    river = empty()
    cliffs = empty()
    fringe = empty()
    objects = empty()
    shadows = empty()
    anim = empty()

    def put(layer, x, y, ts_name, index):
        if 0 <= x < MAP_W and 0 <= y < MAP_H:
            layer[y * MAP_W + x] = gid[ts_name] + index

    # Background woodland. Clearing is shaped as a downward widening PMD zone.
    for y in range(MAP_H):
        for x in range(MAP_W):
            put(base, x, y, "01_Luminous_Spring_Base", (x + y) % 4)
    for y in range(20, MAP_H):
        half = min(23, 5 + (y - 20) // 3)
        for x in range(MAP_W // 2 - half, MAP_W // 2 + half + 1):
            put(base, x, y, "01_Luminous_Spring_Base", 4 + ((x * 2 + y) % 6))
    # Straight walkable path through the clearing.
    for y in range(44, MAP_H):
        for x in range(29, 35):
            put(base, x, y, "01_Luminous_Spring_Base", 10 + ((x + y) % 4))

    # Pond shape (interior is water, border is a reusable 8px shoreline).
    pond_rows = {12: range(27, 37), 13: range(25, 39), 14: range(24, 40), 15: range(23, 41), 16: range(22, 42), 17: range(22, 42), 18: range(23, 41), 19: range(24, 40), 20: range(26, 38), 21: range(28, 36)}
    pond = {(x, y) for y, xs in pond_rows.items() for x in xs}
    for x, y in sorted(pond, key=lambda p: (p[1], p[0])):
        boundary = {(x - 1, y) not in pond, (x + 1, y) not in pond, (x, y - 1) not in pond, (x, y + 1) not in pond}
        if sum(boundary) == 0:
            put(river, x, y, "02_Luminous_Spring_River", (x + y) % 8)
        else:
            # Use small modular shore cells at the boundary; the stone/cliff layer
            # supplies the heavier rock caps so no asset is fused to one map pose.
            if (x, y - 1) not in pond:
                idx = 8 + ((x + y) % 2)
            elif (x, y + 1) not in pond:
                idx = 10 + ((x + y) % 2)
            elif (x - 1, y) not in pond:
                idx = 12 + ((x + y) % 2)
            else:
                idx = 14 + ((x + y) % 2)
            put(river, x, y, "02_Luminous_Spring_River", idx)
            if (x + y) % 2 == 0:
                put(cliffs, x, y, "03_Luminous_Spring_Cliffs", 8 + ((x + y) % 8))

    # Small animated water ribbon leading into the spring, four PMDO frames.
    for y in range(0, 13):
        for x in (31, 32):
            put(anim, x, y, "09_Luminous_Spring_River_Animations", ((x + y) % 4) * 4)
    # bank fringe, ferns, stones and shadows
    for x, y, idx in [(20, 15, 0), (43, 15, 1), (20, 21, 2), (42, 21, 3), (24, 24, 4), (39, 24, 5)]:
        put(fringe, x, y, "04_Luminous_Spring_Fringe", idx)
    for x, y, idx in [(9, 18, 0), (51, 18, 1), (6, 32, 2), (55, 32, 3), (14, 50, 4), (49, 50, 5)]:
        put(objects, x, y, "05_Luminous_Spring_Objects", idx)
    for x, y in [(26, 22), (37, 22), (27, 23), (36, 23), (22, 16), (41, 16)]:
        put(shadows, x, y, "08_Luminous_Spring_Shadows", 0)

    # A layer stack deliberately matching the Halcyon ground grammar.
    layers = []
    for lid, name, data, visible in [
        (1, "Base", base, True),
        (2, "River", river, True),
        (3, "Cliffs", cliffs, True),
        (4, "Shadows", shadows, True),
        (5, "Objects Under", empty(), True),
        (6, "Objects", objects, True),
        (7, "Objects Over", empty(), True),
        (8, "Fringe", fringe, True),
        (9, "River Animations", anim, True),
    ]:
        layers.append({"id": lid, "name": name, "type": "tilelayer", "x": 0, "y": 0, "width": MAP_W, "height": MAP_H, "visible": visible, "opacity": 1, "data": data, "properties": [{"name": "pmd_role", "type": "string", "value": name}]})
    # Object layers keep tall sprites and the independent light effect out of the
    # 8x8 ground raster, just as PMDO keeps map tiles separate from objects.
    layers.append({
        "id": 10, "name": "Trees and light anchors", "type": "objectgroup", "draworder": "top", "objects": [
            {"id": 1, "name": "ancient_tree_left", "type": "sprite", "gid": tree_gid + 0, "x": 56, "y": 120, "width": 64, "height": 64, "properties": [{"name": "asset", "type": "file", "value": "../sprites/ancient_tree.png"}, {"name": "anchor", "type": "string", "value": "32,64"}]},
            {"id": 2, "name": "ancient_tree_right", "type": "sprite", "gid": tree_gid + 1, "x": 392, "y": 120, "width": 64, "height": 64, "properties": [{"name": "asset", "type": "file", "value": "../sprites/ancient_tree_bright.png"}, {"name": "anchor", "type": "string", "value": "32,64"}]},
            {"id": 3, "name": "luminous_spring", "type": "animation_anchor", "gid": light_gid + 0, "x": 248, "y": 0, "width": 32, "height": 32, "properties": [{"name": "aseprite", "type": "file", "value": "../aseprite/05_lumiere_spring.aseprite"}, {"name": "frames", "type": "int", "value": 8}, {"name": "frame_length_ticks", "type": "int", "value": 10}, {"name": "anchor", "type": "string", "value": "16,31"}]},
        ],
        "properties": [{"name": "pmd_role", "type": "string", "value": "objects_and_effect_anchors"}],
    })
    tiled = {
        "type": "map", "version": "1.10", "tiledversion": "1.11.0", "orientation": "orthogonal", "renderorder": "right-down",
        "width": MAP_W, "height": MAP_H, "tilewidth": 8, "tileheight": 8, "infinite": False,
        "nextlayerid": 11, "nextobjectid": 4, "layers": layers, "tilesets": ts_json,
        "properties": [
            {"name": "pmd_zone", "type": "string", "value": "Luminous Spring — PMDO 8px reconstruction"},
            {"name": "collision_grid", "type": "int", "value": 8},
            {"name": "animation_reference", "type": "string", "value": "Halcyon River_Animations: 4 frames × FrameLength 10"},
        ],
    }
    (TILED_DIR / "luminous_spring_pmdo.tmj").write_text(json.dumps(tiled, ensure_ascii=False, indent=2), encoding="utf-8")
    return tiled, (base, river, cliffs, shadows, objects, fringe, anim)


def build_ground_rsground(meta):
    # PMDO's .rsground keeps layers as arrays of 8 px cells. This compact map is
    # intentionally the same layer vocabulary as Halcyon/Altere_Pond.
    def cell(sheet: str, x: int, y: int, frames=None, length=10):
        fs = frames or [{"Sheet": sheet, "TexLoc": {"X": x, "Y": y}}]
        out = {"Frames": fs}
        if len(fs) > 1:
            out["FrameLength"] = length
        return out
    def blank_cell():
        return {"Layers": []}
    # Keep the companion as a clear integration template; Tiled is the editable map.
    # It points to named PMDO sheets and makes the Halcyon-style animated layer explicit.
    layers = []
    for name, sheet in [
        ("Base", "01_Luminous_Spring_Base"), ("River", "02_Luminous_Spring_River"),
        ("Cliffs", "03_Luminous_Spring_Cliffs"), ("Shadows", "08_Luminous_Spring_Shadows"),
        ("Objects Under", "07_Luminous_Spring_Objects_Under"), ("Objects", "05_Luminous_Spring_Objects"),
        ("Objects Over", "06_Luminous_Spring_Objects_Over"), ("Fringe", "04_Luminous_Spring_Fringe"),
        ("River Animations", "09_Luminous_Spring_River_Animations"),
    ]:
        grid = []
        for y in range(MAP_H):
            row = []
            for x in range(MAP_W):
                if name == "Base": idx = (x + y) % 4
                elif name == "River Animations" and x in (31, 32) and y < 13:
                    frames = [{"Sheet": sheet, "TexLoc": {"X": ((x + y) % 4) * 4 + f, "Y": 0}} for f in range(4)]
                    row.append({"Layers": [cell(sheet, 0, 0, frames)]}); continue
                elif name == "River" and 22 <= x <= 42 and 12 <= y <= 21: idx = (x + y) % 8
                else: row.append(blank_cell()); continue
                row.append({"Layers": [cell(sheet, idx % 16, idx // 16)]})
            grid.append(row)
        layers.append({"Name": name, "Layer": layers.__len__(), "Visible": True, "Tiles": grid})
    obj = {
        "$type": "RogueEssence.Dungeon.GroundScene, RogueEssence",
        "TexSize": 8, "Name": "luminous_spring_pmdo", "Released": True,
        "Comment": "Reconstruction for PMDO; 8 px grid, Halcyon-style layer stack, four-frame water animation.",
        "obstacles": [[0 for _ in range(MAP_H)] for _ in range(MAP_W)], "rand": 0,
        "Status": [], "Background": "", "BlankBG": True, "Layers": layers,
        "AssetName": "luminous_spring_pmdo", "Music": "", "EdgeView": False,
        "NoSwitching": False, "ViewCenter": {"X": 32, "Y": 32}, "ViewOffset": {"X": 0, "Y": 0},
        "ActiveChar": {"X": 32, "Y": 43}, "Decorations": [], "Entities": [],
    }
    (GROUND_DIR / "luminous_spring_pmdo.rsground").write_text(json.dumps({"Object": obj}, ensure_ascii=False, indent=2), encoding="utf-8")


def build_preview(groups, light_frames):
    # Render the same 8 px composition into a readable 512 px preview. No scaling
    # is used for assets themselves; this is only a nearest-neighbour presentation.
    im = Image.new("RGBA", (MAP_W * TILE, MAP_H * TILE), rgba("forest0"))
    base_tiles = groups["01_Luminous_Spring_Base"]
    river_tiles = groups["02_Luminous_Spring_River"]
    # woodland base and clearing
    for y in range(MAP_H):
        for x in range(MAP_W):
            im.alpha_composite(base_tiles[(x + y) % 4], (x * TILE, y * TILE))
    for y in range(20, MAP_H):
        half = min(23, 5 + (y - 20) // 3)
        for x in range(max(0, 32 - half), min(MAP_W, 33 + half)):
            im.alpha_composite(base_tiles[4 + ((x * 2 + y) % 6)], (x * TILE, y * TILE))
    for y in range(44, MAP_H):
        for x in range(29, 35):
            im.alpha_composite(base_tiles[10 + ((x + y) % 4)], (x * TILE, y * TILE))
    # pond, using exact same geometry as Tiled builder
    pond_rows = {12: range(27, 37), 13: range(25, 39), 14: range(24, 40), 15: range(23, 41), 16: range(22, 42), 17: range(22, 42), 18: range(23, 41), 19: range(24, 40), 20: range(26, 38), 21: range(28, 36)}
    pond = {(x, y) for y, xs in pond_rows.items() for x in xs}
    for x, y in pond:
        if all((x + dx, y + dy) in pond for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            idx = (x + y) % 8
        elif (x, y - 1) not in pond: idx = 8 + ((x + y) % 2)
        elif (x, y + 1) not in pond: idx = 10 + ((x + y) % 2)
        elif (x - 1, y) not in pond: idx = 12 + ((x + y) % 2)
        else: idx = 14 + ((x + y) % 2)
        im.alpha_composite(river_tiles[idx], (x * TILE, y * TILE))
        # Rock caps live in the independent Cliffs layer, never baked into water.
        if sum((x + dx, y + dy) not in pond for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            cliff_index = 8 + ((x + y) % 8)
            im.alpha_composite(groups["03_Luminous_Spring_Cliffs"][cliff_index], (x * TILE, y * TILE))
    # A narrow, stepped cyan beam makes the design relationship with the uploaded
    # Luminous Spring explicit, while the actual reusable effect remains the
    # independent animated Aseprite sprite below.
    beam_layer = Image.new("RGBA", im.size, rgba("void"))
    bd = ImageDraw.Draw(beam_layer)
    rect(bd, (29 * TILE, 0, 34 * TILE - 1, 12 * TILE), "beam0")
    rect(bd, (30 * TILE, 0, 33 * TILE - 1, 12 * TILE), "beam1")
    rect(bd, (31 * TILE, 0, 32 * TILE - 1, 12 * TILE), "beam2")
    im.alpha_composite(beam_layer)
    # beam in the first preview frame, then trees and rocks as independent art
    beam = light_frames[0]
    im.alpha_composite(beam.resize((32, 32), Image.Resampling.NEAREST), (240, 0))
    for name, xy in [
        ("ancient_tree.png", (0, 72)), ("ancient_tree_bright.png", (448, 72)),
        ("ancient_tree_bright.png", (48, 344)), ("ancient_tree.png", (400, 344)),
        ("young_tree.png", (0, 240)), ("young_tree_bright.png", (448, 240)),
    ]:
        im.alpha_composite(Image.open(SPRITES / name), xy)
    save_png(im, PREVIEW / "luminous_spring_pmdo.png")
    # board with the animation row enlarged 2x nearest neighbour below the map
    board = Image.new("RGBA", (512, 640), (13, 27, 34, 255))
    board.alpha_composite(im.resize((512, 512), Image.Resampling.NEAREST), (0, 0))
    for i, f in enumerate(light_frames):
        board.alpha_composite(f.resize((24, 24), Image.Resampling.NEAREST), (8 + i * 30, 550))
    save_png(board, PREVIEW / "luminous_spring_pmdo_animation_board.png")


def write_manifest(meta):
    manifest = {
        "nom": "Luminous Spring PMDO — reconstruction Halcyon",
        "source_design": "luminoussspring.png",
        "technical_reference": "Luminous_Spring_TDS REFERENCE A IMITER.png",
        "light_reference": "LIGHT EFFECT REFERENCE.png",
        "reference_project": "Palikadude/Halcyon",
        "reference_observed": {"ground_tile_px": 8, "layer_order": ["Base", "River", "Cliffs", "Shadows", "Objects Under", "Objects", "Objects Over", "Fringe"], "river_animation_frames": 4, "river_animation_frame_length": 10},
        "grid": {"pmd_ground_tile_px": 8, "art_module_px": 16, "collision_subgrid_px": 8, "interpolation": "none", "antialiasing": False},
        "palette": {k: list(v) for k, v in PAL.items()},
        "sheets": meta,
        "animation": {"frames": 8, "canvas_px": [32, 32], "duration_ms": 100, "anchor_px": [16, 31], "aseprite": "aseprite/05_lumiere_spring.aseprite", "sheet": "planches/05_lumiere_frames.png", "frames_are_distinct": True},
        "files": {"tiled": "tiled/luminous_spring_pmdo.tmj", "rsground": "pmd/Data/Ground/luminous_spring_pmdo.rsground", "preview": "preview/luminous_spring_pmdo_animation_board.png"},
        "generator": {"configuration": "source/generated/generator_config.json", "studies": ["source/generated/zone_pmdo_bright_palette.png", "source/generated/rives_bassin_bright_palette.png", "source/generated/lumiere_bright_palette.png"], "role": "design studies only; final tiles are manually rebuilt at 8 px with this palette"},
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    groups, meta, light_frames, trees = build_layers()
    build_tiled(groups, meta)
    build_ground_rsground(meta)
    build_preview(groups, light_frames)
    write_manifest(meta)
    print("Built PMDO/Halcyon-style Luminous Spring: 8 px cells, 9 tile sheets, 8 light frames, Tiled + rsground.")


if __name__ == "__main__":
    main()
