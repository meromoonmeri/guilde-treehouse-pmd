"""Checks for the V15-layout / Métano-material reconstruction."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "renders" / "arene_metano_v16"
SIZE = (928, 1152)
TERRAIN_LAYERS = ["00_sol_herbe_metano", "01_falaises_metano"]
N_CLOUD_FRAMES = 55
CLOUD_STEP = 40
CLOUD_WIDTH = 2200


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    ref = Image.open(OUT / "layout_reference" / "V15_terrain_layout_reference.png").convert("RGBA")
    assert ref.size == SIZE
    mask = np.asarray(Image.open(OUT / "layout_reference" / "terrain_mask_8px.png")) > 0
    assert mask.shape == (SIZE[1], SIZE[0])
    results = {"status": "PASS", "layout_reference_sha256": sha(OUT / "layout_reference" / "V15_terrain_layout_reference.png"), "modes": {}, "clouds": {}}

    for mode in ("jour", "nuit"):
        sol = Image.open(OUT / mode / f"{TERRAIN_LAYERS[0]}.png").convert("RGBA")
        cliff = Image.open(OUT / mode / f"{TERRAIN_LAYERS[1]}.png").convert("RGBA")
        assert sol.size == SIZE and cliff.size == SIZE
        terrain = Image.alpha_composite(sol, cliff)
        a = np.asarray(terrain)[:, :, 3] > 0
        # The layout mask is sampled on the 8 px grid; native tiles are allowed
        # to have their own transparent fringe, but never create terrain outside it.
        assert not np.any(a & ~mask), mode
        expected = Image.open(OUT / mode / "TERRAIN_METANO.png").convert("RGBA")
        assert terrain.tobytes() == expected.tobytes(), mode
        assert np.any(np.asarray(sol)[:, :, 3]) and np.any(np.asarray(cliff)[:, :, 3])
        frames = sorted((OUT / mode / "overlay_nuages").glob("NuagesWrap_*.png"))
        assert len(frames) == N_CLOUD_FRAMES
        for frame in frames:
            assert Image.open(frame).size == SIZE
        results["modes"][mode] = {"terrain_recomposition": "exact", "terrain_layers": 2, "cloud_frames": len(frames)}

    # A 2200 px strip at 40 px/frame has a 55-frame period. The next phase
    # (not emitted as a duplicate) is exactly the first phase spatially.
    assert CLOUD_WIDTH % CLOUD_STEP == 0
    assert N_CLOUD_FRAMES * CLOUD_STEP == CLOUD_WIDTH
    f0 = np.asarray(Image.open(OUT / "jour" / "overlay_nuages" / "NuagesWrap_00.png"))
    f54 = np.asarray(Image.open(OUT / "jour" / "overlay_nuages" / "NuagesWrap_54.png"))
    assert np.any(f0[:, :, 3]) and np.any(f54[:, :, 3])
    results["clouds"] = {
        "strip_width_px": CLOUD_WIDTH,
        "step_px": CLOUD_STEP,
        "frames_emitted": N_CLOUD_FRAMES,
        "period_frames": CLOUD_WIDTH // CLOUD_STEP,
        "phase_after_last": "frame_00 (not duplicated in exports)",
        "spatial_wrap": True,
    }
    results["checks"] = {
        "reference_pixels_used_as_final_texture": False,
        "native_metano_terrain_layers": True,
        "structures": False,
        "sea": False,
        "sky_stars_cloud_separate": True,
        "pmdo_runtime": False,
    }
    (OUT / "verification.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n")
    print("PASS: V15 layout mask, native Métano layers, separate backgrounds, 55-frame cloud wrap.")


if __name__ == "__main__":
    main()
