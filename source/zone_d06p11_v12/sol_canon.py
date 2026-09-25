"""Zone D06P11 V11 — calques de SOL et DÉCOR en textures canoniques (déjà-vu Apple Woods / Mt. Bristle).
- Herbe + chemin : tuiles 8x8 exactes de d05p11a (Apple Woods, PMD Sky), choisies case par case par
  correspondance de motif (chemin / liseré d'herbe claire / herbe sombre) + coût de raccord. Pas de recoloration.
- Fleurs : touffes extraites de d05p11a (pixels exacts). Rochers et cailloux : extraits de d13p11a.
- Non canonique : forme des masques (layout V10), liseré 1 px (couleur d'herbe sombre existante de d05p11a)."""
import json, pathlib, numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = pathlib.Path(__file__).resolve().parent; G = HERE / "generation"; R = HERE / "references"
W, H, T = 544, 640, 8; CW, CH = W // T, H // T
rng = np.random.default_rng(11)
meta = json.load(open(G / "falaise_meta.json")); cls = np.array(meta["cls"])
fal = np.array(Image.open(G / "calque_falaise.png")).astype(int); island = fal[..., 3] > 0
by0, bx0, bh, bw = meta["bloc_grotte_px"]; srow = meta["sol_grotte_rangee"]

# ---------- masques ----------
cells = np.array(meta["cls_sol_v12"]).astype(bool)   # V12 : exactement le sable V10 (+ second chemin ouvert)
cells[:srow, bx0 // T:(bx0 + bw) // T] = False                       # la bouche de grotte reste celle de la ROM
ground = np.kron(cells, np.ones((T, T))).astype(bool) & island   # V12 : bords identiques au sable V10 (pas d'arrondi)
Y, X = np.mgrid[:H, :W]
cx = bx0 + bw // 2
xc = cx + 20 * np.sin((H - Y) / 70.0) + 4 * np.sin(Y / 17.0) * np.clip((Y - srow * T) / 80.0, 0, 1)
pw = 17 + 2.5 * np.sin(Y / 11.0) + 1.5 * np.sin(Y / 4.3 + 1)
path = ground & (np.abs(X - xc) < pw) & (Y >= srow * T - 4)
path = nd.binary_opening(path, np.ones((3, 3))) | (ground & (nd.gaussian_filter(path.astype(float), 2.0) + nd.gaussian_filter(rng.standard_normal((H, W)), 1.0) * .25 > .5))
dpath = nd.distance_transform_edt(~path)
target = np.where(dpath <= 18, 1, 2)                               # herbe (sous le chemin : herbe claire)          # 0 chemin, 1 herbe claire, 2 herbe sombre

# ---------- tuiles d05p11a ----------
A = np.array(Image.open(R / "d05p11a.png").convert("RGB")).astype(int)
HS = np.array(Image.open(R / "d05p11a.png").convert("HSV")).astype(int)
AH, AW = A.shape[0] // T, A.shape[1] // T
rpath = (HS[..., 0] < 30) & (HS[..., 1] > 90) & (A[..., 0] > 150); rpath[:, :180] = False; rpath[:, 380:] = False
rpath = nd.binary_closing(nd.binary_opening(rpath, np.ones((3, 3))), np.ones((5, 5)))
rd = nd.distance_transform_edt(~rpath)
rcls = np.where(rpath, 0, np.where(rd <= 22, 1, 2))
flower = ((A[..., 0] > 170) & (A[..., 2] > 150) & (A[..., 1] < 170)) | ((A[..., 0] > 200) & (A[..., 1] > 200) & (A[..., 2] > 200))
apple = (A[..., 0] > 150) & (A[..., 1] < 80)
leaf = ((A[..., 2] < 50) & (A[..., 1] > 85) & (A[..., 0] < 150)) | apple   # canopées/buissons : bleu très bas
tl = lambda a: a[:AH * T, :AW * T].reshape(AH, T, AW, T, *a.shape[2:]).swapaxes(1, 2)
TT, TC = tl(A), tl(rcls)
bad = tl(flower | leaf).reshape(AH, AW, -1).any(-1)
bad |= tl(leaf).reshape(AH, AW, -1).mean(-1) > 0   # (pas de dilatation)
ij = np.argwhere(~bad); P = TT[ij[:, 0], ij[:, 1]].astype(float); PC = TC[ij[:, 0], ij[:, 1]]
print("pool d05p11a", len(ij), "chemin", int((PC == 0).all((1, 2)).sum()), "claire", int((PC == 1).all((1, 2)).sum()), "sombre", int((PC == 2).all((1, 2)).sum()))
need = nd.binary_dilation(ground, np.ones((9, 9)))
def synth(target, need):
    out_ = np.zeros((H, W, 3), int); pick = {}
    for j in range(CH):
        for i in range(CW):
            ys, xs = slice(j * T, j * T + T), slice(i * T, i * T + T)
            if not need[ys, xs].any(): continue
            tc = target[ys, xs]
            cost = (PC != tc[None]).mean((1, 2)) * 60000.
            if (j, i - 1) in pick: cost += ((P[:, :, 0] - out_[ys, i * T - 1][None]) ** 2).mean((1, 2))
            if (j - 1, i) in pick: cost += ((P[:, 0] - out_[j * T - 1, xs][None]) ** 2).mean((1, 2))
            for nb in ((j, i - 1), (j - 1, i), (j - 1, i - 1), (j, i - 2)):
                if nb in pick: cost[(ij[:, 0] == pick[nb][0]) & (ij[:, 1] == pick[nb][1])] += 4000
            cost += rng.random(len(cost)) * 400
            k = int(cost.argmin()); pick[(j, i)] = tuple(int(v) for v in ij[k]); out_[ys, xs] = P[k]
    return out_, pick
sol, pick = synth(target, need)
pierre, pick_c = synth(np.zeros((H, W), int), need & nd.binary_dilation(path, np.ones((9, 9))))
solc = np.zeros((H, W), int)


def rgba(rgb, mask):
    o = np.zeros((H, W, 4), int); o[..., :3] = rgb; o[..., 3] = mask * 255; o[~mask, :3] = 0; return o
chemin = path
herbe = ground & ~chemin
cols, cnt = np.unique(A[(rcls == 2) & ~flower & ~leaf], axis=0, return_counts=True)
DARKG = cols[np.argmin(cols @ [.3, .59, .11] + (cnt < 20) * 999)]
edge = ground & ~nd.binary_erosion(ground, np.ones((3, 3)))
lis = np.zeros((H, W), bool); lis[edge & (fal[..., 3] > 0)] = True
L = {}
L["06_herbe"] = rgba(sol, herbe & ~lis)
pc, pn = np.unique(A[rpath], axis=0, return_counts=True); PDARK = pc[np.argmin(pc @ [.3, .59, .11] + (pn < 30) * 999)]
pedge = chemin & ~nd.binary_erosion(chemin, np.ones((3, 3)))
L["07_chemin"] = rgba(pierre, chemin & ~pedge & ~lis)
L["07b_bord_chemin"] = rgba(np.broadcast_to(PDARK, (H, W, 3)), pedge & ~lis)
L["08_lisere_herbe"] = rgba(np.broadcast_to(DARKG, (H, W, 3)), lis)

# ---------- décor ----------
def sprites(img, mask, lo, hi, pad=2):
    lab, n = nd.label(mask); out = []
    for k, s in enumerate(nd.find_objects(lab)):
        area = (lab[s] == k + 1).sum()
        if lo <= area <= hi:
            y0, y1 = max(0, s[0].start - pad), min(img.shape[0], s[0].stop + pad); x0, x1 = max(0, s[1].start - pad), min(img.shape[1], s[1].stop + pad)
            mk = nd.binary_dilation(lab[y0:y1, x0:x1] == k + 1, iterations=pad)
            out.append((img[y0:y1, x0:x1], mk, (y0, x0)))
    return out
# fleurs : touffe = composante florale dilatée + feuilles de la touffe (pixels plus clairs/saturés que l'herbe environnante)
bg = nd.median_filter(A, size=(15, 15, 1))
tuft = (np.abs(A - bg).sum(-1) > 70) & ~leaf
FL = []
for img, mk, (y0, x0) in sprites(A, nd.binary_dilation(flower, iterations=1) & ~rpath, 6, 120, pad=4):
    t = tuft[y0:y0 + mk.shape[0], x0:x0 + mk.shape[1]] & mk
    if t.sum() > 12: FL.append((img, t))
D = np.array(Image.open(R / "d13p11a.png").convert("RGB")).astype(int)
DH = np.array(Image.open(R / "d13p11a.png").convert("HSV")).astype(int)
sandc = (DH[..., 0] > 25) & (DH[..., 0] < 50) & (D.sum(-1) > 480)
rockm = nd.binary_opening(~sandc, np.ones((2, 2)))
mx_ = D.max(-1); mn_ = D.min(-1); sat = (mx_ - mn_) / np.maximum(mx_, 1); dsand = (sat > .44) & (D.sum(-1) > 440)
def pillar(x0, y0, x1, y1):
    m_ = nd.binary_opening(~dsand[y0:y1, x0:x1], np.ones((2, 2))); lab, _ = nd.label(m_); sz = np.bincount(lab.ravel()); sz[0] = 0
    m_ = nd.binary_fill_holes(lab == sz.argmax()); c = D[y0:y1, x0:x1]
    speck = (c.sum(-1) > 480) & (sat[y0:y1, x0:x1] > .38); m_ &= ~speck
    lab, _ = nd.label(m_); sz = np.bincount(lab.ravel()); sz[0] = 0; return (c, lab == sz.argmax(), (y0, x0))
PIL_ = [pillar(*b) for b in [(118, 210, 190, 295), (272, 275, 318, 332), (378, 315, 420, 350), (300, 330, 345, 370), (95, 365, 130, 400)]]
PEB = [pillar(*b) for b in [(345, 385, 390, 425), (140, 410, 185, 450)]]
print("fleurs", len(FL), "piliers", len(PIL_), "cailloux", len(PEB))
def stamp(layer, spr, y, x, occ):
    img, mk = spr[0], spr[1]; h, w = mk.shape
    if y < 0 or x < 0 or y + h > H or x + w > W: return False
    zone = herbe[y:y + h, x:x + w]
    if not zone[mk].all() or occ[y:y + h, x:x + w][mk].any(): return False
    sub = layer[y:y + h, x:x + w]; sub[mk, :3] = img[mk]; sub[mk, 3] = 255; occ[y:y + h, x:x + w] |= nd.binary_dilation(mk, iterations=3); return True
occ = np.zeros((H, W), bool); occ |= nd.binary_dilation(chemin, iterations=6)
occ[40 * T:52 * T, 24 * T:45 * T] = True   # second chemin : aucun décor, passage totalement libre
fleurs = np.zeros((H, W, 4), int); rochers = np.zeros((H, W, 4), int); cailloux = np.zeros((H, W, 4), int)
placed = {"rochers": [], "fleurs": 0, "cailloux": 0}
PILS = [PIL_[0], PIL_[1], PIL_[2], PIL_[4]]
tries = 0
for sp in PILS:
    for _ in range(4000):
        y = int(rng.integers(0, H)); x = int(rng.integers(0, W))
        if stamp(rochers, sp, y, x, occ): placed["rochers"].append([x, y, int(sp[1].shape[1]), int(sp[1].shape[0])]); break
for n in range(26):
    sp = FL[n % len(FL)]
    for _ in range(3000):
        if stamp(fleurs, sp, int(rng.integers(0, H)), int(rng.integers(0, W)), occ): placed["fleurs"] += 1; break
for n in range(4):
    sp = PEB[n % len(PEB)]
    for _ in range(3000):
        if stamp(cailloux, sp, int(rng.integers(0, H)), int(rng.integers(0, W)), occ): placed["cailloux"] += 1; break
L["10_rochers_d13p11a"] = rochers; L["11_fleurs_d05p11a"] = fleurs; L["12_cailloux_d13p11a"] = cailloux
col = np.array(meta["collisions_8px"])
for x, y, w, h in placed["rochers"]:                 # base des piliers bloquante (moitié basse)
    col[(y + h // 2) // T:(y + h) // T + 1, x // T:(x + w) // T + 1] = 1
for k, v in L.items(): Image.fromarray(v.astype(np.uint8), "RGBA").save(G / f"calque_{k}.png")
json.dump({"calques": list(L), "decor": placed, "collisions_8px": col.tolist(), "cases_marchables": int((col == 0).sum()),
           "tuiles_sol_d05p11a": {f"{j},{i}": v for (j, i), v in pick.items()}}, open(G / "sol_meta.json", "w"))
print(placed["fleurs"], placed["cailloux"], placed["rochers"], int((col == 0).sum()))
