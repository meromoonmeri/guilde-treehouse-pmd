"""Construit le sol du Jardin secret v1 par synthèse guidée depuis secretgarden.png."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import layout as L  # noqa: E402
from quilt import Quilter  # noqa: E402
from segment import BOXES, REF  # noqa: E402

WORK = HERE / "travail"

# Restes d'ombres d'arbres laissés dans le sol d'origine : exclus des patchs sources
EXCLUDE_REF = [(40, 176, 118, 214), (272, 126, 352, 166), (118, 0, 292, 112)]  # dernière = rayon + halo


def exemplar():
    seg = np.load(HERE / "segmentation" / "segmentation.npz")
    ref = np.array(Image.open(REF).convert("RGB"))
    cls = seg["cls"].astype(np.int8)
    tone = seg["tone"]
    objects = seg["objects"]
    valid = ~ndi.binary_dilation(objects, np.ones((5, 5)))
    for x0, y0, x1, y1 in EXCLUDE_REF:
        valid[y0:y1, x0:x1] = False
    fe = L.features(cls, tone)
    return ref, cls, tone, objects, valid, fe


def build(seed: int = 7, block: int = 24, overlap: int = 8, tol: float = 0.06):
    WORK.mkdir(exist_ok=True)
    ref, rcls, rtone, objects, valid, fe = exemplar()
    cls_t = L.target_classes(rcls)
    tone_t = L.target_tone()
    # ton de la référence dans la zone du module
    x0, y0, x1, y1 = L.MODULE_REF
    tone_t[y0:y1, x0 + L.DX:x1 + L.DX] = rtone[y0:y1, x0:x1]
    ft = L.features(cls_t, tone_t)

    # pixels imposés : module d'origine sans les objets (le sol caché sera synthétisé)
    fixed_mask = np.zeros((L.H, L.W), bool)
    fixed_rgb = np.zeros((L.H, L.W, 3), np.uint8)
    fixed_src = np.full((L.H, L.W, 2), -1, np.int32)
    sub_obj = ndi.binary_dilation(objects, np.ones((3, 3)))[y0:y1, x0:x1]
    region = np.zeros((L.H, L.W), bool)
    region[y0 + L.DY:y1 + L.DY, x0 + L.DX:x1 + L.DX] = ~sub_obj
    fixed_mask |= region
    fixed_rgb[y0 + L.DY:y1 + L.DY, x0 + L.DX:x1 + L.DX] = ref[y0:y1, x0:x1]
    yy, xx = np.mgrid[y0:y1, x0:x1]
    fixed_src[y0 + L.DY:y1 + L.DY, x0 + L.DX:x1 + L.DX] = np.stack([yy, xx], -1)

    q = Quilter(ref, fe, valid, block=block, overlap=overlap, w_ov=1.0, w_f=1.0, tol=tol, seed=seed)
    t = time.time()
    img, src, picks = q.synth(ft, fixed_rgb, fixed_src, fixed_mask)
    print(f"synthèse {time.time() - t:.1f}s, {len(picks)} patchs")
    np.savez_compressed(WORK / "sol.npz", rgb=img, src=src, cls=cls_t, tone=tone_t,
                        fixed=fixed_mask, picks=np.array(picks))
    Image.fromarray(img).save(WORK / "sol.png")
    pal = np.array([[30, 30, 90], [120, 220, 120], [230, 220, 60]], np.uint8)
    Image.fromarray(pal[cls_t]).save(WORK / "plan.png")
    return img, src


if __name__ == "__main__":
    build(seed=int(sys.argv[1]) if len(sys.argv) > 1 else 7)
