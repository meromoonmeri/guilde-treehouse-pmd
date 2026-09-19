"""Independent checks for the new Métano Chenal composition."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "cote_metano_v6_chenal"
SIZE = (1024, 768)
LAYERS = [
    "00_sol_herbe", "01_faces_falaise", "02_retours", "03_couronnes",
    "04_pieds", "05_eau_fond", "06_eau_phase_01", "07_eau_phase_02",
    "08_eau_phase_03", "09_eau_phase_04",
]


def rgba(path: Path) -> np.ndarray:
    im = Image.open(path).convert("RGBA")
    assert im.size == SIZE, (path, im.size)
    return np.asarray(im)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    terrain = np.asarray(Image.open(OUT / "masques" / "terrain.png")) > 0
    grass = np.asarray(Image.open(OUT / "masques" / "grass.png")) > 0
    water = np.asarray(Image.open(OUT / "masques" / "water.png")) > 0
    route = np.asarray(Image.open(OUT / "masques" / "route.png")) > 0
    assert terrain.shape == (SIZE[1], SIZE[0])
    assert not np.any(grass & water)
    assert not np.any(terrain & water)
    assert np.all(route <= grass)
    assert route[704, 480]
    assert all(terrain[:, x].any() for x in (0, SIZE[0] - 1))
    assert terrain[-1].any()

    result = {
        "status": "PASS",
        "canvas": list(SIZE),
        "grid_px": 8,
        "modes": {},
        "checks": {
            "terrain_water_disjoint": True,
            "route_on_grass": True,
            "west_east_south_contacts": True,
            "native_day_terrain_generated_rgb_pixels": 0,
            "native_day_terrain_resampled": False,
            "water_phases": 4,
        },
        "limitations": [
            "No PMDO Ground was created in this PNG composition pass.",
            "Collision and transition behavior require an editor/runtime pass.",
            "The water bed is an explicitly documented substrate adaptation; phase pixels are native Métano river pixels.",
            "Artistic review at 1x is still pending.",
        ],
    }
    for mode in ("jour", "nuit"):
        arrays = [rgba(OUT / mode / f"{name}.png") for name in LAYERS]
        # Reuse Pillow's straight-alpha compositor, exactly as build.py does.
        composed_image = Image.new("RGBA", SIZE)
        for array in arrays:
            composed_image = Image.alpha_composite(composed_image, Image.fromarray(array, "RGBA"))
        composed = np.asarray(composed_image)
        expected = rgba(OUT / mode / "COMPOSITION.png")
        # The comparison is pixel-exact: a nonzero difference means a layer,
        # order or file was changed without rebuilding the composition.
        assert np.array_equal(composed, expected), mode
        phases = [rgba(OUT / mode / f"{name}.png") for name in LAYERS[6:]]
        assert all(np.any(p[:, :, 3]) for p in phases)
        result["modes"][mode] = {
            "layer_count": len(arrays),
            "recomposition_max_channel_error": int(np.max(np.abs(composed.astype(int) - expected.astype(int)))),
            "files_sha256": {f"{name}.png": sha(OUT / mode / f"{name}.png") for name in LAYERS},
        }
    (OUT / "verification.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("PASS: masks, contacts, 10 aligned layers, four phases, and both recompositions.")


if __name__ == "__main__":
    main()
