#!/usr/bin/env python3
"""Foret Sinister generee V1 — partition en calques d'un brut genere.

Entree : renders/foret_sinister_brume_v1/bruts/foret_sinister_complete.png (848x1264, genere).
Methode : dessin genere integre (PAS des bouts de map, PAS des pixels natifs).
Sortie : 8 calques PNG + composite + planche. Aucun resampling.
Recomposition des calques = brut exact au pixel pres.
Le sol sous les elements est reconstitue depuis l'herbe/chemin visibles
de la MEME image (pas de texture exterieure).
"""
import json, os
import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REN = os.path.join(ROOT, "renders", "foret_sinister_brume_v1")
os.makedirs(os.path.join(REN, "calques"), exist_ok=True)
os.makedirs(os.path.join(REN, "review"), exist_ok=True)

gen = np.asarray(Image.open(os.path.join(REN, "bruts", "foret_sinister_complete.png")).convert("RGB")).astype(int)
H, W, _ = gen.shape
assert (W % 8, H % 8) == (0, 0), (W, H)
R, G, B = gen[:, :, 0], gen[:, :, 1], gen[:, :, 2]
lum = R + G + B
yy, xx = np.mgrid[0:H, 0:W]

# --- 02 chemin : tan + composante touchee au bas ---
tan = (R - B > 35) & (R > 110) & (G > 80) & (G - R < 25)
tan = ndimage.binary_closing(tan, iterations=2)
lab, n = ndimage.label(tan)
best, bestsize = None, 0
for i in range(1, n + 1):
    m = lab == i
    if m[H - 8:H, :].any() and m.sum() > bestsize:
        best, bestsize = m, m.sum()
if best is None:
    for i in range(1, n + 1):
        m = lab == i
        if m.sum() > bestsize:
            best, bestsize = m, m.sum()
path_m = ndimage.binary_fill_holes(best)
print("chemin px:", int(path_m.sum()))

# --- 04 rochers : gris bleutes (B-R>8), hors chemin ---
gray = (B - R > 8) & (R > 25) & (R < 185) & (B > 50) & ((G - R) >= 8) & ((G - R) <= 30) & (~path_m)
gray = ndimage.binary_opening(gray, iterations=1)
lab, n = ndimage.label(gray)
rock = np.zeros_like(gray)
for i in range(1, n + 1):
    if (lab == i).sum() >= 60:
        rock |= lab == i
rim = rock & (yy < 330)
rocks = rock & (yy >= 330)
print("rochers px:", int(rocks.sum()), "rim px:", int(rim.sum()))

# --- 07 profondeur : sombre non-vert du tiers nord + rim ---
grove_zone = (yy > 90) & (yy < 290) & (xx > 310) & (xx < 540)
prof_raw = ((lum < 95) & grove_zone & ((G - R) < 12)) | rim
lab, n = ndimage.label(prof_raw)
prof = np.zeros_like(prof_raw)
for i in range(1, n + 1):
    if (lab == i).sum() >= 60:
        prof |= lab == i
profondeur = ndimage.binary_fill_holes(prof)
print("profondeur px:", int(profondeur.sum()))

# --- 08 frange : quasi-noir non-vert colle aux bords ---
edge = (xx < 110) | (xx >= W - 110) | (yy < 60)
fr_raw = (lum < 90) & edge & ((G - R) < 10) & (~profondeur)
lab, n = ndimage.label(fr_raw)
fringe = np.zeros_like(fr_raw)
for i in range(1, n + 1):
    m = lab == i
    touching = m[:, 0].any() or m[:, -1].any() or m[0, :].any()
    if touching and m.sum() >= 200:
        fringe |= m
print("frange px:", int(fringe.sum()))

# --- verts : herbe claire (sol) vs masses sombres ---
taken = path_m | rock | profondeur | fringe
green_all = (G > R + 3) & (G >= B - 5)
lightG = green_all & (G > 85) & (G - R > 15) & (~taken)
canopy_raw = green_all & (~lightG) & (~taken)

# --- 05 troncs : ecorce desaturee au contact des canopees ---
near = ndimage.binary_dilation(canopy_raw, iterations=15)
bark = canopy_raw & ((G - R) <= 24) & ((B - R) < 8) & (R < 135) & near
lab, n = ndimage.label(bark)
trunks = np.zeros_like(bark)
for i in range(1, n + 1):
    if (lab == i).sum() >= 25:
        trunks |= lab == i
print("troncs px:", int(trunks.sum()))

# --- 06 canopees ---
canopy = canopy_raw & (~trunks)
lab, n = ndimage.label(canopy)
can = np.zeros_like(canopy)
for i in range(1, n + 1):
    if (lab == i).sum() >= 40:
        can |= lab == i
canopy = can
print("canopee px:", int(canopy.sum()))

# --- 03 sous-bois : tout le reste sombre (filet,ombres profondes) ---
taken3 = taken | trunks | canopy
under = (~taken3) & (~lightG) & (~path_m)
print("sous-bois px:", int(under.sum()))

sol_direct = lightG

# --- 01_sol : remplit les trous depuis herbe/chemin proches (meme image) ---
hole = ~(sol_direct | path_m)
sol_tex = sol_direct | path_m
_, idx = ndimage.distance_transform_edt(hole, return_indices=True)
rng = np.random.default_rng(11)
jy = rng.integers(-12, 13, size=(H, W))
jx = rng.integers(-12, 13, size=(H, W))
sy = np.clip(idx[0] + jy * hole, 0, H - 1)
sx = np.clip(idx[1] + jx * hole, 0, W - 1)
ok = sol_tex[sy, sx]
sy = np.where(ok, sy, idx[0])
sx = np.where(ok, sx, idx[1])
sol = gen.copy()
sol[hole] = gen[sy[hole], sx[hole]]

layers = {
    "01_sol": (np.ones((H, W), bool), sol),
    "02_chemin": (path_m, gen),
    "03_sous_bois": (under, gen),
    "04_rochers": (rocks, gen),
    "05_troncs": (trunks, gen),
    "06_canpees": (canopy, gen),
    "07_profondeur": (profondeur, gen),
    "08_fringe": (fringe, gen),
}
order = ["01_sol", "02_chemin", "03_sous_bois", "04_rochers", "05_troncs", "06_canpees", "07_profondeur", "08_fringe"]
claim = {}
covered = np.zeros((H, W), bool)
for name in reversed(order):
    m, _ = layers[name]
    claim[name] = m & (~covered)
    covered |= m
assert covered.all(), "pixels orphelins: %d" % int((~covered).sum())
claim["01_sol"] = np.ones((H, W), bool)

# exactitude stricte : le sol n'est repeint QUE sous les calques superieurs
upper = np.zeros((H, W), bool)
for name in order[1:]:
    upper |= claim[name]
sol_final = sol.copy()
sol_final[~upper] = gen[~upper]
layers["01_sol"] = (np.ones((H, W), bool), sol_final)

for name in order:
    m = claim[name]
    _, src = layers[name]
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[m, :3] = src[m].astype(np.uint8)
    rgba[m, 3] = 255
    Image.fromarray(rgba).save(os.path.join(REN, "calques", "SinisterGenV1_%s.png" % name))

comp = np.zeros((H, W, 3), np.uint8)
for name in order:
    m = claim[name]
    _, src = layers[name]
    comp[m] = src[m].astype(np.uint8)
diff = (comp.astype(int) != gen).any(axis=2)
print("pixels differents du brut:", int(diff.sum()))
assert int(diff.sum()) == 0
Image.fromarray(comp).save(os.path.join(REN, "SinisterGenV1_composite.png"))

cell_w, cell_h = 212, 316
sheet = np.full((2 * cell_h + 12, 4 * cell_w + 24, 3), 255, np.uint8)
for i, name in enumerate(order):
    m = claim[name]
    _, _src = layers[name]
    thumb = np.full((H, W, 3), 255, np.uint8)
    thumb[m] = _src[m].astype(np.uint8)
    t = np.asarray(Image.fromarray(thumb).resize((cell_w, cell_h), Image.NEAREST))
    r, c = divmod(i, 4)
    sheet[r * (cell_h + 6):r * (cell_h + 6) + cell_h, c * (cell_w + 8):c * (cell_w + 8) + cell_w] = t
Image.fromarray(sheet).save(os.path.join(REN, "review", "planche_masques.png"))
Image.fromarray(sol_final.astype(np.uint8)).save(os.path.join(REN, "review", "sol_reconstitue.png"))

meta = {"scene": [W, H], "brut": "bruts/foret_sinister_complete.png",
        "brut_sol_var": "bruts/foret_sinister_sol.png (variante non recalee, bonus)",
        "counts": {k: int(v.sum()) for k, v in claim.items()}, "diff_vs_brut": 0}
json.dump(meta, open(os.path.join(REN, "calques", "manifest.json"), "w"), indent=2)
print("OK", meta["counts"])
