"""FX poussiere proposes (12 frames, boucle parfaite).

Translations pures (RGB exacts du brut) + alpha fixe 150 pour les voiles
(translucidite documentee, pas des pixels natifs). Mouvements sinusoidaux
de periode 12 (ou diviseur) -> frame 12 == frame 0 exactement.
"""
from pathlib import Path
import numpy as np
from PIL import Image
from scipy.ndimage import label
from build import load_small, flood_transparent, despill, clean

R = Path(__file__).resolve().parents[2]
OUT = R / "renders/aride_generee_v1"
N = 12
WISP_ALPHA = 150

# voiles : (nom, dy_place) ; les x restent ceux du brut (/3)
WISPS = ["voile0", "voile1", "voile2"]
PHASES = [0.0, 2.1, 4.2]
AMPS = [12, 10, 8]
# repositionnes sur le sol (le brut les met en haut, zone des parois)
WISP_POS = [(40, 195), (150, 232), (180, 160)]


def wisp_dx(i, ph, amp):
    return int(round(amp * np.sin(2 * np.pi * i / N + ph)))


def grain_dx(i, k):
    return int(round(8 * np.sin(2 * np.pi * i / N + 1.0 + k * 0.7)))


def grain_dy(i, k):
    return int(round(-5 * np.sin(4 * np.pi * i / N + k * 0.4)))


def main():
    fx = load_small("fx_poussiere.png")
    rgba, _ = flood_transparent(fx)
    rgba = despill(rgba)
    solid = rgba[:, :, 3] > 0
    lab, n = label(solid)
    comps = []
    for i in range(1, n + 1):
        m = lab == i
        if m.sum() > 80:
            yy, xx = np.where(m)
            comps.append({"n": int(m.sum()),
                          "bbox": [int(xx.min()), int(yy.min()),
                                   int(xx.max()), int(yy.max())],
                          "id": i})
    comps.sort(key=lambda c: c["bbox"][1])
    print("fx composantes:", [(c["bbox"], c["n"]) for c in comps])
    wcomps = [c for c in comps if c["n"] > 300]
    gcomps = [c for c in comps if c["n"] <= 300 and c["bbox"][1] > 150]
    assert len(wcomps) == 3 and len(gcomps) >= 3, (wcomps, gcomps)

    def sprite(c):
        x0, y0, x1, y1 = c["bbox"]
        return clean(rgba[y0:y1 + 1, x0:x1 + 1].copy())

    wisps = [sprite(c) for c in wcomps]
    grains = [(sprite(c), c["bbox"]) for c in gcomps]
    # translucidite des voiles
    for w in wisps:
        w[:, :, 3] = np.where(w[:, :, 3] > 0, WISP_ALPHA, 0).astype(np.uint8)
    (OUT / "fx").mkdir(exist_ok=True)
    for w, name in zip(wisps, WISPS):
        Image.fromarray(w).save(OUT / "fx" / f"{name}.png")
    for k, (g, _) in enumerate(grains):
        Image.fromarray(g).save(OUT / "fx" / f"grain_{k}.png")

    for i in range(N):
        f = np.zeros((288, 408, 4), np.uint8)
        for w, (x0, y0), ph, amp in zip(wisps, WISP_POS, PHASES, AMPS):
            dx = wisp_dx(i, ph, amp)
            h, ww = w.shape[:2]
            x = min(max(x0 + dx, 0), 408 - ww)
            f[y0:y0 + h, x:x + ww] = np.where(
                w[:, :, 3:4] > 0, w, f[y0:y0 + h, x:x + ww])
        for k, (g, (gx0, gy0, _, _)) in enumerate(grains):
            gdx = grain_dx(i, k)
            gdy = grain_dy(i, k)
            h, ww = g.shape[:2]
            gx = min(max(gx0 + gdx, 0), 408 - ww)
            gy = min(max(gy0 + gdy, 0), 288 - h)
            f[gy:gy + h, gx:gx + ww] = np.where(
                g[:, :, 3:4] > 0, g, f[gy:gy + h, gx:gx + ww])
        Image.fromarray(f).save(OUT / "fx" / f"frame_{i:02d}.png")
    print(f"fx: {N} frames OK, {len(grains)} grains")


if __name__ == "__main__":
    main()
