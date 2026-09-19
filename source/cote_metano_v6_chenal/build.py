"""Build one new Métano river-terrace composition from native 8 px material.

The layout is new; the RGB of the terrain and water surface comes only from
verified native sheets. No generated image, scaling, rotation or recolouring is
used for the day terrain. The guide is the organic composition grammar recorded
in the Métano packs, not an image to paste into the result.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OUT = ROOT / "renders" / "cote_metano_v6_chenal"
SIZE = (1024, 768)
GRID = 8

sys.path.insert(0, str(ROOT / "source" / "cote_v4_abyss"))
from sample import decode  # noqa: E402
from night import night  # noqa: E402

NATIVE = ROOT / "source" / "cote_v4_abyss" / "natifs"
RIVER = ROOT / "sprites" / "eau_metano" / "Riviere_Metano_Compacte.png"
BG_DIR = ROOT / "sprites" / "cote_v2" / "01_promontoire"

# Native material rectangles, in the decoded source sheets.
MODULES = {
    "grass": ("Base", (0, 640, 128, 768)),
    "face": ("Cliffs", (912, 464, 976, 512)),
    "return": ("Cliffs", (680, 464, 744, 512)),
    "crown": ("Cliffs", (912, 448, 976, 464)),
    "foot": ("Cliffs", (912, 528, 976, 544)),
}
LAYER_NAMES = [
    "00_sol_herbe",
    "01_faces_falaise",
    "02_retours",
    "03_couronnes",
    "04_pieds",
    "05_eau_fond",
    "06_eau_phase_01",
    "07_eau_phase_02",
    "08_eau_phase_03",
    "09_eau_phase_04",
]


def polygon(points: list[tuple[int, int]]) -> np.ndarray:
    im = Image.new("1", SIZE)
    ImageDraw.Draw(im).polygon(points, fill=1)
    return np.asarray(im, dtype=bool)


def extrude(surface: np.ndarray, depth: int) -> np.ndarray:
    out = surface.copy()
    for delta in range(GRID, depth + GRID, GRID):
        if delta >= surface.shape[0]:
            break
        out[delta:] |= surface[:-delta]
    return out


def shift_up(mask: np.ndarray, amount: int = GRID) -> np.ndarray:
    out = np.zeros_like(mask)
    out[:-amount] = mask[amount:]
    return out


def shift_down(mask: np.ndarray, amount: int = GRID) -> np.ndarray:
    out = np.zeros_like(mask)
    out[amount:] = mask[:-amount]
    return out


def make_masks() -> dict[str, np.ndarray]:
    """Three organic terraces, one connecting neck and a winding water cut."""
    surfaces: list[np.ndarray] = []

    # Broad south terrace: the arrival remains in a readable, continuous floor.
    south = polygon([
        (-64, 520), (96, 456), (320, 472), (504, 520),
        (704, 456), (928, 472), (1088, 528), (1088, 800),
        (-64, 800),
    ])
    surfaces.append(extrude(south, 136))

    # Two offset upper shelves leave a diagonal channel between them.
    west = polygon([
        (-64, 152), (176, 128), (360, 176), (432, 272),
        (368, 384), (136, 376), (-64, 320),
    ])
    east = polygon([
        (696, 136), (904, 120), (1088, 200), (1088, 360),
        (912, 408), (744, 344), (664, 248),
    ])
    surfaces.extend([extrude(west, 104), extrude(east, 96)])

    # A northern cap and an 8 px-grid neck preserve a traversable reading.
    north = polygon([
        (368, 16), (584, 24), (672, 104), (632, 200),
        (456, 216), (344, 136),
    ])
    neck = polygon([(432, 368), (592, 368), (664, 464), (608, 536),
                    (472, 536), (400, 456)])
    surfaces.extend([extrude(north, 80), extrude(neck, 72)])

    land = np.zeros((SIZE[1], SIZE[0]), dtype=bool)
    for part in surfaces:
        land |= part

    # The river is a visual and structural cut, not a blue rectangle.
    water = polygon([
        (552, -32), (728, -32), (760, 112), (704, 248),
        (776, 376), (720, 496), (784, 800), (592, 800),
        (616, 560), (544, 432), (592, 296), (528, 152),
    ]).copy()
    # Keep the connecting neck as the route across the channel.
    water &= ~neck
    land &= ~water
    grass = np.zeros_like(land)
    for part in [south, west, east, north, neck]:
        grass |= part
    grass &= land

    # A separate logical route mask is shipped for collision/layout work. It
    # deliberately remains grass: Métano has no invented path texture here.
    route = polygon([(472, 744), (552, 744), (584, 568), (592, 496),
                     (544, 408), (496, 408), (520, 496)]).copy()
    route &= grass
    return {"terrain": land, "grass": grass, "water": water, "route": route}


def source_sheets(mode: str) -> dict[str, np.ndarray]:
    suffix = "" if mode == "jour" else "_Night"
    return {
        name: decode(NATIVE / f"Metano_Town_{name}{suffix}.tile")
        for name in ("Base", "Cliffs")
    }


def stamp_pattern(dst: np.ndarray, src: np.ndarray, rect: tuple[int, int, int, int],
                  mask: np.ndarray, step_x: int, step_y: int,
                  layer_name: str, placements: list[dict]) -> None:
    sx, sy, ex, ey = rect
    mw, mh = ex - sx, ey - sy
    h, w = mask.shape
    for y in range(0, h, step_y):
        for x in range(0, w, step_x):
            left, top = max(0, x), max(0, y)
            right, bottom = min(w, x + mw), min(h, y + mh)
            if right <= left or bottom <= top:
                continue
            patch = src[sy + top - y:sy + bottom - y,
                        sx + left - x:sx + right - x]
            selected = mask[top:bottom, left:right] & (patch[:, :, 3] > 0)
            if not selected.any():
                continue
            dst[top:bottom, left:right][selected] = patch[selected]
            placements.append({
                "layer": layer_name,
                "module": [sx, sy, ex, ey],
                "source_sheet": "Base" if layer_name == "00_sol_herbe" else "Cliffs",
                "destination": [x, y],
                "selected_pixels": int(selected.sum()),
            })


def edge_mask(mask: np.ndarray, direction: str) -> np.ndarray:
    if direction == "top":
        return mask & ~shift_down(mask)
    if direction == "bottom":
        return mask & ~shift_up(mask)
    raise ValueError(direction)


def terrain_layers(mode: str, masks: dict[str, np.ndarray]) -> tuple[list[np.ndarray], list[dict]]:
    sheets = source_sheets(mode)
    land, grass = masks["terrain"], masks["grass"]
    rock = land & ~grass
    h, w = land.shape
    layers = [np.zeros((h, w, 4), dtype=np.uint8) for _ in range(5)]
    placements: list[dict] = []

    stamp_pattern(layers[0], sheets["Base"], MODULES["grass"][1], grass,
                  128, 128, "00_sol_herbe", placements)
    stamp_pattern(layers[1], sheets["Cliffs"], MODULES["face"][1], rock,
                  64, 48, "01_faces_falaise", placements)

    top = edge_mask(rock, "top")
    bottom = edge_mask(rock, "bottom")
    stamp_pattern(layers[2], sheets["Cliffs"], MODULES["return"][1], top,
                  64, 48, "02_retours", placements)
    stamp_pattern(layers[3], sheets["Cliffs"], MODULES["crown"][1], top,
                  64, 16, "03_couronnes", placements)
    stamp_pattern(layers[4], sheets["Cliffs"], MODULES["foot"][1], bottom,
                  64, 16, "04_pieds", placements)
    return layers, placements


def dominant_water_colour(river: np.ndarray) -> np.ndarray:
    opaque = river[river[:, :, 3] == 255][:, :3]
    colours, counts = np.unique(opaque, axis=0, return_counts=True)
    return colours[int(np.argmax(counts))]


def water_layers(mode: str, water: np.ndarray) -> list[np.ndarray]:
    raw = np.asarray(Image.open(RIVER).convert("RGBA"))
    phases = [raw[i * 488:(i + 1) * 488] for i in range(4)]
    base_colour = dominant_water_colour(raw)
    h, w = water.shape
    bed = np.zeros((h, w, 4), dtype=np.uint8)
    bed[water, :3] = base_colour
    bed[water, 3] = 255
    outputs = [bed]
    for phase in phases:
        overlay = np.zeros_like(bed)
        for y in range(0, h, 8):
            for x in range(0, w, 8):
                src = phase[(y // 8 * 8) % phase.shape[0]:(y // 8 * 8) % phase.shape[0] + 8,
                            (x // 8 * 8) % phase.shape[1]:(x // 8 * 8) % phase.shape[1] + 8]
                # The compact canonical bank has full 8 px cells. At the bottom
                # edge the modulo keeps the source inside the same native phase.
                yy, xx = min(y, h - 8), min(x, w - 8)
                target_mask = water[yy:yy + 8, xx:xx + 8]
                if target_mask.any():
                    tile = src[:min(8, h - yy), :min(8, w - xx)]
                    alpha = (tile[:, :, 3] > 0) & target_mask[:tile.shape[0], :tile.shape[1]]
                    overlay[yy:yy + tile.shape[0], xx:xx + tile.shape[1]][alpha] = tile[alpha]
        outputs.append(overlay)
    if mode == "nuit":
        outputs = [np.asarray(night(Image.fromarray(layer, "RGBA"))) for layer in outputs]
    return outputs


def composite(layers: list[np.ndarray]) -> Image.Image:
    result = Image.new("RGBA", SIZE)
    for layer in layers:
        result = Image.alpha_composite(result, Image.fromarray(layer, "RGBA"))
    return result


def preview_background_layers(mode: str) -> list[Image.Image]:
    """Return validated coast background layers for review only.

    They remain separate from the terrain PNGs and are not importable tiles.
    Keeping them separate makes the depth and transparent cutouts readable
    without changing the native multi-layer deliverable.
    """
    names = [
        "COTEV2_01_00_CIEL_SANS_NUAGES.png",
        "COTEV2_01_01_NUAGES_POSITION_0.png",
        "COTEV2_01_02_MER_PALETTE_00.png",
    ]
    layers = []
    for name in names:
        layer = Image.open(BG_DIR / name).convert("RGBA").crop((0, 0, SIZE[0], SIZE[1]))
        layers.append(night(layer) if mode == "nuit" else layer)
    return layers


def preview_background(mode: str) -> Image.Image:
    base = Image.new("RGBA", SIZE, (10, 42, 72, 255))
    for layer in preview_background_layers(mode):
        base = Image.alpha_composite(base, layer)
    return base


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    masks = make_masks()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "masques").mkdir(exist_ok=True)
    for name in ("terrain", "grass", "water", "route"):
        Image.fromarray(masks[name].astype(np.uint8) * 255, "L").save(OUT / "masques" / f"{name}.png")

    manifest = {
        "id": "cote_metano_v6_chenal",
        "title": "Les Terrasses du Chenal",
        "mode": "A — extension de matière Métano canonique",
        "canvas": list(SIZE), "grid_px": 8, "tex_size": 1,
        "layout": {
            "arrival": [480, 704],
            "route": "south_to_north via the central neck; grass continuity, no invented path tile",
            "water": "winding canonical river cut between three terraces",
            "connections": ["west", "east", "south"],
        },
        "references": {
            "layout_grammar": [
                "source/cote_v5_expeditions/README.md",
                "sprites/cote_v5_expeditions/layouts.json",
                "renders/metano_expeditions_actuel/README.md",
            ],
            "terrain_day": [str(p.relative_to(ROOT)) for p in sorted(NATIVE.glob("Metano_Town_*.tile")) if "Night" not in p.name],
            "terrain_night": [str(p.relative_to(ROOT)) for p in sorted(NATIVE.glob("Metano_Town_*_Night.tile"))],
            "water": ["sprites/eau_metano/Riviere_Metano_Compacte.png", "sprites/eau_metano/README.md"],
            "review_background_only": [
                "sprites/cote_v2/01_promontoire/COTEV2_01_00_CIEL_SANS_NUAGES.png",
                "sprites/cote_v2/01_promontoire/COTEV2_01_01_NUAGES_POSITION_0.png",
                "sprites/cote_v2/01_promontoire/COTEV2_01_02_MER_PALETTE_00.png",
            ],
            "night_filter": "source/cote_v4_abyss/night.py and Abyss V4 reference blob 438383f4",
        },
        "layers": LAYER_NAMES,
        "provenance": {
            "generated_rgb_pixels_day_terrain": 0,
            "scaled_or_rotated_native_pixels": False,
            "generated_layout_only": True,
            "water_bed": "opaque substrate sampled from the most common opaque RGB in the canonical river bank; canonical river pixels remain in phase overlays",
        },
        "placements": {},
        "status": {"image_checks": "verify.py required after build", "pmdo_runtime": False, "art_review": "pending"},
    }

    for mode in ("jour", "nuit"):
        directory = OUT / mode
        directory.mkdir(exist_ok=True)
        terrain, placements = terrain_layers(mode, masks)
        water = water_layers(mode, masks["water"])
        all_layers = terrain + water
        for name, arr in zip(LAYER_NAMES, all_layers):
            Image.fromarray(arr, "RGBA").save(directory / f"{name}.png", optimize=True)
        for bg_name, bg_layer in zip(("bg_00_ciel", "bg_01_nuages", "bg_02_mer_revue"), preview_background_layers(mode)):
            bg_layer.save(directory / f"{bg_name}.png", optimize=True)
        scene = composite(all_layers)
        scene.save(directory / "COMPOSITION.png", optimize=True)
        review = preview_background(mode)
        review = Image.alpha_composite(review, scene)
        review.save(directory / "PREVIEW.png", optimize=True)
        manifest["placements"][mode] = placements

    # Fill the hashes only after files exist, so the manifest pins the render.
    manifest["files"] = {}
    for p in sorted(OUT.rglob("*.png")):
        manifest["files"][str(p.relative_to(OUT))] = sha(p)
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print(f"Built {manifest['id']} — {len(LAYER_NAMES)} layers × 2 ambiances, 4 water phases.")


if __name__ == "__main__":
    main()
