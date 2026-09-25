"""Zone D06P11 V1 — nouveau layout multicalque avec les TEXTURES ROM de d06p11a (PMD Sky).
- Synthèse par chunks 24x24 (unité native BMA) : chaque case cible reçoit un chunk source entier
  (couche basse + couche haute + ses 3x3 cases de collision), choisi par classe (roche/sable/grotte/mer),
  contexte des 8 voisins et cohérence avec les chunks déjà posés -> aucun pixel inventé.
- Calques séparés par horloge (durées réelles ROM) : base, mer BPA (10 f x 10), scintillement palette (7 f x 5), couche haute.
- Colorimétrie : les couleurs propres à la roche sont réchauffées vers la teinte du sable (LUT sur couleurs, pas de filtre).
"""
import json, colorsys, pathlib, zipfile, numpy as np
from PIL import Image
from rom_layers import layer, col, NX, NY, NPAL, CW
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parents[1]
OUT = ROOT / "renders" / "zone_d06p11_v1"; PFX = "D06P11_V1_"
NB, DB, DP = 10, 10, 5          # BPA : 10 frames x 10 f ; palette : 7 frames x 5 f (60 fps)
L0 = {(b, p): layer(0, b, p)[0] for b in range(NB) for p in ([0] if b else range(NPAL))}
for b in range(NB): L0[(b, 0)] = layer(0, b, 0)[0]
for p in range(NPAL): L0[(0, p)] = layer(0, 0, p)[0]
L1 = layer(1)[0]
comp = np.where(L1[..., 3:] > 0, L1[..., :3], L0[(0, 0)][..., :3]).astype(int)
walk = col == 0
def cls(x, y):
    p = comp[y*CW:(y+1)*CW, x*CW:(x+1)*CW]; w = walk[y*3:y*3+3, x*3:x*3+3].sum()
    if (p[..., 2] > p[..., 0] + 15).mean() > .5: return "M"
    if (p.sum(-1) < 120).mean() > .25: return "K"
    return "S" if w >= 5 else "R"
SRC = [[cls(x, y) for x in range(NX)] for y in range(NY)]
TGT = """RRRRRRRRRRRRRMMM
RRRRRRRRRRRRRMMM
RRRRRRRRRRRRRMMM
RRRRRRRRRRRRRMMM
RRRKKRRRRRRRRMMM
RRRRSRRRRRRRRMMM
RRRSSSRRRRRRRMMM
RRRSSSSSSSRRRMMM
RRRRSSSSSSSRRMMM
RRRRRRRRSSSRRMMM
RRRRRRRRSSSRRMMM
RRRSSSSSSSSRRMMM
RRSSSSSSSSRRRMMM
RRSSSSRRRRRRRMMM
RRSSSSSSSSSSRMMM
RRRRRSSSSSSSRMMM
RRRRRRRRRRRRRMMM
RRRRRRRRRRRRRMMM""".split()
TW, TH = len(TGT[0]) * 3, len(TGT) * 3
# ---------- synthèse au pas de la tuile 8x8 (unité BPC) ----------
from scipy import ndimage as nd
T = 8; SW, SH = NX * 3, NY * 3
def tcls(x, y):
    p = comp[y*T:(y+1)*T, x*T:(x+1)*T]
    if (p[..., 2] > p[..., 0] + 15).mean() > .5: return 3   # mer/ciel
    if (p.sum(-1) < 120).mean() > .4: return 2             # grotte
    return 1 if walk[y, x] else 0                          # sable / roche
SC = np.array([[tcls(x, y) for x in range(SW)] for y in range(SH)])
cmap = {"R": 0, "S": 1, "K": 2, "M": 3}
TG = np.kron(np.array([[cmap[c] for c in r] for r in TGT]), np.ones((3, 3), int))
# bords organiques : lissage majoritaire du sable (la roche/mer/grotte restent)
# blocs structurels copiés tels quels (grotte + falaise/mer) : (src_x, src_y, w, h, dst_x, dst_y) en tuiles
FIXED = [(13*3, 4*3, 5*3, 5*3, 2*3, 2*3), (19*3, 0, 4*3, SH, 12*3, 0)]
P = -np.ones((TH, TW), int)
for sx0, sy0, w, h, dx0, dy0 in FIXED:
    for yy in range(h):
        for xx in range(w):
            P[dy0+yy, dx0+xx] = (sy0+yy) * SW + sx0 + xx; TG[dy0+yy, dx0+xx] = SC[sy0+yy, sx0+xx]
# bords de sable organiques : bruit lisse sur la frontière sable/roche (hors blocs fixes)
_r = np.random.default_rng(3); nz = nd.zoom(_r.random((TH // 4 + 2, TW // 4 + 2)), 4, order=1)[:TH, :TW]
sd = nd.distance_transform_edt(TG == 1) - nd.distance_transform_edt(TG != 1)
org = np.where(TG <= 1, (sd + (nz - .5) * 3.2 > 0.5).astype(int), TG)
TG = np.where(P >= 0, TG, org)
Rw = 2; K = 2 * Rw + 1
padS = np.pad(SC, Rw, constant_values=-1); padT = np.pad(TG, Rw, constant_values=-1)
WS = np.stack([padS[y:y+K, x:x+K].ravel() for y in range(SH) for x in range(SW)])   # (N, 25)
TILES = np.stack([comp[y*T:(y+1)*T, x*T:(x+1)*T] for y in range(SH) for x in range(SW)]).astype(np.int32)
SXY = np.array([(x, y) for y in range(SH) for x in range(SW)])
own = SC.ravel()
FIX = None
rng = np.random.default_rng(6); N8 = [(-1, -1), (0, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
FIXM = P >= 0
for it in range(3):
  for ty in range(TH):
    for tx in range(TW):
        if FIXM[ty, tx]: continue
        wt = padT[ty:ty+K, tx:tx+K].ravel(); valid = wt >= 0
        c = ((WS != wt) & valid & (WS >= 0)).sum(1) * 30.0 + ((WS < 0) & valid).sum(1) * 30.0
        c[own != TG[ty, tx]] = 1e9
        if TG[ty, tx] == 3: c += 40 * np.abs(SXY[:, 1] - ty) / 3
        for dx, dy in N8:
            if not (0 <= tx+dx < TW and 0 <= ty+dy < TH): continue
            q = P[ty+dy, tx+dx]
            if q < 0: continue
            ex, ey = SXY[:, 0] + dx, SXY[:, 1] + dy
            ok = (ex >= 0) & (ex < SW) & (ey >= 0) & (ey < SH)
            ei = np.where(ok, ey * SW + ex, 0)
            d = np.abs(TILES[ei] - TILES[q]).mean((1, 2, 3))
            c += np.where(ok, np.where(ei == q, -60, d * 1.5), 40)
        c += rng.random(len(c)) * 3
        P[ty, tx] = int(np.argmin(c))
place = {(tx, ty): tuple(SXY[P[ty, tx]]) for ty in range(TH) for tx in range(TW)}
W, H = TW*T, TH*T
def assemble(src):
    o = np.zeros((H, W) + src.shape[2:], src.dtype)
    for (tx, ty), (sx, sy) in place.items(): o[ty*T:(ty+1)*T, tx*T:(tx+1)*T] = src[sy*T:(sy+1)*T, sx*T:(sx+1)*T]
    return o
colT = np.zeros((TH, TW), int)
for (tx, ty), (sx, sy) in place.items(): colT[ty, tx] = col[sy, sx]
_l, _n = nd.label(colT == 0); _sz = np.bincount(_l.ravel()); _sz[0] = 0
colT[(_l > 0) & (_l != _sz.argmax())] = 1   # îlots marchables isolés -> bloqués
# ---------- colorimétrie roche ----------
chunk = lambda sx, sy: comp[sy*CW:(sy+1)*CW, sx*CW:(sx+1)*CW]
R_px, S_px = [], []
for y in range(NY):
    for x in range(NX):
        p = chunk(x, y).reshape(-1, 3); (R_px if SRC[y][x] == "R" else S_px if SRC[y][x] == "S" else []).append(p) if SRC[y][x] in "RS" else None
def cnt(ps):
    c, n = np.unique(np.concatenate(ps), axis=0, return_counts=True); return {tuple(k): v for k, v in zip(c.tolist(), n)}
cr, cs = cnt(R_px), cnt(S_px)
sand = np.concatenate(S_px); sand = sand[(sand.sum(1) > 450)]  # sable clair
sh, ss, sv = colorsys.rgb_to_hsv(*(sand.mean(0) / 255))
LUT = {}
for c, n in cr.items():
    if c[2] > c[0] + 8: continue  # bleue (mer/ciel) : intacte
    h, s, v = colorsys.rgb_to_hsv(*(np.array(c) / 255))
    dh = ((sh - h + .5) % 1) - .5
    r, g, b = colorsys.hsv_to_rgb((h + 1.0 * dh) % 1, min(1, s * .8 + ss * .2), v)
    tone = np.array(colorsys.hsv_to_rgb(sh, ss, v))          # teinte du sable à la même valeur
    r, g, b = np.array([r, g, b]) * .7 + tone * .3
    LUT[c] = tuple(min(248, int(round(k * 255 / 8)) * 8) for k in (r, g, b))
# masque roche : tuiles dont la tuile source est de classe roche (le sable garde ses couleurs exactes)
RM = np.zeros((H, W), bool)
for (tx, ty), (sx, sy) in place.items(): RM[ty*T:(ty+1)*T, tx*T:(tx+1)*T] = SC[sy, sx] == 0
def recolor(a):
    a = a.copy(); ys, xs = np.nonzero(RM & ((a[..., 3] > 0) if a.shape[-1] == 4 else True))
    for y, x in zip(ys, xs):
        k = tuple(int(v) for v in a[y, x, :3])
        if k in LUT: a[y, x, :3] = LUT[k]
    return a
# ---------- calques par horloge ----------
base0 = L0[(0, 0)]
chg_b = np.zeros(base0.shape[:2], bool); chg_p = np.zeros_like(chg_b)
for b in range(NB): chg_b |= (L0[(b, 0)] != base0).any(-1)
for p in range(NPAL): chg_p |= (L0[(0, p)] != base0).any(-1)
chg_p &= ~chg_b
def masked(a, m): a = a.copy(); a[~m] = 0; return a
base = masked(base0, ~(chg_b | chg_p))
LAY = {"00_base": recolor(assemble(base)), "03_haut": recolor(assemble(L1))}
BPA = [recolor(assemble(masked(L0[(b, 0)], chg_b))) for b in range(NB)]
PAL = [recolor(assemble(masked(L0[(0, p)], chg_p))) for p in range(NPAL)]
for d in ["calques", "mer_bpa", "scintillement_palette", "import_png_8px", "apercu", "source_rom"]: (OUT / d).mkdir(parents=True, exist_ok=True)
def save(a, p): a = a.copy(); a[a[..., 3] == 0, :3] = 0; Image.fromarray(a.astype(np.uint8), "RGBA").save(p, optimize=True)
for n, a in LAY.items(): save(a, OUT / "calques" / f"{n}.png"); save(a, OUT / "import_png_8px" / f"{PFX}{n}.png")
for i, a in enumerate(BPA): save(a, OUT / "mer_bpa" / f"{PFX}01_mer_bpa_f{i:02d}.png")
for i, a in enumerate(PAL): save(a, OUT / "scintillement_palette" / f"{PFX}02_palette_f{i:02d}.png")
save(BPA[0], OUT / "calques" / "01_mer_bpa.png"); save(PAL[0], OUT / "calques" / "02_scintillement_palette.png")
def compose(fb, fp, rec=True):
    img = np.zeros((H, W, 3), float)
    for a in (LAY["00_base"], BPA[fb], PAL[fp], LAY["03_haut"]):
        m = a[..., 3:4] / 255.; img = img * (1 - m) + a[..., :3] * m
    return img.astype(np.uint8)
FR = []; step = 5  # pas commun (frames 60 fps)
for t in range(0, NB*DB*NPAL*DP // np.gcd(NB*DB, NPAL*DP), step):
    FR.append(Image.fromarray(compose((t // DB) % NB, (t // DP) % NPAL)))
FR[0].save(OUT / "apercu" / "animation.gif", save_all=True, append_images=FR[1:], duration=int(step * 1000 / 60), loop=0)
FR[0].save(OUT / "apercu" / "scene_statique.png")
ov = np.array(FR[0]).astype(float); cm = np.kron(colT, np.ones((8, 8)))[..., None] > 0
Image.fromarray((ov * np.where(cm, .55, 1) + np.where(cm, [110, 0, 0], 0)).clip(0, 255).astype(np.uint8)).save(OUT / "apercu" / "collisions.png")
src_prev = np.where(L1[..., 3:] > 0, L1[..., :3], L0[(0, 0)][..., :3]).astype(np.uint8)
Image.fromarray(src_prev).save(OUT / "source_rom" / "d06p11a_original.png")
# comparaison
A = Image.fromarray(src_prev); Bm = FR[0]; cmp_ = Image.new("RGB", (A.width + Bm.width + 16, max(A.height, Bm.height)), (20, 20, 20)); cmp_.paste(A, (0, 0)); cmp_.paste(Bm, (A.width + 16, 0)); cmp_.save(OUT / "apercu" / "original_vs_v1.png")
walkable = int((colT == 0).sum()); lab = __import__("scipy.ndimage", fromlist=["x"]).label(colT == 0)[1]
checks = {"canvas": [W, H], "chunks_source_distincts": len(set(place.values())), "couleurs_roche_recolorees": len(LUT),
          "cases_marchables": walkable, "zones_marchables_connexes": int(lab), "pixels_inventes": 0,
          "mer_bpa": {"frames": NB, "FrameLength": DB}, "palette": {"frames": NPAL, "FrameLength": DP}}
manifest = {"source": "pret/pmd-sky files/MAP_BG/d06p11a (.bma/.bpc/.bpl/.bpa)", "prefixe_import": PFX, "canvas": [W, H], "grille": 8,
            "ordre_calques": ["00_base", "01_mer_bpa", "02_scintillement_palette", "03_haut"],
            "animations": {"01_mer_bpa": {"frames": [f"mer_bpa/{PFX}01_mer_bpa_f{i:02d}.png" for i in range(NB)], "FrameLength_60fps": DB, "ms": round(DB*1000/60, 1)},
                           "02_scintillement_palette": {"frames": [f"scintillement_palette/{PFX}02_palette_f{i:02d}.png" for i in range(NPAL)], "FrameLength_60fps": DP, "ms": round(DP*1000/60, 1)}},
            "layout_cible": TGT, "placement_chunks": {f"{k[0]},{k[1]}": v for k, v in place.items()},
            "lut_roche": {",".join(map(str, k)): v for k, v in LUT.items()}, "collisions_8px": colT.tolist(), "controles": checks}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1, default=int))
with zipfile.ZipFile(OUT.parent / "zone_d06p11_v1_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(OUT.parent))
    for f in ("build.py", "rom_layers.py"): z.write(HERE / f, f"zone_d06p11_v1/source/{f}")
print(json.dumps(checks))
