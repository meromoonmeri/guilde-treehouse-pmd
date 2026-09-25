"""Thunder Meadow V3b — entrée sans rochers : montagne nord + grotte intégrée, nuages et foudre en contrebas.

Guide de composition généré (generation/terrain_guide.png, ciel magenta), réduit à la
résolution native puis ramené sur la palette exacte de 5394.png (aucune couleur inventée).
Animations canoniques reprises de V1 : palette flash des nuages + frames d'éclairs de la planche.
"""
import json, hashlib, pathlib, zipfile, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "source" / "thunder_meadow_v1"))
REF = ROOT / "5394.png"
GUIDE = HERE / "generation" / "entree_guide_sans_rochers.png"
OUT = ROOT / "renders" / "thunder_meadow_v3b_entree"
PFX = "THUNDERMEADOW_V3B_"
W, H = 456, 336
sheet = np.array(Image.open(REF).convert("RGB")).astype(np.int16)
refmap = sheet[:335, :W]
eq = lambda img, c: np.all(img == np.array(c), axis=-1)

FLASH = [[tuple(int(v) for v in sheet[57 + 9 * r + 3, 519 + 9 * c + 3]) for c in range(8)] for r in range(6)]
allc = sorted(set(map(tuple, refmap.reshape(-1, 3).tolist())))
terrain_pal = np.array([c for c in allc if c not in FLASH[0]], np.int16)

# ---------- guide -> natif ----------
g = Image.open(GUIDE).convert("RGB")
gs = np.array(g.resize((W, H), Image.BOX)).astype(np.int16)
gb = np.array(g).astype(np.int16)
mag_big = (gb[..., 0] > 200) & (gb[..., 1] < 90) & (gb[..., 2] > 200)
sky = np.array(Image.fromarray((mag_big * 255).astype(np.uint8)).resize((W, H), Image.BOX)) > 100
def snap(img, pal):
    d = ((img[:, :, None, :].astype(np.int32) - pal[None, None].astype(np.int32)) ** 2).sum(-1)
    return pal[d.argmin(-1)]
# montagnes lointaines : pixels violets/gris sous le ciel, au-dessus de la falaise
R, G, B = gs[..., 0], gs[..., 1], gs[..., 2]
yy, xx = np.mgrid[:H, :W]
snapped0 = snap(gs, terrain_pal)
yel0 = (snapped0[..., 0] >= 190) & (snapped0[..., 1] >= 170) & (snapped0[..., 2] <= 130)
wallc = ~sky & ~yel0 & (yy < 150)
ml, _ = nd.label(wallc)
top = set(ml[0][ml[0] > 0]); mount = np.isin(ml, list(top))
mount = nd.binary_opening(mount, iterations=1)
terrain = ~sky & ~mount
snapped = snap(gs, terrain_pal)
# rochers bleus -> calque détails
blue = terrain & (B > R + 10) & (B > 110)
bl, bn = nd.label(nd.binary_closing(blue, iterations=1))
details_m = np.zeros((H, W), bool)
for i in range(1, bn + 1):
    m = bl == i
    if m.sum() >= 20: details_m |= nd.binary_fill_holes(m)
details_m &= terrain

def rgba(mask, col):
    a = np.zeros((H, W, 4), np.uint8); a[..., :3] = col; a[..., 3] = mask * 255; return a
mont_rgba = rgba(mount, snapped)
terr_rgba = rgba(terrain & ~details_m, snapped)
# sous les rochers, le sol voisin (le calque terrain reste plein)
under = terr_rgba.copy()
for y, x in zip(*np.where(details_m)):
    for dx in (-12, 12, -20, 20, -28, 28):
        if 0 <= x + dx < W and terrain[y, x + dx] and not details_m[y, x + dx]:
            under[y, x, :3] = snapped[y, x + dx]; under[y, x, 3] = 255; break
terr_rgba = under
det_rgba = rgba(details_m, snapped)

# ---------- nuages canoniques (palette flash) ----------
ref_idx = np.full((335, W), -1, np.int8)
for i, c in enumerate(FLASH[0]): ref_idx[eq(refmap, c)] = i
band = ref_idx[:112].copy()
for x in range(W):
    col = band[:, x]
    for y in range(1, 112):
        if col[y] < 0: col[y] = col[y - 1]
cloud_idx = np.concatenate([band] * 3, axis=0)[:H]  # mer de nuages en contrebas (bande canonique répétée)
CLOUDS = []
for lv in range(6):
    a = np.zeros((H, W, 4), np.uint8)
    for i, c in enumerate(FLASH[lv]): a[cloud_idx == i] = c + (255,)
    CLOUDS.append(a)

# ---------- éclairs canoniques (mêmes frames que V1) ----------
def crop(y0, y1, x0, x1):
    s = sheet[y0:y1, x0:x1]; m = s.sum(2) > 0
    a = np.zeros(s.shape[:2] + (4,), np.uint8); a[..., :3] = s; a[..., 3] = m * 255; return a
ROWS = {
    "A": ((129, 140), [(471, 492), (495, 516), (518, 539), (541, 562), (564, 584), (588, 608)], (131, 173), [(614, 619), (624, 629), (633, 643), (648, 659), (664, 675), (679, 690)]),
    "B": ((175, 186), [(474, 495), (495, 516), (518, 539), (544, 565), (565, 585), (589, 609)], (177, 219), [(617, 622), (624, 629), (634, 644), (648, 659), (666, 677), (686, 697)]),
    "C": ((225, 235), [(475, 491), (495, 511), (515, 531), (533, 551)], (227, 254), [(555, 559), (562, 568), (570, 579), (584, 590)]),
    "D": ((265, 275), [(476, 492), (495, 511), (516, 532), (534, 552)], (267, 294), [(555, 559), (563, 569), (572, 581), (584, 590)]),
    "E": ((350, 360), [(476, 492), (496, 512), (517, 533), (536, 554)], None, []),
    "F": ((372, 382), [(476, 492), (496, 512), (516, 532), (537, 555)], None, []),
}
FLASHLV = {6: [1, 3, 5, 5, 3, 1], 4: [1, 3, 4, 2]}
def strike(row, cx, cy, mirror=False):
    (cy0, cy1), cs, by, bs = ROWS[row]
    cracks = [crop(cy0, cy1, a, b) for a, b in cs]
    bolts = [crop(by[0], by[1], a, b) for a, b in bs] if by else []
    if mirror: cracks = [c[:, ::-1] for c in cracks]; bolts = [b[:, ::-1] for b in bolts]
    last = cracks[-1][..., 3] > 0
    ly = int(np.where(last.any(1))[0].max()); lx = int(np.where(last[ly])[0].mean())
    out = []
    for i, c in enumerate(cracks):
        f = np.zeros((H, W, 4), np.uint8); x0 = cx - c.shape[1] // 2
        f[cy:cy + c.shape[0], x0:x0 + c.shape[1]][c[..., 3] > 0] = c[c[..., 3] > 0]
        if bolts:
            b = bolts[i]; bm = b[..., 3] > 0
            tx = int(np.where(bm[np.where(bm.any(1))[0].min()])[0].mean())
            f[cy + ly:cy + ly + b.shape[0], x0 + lx - tx:x0 + lx - tx + b.shape[1]][bm] = b[bm]
        out.append(f)
    return out, (FLASHLV.get(len(out), [1, 2, 2, 1]) if bolts else [1, 2, 2, 1])
EMPTY = np.zeros((H, W, 4), np.uint8)
# éclairs au-dessus / derrière la chaîne de montagnes (calque sous les montagnes)
# placement automatique dans le vide (nuages en contrebas) : visibilité max de la frame la plus grande
occ = mount | terrain
ORDER = [("A", False), ("C", False), ("B", True), ("E", False), ("D", True), ("F", True)]
PLAN, used = [], []
for row, mir in ORDER:
    best = None
    for cy in range(150, H - 62, 3):
        for cx in range(14, W - 14, 3):
            if any(abs(cx - ux) < 36 and abs(cy - uy) < 60 for ux, uy in used): continue
            fr, _ = strike(row, cx, cy, mir)
            a = fr[-1][..., 3] > 0
            if not a.any(): continue
            v = (a & ~occ).sum() / a.sum()
            if best is None or v > best[0]: best = (v, cx, cy)
        if best and best[0] >= 0.999: break
    used.append(best[1:]); PLAN.append((row, best[1], best[2], mir))
TL = []
for row, cx, cy, mir in PLAN:
    TL.append((EMPTY, 0, 900))
    fr, lv = strike(row, cx, cy, mir)
    TL += [(f, l, 67) for f, l in zip(fr, lv)]
    TL.append((EMPTY, 1, 67))

# ---------- collisions : sol jaune de l'arène + chemin ----------
walkc = terr_rgba[..., :3].astype(int)
yel = (walkc[..., 0] >= 190) & (walkc[..., 1] >= 180) & (walkc[..., 2] <= 130) & (terr_rgba[..., 3] > 0)
yl, _ = nd.label(yel); cent = yl[H - 20, W // 2] or yl[200, W // 2]
walk = nd.binary_erosion(nd.binary_closing(yl == cent, iterations=2), iterations=2)
grid = walk.reshape(H // 8, 8, W // 8, 8).mean(axis=(1, 3)) > 0.8

# ---------- sorties ----------
for d in ["calques", "nuages_flash", "eclairs", "import_png_8px", "apercu"]:
    (OUT / d).mkdir(parents=True, exist_ok=True)
def save(a, p):
    a = a.copy(); a[a[..., 3] == 0, :3] = 0; Image.fromarray(a, "RGBA").save(p, optimize=True)
LAYERS = [("00_nuages", CLOUDS[0]), ("01_eclairs", None), ("02_montagne_grotte", mont_rgba), ("03_terrain", terr_rgba), ("04_details", det_rgba)]
for nme, a in LAYERS:
    if a is not None:
        save(a, OUT / "calques" / f"{nme}.png"); save(a, OUT / "import_png_8px" / f"{PFX}{nme}.png")
for i, a in enumerate(CLOUDS): save(a, OUT / "nuages_flash" / f"{PFX}00_nuages_flash{i}.png")
timeline = []
for i, (a, lv, ms) in enumerate(TL):
    fn = f"{PFX}01_eclairs_f{i:02d}.png"; save(a, OUT / "eclairs" / fn)
    timeline.append({"eclair": fn, "nuages_niveau": lv, "ms": ms})
def compose(e, lv):
    img = np.zeros((H, W, 3), float)
    for a in (CLOUDS[lv], e, mont_rgba, terr_rgba, det_rgba):
        m = a[..., 3:4] / 255.0; img = img * (1 - m) + a[..., :3] * m
    return Image.fromarray(img.astype(np.uint8))
frames = [compose(e, lv) for e, lv, _ in TL]
frames[0].save(OUT / "apercu" / "animation.gif", save_all=True, append_images=frames[1:], duration=[m for *_, m in TL], loop=0)
frames[0].save(OUT / "apercu" / "scene_statique.png")
peak = max(range(len(TL)), key=lambda i: (TL[i][1], (TL[i][0][..., 3] > 0).sum()))
frames[peak].save(OUT / "apercu" / "scene_eclair.png")
cmp_ = Image.new("RGB", (W * 2 + 8, H)); cmp_.paste(g.resize((W, H), Image.BOX), (0, 0)); cmp_.paste(frames[peak], (W + 8, 0))
cmp_.save(OUT / "apercu" / "guide_vs_v3.png")
ov = np.array(frames[0]).astype(int); blk = np.kron(~grid, np.ones((8, 8), bool)); ov[blk] = ov[blk] // 2 + [100, 0, 0]
Image.fromarray(ov.astype(np.uint8)).save(OUT / "apercu" / "collisions.png")

refc = set(map(tuple, sheet.reshape(-1, 3).tolist()))
cols = lambda a: set(map(tuple, a[a[..., 3] > 0][:, :3].astype(int).tolist()))
checks = {nme: {"taille": [a.shape[1], a.shape[0]], "alpha_binaire": bool(np.isin(a[..., 3], [0, 255]).all()),
                "couleurs_hors_planche": len(cols(a) - refc)} for nme, a in LAYERS if a is not None}
checks["01_eclairs"] = {"frames": len(TL), "cycle_ms": sum(m for *_, m in TL), "couleurs_hors_planche": len(set().union(*[cols(a) for a, _, _ in TL]) - refc)}
checks["cases_marchables"] = int(grid.sum())
manifest = {"reference": {"file": REF.name, "sha256": hashlib.sha256(REF.read_bytes()).hexdigest()},
            "guide_genere": {"file": "source/thunder_meadow_v3b_entree/generation/entree_guide_sans_rochers.png", "sha256": hashlib.sha256(GUIDE.read_bytes()).hexdigest(),
                             "role": "composition + dessin, réduit BOX puis palette 5394 exacte (non canonique)"},
            "seuil_donjon": {"x": 228, "y": 128, "direction": "nord", "note": "bouche de grotte ; destination non configurée"}, "canvas": [W, H], "grille": 8, "prefixe_import": PFX, "ordre_calques": [nme for nme, _ in LAYERS],
            "nuages": {"methode": "palette flash canonique 6 niveaux", "palette": FLASH},
            "timeline": timeline, "eclairs_positions": PLAN, "collisions_8px": grid.astype(int).tolist(), "controles": checks}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1, default=int))
with zipfile.ZipFile(OUT.parent / "thunder_meadow_v3b_entree_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(OUT.parent))
    z.write(__file__, "thunder_meadow_v3b_entree/source/build.py"); z.write(GUIDE, "thunder_meadow_v3b_entree/source/entree_guide_sans_rochers.png")
print(json.dumps(checks, ensure_ascii=False))
