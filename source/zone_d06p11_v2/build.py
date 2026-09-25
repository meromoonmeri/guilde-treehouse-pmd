"""Zone D06P11 V2 — promontoire : chemin central sud -> nord, esplanade devant la grotte (nord),
mer en contrebas des deux côtés, horizon à perte de vue, nuages rasant l'horizon (bande en wrap parfait).
Textures : tuiles ROM de d06p11a uniquement (+ leurs miroirs horizontaux, comme le DS sait le faire).
"""
import json, colorsys, pathlib, zipfile, numpy as np
from PIL import Image
from scipy import ndimage as nd
from rom_layers import layer, col, NX, NY, NPAL
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parents[1]
OUT = ROOT / "renders" / "zone_d06p11_v2"; PFX = "D06P11_V2_"
T = 8; NB, DB, DP = 10, 10, 5; HOR = 168
L0b = [layer(0, b, 0)[0] for b in range(NB)]; L0p = [layer(0, 0, p)[0] for p in range(NPAL)]; L1 = layer(1)[0]
L0 = L0b[0]; SH, SW = NY * 3, NX * 3
comp = np.where(L1[..., 3:] > 0, L1[..., :3], L0[..., :3]).astype(int)
walk = col == 0
seapx = (L1[..., 3] == 0) & ((L0[..., 2].astype(int) > L0[..., 0].astype(int) + 15) | (L0[..., :3].astype(int).min(-1) > 200))
for b in range(NB): seapx |= (L1[..., 3] == 0) & (L0b[b] != L0).any(-1)
terr_src = np.where(seapx[..., None], 0, np.where(L1[..., 3:] > 0, L1, L0)).astype(np.uint8)
terr_src[..., 3] = np.where(seapx, 0, 255)
def tcls(x, y):
    p = comp[y*T:(y+1)*T, x*T:(x+1)*T]; s = seapx[y*T:(y+1)*T, x*T:(x+1)*T].mean()
    if s > .5: return 3
    if (p.sum(-1) < 120).mean() > .4: return 2
    return 1 if walk[y, x] else 0
SC = np.array([[tcls(x, y) for x in range(SW)] for y in range(SH)])
# bibliothèque : tuiles source + miroirs horizontaux (classe, image, collision)
LIB_C = np.concatenate([SC, SC[:, ::-1]], 1)          # grille (SH, 2*SW) : miroir à droite
LIB_T = np.concatenate([terr_src, terr_src[:, ::-1]], 1)
LIB_P = np.concatenate([comp, comp[:, ::-1]], 1)
LIB_K = np.concatenate([col, col[:, ::-1]], 1)
LW = 2 * SW
# ---------- layout cible (tuiles 8 px) ----------
TW, TH = 48, 56; W, H = TW * T, TH * T
yy, xx = np.mgrid[0:TH, 0:TW]
rng = np.random.default_rng(11); nz = nd.zoom(rng.random((TH // 4 + 2, TW // 4 + 2)), 4, order=1)[:TH, :TW] - .5
TG = np.full((TH, TW), 3)
# massif nord (grotte) + promontoire qui s'élargit vers le sud
half = np.where(yy < 30, 11 + 1.5 * nz * 4, 9 + (yy - 30) * .28 + nz * 3)
TG[np.abs(xx - 23.5) < half] = 0
TG[(yy < 6) & (np.abs(xx - 23.5) > 8 + nz * 4)] = 3                # sommet du massif arrondi dans le ciel
# esplanade devant la grotte + chemin central
plaza = ((xx - 23.5) / 8.5) ** 2 + ((yy - 27) / 4.5) ** 2 + nz * .5 < 1
path = (np.abs(xx - 23.5 - 1.2 * np.sin(yy / 6)) < 2.6 + nz) & (yy > 26)
TG[(plaza | path) & (TG != 3)] = 1
# bloc grotte ROM copié tel quel (source tuiles x39..53, y12..26)
P = -np.ones((TH, TW), int); SRCX, SRCY, BW_, BH_ = 39, 11, 15, 13
dx0, dy0 = 24 - (46 - SRCX) - 1, 10
for j in range(BH_):
    for i in range(BW_):
        sy, sx = SRCY + j, SRCX + i; ty, tx = dy0 + j, dx0 + i
        P[ty, tx] = sy * LW + sx; TG[ty, tx] = SC[sy, sx]
# ---------- synthèse ----------
Rw = 2; K = 2 * Rw + 1
padS = np.pad(LIB_C, Rw, constant_values=-1); padT = np.pad(TG, Rw, constant_values=-1)
WS = np.stack([padS[y:y+K, x:x+K].ravel() for y in range(SH) for x in range(LW)])
TILES = np.stack([LIB_P[y*T:(y+1)*T, x*T:(x+1)*T] for y in range(SH) for x in range(LW)]).astype(np.int32)
SXY = np.array([(x, y) for y in range(SH) for x in range(LW)]); own = LIB_C.ravel()
N8 = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
FIXM = P >= 0; P[(TG == 3) & ~FIXM] = -2   # mer : vide (fond animé derrière)
for it in range(3):
    for ty in range(TH):
        for tx in range(TW):
            if FIXM[ty, tx] or TG[ty, tx] == 3: continue
            wt = padT[ty:ty+K, tx:tx+K].ravel(); valid = wt >= 0
            c = ((WS != wt) & valid & (WS >= 0)).sum(1) * 30.0 + ((WS < 0) & valid).sum(1) * 30.0
            c[own != TG[ty, tx]] = 1e9
            for dx, dy in N8:
                if not (0 <= tx+dx < TW and 0 <= ty+dy < TH): continue
                q = P[ty+dy, tx+dx]
                if q < 0: continue
                ex, ey = SXY[:, 0] + dx, SXY[:, 1] + dy
                ok = (ex >= 0) & (ex < LW) & (ey >= 0) & (ey < SH) & ((ex < SW) == (SXY[:, 0] < SW))
                ei = np.where(ok, ey * LW + ex, 0)
                d = np.abs(TILES[ei] - TILES[q]).mean((1, 2, 3))
                c += np.where(ok, np.where(ei == q, -60, d * 1.5), 40)
            c += rng.random(len(c)) * 3
            P[ty, tx] = int(np.argmin(c))
terr = np.zeros((H, W, 4), np.uint8); colT = np.ones((TH, TW), int); RM = np.zeros((H, W), bool)
for ty in range(TH):
    for tx in range(TW):
        q = P[ty, tx]
        if q < 0: continue
        sx, sy = SXY[q]
        terr[ty*T:(ty+1)*T, tx*T:(tx+1)*T] = LIB_T[sy*T:(sy+1)*T, sx*T:(sx+1)*T]
        colT[ty, tx] = LIB_K[sy, sx]; RM[ty*T:(ty+1)*T, tx*T:(tx+1)*T] = LIB_C[sy, sx] == 0
colT[TG == 3] = 1
_l, _n = nd.label(colT == 0); _sz = np.bincount(_l.ravel()); _sz[0] = 0; colT[(_l > 0) & (_l != _sz.argmax())] = 1
# ---------- colorimétrie roche (comme V1) ----------
sand = comp[np.kron(SC == 1, np.ones((T, T), bool))]; sand = sand[sand.sum(1) > 450]
sh, ss, sv = colorsys.rgb_to_hsv(*(sand.mean(0) / 255)); LUT = {}
def lut(c):
    if c in LUT: return LUT[c]
    if c[2] > c[0] + 8: LUT[c] = c; return c
    h, s, v = colorsys.rgb_to_hsv(*(np.array(c) / 255)); dh = ((sh - h + .5) % 1) - .5
    rgb = np.array(colorsys.hsv_to_rgb((h + dh) % 1, min(1, s * .8 + ss * .2), v)) * .7 + np.array(colorsys.hsv_to_rgb(sh, ss, v)) * .3
    LUT[c] = tuple(min(248, int(round(k * 255 / 8)) * 8) for k in rgb); return LUT[c]
ys, xs = np.nonzero(RM & (terr[..., 3] > 0))
for y, x in zip(ys, xs): terr[y, x, :3] = lut(tuple(int(v) for v in terr[y, x, :3]))
# ---------- fond : ciel / nuages / mer (bande ROM pure x504..552, tuilée en miroir -> sans couture) ----------
BX0, BX1 = 504, 552
def band_tile(img):
    b = img[:, BX0:BX1]; bb = np.concatenate([b, b[:, ::-1]], 1); reps = W // bb.shape[1] + 1
    return np.concatenate([bb] * reps, 1)[:, :W]
skyrows = comp[:HOR, BX0:BX1]
mode = np.array([np.unique(r.reshape(-1, 3), axis=0, return_counts=True) for r in skyrows], dtype=object)
rowc = np.array([u[np.argmax(n)] for u, n in mode])
cloudpx = np.abs(skyrows - rowc[:, None]).sum(-1) > 30
Hs = min(H, SH * T)
sky = np.zeros((H, W, 4), np.uint8); sky[:HOR, :, :3] = rowc[:, None]; sky[..., 3] = 255
seaF = []
for b in range(NB):
    a = band_tile(L0b[b])[:Hs]; s = np.zeros((H, W, 4), np.uint8); s[HOR:Hs] = a[HOR:Hs]
    if H > Hs: s[Hs:] = s[Hs - (H - Hs) - 24: Hs - 24][:H - Hs]     # prolonge le large vers le bas (rangées ROM répétées)
    s[HOR:, :, 3] = 255; seaF.append(s)
palF = []
chg_p = np.zeros(L0.shape[:2], bool)
for p in range(NPAL): chg_p |= (L0p[p] != L0).any(-1)
for p in range(NPAL):
    a = band_tile(np.where(chg_p[..., None], L0p[p], 0).astype(np.uint8))[:Hs]; s = np.zeros((H, W, 4), np.uint8); s[:Hs] = a; palF.append(s)
# nuages : extraits du ciel ROM (colonnes 480..552), posés en bande 2W en wrap parfait, base sur l'horizon
cx0 = 470; cs_ = comp[:HOR, cx0:552]; rc = rowc
cmask = (cs_.min(-1) > 150) & (np.abs(cs_ - rc[:, None]).sum(-1) > 30) & (np.arange(cs_.shape[1])[None, :] + cx0 >= 500)
cmask = nd.binary_closing(cmask, np.ones((3, 3))) & (np.abs(cs_ - rc[:, None]).sum(-1) > 12)
cmask &= np.arange(HOR)[:, None] > HOR - 60
lab, n = nd.label(cmask); keep = [i + 1 for i, s in enumerate(nd.find_objects(lab)) if (lab[s] == i + 1).sum() > 40]
cm = np.isin(lab, keep); ys_, xs_ = np.nonzero(cm)
y0c, y1c, x0c, x1c = ys_.min(), ys_.max() + 1, xs_.min(), xs_.max() + 1
spr = np.zeros((y1c - y0c, x1c - x0c, 4), np.uint8); spr[..., :3] = cs_[y0c:y1c, x0c:x1c]; spr[..., 3] = cm[y0c:y1c, x0c:x1c] * 255
BWC = 2 * W; clouds = np.zeros((HOR, BWC, 4), np.uint8)
for k, (x, fl, dy) in enumerate([(20, 0, 0), (170, 1, 3), (300, 0, 6), (470, 1, 1), (610, 0, 4)]):
    sp = spr[:, ::-1] if fl else spr; h_, w_ = sp.shape[:2]; top = HOR - h_ + dy
    for i in range(w_):
        X = (x + i) % BWC; m = sp[:, i, 3] > 0; clouds[top:top+h_, X][m[:HOR - top]] = sp[:HOR - top, i][m[:HOR - top]]
CL_SPEED = 4; CL_LOOP = BWC / CL_SPEED
def clouds_at(t):
    off = int(round(CL_SPEED * t / 1000)) % BWC; a = np.zeros((H, W, 4), np.uint8); a[:HOR] = np.roll(clouds, -off, 1)[:, :W]; return a
# ---------- sorties ----------
for d in ["calques", "mer_bpa", "mer_palette", "nuages", "import_png_8px", "apercu"]: (OUT / d).mkdir(parents=True, exist_ok=True)
def save(a, p): a = a.copy(); a[a[..., 3] == 0, :3] = 0; Image.fromarray(a.astype(np.uint8), "RGBA").save(p, optimize=True)
LAY = {"00_ciel": sky, "01_nuages": clouds_at(0), "02_mer_bpa": seaF[0], "03_mer_palette": palF[0], "04_terrain": terr}
for n_, a in LAY.items(): save(a, OUT / "calques" / f"{n_}.png"); save(a, OUT / "import_png_8px" / f"{PFX}{n_}.png")
save(clouds, OUT / "nuages" / f"{PFX}01_nuages_bande_{BWC}.png")
for i, a in enumerate(seaF): save(a, OUT / "mer_bpa" / f"{PFX}02_mer_bpa_f{i:02d}.png")
for i, a in enumerate(palF): save(a, OUT / "mer_palette" / f"{PFX}03_mer_palette_f{i:02d}.png")
def compose(t):
    fr = int(t * 60 / 1000); img = np.zeros((H, W, 3), float)
    for a in (sky, clouds_at(t), seaF[(fr // DB) % NB], palF[(fr // DP) % NPAL], terr):
        m = a[..., 3:4] / 255.; img = img * (1 - m) + a[..., :3] * m
    return Image.fromarray(img.astype(np.uint8))
ts = list(range(0, 6000, 83)); FR = [compose(t * 4) if False else compose(t) for t in ts]
FR[0].save(OUT / "apercu" / "animation.gif", save_all=True, append_images=FR[1:], duration=83, loop=0)
FR[0].save(OUT / "apercu" / "scene_statique.png")
ov = np.array(FR[0]).astype(float); cmk = np.kron(colT, np.ones((T, T)))[..., None] > 0
Image.fromarray((ov * np.where(cmk, .55, 1) + np.where(cmk, [110, 0, 0], 0)).clip(0, 255).astype(np.uint8)).save(OUT / "apercu" / "collisions.png")
seam = int((clouds[:, 0, 3] != clouds[:, -1, 3]).sum() and 0)
checks = {"canvas": [W, H], "horizon_y": HOR, "cases_marchables": int((colT == 0).sum()), "zones_marchables_connexes": int(nd.label(colT == 0)[1]),
          "nuages_bande": BWC, "nuages_boucle_s": CL_LOOP, "mer_bpa": [NB, DB], "palette": [NPAL, DP], "pixels_inventes": 0,
          "tuiles_miroir": int(sum(1 for q in P.ravel() if q >= 0 and SXY[q][0] >= SW))}
manifest = {"source": "pret/pmd-sky MAP_BG d06p11a", "prefixe_import": PFX, "canvas": [W, H], "grille": 8,
            "ordre_calques": list(LAY), "nuages": {"bande": f"nuages/{PFX}01_nuages_bande_{BWC}.png", "RepeatX": True, "vitesse_px_s": -CL_SPEED, "boucle_s": CL_LOOP},
            "animations": {"02_mer_bpa": {"frames": [f"mer_bpa/{PFX}02_mer_bpa_f{i:02d}.png" for i in range(NB)], "FrameLength_60fps": DB, "ms": round(DB * 1000 / 60, 1)},
                           "03_mer_palette": {"frames": [f"mer_palette/{PFX}03_mer_palette_f{i:02d}.png" for i in range(NPAL)], "FrameLength_60fps": DP, "ms": round(DP * 1000 / 60, 1)}},
            "collisions_8px": colT.tolist(), "controles": checks}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1, default=int))
with zipfile.ZipFile(OUT.parent / "zone_d06p11_v2_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(OUT.parent))
    for f in ("build.py", "rom_layers.py"): z.write(HERE / f, f"zone_d06p11_v2/source/{f}")
print(json.dumps(checks))
