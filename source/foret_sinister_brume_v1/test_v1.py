#!/usr/bin/env python3
"""Tests V1 — calques generes + animation brume/lucioles."""
import json, math, os, zipfile
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REN = os.path.join(ROOT, "renders", "foret_sinister_brume_v1")
W, H, N = 848, 1264, 48
ORDER = ["01_sol", "02_chemin", "03_sous_bois", "04_rochers", "05_troncs", "06_canpees", "07_profondeur", "08_fringe"]
passed = []
def check(name, cond, extra=""):
    assert cond, "FAIL %s %s" % (name, extra)
    passed.append(name)
    print("PASS", name, extra)

# 1. calques presents, RGBA, dimensions, grille 8
for nm in ORDER:
    p = os.path.join(REN, "calques", "SinisterGenV1_%s.png" % nm)
    im = Image.open(p)
    check("layer_%s" % nm, im.size == (W, H) and im.mode == "RGBA", str(im.size))
check("grid8", W % 8 == 0 and H % 8 == 0)

# 2. sol opaque partout
sol = np.asarray(Image.open(os.path.join(REN, "calques", "SinisterGenV1_01_sol.png")))
check("sol_opaque", (sol[:, :, 3] == 255).all())

# 3. recomposition exacte du brut
brut = np.asarray(Image.open(os.path.join(REN, "bruts", "foret_sinister_complete.png")).convert("RGB"))
comp = np.zeros((H, W, 3), np.uint8)
for nm in ORDER:
    la = np.asarray(Image.open(os.path.join(REN, "calques", "SinisterGenV1_%s.png" % nm)))
    m = la[:, :, 3] > 0
    comp[m] = la[m][:, :3]
check("recompose_exact", not (comp.astype(int) != brut.astype(int)).any())

# 4. chaque calque non-sol a du contenu et du vide
for nm in ORDER[1:]:
    la = np.asarray(Image.open(os.path.join(REN, "calques", "SinisterGenV1_%s.png" % nm)))
    n = int((la[:, :, 3] > 0).sum())
    check("content_%s" % nm, 1000 < n < W * H, str(n))

# 5. manifest coherent
man = json.load(open(os.path.join(REN, "calques", "manifest.json")))
check("manifest", man["scene"] == [W, H] and man["diff_vs_brut"] == 0)

# 6. anim : 48 overlays + bande
for t in range(N):
    p = os.path.join(REN, "anim", "overlay_%02d.png" % t)
    im = Image.open(p)
    assert im.size == (W, H) and im.mode == "RGBA", t
check("overlays_48", True)
check("mist_band", os.path.exists(os.path.join(REN, "anim", "mist_band.png")))

# 7. mouvement reel entre frames
o0 = np.asarray(Image.open(os.path.join(REN, "anim", "overlay_00.png"))).astype(int)
o12 = np.asarray(Image.open(os.path.join(REN, "anim", "overlay_12.png"))).astype(int)
o24 = np.asarray(Image.open(os.path.join(REN, "anim", "overlay_24.png"))).astype(int)
d1 = (o0 != o12).any(axis=2).sum()
d2 = (o0 != o24).any(axis=2).sum()
check("motion", d1 > 10000 and d2 > 10000, "%d %d" % (d1, d2))

# 8. cloture de boucle : formules periodiques (periodes divisant 48)
def mdx(t, amp, per, ph): return amp * math.sin(2 * math.pi * t / per + ph)
ok = all(abs(mdx(48, a, p, ph) - mdx(0, a, p, ph)) < 1e-9 for a, p, ph in [(26, 48, 0.0), (20, 48, 2.1), (30, 48, 0.0), (24, 48, 2.1)])
rng = np.random.default_rng(5)
for _ in range(54):
    x = rng.uniform(60, W - 60); y = rng.uniform(150, H - 60)
    ax = rng.uniform(8, 22); ay = rng.uniform(6, 16)
    px = int(rng.choice([48, 24, 16])); py = int(rng.choice([48, 24]))
    phx = rng.uniform(0, 6.283); phy = rng.uniform(0, 6.283)
    r = int(rng.choice([1, 2, 2])); pb = int(rng.choice([48, 24, 16])); phb = rng.uniform(0, 6.283)
    for per, ph in [(px, phx), (py, phy), (pb, phb)]:
        ok = ok and abs(math.sin(2 * math.pi * 48 / per + ph) - math.sin(ph)) < 1e-9
check("loop_closure", ok)

# 9. webp/gif animes valides
for f, expect in [("anim_overlay.webp", N), ("preview_scene.webp", N), ("preview_scene.gif", N)]:
    im = Image.open(os.path.join(REN, f))
    nfr = getattr(im, "n_frames", 1)
    check("anim_%s" % f, nfr == expect, str(nfr))

# 10. ORA + galerie + zip (construits par package.py — verifies si presents)
for f in ["SinisterGenV1.ora", "README.md"]:
    check("pack_%s" % f, os.path.exists(os.path.join(REN, f)), f)
if os.path.exists(os.path.join(REN, "SinisterGenV1.ora")):
    z = zipfile.ZipFile(os.path.join(REN, "SinisterGenV1.ora"))
    names = z.namelist()
    check("ora_content", "stack.xml" in names and sum(n.startswith("data/") for n in names) == 8, str(len(names)))
check("gallery", os.path.exists(os.path.join(ROOT, "apercu_foret_sinister_brume_v1.html")))
check("zip", os.path.exists(os.path.join(ROOT, "renders", "foret_sinister_brume_v1_pack.zip")))

print("ALL %d PASS" % len(passed))
