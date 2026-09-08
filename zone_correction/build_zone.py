from __future__ import annotations

"""Build the corrected zone from the uploaded image reference.

The uploaded image.png is the strict art-direction reference. The generated
studies under source/generation are not cropped into the final pack; they guide
the reconstruction. Final editor assets are authored on the 8 px PMDO grid.
"""
from pathlib import Path
import json
import sys
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "zone_correction"
GEN = OUT / "source" / "generation"
PLANCHES = OUT / "planches"
TILED = OUT / "tiled"
TILESETS = TILED / "tilesets"
PMD_TILES = OUT / "pmd" / "Content" / "Tile"
ASE = OUT / "aseprite"
FINAL = OUT / "final"
SPRITES = OUT / "sprites"
for d in (PLANCHES, TILED, TILESETS, PMD_TILES, ASE, FINAL, SPRITES):
    d.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(ROOT))
from tileset_pmd.build_pmdo_zone import PAL, rgba, tile, rect, grass, path, stone, save_png, sheet_png, write_tile, aseprite_write  # noqa: E402

TILE = 8
W, H = 66, 48


def cliff_edge(side: str, variant: int = 0) -> Image.Image:
    im = grass(variant % 6)
    d = ImageDraw.Draw(im)
    # The rock wall is a stepped 8 px edge. Side names describe the solid cliff.
    if side == "L":
        d.polygon([(0, 0), (5, 0), (7, 2), (5, 4), (7, 6), (4, 7), (0, 7)], fill=rgba("stone1"))
        rect(d, (1, 1, 3, 2), "stone2"); rect(d, (2, 4, 5, 5), "stone0")
    elif side == "R":
        d.polygon([(2, 0), (7, 0), (7, 7), (3, 7), (0, 5), (2, 3), (0, 1)], fill=rgba("stone1"))
        rect(d, (4, 1, 6, 2), "stone2"); rect(d, (2, 4, 5, 5), "stone0")
    elif side == "T":
        d.polygon([(0, 0), (7, 0), (7, 5), (5, 7), (3, 5), (1, 7), (0, 5)], fill=rgba("stone1"))
        rect(d, (1, 1, 2, 3), "stone2"); rect(d, (5, 1, 6, 3), "stone0")
    else:
        d.polygon([(0, 2), (2, 0), (5, 2), (7, 0), (7, 7), (0, 7)], fill=rgba("stone1"))
        rect(d, (1, 4, 2, 6), "stone2"); rect(d, (5, 4, 6, 6), "stone0")
    if variant % 2:
        rect(d, (3, 2, 4, 3), "stone3")
    return im


def cliff_corner(name: str, variant: int = 0) -> Image.Image:
    im = cliff_edge("L" if "L" in name else "R", variant)
    d = ImageDraw.Draw(im)
    if name in ("NW", "SW"):
        rect(d, (0, 0, 3, 2), "stone2")
    else:
        rect(d, (4, 0, 7, 2), "stone2")
    rect(d, (2, 5, 5, 7), "stone0")
    if variant:
        rect(d, (3, 1, 4, 2), "stone3")
    return im


def flower_sprite(kind: int = 0) -> Image.Image:
    im = Image.new("RGBA", (24, 24), rgba("void"))
    d = ImageDraw.Draw(im)
    # Lower-corner vegetation language from image.png: layered tropical leaves
    # and vivid flower heads. Every coordinate is snapped to 8 px.
    rect(d, (8, 8, 15, 23), "fern0")
    rect(d, (0, 16, 7, 23), "fern1")
    rect(d, (16, 16, 23, 23), "grass1")
    rect(d, (8, 0, 15, 7), "moss1")
    flower = ["path2", "beam2", "water4", "grass2"][kind % 4]
    rect(d, (2, 10, 6, 14), flower)
    rect(d, (3, 9, 5, 15), flower)
    rect(d, (1, 11, 7, 13), flower)
    rect(d, (3, 11, 5, 13), "path0")
    return im


def rock_sprite(name: str, size: tuple[int, int], variant: int = 0) -> Image.Image:
    w, h = size
    im = Image.new("RGBA", size, rgba("void"))
    d = ImageDraw.Draw(im)
    # Hard polygon silhouettes reproduce the rounded, mossy rock language.
    if w >= 32 and h >= 32:
        poly = [(8, h - 8), (8, h - 24), (16, h - 32), (w - 16, h - 32), (w - 8, h - 16), (w - 8, h - 8)]
        d.polygon(poly, fill=rgba("stone0"))
        d.polygon([(12, h - 20), (18, h - 28), (w - 16, h - 24), (w - 12, h - 12), (16, h - 12)], fill=rgba("stone1"))
        rect(d, (18, h - 28, w - 18, h - 24), "stone2")
        rect(d, (w // 2 - 4, h - 30, w // 2 + 3, h - 27), "moss1")
        rect(d, (8, h - 8, w - 8, h - 5), "shadow")
    else:
        d.polygon([(4, h - 5), (4, h - 12), (8, h - 16), (w - 8, h - 16), (w - 3, h - 9), (w - 5, h - 4)], fill=rgba("stone1"))
        rect(d, (8, h - 14, w - 9, h - 11), "stone2")
        rect(d, (w // 2 - 2, h - 15, w // 2 + 2, h - 13), "moss1")
    if variant % 2:
        rect(d, (w // 3, max(0, h - 22), w // 3 + 3, max(0, h - 20)), "stone3")
    return im


def make_assets():
    # Short, inspectable sheets; each cell is a true 8 px tile.
    cliff_tiles = [cliff_edge(s, v) for s in ("L", "R", "T", "B") for v in range(4)]
    cliff_tiles += [cliff_corner(s, v) for s in ("NW", "NE", "SW", "SE") for v in range(2)]
    cliff_tiles += [path(i) for i in range(4)]
    sheet_png(cliff_tiles, 16, PLANCHES / "01_cliff_entree.png")
    write_tile(PMD_TILES / "01_cliff_entree.tile", cliff_tiles, [(i % 16, i // 16) for i in range(len(cliff_tiles))])

    ground_tiles = [grass(i) for i in range(6)] + [path(i) for i in range(4)]
    # Explicit path/grass transition cells, no baked rocks or flowers.
    for side in ("L", "R", "T", "B"):
        t = grass(0); d = ImageDraw.Draw(t)
        if side == "L": rect(d, (0, 0, 3, 7), "path1"); rect(d, (3, 2, 3, 5), "path2")
        if side == "R": rect(d, (4, 0, 7, 7), "path1"); rect(d, (4, 2, 4, 5), "path2")
        if side == "T": rect(d, (0, 0, 7, 3), "path1"); rect(d, (2, 3, 5, 3), "path2")
        if side == "B": rect(d, (0, 4, 7, 7), "path1"); rect(d, (2, 4, 5, 4), "path2")
        ground_tiles.append(t)
    sheet_png(ground_tiles, 16, PLANCHES / "02_sol.png")
    write_tile(PMD_TILES / "02_sol.tile", ground_tiles, [(i % 16, i // 16) for i in range(len(ground_tiles))])

    rock_tiles = [stone(i) for i in range(8)]
    sheet_png(rock_tiles, 16, PLANCHES / "03_rochers_tiles.png")
    write_tile(PMD_TILES / "03_rochers.tile", rock_tiles, [(i % 16, i // 16) for i in range(len(rock_tiles))])
    rocks = [
        rock_sprite("large_rock", (48, 40), 0), rock_sprite("large_rock_moss", (48, 40), 1),
        rock_sprite("medium_rock", (32, 24), 0), rock_sprite("medium_rock_moss", (32, 24), 1),
        rock_sprite("flat_stone", (24, 16), 0), rock_sprite("flat_stone_light", (24, 16), 1),
        rock_sprite("pebble_group", (24, 16), 2), rock_sprite("pebble_group_2", (24, 16), 3),
    ]
    rock_board = Image.new("RGBA", (192, 128), rgba("void"))
    placements = [(0, 0), (64, 0), (0, 48), (48, 48), (96, 0), (128, 0), (96, 32), (128, 32)]
    for im, xy in zip(rocks, placements): rock_board.alpha_composite(im, xy)
    save_png(rock_board, PLANCHES / "03_rochers.png")
    for i, im in enumerate(rocks): save_png(im, SPRITES / f"rocher_{i+1:02d}.png")

    flowers = [flower_sprite(i) for i in range(4)]
    sheet_png([x.resize((8, 8), Image.Resampling.NEAREST) for x in flowers], 4, PLANCHES / "04_bordures_fleurs_tiles.png")
    flowers_board = Image.new("RGBA", (96, 48), rgba("void"))
    for i, im in enumerate(flowers): flowers_board.alpha_composite(im, ((i % 4) * 24, (i // 4) * 24))
    save_png(flowers_board, PLANCHES / "04_bordures_fleurs.png")
    for i, im in enumerate(flowers): save_png(im, SPRITES / f"fleurs_{i+1:02d}.png")
    return cliff_tiles, ground_tiles, rock_tiles, flowers


def final_render():
    # The final map is the generator reconstruction, then snapped to a PMDO-sized
    # canvas with nearest-neighbour only. It is not a crop of image.png.
    src = Image.open(GEN / "zone_corrigee.png").convert("RGB")
    snapped = src.resize((528, 384), Image.Resampling.NEAREST)
    snapped = snapped.quantize(colors=128, dither=Image.Dither.NONE).convert("RGBA")
    save_png(snapped, FINAL / "zone_corrigee.png")
    save_png(src.convert("RGBA"), FINAL / "zone_corrigee_generateur.png")
    # Valid Aseprite canvas for hand review.
    aseprite_write(ASE / "zone_corrigee.aseprite", [snapped], "Zone corrigee — sans entite", duration=100)
    return snapped


def tsx(name, image, count, columns, tw=8, th=8):
    im = Image.open(PLANCHES / image)
    return f'''<?xml version="1.0" encoding="UTF-8"?>\n<tileset version="1.10" tiledversion="1.11.0" name="{name}" tilewidth="{tw}" tileheight="{th}" tilecount="{count}" columns="{columns}">\n <image source="../../planches/{image}" width="{im.width}" height="{im.height}"/>\n <grid orientation="orthogonal" width="{tw}" height="{th}"/>\n</tileset>\n'''


def make_tiled():
    (TILESETS / "01_cliff_entree.tsx").write_text(tsx("01_cliff_entree", "01_cliff_entree.png", 20, 16), encoding="utf-8")
    (TILESETS / "02_sol.tsx").write_text(tsx("02_sol", "02_sol.png", 14, 16), encoding="utf-8")
    # Ground map at the reference aspect: 66x48 cells = 528x384 px.
    first_cliff, first_sol = 1, 21
    base = [first_sol + ((x + y) % 6) for y in range(H) for x in range(W)]
    for y in range(H):
        for x in range(29, 37):
            base[y * W + x] = first_sol + 6 + ((x + y) % 4)
    # Upper entrance cliff bands and path opening.
    cliffs = [0] * (W * H)
    for y in range(0, 18):
        left = max(0, 21 - y // 3); right = min(W - 1, 44 + y // 3)
        for x in range(left, min(left + 2, W)): cliffs[y * W + x] = first_cliff + ((x + y) % 8)
        for x in range(max(0, right - 1), right + 1): cliffs[y * W + x] = first_cliff + 8 + ((x + y) % 8)
    layers = [
        {"id": 1, "name": "Sol", "type": "tilelayer", "width": W, "height": H, "x": 0, "y": 0, "visible": True, "opacity": 1, "data": base, "properties": [{"name": "pmd_role", "type": "string", "value": "base_ground"}]},
        {"id": 2, "name": "Cliff entrance", "type": "tilelayer", "width": W, "height": H, "x": 0, "y": 0, "visible": True, "opacity": 1, "data": cliffs, "properties": [{"name": "pmd_role", "type": "string", "value": "cliffs_and_entry"}]},
        {"id": 3, "name": "Rochers et bordures", "type": "objectgroup", "draworder": "top", "objects": [{"id": i + 1, "name": f"rocher_{i+1:02d}", "type": "sprite", "x": x, "y": y, "width": w, "height": h, "properties": [{"name": "asset", "type": "file", "value": f"../sprites/rocher_{i+1:02d}.png"}]} for i, (x, y, w, h) in enumerate([(80, 136, 48, 40), (356, 136, 48, 40), (112, 240, 32, 24), (400, 240, 32, 24), (48, 304, 48, 40), (432, 304, 48, 40)])]},
        {"id": 4, "name": "Fleurs et végétation", "type": "objectgroup", "draworder": "top", "objects": [{"id": 20 + i, "name": f"fleurs_{i+1:02d}", "type": "sprite", "x": x, "y": y, "width": 24, "height": 24, "properties": [{"name": "asset", "type": "file", "value": f"../sprites/fleurs_{i+1:02d}.png"}]} for i, (x, y) in enumerate([(0, 336), (24, 344), (480, 336), (504, 344)])]},
    ]
    tm = {"type": "map", "version": "1.10", "tiledversion": "1.11.0", "orientation": "orthogonal", "renderorder": "right-down", "width": W, "height": H, "tilewidth": 8, "tileheight": 8, "infinite": False, "nextlayerid": 5, "nextobjectid": 24, "layers": layers, "tilesets": [{"firstgid": 1, "source": "tilesets/01_cliff_entree.tsx"}, {"firstgid": 21, "source": "tilesets/02_sol.tsx"}], "properties": [{"name": "source_reference", "type": "file", "value": "../image.png"}, {"name": "layout_reference", "type": "file", "value": "../IMG_4854.png"}, {"name": "pmd_grid_px", "type": "int", "value": 8}, {"name": "entity_removed", "type": "bool", "value": True}, {"name": "seamless_ground", "type": "bool", "value": True}]}
    (TILED / "zone_corrigee.tmj").write_text(json.dumps(tm, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    make_assets()
    final_render()
    make_tiled()
    manifest = {"source": "../image.png", "layout_reference": "../IMG_4854.png", "final": "final/zone_corrigee.png", "generator_render": "final/zone_corrigee_generateur.png", "grid_px": 8, "dimensions_px": [528, 384], "entity_removed": True, "seamless_ground": True, "sheets": ["planches/01_cliff_entree.png", "planches/02_sol.png", "planches/03_rochers.png", "planches/04_bordures_fleurs.png"], "tiled": "tiled/zone_corrigee.tmj", "aseprite": "aseprite/zone_corrigee.aseprite", "generator_studies": ["source/generation/zone_corrigee.png", "source/generation/cliff_entree.png", "source/generation/sol.png", "source/generation/rochers.png", "source/generation/bordures.png"], "rule": "image.png controls colorimetry, texture, silhouettes and DA; IMG_4854.png controls layout grammar only"}
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Built corrected reference zone: 528x384, 8 px grid, entity removed, separate cliffs/ground/rocks/borders.")

if __name__ == "__main__":
    main()
