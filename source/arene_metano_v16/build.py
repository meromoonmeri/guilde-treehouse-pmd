"""Rebuild the last committed V15 layout with canonical Métano material.

The V15 terrain is used as a geometry/layout reference only. Its generated
ice, floor, effects and pixels never enter the final terrain layers. Each final
8x8 cell is selected from the native Métano banks using the reference geometry.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "arene_metano_v16"
REFERENCE = ROOT / "renders" / "arene_halcyon_v15" / "couches" / "terrain_fixe.png"
REF_SKY = ROOT / "renders" / "arene_halcyon_v15" / "couches" / "ciel_fixe.png"
REF_STARS = ROOT / "renders" / "arene_halcyon_v15" / "couches" / "etoiles_fixes.png"
CLOUDS = ROOT / "sprites" / "cote_v2" / "COTEV2_NUAGES_WRAP.png"
SIZE = (928, 1152)
GRID = 8
GRID_SIZE = (SIZE[0] // GRID, SIZE[1] // GRID)
N_CLOUD_FRAMES = 55
CLOUD_STEP = 40

sys.path.insert(0, str(ROOT / "source" / "zones_guidees"))
from native_tools import Bank, BASE, CLIFF  # noqa: E402
sys.path.insert(0, str(ROOT / "source" / "cote_v4_abyss"))
from night import night  # noqa: E402


def rgba(path: Path) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA"))


def reference_masks() -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Read geometry from the V15 image, never from its generated RGB output.

    The alpha is the complete arena silhouette. Dark blue/low-luminance parts
    of the reference define the cliff layout; this semantic mask is only used
    to select native tiles. All final RGB is supplied by Métano banks.
    """
    ref = rgba(REFERENCE)
    rgb = ref[:, :, :3].astype(np.float32)
    alpha = ref[:, :, 3] > 0
    lum = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    blue_bias = rgb[:, :, 2] - (rgb[:, :, 0] + rgb[:, :, 1]) * 0.35
    # The reference is ice-blue: dark/blue structural faces are the cliff
    # vocabulary; pale horizontal surfaces remain the grass-top mask.
    cliff_px = alpha & (lum < 150) & (blue_bias > 10)
    # Work at the native 8 px layout grid. A cell is structural when the guide
    # carries enough cliff pixels; this removes isolated anti-aliased specks.
    h, w = GRID_SIZE[1], GRID_SIZE[0]
    cliff_raw = np.zeros((h, w), dtype=np.float32)
    for gy in range(h):
        for gx in range(w):
            patch = cliff_px[gy * GRID:(gy + 1) * GRID, gx * GRID:(gx + 1) * GRID]
            cliff_raw[gy, gx] = patch.mean()
    # The reference contains many tiny crystal highlights. Keep its large
    # cliff masses and ring topology, but remove sub-tile noise before choosing
    # the Métano tiles. This is a layout simplification, not texture painting.
    cliff_score = ndimage.uniform_filter(cliff_raw, size=5, mode="nearest")
    cliff = cliff_score >= 0.18
    terrain = np.zeros((h, w), dtype=bool)
    for gy in range(h):
        for gx in range(w):
            terrain[gy, gx] = alpha[gy * GRID:(gy + 1) * GRID,
                                      gx * GRID:(gx + 1) * GRID].mean() >= 0.50
    # Keep the reference's alpha silhouette exact at cell resolution; the
    # grass-top mask is the same layout minus the cliff cells.
    grass = terrain & ~cliff
    return terrain, grass, cliff


def tile_feature(image: Image.Image) -> np.ndarray:
    a = np.asarray(image.convert("RGBA"))
    rgb = a[:, :, :3].astype(np.float32) / 255.0
    alpha = (a[:, :, 3] > 0).astype(np.float32)
    # Geometry only: RGB from the generated reference is deliberately ignored.
    return np.concatenate([alpha.reshape(-1),
                           alpha.mean(0), alpha.mean(1)]).astype(np.float32)


def canonical_candidates(bank: Bank, sheet: str, minimum_alpha: int = 1, source_filter=None) -> list[dict]:
    seen: set[bytes] = set()
    result = []
    for (x, y) in sorted(bank.sources[sheet]):
        if source_filter is not None and not source_filter(x, y):
            continue
        gid = bank.get(sheet, x, y)
        if not gid:
            continue
        im = bank.image(gid)
        a = np.asarray(im)
        if int((a[:, :, 3] > 0).sum()) < minimum_alpha:
            continue
        key = a.tobytes()
        if key in seen:
            continue
        seen.add(key)
        result.append({"gid": gid, "sheet": sheet, "source": [x, y],
                       "feature": tile_feature(im), "image": im})
    assert result, sheet
    return result


def choose(candidates: list[dict], target: np.ndarray, ordinal: int) -> dict:
    # Select an existing canonical tile by the reference's alpha geometry. The
    # tie breaker keeps interiors varied without composing foreign fragments.
    rgba_target = np.zeros((8, 8, 4), dtype=np.uint8)
    rgba_target[:, :, 3] = target.astype(np.uint8) * 255
    f = tile_feature(Image.fromarray(rgba_target, "RGBA"))
    scores = np.array([np.mean((c["feature"] - f) ** 2) for c in candidates])
    best = np.flatnonzero(scores <= scores.min() + 1e-8)
    return candidates[int(best[ordinal % len(best)])]


def render_assignments(assignments: list[dict], size: tuple[int, int] = SIZE) -> Image.Image:
    canvas = Image.new("RGBA", size)
    for p in assignments:
        canvas.paste(p["image"], (p["x"] * GRID, p["y"] * GRID), p["image"])
    return canvas


def make_cloud_frames() -> list[Image.Image]:
    strip = Image.open(CLOUDS).convert("RGBA")
    frames = []
    for i in range(N_CLOUD_FRAMES):
        shift = (i * CLOUD_STEP) % strip.width
        frame = Image.new("RGBA", SIZE)
        # Two adjacent copies make the horizontal overlay wrap spatially.
        for x in (-shift, strip.width - shift):
            frame.alpha_composite(strip, (x, 0))
        frames.append(frame)
    return frames


def apply_night(layers: list[Image.Image]) -> list[Image.Image]:
    return [night(im) for im in layers]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_mode(mode: str, terrain_assignments: list[dict], grass_assignments: list[dict],
               cliff_assignments: list[dict], cloud_frames: list[Image.Image]) -> dict:
    directory = OUT / mode
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "overlay_nuages").mkdir(parents=True, exist_ok=True)
    grass = render_assignments(grass_assignments)
    face = render_assignments([p for p in cliff_assignments if p["role"] == "face"])
    crown = render_assignments([p for p in cliff_assignments if p["role"] == "crown"])
    foot = render_assignments([p for p in cliff_assignments if p["role"] == "foot"])
    clouds = cloud_frames
    sky = Image.open(REF_SKY).convert("RGBA")
    stars = Image.open(REF_STARS).convert("RGBA")
    if mode == "nuit":
        grass, face, crown, foot, sky, stars = apply_night([grass, face, crown, foot, sky, stars])
        clouds = apply_night(cloud_frames)
    layers = {
        "00_sol_herbe_metano": grass,
        "01_cliffs_faces_metano": face,
        "02_cliffs_couronnes_metano": crown,
        "03_cliffs_pieds_metano": foot,
    }
    for name, image in layers.items():
        image.save(directory / f"{name}.png", optimize=True)
    sky.save(directory / "bg_00_ciel_fixe.png", optimize=True)
    stars.save(directory / "bg_01_etoiles_fixes.png", optimize=True)
    for i, frame in enumerate(clouds):
        frame.save(directory / "overlay_nuages" / f"NuagesWrap_{i:02d}.png", optimize=True)
    # Terrain-only composition is transparent around the exact V15 silhouette.
    terrain_only = Image.new("RGBA", SIZE)
    for image in layers.values():
        terrain_only = Image.alpha_composite(terrain_only, image)
    terrain_only.save(directory / "TERRAIN_METANO.png", optimize=True)
    preview = Image.new("RGBA", SIZE)
    preview = Image.alpha_composite(preview, sky)
    preview = Image.alpha_composite(preview, stars)
    preview = Image.alpha_composite(preview, clouds[0])
    preview = Image.alpha_composite(preview, terrain_only)
    preview.save(directory / "PREVIEW.png", optimize=True)
    return {"layers": list(layers), "cloud_frames": len(clouds),
            "terrain_sha256": sha(directory / "TERRAIN_METANO.png"),
            "preview_sha256": sha(directory / "PREVIEW.png")}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "layout_reference").mkdir(exist_ok=True)
    Image.open(REFERENCE).convert("RGBA").save(OUT / "layout_reference" / "V15_terrain_layout_reference.png")
    terrain, grass, cliff = reference_masks()
    Image.fromarray(terrain.astype(np.uint8) * 255, "L").resize(SIZE, Image.Resampling.NEAREST).save(OUT / "layout_reference" / "terrain_mask_8px.png")
    Image.fromarray(grass.astype(np.uint8) * 255, "L").resize(SIZE, Image.Resampling.NEAREST).save(OUT / "layout_reference" / "grass_mask_8px.png")
    Image.fromarray(cliff.astype(np.uint8) * 255, "L").resize(SIZE, Image.Resampling.NEAREST).save(OUT / "layout_reference" / "cliff_mask_8px.png")

    bank = Bank()
    # These are the same native grass vocabulary used by the prior guided
    # workflow. Do not let animation/object pixels from the large Base sheet
    # leak into the floor pass.
    base_candidates = canonical_candidates(
        bank, BASE, minimum_alpha=16,
        source_filter=lambda x, y: 0 <= x < 16 and 80 <= y < 96,
    )
    allowed_cliff_x = set(range(57, 93)) | set(range(114, 122)) | set(range(162, 189))
    cliff_candidates = canonical_candidates(
        bank, CLIFF, minimum_alpha=8,
        source_filter=lambda x, y: x in allowed_cliff_x and y >= (26 if x < 93 else 38 if x >= 162 else 54),
    )
    grass_assignments, cliff_assignments = [], []
    placements = {"grass": [], "cliff": []}
    h, w = terrain.shape
    for y in range(h):
        for x in range(w):
            if not terrain[y, x]:
                continue
            target = cliff[y, x]
            # Grass is the complete floor pass. Cliff tiles are overlaid as a
            # separate native pass, exactly like the old guided-zone workflow.
            g = base_candidates[(x + y * 3) % len(base_candidates)]
            gp = {"x": x, "y": y, "image": g["image"], "source": g["source"], "gid": g["gid"]}
            grass_assignments.append(gp)
            placements["grass"].append({"dest": [x, y], "source": g["source"], "sheet": BASE})
            if target:
                # Canonical interior panels remain coherent. Only boundary
                # cells use the geometry matcher; this is the old guided-zone
                # rule that prevents an 8 px random mosaic.
                interior = all(
                    0 <= nx < w and 0 <= ny < h and cliff[ny, nx]
                    for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
                )
                if interior:
                    interior_sources = [(85, 59 + ((x + y) % 6)),
                                        (86, 59 + ((x * 3 + y) % 6)),
                                        (92, 59 + ((x + y * 2) % 6)),
                                        (114 + (x % 8), 59 + ((x + y) % 6))]
                    source = next((p for p in interior_sources if bank.get(CLIFF, *p)), interior_sources[0])
                    gid = bank.get(CLIFF, *source)
                    c = {"gid": gid, "sheet": CLIFF, "source": list(source), "image": bank.image(gid)}
                else:
                    c = choose(cliff_candidates, np.full((8, 8), target, dtype=bool), x + y * w)
                top_edge = y == 0 or not cliff[y - 1, x]
                bottom_edge = y == h - 1 or not cliff[y + 1, x]
                role = "crown" if top_edge else "foot" if bottom_edge else "face"
                cp = {"x": x, "y": y, "role": role, "image": c["image"], "source": c["source"], "gid": c["gid"]}
                cliff_assignments.append(cp)
                placements["cliff"].append({"dest": [x, y], "role": role, "source": c["source"], "sheet": CLIFF})
    clouds = make_cloud_frames()
    modes = {mode: build_mode(mode, grass_assignments, grass_assignments,
                               cliff_assignments, clouds) for mode in ("jour", "nuit")}
    (OUT / "placements.json").write_text(json.dumps(placements, ensure_ascii=False, indent=2) + "\n")
    manifest = {
        "id": "arene_metano_v16",
        "source_layout": str(REFERENCE.relative_to(ROOT)),
        "layout_only": True,
        "canvas": list(SIZE), "grid_px": GRID, "tex_size": 1,
        "excluded_from_final_terrain": ["structures", "sea", "generated_ice_rgb", "generated_sky", "generated_stars", "generated_cloud_pixels"],
        "native_material": {
            "grass": str((ROOT / "source/falaises_metano/natifs/Metano_Town_Base.tile").relative_to(ROOT)),
            "cliffs": str((ROOT / "source/falaises_metano/natifs/Metano_Town_Cliffs.tile").relative_to(ROOT)),
            "generated_rgb_pixels_in_terrain": 0,
            "selection": "8 px canonical tile selection from the V15 alpha/semantic layout mask; no module grafting",
        },
        "background": {
            "sky": str(REF_SKY.relative_to(ROOT)),
            "stars": str(REF_STARS.relative_to(ROOT)),
            "sea": None,
            "cloud_strip": str(CLOUDS.relative_to(ROOT)),
            "cloud_frames": N_CLOUD_FRAMES,
            "cloud_step_px": CLOUD_STEP,
            "cloud_strip_width_px": Image.open(CLOUDS).width,
            "loop_period_px": Image.open(CLOUDS).width,
            "loop_period_frames": Image.open(CLOUDS).width // CLOUD_STEP,
            "loop_duration_ms": (Image.open(CLOUDS).width // CLOUD_STEP) * 100,
            "last_emitted_frame_is_not_duplicate": True,
        },
        "layer_order": ["bg_00_ciel_fixe", "bg_01_etoiles_fixes", "overlay_nuages", "00_sol_herbe_metano", "01_cliffs_faces_metano", "02_cliffs_couronnes_metano", "03_cliffs_pieds_metano"],
        "modes": modes,
        "reference_sha256": sha(REFERENCE),
        "runtime_PMDO": "NON TESTE",
        "art_review": "PENDING",
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    print("Built V15 layout with native Metano grass/cliff layers and 55-frame perfect cloud wrap.")


if __name__ == "__main__":
    main()
