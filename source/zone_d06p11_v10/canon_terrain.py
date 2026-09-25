"""Zone D06P11 V10 — terrain reconstruit avec les VRAIES tuiles 8x8 de la ROM d06p11a (pixels non modifiés).
Guide de composition : falaise générée V9 (structure lumineuse des colonnes), collisions V8 (sable/chemins).
Méthode (cf. V1) : pour chaque case 8x8, choix d'une tuile ROM de la même classe (roche/sable) minimisant
  écart à la luminance du guide + coût de raccord avec voisins gauche/haut − bonus si voisin ROM d'origine
  (préserve des runs entiers de la ROM). Aucune rotation, miroir, recoloration ou redimensionnement des tuiles.
Seules exceptions : silhouette (alpha) reprise du guide + liseré 1 px de la couleur la plus sombre de la roche ROM ;
bouche de grotte + escaliers conservés du guide (palette ROM) ; sommet forcé en roche jusqu'au bord haut."""
import json, pathlib, numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parents[1]; G = HERE / "generation"
W, H = 544, 640; T = 8; CW, CH = W // T, H // T
def is_mag(a): return (a[..., 0] > 170) & (a[..., 1] < 110) & (a[..., 2] > 170)
LUM = lambda a: a[..., :3] @ np.array([.3, .59, .11])

rom = np.array(Image.open(ROOT / "source/zone_d06p11_v1/source_rom/d06p11a_f0.png").convert("RGB")).astype(int)
RH, RW = rom.shape[0] // T, rom.shape[1] // T
tiles = rom[:RH * T, :RW * T].reshape(RH, T, RW, T, 3).transpose(0, 2, 1, 3, 4)
m = tiles.mean((2, 3)); sd = tiles.std((2, 3)).mean(-1); lum = m.mean(-1)
blue = m[..., 2] > m[..., 0] + 20
nearblue = nd.binary_dilation(blue, np.ones((3, 3)))
cave = np.zeros_like(blue); cave[9:27, 38:53] = True
sand0 = (~blue) & (sd < 14) & (lum > 150)
lab, _ = nd.label(sand0); sz = np.bincount(lab.ravel()); sz[0] = 0
sand = lab == sz.argmax()
sand_in = nd.binary_erosion(sand, np.ones((3, 1)))          # sable pur (pas les bords)
rock = (~blue) & (~nearblue) & (~sand) & (~cave) & (~nd.binary_dilation(sand, np.ones((3, 3))))
def pool(mask):
    ij = np.argwhere(mask); return ij, tiles[ij[:, 0], ij[:, 1]].astype(float)
okr = (~blue) & (~nearblue) & (~cave) & (~sand)
up_s = np.zeros_like(sand); up_s[1:] = sand[:-1]; dn_s = np.zeros_like(sand); dn_s[:-1] = sand[1:]
up2 = np.zeros_like(sand); up2[2:] = sand[:-2]; dn2 = np.zeros_like(sand); dn2[:-2] = sand[2:]
POOL = {"roche": pool(rock), "sable": pool(sand_in), "levre": pool(okr & up_s), "levre2": pool(okr & up2 & ~up_s),
        "pied": pool(okr & dn_s), "pied2": pool(okr & dn2 & ~dn_s), "sable_bord": pool(sand & ~sand_in)}
PAL_ROCK = np.unique(tiles[rock].reshape(-1, 3), axis=0); DARK = PAL_ROCK[LUM(PAL_ROCK).argmin()]

g = np.array(Image.open(G / "falaise_style_d06p11a.png").convert("RGB").resize((W, H), Image.BOX)).astype(int)
mag = is_mag(g); mag = nd.binary_opening(nd.binary_closing(mag, np.ones((3, 3))), np.ones((2, 2)))
col8 = np.array(json.load(open(ROOT / "renders/zone_d06p11_v8/manifest.json"))["collisions_8px"])
FX, FY = W / 960, H / 1120
cave_box = (int(260 * FY) // T, int(520 * FY) // T + 1, int(395 * FX) // T, int(575 * FX) // T + 1)  # bouche + marches
TOP_ROWS = 6                                                   # sommet : roche continue jusqu'au bord haut
cls = np.full((CH, CW), "roche", object)
cls[col8 == 0] = "sable"; cls[:TOP_ROWS] = "roche"
y0, y1, x0, x1 = cave_box
# sommet : chaque colonne haute prend la silhouette de la rangée TOP_ROWS*T (massif qui monte droit jusqu'au bord)
mag[:TOP_ROWS * T] = mag[TOP_ROWS * T][None]

# ---- lissage des bords du sable (lèvres/pieds) : médiane ±3 colonnes des lignes de transition ----
def smooth_cls(cls):
    S = (cls == "sable"); new = S.copy()
    for kind in (1, -1):          # 1 : sable -> roche (lèvre) ; -1 : roche -> sable (pied)
        tr = {}
        for i in range(CW):
            for j in range(1, CH):
                if (kind == 1 and S[j - 1, i] and not S[j, i] and cls[j, i] == "roche") or (kind == -1 and not S[j - 1, i] and S[j, i] and cls[j - 1, i] == "roche"):
                    tr.setdefault(i, []).append(j)
        for i, js in tr.items():
            for j in js:
                nb = [jj for ii in range(i - 3, i + 4) for jj in tr.get(ii, []) if abs(jj - j) <= 3]
                m_ = int(round(np.median(nb)))
                if kind == 1:
                    if m_ > j: new[j:m_, i] = True
                    else: new[m_:j, i] = False
                else:
                    if m_ < j: new[m_:j, i] = True
                    else: new[j:m_, i] = False
    out = cls.copy(); out[(cls != "garde") & new] = "sable"; out[(cls == "sable") & ~new] = "roche"; return out
cls = smooth_cls(cls); cls[:TOP_ROWS][cls[:TOP_ROWS] == "sable"] = "roche"
# ---- copie par colonnes ROM alignées (lèvre sous le sable / pied au-dessus du sable) ----
cols_ok = [rc for rc in range(RW) if sand[:, rc].any() and not cave[:, rc].any() and not nearblue[:, rc].any()
           and rock[:np.argmax(sand[:, rc]), rc].sum() >= 8]
ST = {rc: int(np.argmax(sand[:, rc])) for rc in cols_ok}
SB = {rc: int(RH - 1 - np.argmax(sand[::-1, rc])) for rc in cols_ok}
out = np.zeros((H, W, 3), int); pick = {}
def put(j, i, r, rc): pick[(j, i)] = (int(r), int(rc)); out[j*T:j*T+T, i*T:i*T+T] = tiles[r, rc]
RC = [4 + (i % 10) for i in range(CW)]   # période horizontale ROM du mur = 80 px (10 tuiles), lèvre = 40 px
segs = []   # (i, j, k, c, above, below)
for i in range(CW):
    j = 0
    while j < CH:
        c = cls[j, i]; k = j
        while k < CH and cls[k, i] == c: k += 1
        segs.append([i, j, k, c, j > 0 and cls[j - 1, i] == "sable", k < CH and cls[k, i] == "sable"]); j = k
# ancres lissées : lèvre = ligne j du haut du segment, pied = ligne k ; médiane sur ±3 colonnes (segments qui se chevauchent)
def smooth(seg, key):
    i, j, k = seg[:3]; vals = []
    for t in segs:
        if abs(t[0] - i) <= 3 and t[3] == "roche" and t[1] < k and t[2] > j and (t[4] if key == 1 else t[5]):
            vals.append(t[key])
    return int(np.median(vals)) if vals else seg[key]
# ancre commune par série de colonnes voisines : lèvre = min(j), pied = max(k)  -> tuiles ROM contiguës en largeur
def anchors(flag, key, agg):
    A = {}; items = sorted([t for t in segs if t[3] == "roche" and t[flag]], key=lambda t: t[0])
    groups = []
    for t in items:
        for gp in groups:
            if any(abs(u[0] - t[0]) == 1 and abs(u[key] - t[key]) <= 3 for u in gp): gp.append(t); break
        else: groups.append([t])
    for gp in groups:
        v = agg([u[key] for u in gp])
        for u in gp: A[id(u)] = v
    return A
LIP = anchors(4, 1, min); BASE = anchors(5, 2, max)
STMIN = min(ST.values()); KB = int(np.median([t[2] for t in segs if t[3] == "roche" and t[5]]))
WALL = list(range(ST[4] - 15, ST[4]))   # période verticale ROM du mur = 120 px (15 tuiles) -> pavage sans couture           # rangées de mur communes à toutes les colonnes -> blocs ROM contigus en largeur
for seg in segs:
    i, j, k, c, above, below = seg; rc = RC[i]
    low = list(range(SB[rc] + 1, RH)); sandr = list(range(ST[rc], SB[rc] + 1))
    if c == "sable":
        for n in range(j, k): put(n, i, sandr[n % len(sandr)], rc)
    elif c in ("roche", "garde"):
        for n in range(j, k):
            ka = LIP.get(id(seg), j); kb = BASE.get(id(seg), k)
            if above and 0 <= n - ka < len(low) and (not below or n - j < (k - j) // 2 + 1):
                r = low[n - ka]                       # lèvre sous le sable (alignée sur la colonne)
            elif below and 0 < kb - n <= 6:
                r = ST[rc] - (kb - n)                 # pied du mur juste au-dessus du sable
            else:
                r = 3 + ((n - KB + 3) % 15)          # mur : rangées ROM 3..17 (période 120 px vérifiée), phase raccord au pied
            put(n, i, r, rc)
# grotte : bloc ROM d06p11a d'origine (bouche + marches + sable devant), aligné sur la ligne de sable -> 100 % canonique
CAVE_C0, CAVE_C1 = 38, 53
st_c = int(np.argmax(sand[:, 45])); CAVE_R0 = 4; CAVE_R1 = st_c + 1
before = out.copy()
ci = (x0 + x1) // 2; S = next(jj for jj in range(y1 - 4, CH) if cls[jj, ci] == "sable")
oy = S - (st_c - CAVE_R0); ox = ci - (45 - CAVE_C0)
for rr in range(CAVE_R0, CAVE_R1):
    for cc in range(CAVE_C0, CAVE_C1):
        jj, ii = oy + (rr - CAVE_R0), ox + (cc - CAVE_C0)
        if 0 <= jj < CH and 0 <= ii < CW and not blue[rr, cc]:
            put(jj, ii, rr, cc)
            if sand[rr, cc]: cls[jj, ii] = "sable"
            elif rr >= st_c - 3 and 42 <= cc <= 48: cls[jj, ii] = "garde"   # sol de la bouche (warp)
GUIDE_PX = 0
# raccord par couture d'erreur minimale (image quilting) sur bandes de 20 px : pixels ROM (bloc ou mur), frontière organique
BW = 20; bh = (CAVE_R1 - CAVE_R0) * T; bw_ = (CAVE_C1 - CAVE_C0) * T; by0, bx0 = oy * T, ox * T
def vseam(err):                       # err (h, BW) -> index de coupe par ligne (DP)
    h, w = err.shape; C = err.copy(); B = np.zeros((h, w), int)
    for y in range(1, h):
        for x in range(w):
            lo, hi = max(0, x - 1), min(w, x + 2); k = lo + np.argmin(C[y - 1, lo:hi]); B[y, x] = k; C[y, x] += C[y - 1, k]
    x = int(np.argmin(C[-1])); path = [x]
    for y in range(h - 1, 0, -1): x = B[y, x]; path.append(x)
    return path[::-1]
E_ = ((out.astype(float) - before) ** 2).sum(-1)
keep_wall = np.zeros((H, W), bool)
rows = slice(max(0, by0), by0 + bh - 3 * T)            # pas sur le sable/bas du bloc
yr = np.arange(H)[rows]
L = vseam(E_[rows, bx0:bx0 + BW]); Rr = vseam(E_[rows, bx0 + bw_ - BW:bx0 + bw_])
for n, y in enumerate(yr):
    keep_wall[y, bx0:bx0 + L[n]] = True; keep_wall[y, bx0 + bw_ - BW + Rr[n] + 1:bx0 + bw_] = True
if by0 >= 0:
    Tp = vseam(E_[by0:by0 + BW, bx0:bx0 + bw_].T)
    for n, x in enumerate(range(bx0, bx0 + bw_)): keep_wall[by0:by0 + Tp[n], x] = True
keep_wall &= np.kron(cls == "roche", np.ones((T, T))).astype(bool)
out[keep_wall] = before[keep_wall]
alpha = ~mag
edge = alpha & ~nd.binary_erosion(alpha, np.ones((3, 3)))
out[edge] = DARK
terr = np.zeros((H, W, 4), int); terr[..., :3] = out; terr[..., 3] = alpha * 255; terr[~alpha, :3] = 0
Image.fromarray(terr.astype(np.uint8), "RGBA").save(G / "terrain_canonique.png")
cells = [(j, i) for (j, i) in pick]
runs = sum(1 for (j, i) in cells if (j, i - 1) in pick and pick[(j, i - 1)] == (pick[(j, i)][0], pick[(j, i)][1] - 1))
prov = {"source": "pmd-sky ROM MAP_BG d06p11a (rendu source/zone_d06p11_v1/source_rom/d06p11a_f0.png)",
        "cases_tuiles_rom": len(pick), "cases_contigues_rom_horizontales": runs,
        "pool_roche": int(len(POOL["roche"][0])), "pool_sable": int(len(POOL["sable"][0])),
        "zone_guide_grotte_cases": [int(y0), int(y1), int(x0), int(x1)], "pixels_guide_grotte_marches": GUIDE_PX,
        "tuiles": {f"{j},{i}": [int(pick[(j, i)][0]), int(pick[(j, i)][1])] for (j, i) in pick}}
walk = (cls == "sable") | (cls == "garde"); y0, y1, x0, x1 = cave_box
gb = np.zeros_like(walk); gb[y0:y1, x0:x1] = True; walk &= ~gb | (cls == "garde") | (cls == "sable")
lab_, _ = nd.label(walk); sz_ = np.bincount(lab_.ravel()); sz_[0] = 0; walk = lab_ == sz_.argmax()
prov["collisions_8px"] = (~walk).astype(int).tolist(); prov["cases_marchables"] = int(walk.sum())
(G / "provenance_tuiles.json").write_text(json.dumps(prov))
print({k: v for k, v in prov.items() if k not in ("tuiles", "collisions_8px")})
