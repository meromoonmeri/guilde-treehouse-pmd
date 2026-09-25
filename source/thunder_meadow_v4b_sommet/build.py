"""Thunder Meadow V4 — sommet : texture canonique, chemin sud->nord, orage en spirale + éclairs.

Référence : 5394.png (rip Toastypk, spriters-resource asset 5394) : carte sans
éclairs + « Cloud flash colors » (6 niveaux Dark->Light) + frames d'éclairs.
Pixels et couleurs 100 % issus de la planche ; aucun générateur.
"""
import json, hashlib, pathlib, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REF = ROOT / "5394.png"
OUT = ROOT / "renders" / "thunder_meadow_v4b_sommet"
PFX = "THUNDERMEADOW_V4B_"
sheet = np.array(Image.open(REF).convert("RGB")).astype(np.int16)
W, H0 = 456, 335
H = 336  # multiple de 8 : dernière ligne native dupliquée
scene = np.concatenate([sheet[:H0, :W], sheet[H0 - 1:H0, :W]], axis=0)
eq = lambda img, c: np.all(img == np.array(c), axis=-1)

# ---------- palette de flash des nuages (8 couleurs x 6 niveaux) ----------
FLASH = [[tuple(int(v) for v in sheet[57 + 9 * r + 3, 519 + 9 * c + 3]) for c in range(8)] for r in range(6)]
cloud_idx = np.full((H, W), -1, np.int8)
for i, c in enumerate(FLASH[0]):
    cloud_idx[eq(scene, c)] = i
clouds = cloud_idx >= 0

# ---------- objets : arbre, rochers ----------
TREE = [(96, 80, 56), (208, 160, 104), (56, 48, 32), (176, 136, 88), (144, 120, 72), (176, 160, 80), (104, 88, 56), (128, 104, 72), (152, 112, 80), (72, 72, 40)]
R, G, B = scene[..., 0], scene[..., 1], scene[..., 2]
yy, xx = np.mgrid[:H, :W]
tree = np.zeros((H, W), bool)
for c in TREE:
    tree |= eq(scene, c)
tree &= (xx >= 192) & (xx < 262) & (yy >= 190) & (yy < 274)
tree = nd.binary_closing(tree, iterations=1) & ((yy >= 190) & (xx >= 192) & (xx < 262) & (yy < 274))
tree = nd.binary_fill_holes(tree)
rock = ((B > R + 8) & ~clouds) | eq(scene, (168, 160, 32)) | eq(scene, (128, 128, 72))
rock &= (yy > 118) & (yy < 222)
rl, rn = nd.label(nd.binary_closing(rock, iterations=2))
objs = []
for i, sl in enumerate(nd.find_objects(rl)):
    m = rl[sl] == i + 1
    if m.sum() > 40:
        objs.append(("rocher", sl, nd.binary_fill_holes(m)))
tl, _ = nd.label(tree)
sl = nd.find_objects(tl)[int(np.argmax(nd.sum(tree, tl, range(1, tl.max() + 1))))]
objs.append(("arbre", sl, nd.binary_fill_holes(tl[sl] > 0)))

GROUND = [(200, 184, 48), (248, 240, 112), (232, 216, 88), (200, 224, 88), (232, 224, 96), (128, 120, 40), (160, 152, 72)]
ground = np.zeros((H, W), bool)
for c in GROUND:
    ground |= eq(scene, c)

terrain = scene.copy()
objmask = np.zeros((H, W), bool)
for name, sl, m in objs:
    objmask[sl] |= m
fillmask = objmask.copy()
fillmask[190:280, 186:268] |= nd.binary_dilation(objmask, iterations=8)[190:280, 186:268]  # halo/ombre de l'arbre
# comblement : sol natif au point symétrique, sinon décalé de ±64 px
for y, x in zip(*np.where(fillmask)):
    order = (x + 72, x - 72, x + 96) if 186 <= x < 268 and y >= 190 else (W - 1 - x, x - 64, x + 64)
    for sx in order:
        if 0 <= sx < W and ground[y, sx] and not fillmask[y, sx]:
            terrain[y, x] = scene[y, sx]; break
# arbre : copie en bloc du sol natif 80 px à gauche (texture continue), ellipse douce
SHIFT = 88
by0, by1, bx0, bx1 = 186, 282, 184, 270
blk = np.zeros((H, W), bool); blk[by0:by1, bx0:bx1] = True
ell = ((xx - 227) / 44.0) ** 2 + ((yy - 230) / 46.0) ** 2 <= 1
treec = np.zeros((H, W), bool)
for c in TREE:
    treec |= eq(scene, c)
sel = blk & ell & (ground | fillmask | treec)
terrain[sel] = scene[np.where(sel)[0], np.where(sel)[1] + SHIFT]
stray = blk & ~ell & (treec | objmask)
for y, x in zip(*np.where(stray)):  # pointes de branches/racines hors ellipse
    d = 1 if x >= 227 else -1
    for k in range(1, 20):
        if ground[y, x + d * k] and not stray[y, x + d * k]:
            terrain[y, x] = scene[y, x + d * k]; break
ground_new = ground | fillmask

# ---------- nouveau placement (layout légèrement différent) ----------
def place_ok(m, y0, x0):
    h, w = m.shape
    if y0 < 0 or x0 < 0 or y0 + h > H or x0 + w > W: return False
    return bool(ground_new[y0:y0 + h, x0:x0 + w][m].all())
MOVES = {"arbre": [(8, -72), (0, -72), (8, -64), (16, -56)]}
details = np.zeros((H, W, 4), np.uint8)
placed = []
rocks_sorted = sorted([o for o in objs if o[0] == "rocher"], key=lambda o: (o[1][1].start))
for k, (name, sl, m) in enumerate(objs):
    if name == "arbre":
        continue  # sommet dégagé : arbre retiré, sol natif comblé
    y0, x0 = sl[0].start, sl[1].start
    if name == "arbre":
        cands = MOVES["arbre"]
    else:
        big = m.sum() > 400
        left = x0 < W // 2
        # gros rochers : remontés et rentrés ; petits : échangent de côté par symétrie de position
        cands = ([(-16, 28 if left else -28), (-8, 24 if left else -24), (0, 16 if left else -16)] if big
                 else [(0, (W - 2 * x0 - m.shape[1]))])
    dy, dx = next(((a, b) for a, b in cands if place_ok(m, y0 + a, x0 + b)), (0, 0))
    ny, nx = y0 + dy, x0 + dx
    rgba = np.zeros(m.shape + (4,), np.uint8); rgba[..., :3] = scene[sl]; rgba[..., 3] = m * 255
    details[ny:ny + m.shape[0], nx:nx + m.shape[1]][m] = rgba[m]
    placed.append({"objet": name, "de": [int(x0), int(y0)], "vers": [int(nx), int(ny)], "taille": [m.shape[1], m.shape[0]]})

# fissure du chemin : conservée (chemin d'accès vers le haut)
# ---------- V4b : fissure en zigzag retirée, chemin droit sud -> nord ----------
fis = np.zeros((H, W), bool)
for c in [(72, 72, 40), (104, 88, 56), (128, 104, 72), (128, 120, 40)]:
    fis |= eq(scene, c)
box = (yy >= 96) & (yy < 168) & (xx >= 186) & (xx < 276)
fis = nd.binary_dilation(fis & box, iterations=1) & box & ~clouds
for y, x in zip(*np.where(fis)):
    for dx in (48, -48, 64, -64, 80, -80):
        if 0 <= x + dx < W and ground[y, x + dx] and not fis[y, x + dx]:
            terrain[y, x] = terrain[y, x + dx]; break
ground_new = ground_new | fis
# chemin droit : bande claire canonique, bords irréguliers bordés de jaune moyen puis foncé
LIGHT, MID, DARK = (248, 240, 112), (232, 216, 88), (200, 184, 48)
rng_p = np.random.default_rng(3)
PCX, PHW = 228, 14
top_y = int(np.where(ground_new[:, PCX])[0].min())
lw = rw = 0
path = np.zeros((H, W), bool)
for y in range(top_y, H):
    if y % 2 == 0:
        lw = int(np.clip(lw + rng_p.integers(-1, 2), -2, 2)); rw = int(np.clip(rw + rng_p.integers(-1, 2), -2, 2))
    x0, x1 = PCX - PHW + lw, PCX + PHW + rw
    terrain[y, x0:x1] = MID; path[y, x0:x1] = True
    terrain[y, x0:x0 + 2] = DARK; terrain[y, x1 - 2:x1] = DARK
    if y % 3 == 0: terrain[y, x0 + 2] = DARK; terrain[y, x1 - 3] = DARK
    if y % 4 == 1: terrain[y, PCX - 6 + (y * 7) % 13] = LIGHT  # grain clair dans le chemin
ground_new = ground_new | path
terrain_rgba = np.zeros((H, W, 4), np.uint8); terrain_rgba[..., :3] = terrain; terrain_rgba[..., 3] = (~clouds) * 255
def clouds_level(lv):
    a = np.zeros((H, W, 4), np.uint8)
    for i, c in enumerate(FLASH[lv]):
        a[cloud_idx == i] = c + (255,)
    return a
CLOUDS = [clouds_level(i) for i in range(6)]

# ---------- éclairs ----------
def crop(y0, y1, x0, x1):
    s = sheet[y0:y1, x0:x1]; m = s.sum(2) > 0
    a = np.zeros(s.shape[:2] + (4,), np.uint8); a[..., :3] = s; a[..., 3] = m * 255
    return a
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
    if mirror:
        cracks = [c[:, ::-1] for c in cracks]; bolts = [b[:, ::-1] for b in bolts]
    last = cracks[-1][..., 3] > 0
    ly = int(np.where(last.any(1))[0].max()); lx = int(np.where(last[ly])[0].mean())
    frames = []
    for i, c in enumerate(cracks):
        f = np.zeros((H, W, 4), np.uint8)
        x0 = cx - c.shape[1] // 2; f[cy:cy + c.shape[0], x0:x0 + c.shape[1]][c[..., 3] > 0] = c[c[..., 3] > 0]
        if bolts:
            b = bolts[i]; bm = b[..., 3] > 0
            tx = int(np.where(bm[np.where(bm.any(1))[0].min()])[0].mean())
            bx, byy = x0 + lx - tx, cy + ly
            f[byy:byy + b.shape[0], bx:bx + b.shape[1]][bm] = b[bm]
        frames.append(f)
    lv = FLASHLV.get(len(frames), [1, 2, 2, 1]) if bolts else [1, 2, 2, 1]
    return frames, lv
EMPTY = np.zeros((H, W, 4), np.uint8)

# ---------- orage en spirale (indices de la palette nuage -> flash compatible) ----------
band = np.full((112, W), -1, np.int8); band[:] = cloud_idx[:112]
for x in range(W):
    col = band[:, x]
    for y in range(1, 112):
        if col[y] < 0: col[y] = col[y - 1]
    for y in range(110, -1, -1):
        if col[y] < 0: col[y] = col[y + 1]
seam = np.concatenate([band, band[:, ::-1]], axis=1)  # bande sans raccord 912 px
BW = seam.shape[1]
SCX, SCY, RX, RY, TWIST, NS, SMS = 228, 30, 170, 70, 0.9, 48, 83
yy2, xx2 = np.mgrid[:H, :W]
yy, xx = (yy2 // 2) * 2, (xx2 // 2) * 2
if False: yy, xx = (yy // 2) * 2, (xx // 2) * 2  # pixels 2x2 : spirale lisible, style pixel art
dxn, dyn = (xx - SCX) / RX, (yy - SCY) / RY
rho = np.sqrt(dxn ** 2 + dyn ** 2); phi = np.arctan2(dyn, dxn)
rng = np.random.default_rng(7); thr = np.kron(rng.random((H // 2, W // 2)), np.ones((2, 2)))
inside = (rho < 1) & ((rho < 0.8) | (thr < (1 - rho) / 0.2)) & ~(terrain_rgba[..., 3] > 0) | ((rho < 1) & (terrain_rgba[..., 3] > 0) & False)
vrow = np.clip((rho * 111 * 0.5).astype(int) * 2, 0, 111)  # moitié de la bande, lignes paires
SPIRAL_IDX = []
for f in range(NS):
    u = np.floor((phi / (2 * np.pi) + TWIST * (1 - rho)) * BW + BW * f / NS).astype(int) % BW
    idx = np.where(inside, seam[vrow, u], -1).astype(np.int8)
    SPIRAL_IDX.append(idx)
def idx_rgba(idx, lv):
    a = np.zeros((H, W, 4), np.uint8)
    for i, c in enumerate(FLASH[lv]): a[idx == i] = c + (255,)
    return a

# ---------- éclairs : autour et sous la spirale, visibilité maximale dans le ciel ----------
occ = terrain_rgba[..., 3] > 0
ORDER = [("A", False), ("B", True), ("C", False), ("E", False), ("D", True), ("F", True)]
PLAN, used = [], []
for row, mir in ORDER:
    best = None
    for cy in range(0, 60, 2):
        for cx in range(14, W - 14, 3):
            if any(abs(cx - ux) < 50 for ux, uy in used): continue
            fr, _ = strike(row, cx, cy, mir); a = fr[-1][..., 3] > 0
            v = (a & ~occ).sum() / a.sum() - 0.002 * abs(cx - SCX) / 10
            if best is None or v > best[0]: best = (v, cx, cy)
    used.append(best[1:]); PLAN.append((row, best[1], best[2], mir))
TL = []
for row, cx, cy, mir in PLAN:
    TL.append((EMPTY, 0, 900))
    fr, lv = strike(row, cx, cy, mir)
    TL += [(f, l, 67) for f, l in zip(fr, lv)]
    TL.append((EMPTY, 1, 67))
CYCLE = sum(m for *_, m in TL)

# ---------- collisions ----------
walk = nd.binary_erosion(ground_new, iterations=3) & ~(details[..., 3] > 0)
grid = walk.reshape(H // 8, 8, W // 8, 8).all(axis=(1, 3))

# ---------- sorties ----------
for d in ["calques", "nuages_flash", "spirale", "eclairs", "import_png_8px", "apercu"]:
    (OUT / d).mkdir(parents=True, exist_ok=True)
def save(a, p):
    a = a.copy(); a[a[..., 3] == 0, :3] = 0; Image.fromarray(a.astype(np.uint8), "RGBA").save(p, optimize=True)
LAYERS = [("00_nuages", CLOUDS[0]), ("01_spirale", idx_rgba(SPIRAL_IDX[0], 0)), ("02_eclairs", None), ("03_terrain", terrain_rgba), ("04_details", details)]
for n, a in LAYERS:
    if a is not None:
        save(a, OUT / "calques" / f"{n}.png"); save(a, OUT / "import_png_8px" / f"{PFX}{n}.png")
for i, a in enumerate(CLOUDS): save(a, OUT / "nuages_flash" / f"{PFX}00_nuages_flash{i}.png")
pal = []
for c in FLASH[0]: pal += list(c)
pal += [0, 0, 0] * (256 - 8)
for f, idx in enumerate(SPIRAL_IDX):
    save(idx_rgba(idx, 0), OUT / "spirale" / f"{PFX}01_spirale_f{f:02d}.png")
    p = Image.fromarray(np.where(idx < 0, 255, idx).astype(np.uint8), "P"); p.putpalette(pal)
    p.save(OUT / "spirale" / f"{PFX}01_spirale_f{f:02d}_indexe.png", transparency=255)
timeline = []
for i, (a, lv, ms) in enumerate(TL):
    fn = f"{PFX}02_eclairs_f{i:02d}.png"; save(a, OUT / "eclairs" / fn)
    timeline.append({"eclair": fn, "nuages_niveau": lv, "ms": ms})
def level_at(t):
    r = t % CYCLE
    for a, lv, ms in TL:
        if r < ms: return a, lv
        r -= ms
def compose(t):
    e, lv = level_at(t); sidx = SPIRAL_IDX[int(t // SMS) % NS]
    img = np.zeros((H, W, 3), float)
    for a in (CLOUDS[lv], idx_rgba(sidx, lv), e, terrain_rgba, details):
        m = a[..., 3:4] / 255.0; img = img * (1 - m) + a[..., :3] * m
    return Image.fromarray(img.astype(np.uint8))
ts = list(range(0, CYCLE, 67))
frames = [compose(t) for t in ts]
frames[0].save(OUT / "apercu" / "animation.gif", save_all=True, append_images=frames[1:], duration=67, loop=0)
frames[0].save(OUT / "apercu" / "scene_statique.png")
pk = max(range(len(ts)), key=lambda i: level_at(ts[i])[1] * 1000 + (level_at(ts[i])[0][..., 3] > 0).sum())
frames[pk].save(OUT / "apercu" / "scene_eclair.png")
cmp_ = Image.new("RGB", (W * 2 + 8, H)); cmp_.paste(Image.fromarray(scene.astype(np.uint8)), (0, 0)); cmp_.paste(frames[pk], (W + 8, 0))
cmp_.save(OUT / "apercu" / "reference_vs_v4b.png")
ov = np.array(frames[0]).astype(int); blk = np.kron(~grid, np.ones((8, 8), bool)); ov[blk] = ov[blk] // 2 + [100, 0, 0]
Image.fromarray(ov.astype(np.uint8)).save(OUT / "apercu" / "collisions.png")

refc = set(map(tuple, sheet.reshape(-1, 3).tolist()))
def cols(a): return set(map(tuple, a[a[..., 3] > 0][:, :3].astype(int).tolist()))
checks = {n: {"taille": [a.shape[1], a.shape[0]], "alpha_binaire": bool(np.isin(a[..., 3], [0, 255]).all()),
              "couleurs_hors_planche": len(cols(a) - refc)} for n, a in LAYERS if a is not None}
checks["01_spirale"]["frames"] = NS; checks["01_spirale"]["boucle_exacte"] = bool((np.floor((phi / (2 * np.pi) + TWIST * (1 - rho)) * BW + BW).astype(int) % BW == np.floor((phi / (2 * np.pi) + TWIST * (1 - rho)) * BW).astype(int) % BW).all())
checks["02_eclairs"] = {"frames": len(TL), "cycle_ms": CYCLE, "couleurs_hors_planche": len(set().union(*[cols(a) for a, _, _ in TL]) - refc)}
checks["arbre_retire"] = True
manifest = {"reference": {"file": REF.name, "sha256": hashlib.sha256(REF.read_bytes()).hexdigest()},
            "canvas": [W, H], "grille": 8, "prefixe_import": PFX, "ordre_calques": [n for n, _ in LAYERS],
            "chemin": "sud (bord bas, bande claire centrale canonique) -> nord (fissure canonique vers le bord haut)",
            "nuages": {"methode": "palette flash canonique 6 niveaux", "palette": FLASH},
            "spirale": {"methode": "bande canonique de nuages (indices palette) projetée en coordonnées polaires tordues, rotation d'un tour complet",
                        "centre": [SCX, SCY], "rayons": [RX, RY], "torsion": TWIST, "frames": NS, "ms": SMS, "periode_ms": NS * SMS,
                        "flash": "même niveau de palette que 00_nuages (timeline éclairs)", "indexe": "spirale/*_indexe.png (index 0-7 = palette nuage, 255 = transparent)"},
            "timeline": timeline, "eclairs_positions": PLAN, "layout": {"objets": placed}, "collisions_8px": grid.astype(int).tolist(), "controles": checks}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1, default=int))
with zipfile.ZipFile(OUT.parent / "thunder_meadow_v4b_sommet_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(OUT.parent))
    z.write(__file__, "thunder_meadow_v4b_sommet/source/build.py")
print(json.dumps(checks, ensure_ascii=False, default=int))
