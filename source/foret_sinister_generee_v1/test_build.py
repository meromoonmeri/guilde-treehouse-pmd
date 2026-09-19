#!/usr/bin/env python3
"""Tests V1 — foret Sinister generee (partition + animation)."""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REN = os.path.join(ROOT, "renders", "foret_sinister_generee_v1")
CAL = os.path.join(REN, "calques")
ANI = os.path.join(REN, "animation")
ORDER = ["01_sol", "02_chemin", "03_sous_bois", "04_rochers", "05_troncs", "06_canpees", "07_profondeur", "08_fringe"]
N = 0

def check(name, cond):
    global N
    assert cond, "FAIL: " + name
    N += 1
    print("PASS %d - %s" % (N, name))

brut = np.asarray(Image.open(os.path.join(REN, "bruts", "foret_sinister_complete.png")).convert("RGB"))
H, W, _ = brut.shape
check("scene 848x1264, grille 8px", (W, H) == (848, 1264) and W % 8 == 0 and H % 8 == 0)

comp = np.zeros((H, W, 3), np.uint8)
union = np.zeros((H, W), bool)
counts = {}
for name in ORDER:
    la = np.asarray(Image.open(os.path.join(CAL, "SinisterGenV1_%s.png" % name)))
    check("calque %s RGBA %dx%d" % (name, W, H), la.shape == (H, W, 4))
    m = la[:, :, 3] > 0
    check("calque %s alpha stricte 0/255" % name, bool(((la[:, :, 3] == 0) | (la[:, :, 3] == 255)).all()))
    counts[name] = int(m.sum())
    comp[m] = la[m][:, :3]
    union |= m
check("recomposition = brut exact", bool((comp.astype(int) != brut.astype(int)).sum() == 0))
check("couverture totale", bool(union.all()))
check("sol opaque", counts["01_sol"] == W * H)
check("chaque calque superieur non vide", all(counts[n] > 500 for n in ORDER[1:]))
check("composite.png = brut", bool((np.asarray(Image.open(os.path.join(REN, "SinisterGenV1_composite.png")).convert("RGB")).astype(int) != brut.astype(int)).sum() == 0))

man = json.load(open(os.path.join(CAL, "manifest.json")))
check("manifest counts coherents", man["counts"] == counts and man["diff_vs_brut"] == 0)

f0 = np.asarray(Image.open(os.path.join(ANI, "frame_00.png")).convert("RGB"))
check("anim frame0 = brut", bool((f0.astype(int) != brut.astype(int)).sum() == 0))
frames = [np.asarray(Image.open(os.path.join(ANI, "frame_%02d.png" % t)).convert("RGB")) for t in range(8)]
diffs = [bool((frames[t].astype(int) != f0.astype(int)).any()) for t in range(1, 8)]
check("anim 7 frames distinctes", all(diffs))
can = np.asarray(Image.open(os.path.join(CAL, "SinisterGenV1_06_canpees.png")))[:, :, 3] > 0
moved = (frames[4].astype(int) != f0.astype(int)).any(axis=2)
check("anim : seule canopee bouge", bool((moved & (~can)).sum() == 0) and moved.sum() > 1000)
check("webp present", os.path.getsize(os.path.join(REN, "SinisterGenV1_animation.webp")) > 100000)
check("gif present", os.path.getsize(os.path.join(REN, "SinisterGenV1_animation.gif")) > 100000)
print("TOUS LES TESTS PASS (%d)" % N)
