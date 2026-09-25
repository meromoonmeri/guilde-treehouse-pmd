"""Sommet au coucher du soleil (112438.png, rip SparkuG23) -> multicalque V5.

Layout légèrement différent : sommet élargi de 64 px (deux bandes de 32 px dupliquées
de part et d'autre du chemin, qui reste droit et centré). Soleil animé : 12 frames de la planche.
Pixels 100 % planche, aucun générateur.
"""
import json, hashlib, pathlib, zipfile
import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REF = ROOT / "112438.png"
OUT = ROOT / "renders" / "summit_coucher_v5"
PFX = "SUMMITSUNSET_V5_"
src = np.array(Image.open(REF).convert("RGB")).astype(np.int16)
SHEET_BG = (112, 146, 190); FRAME_BG = (73, 111, 160)
eq = lambda a, c: np.all(a == np.array(c), axis=-1)

comp = src[137:431, 2:242]          # carte composée 240x294 (contrôle)
ter = src[174:431, 245:485]         # terrain seul 240x257, posé à y=37
sky_blk = src[434:519, 2:242]       # ciel orange 240x85
suns = [src[1 + 34 * r:32 + 34 * r, 2 + 99 * c:98 + 99 * c] for r in range(4) for c in range(3)]
W0, H0, TY = 240, 294, 37
# position du soleil par frame (recherche sur la carte composée, ciel visible)
sun_pos = []
for f in suns:
    fm = ~eq(f, FRAME_BG)
    best = max((((comp[y:y + 31, x:x + 96][fm] == f[fm]).all(1).mean()), y, x) for y in range(8, 20) for x in range(62, 80))
    sun_pos.append((best[1], best[2]))

# ---------- élargissement ----------
L_BAND, R_BAND = (24, 56), (184, 216)   # bandes dupliquées (hors chemin)
def widen(a):
    return np.concatenate([a[:, :L_BAND[1]], a[:, L_BAND[0]:L_BAND[1]], a[:, L_BAND[1]:R_BAND[0]],
                           a[:, R_BAND[0]:R_BAND[1]], a[:, R_BAND[0]:]], axis=1)
H = 296
terr = np.zeros((H0, W0, 4), np.uint8)
terr[TY:, :, :3] = ter; terr[TY:, :, 3] = (~eq(ter, SHEET_BG)) * 255
terr = np.concatenate([terr, terr[-1:], terr[-1:]], axis=0)  # 296 : lignes natives dupliquées
terr = widen(terr); W = terr.shape[1]
sky = np.zeros((H, W, 4), np.uint8)
rows = np.concatenate([sky_blk, np.repeat(sky_blk[-1:], H - sky_blk.shape[0], 0)], 0)
sky[..., :3] = widen(rows)[:, :W] if widen(rows).shape[1] >= W else 0; sky[..., 3] = 255
SHIFT = L_BAND[1] - L_BAND[0]
sun_frames = []
for f, (y, x) in zip(suns, sun_pos):
    a = np.zeros((H, W, 4), np.uint8); m = ~eq(f, FRAME_BG)
    X = x + SHIFT
    a[y:y + 31, X:X + 96][m] = np.concatenate([f, np.full(f.shape[:2] + (1,), 255, np.int16)], 2)[m]
    sun_frames.append(a)
SUN_MS = 100

# ---------- collisions : sol clair du sommet (sable), pas les mesas ----------
tc = terr[..., :3].astype(int)
from scipy import ndimage as nd
sandc = (terr[..., 3] > 0) & (tc[..., 0] >= 180) & (tc[..., 1] >= 140) & (np.arange(H)[:, None] > 60)
lab, n = nd.label(nd.binary_closing(sandc, iterations=2))
walk = nd.binary_erosion(lab == (np.argmax(nd.sum(sandc, lab, range(1, n + 1))) + 1), iterations=2)
grid = walk.reshape(H // 8, 8, W // 8, 8).mean(axis=(1, 3)) > 0.8

# ---------- sorties ----------
for d in ["calques", "soleil", "import_png_8px", "apercu"]: (OUT / d).mkdir(parents=True, exist_ok=True)
def save(a, p):
    a = a.copy(); a[a[..., 3] == 0, :3] = 0; Image.fromarray(a.astype(np.uint8), "RGBA").save(p, optimize=True)
LAYERS = [("00_ciel", sky), ("01_soleil", sun_frames[0]), ("02_terrain", terr)]
for n_, a in LAYERS:
    save(a, OUT / "calques" / f"{n_}.png"); save(a, OUT / "import_png_8px" / f"{PFX}{n_}.png")
for i, a in enumerate(sun_frames): save(a, OUT / "soleil" / f"{PFX}01_soleil_f{i:02d}.png")
def compose(i):
    img = np.zeros((H, W, 3), float)
    for a in (sky, sun_frames[i], terr):
        m = a[..., 3:4] / 255.0; img = img * (1 - m) + a[..., :3] * m
    return Image.fromarray(img.astype(np.uint8))
frames = [compose(i) for i in range(12)]
frames[0].save(OUT / "apercu" / "animation.gif", save_all=True, append_images=frames[1:], duration=SUN_MS, loop=0)
frames[0].save(OUT / "apercu" / "scene_statique.png")
cmp_ = Image.new("RGB", (W0 + 8 + W, H)); cmp_.paste(Image.fromarray(comp.astype(np.uint8)), (0, 0)); cmp_.paste(frames[8], (W0 + 8, 0))
cmp_.save(OUT / "apercu" / "reference_vs_v5.png")
ov = np.array(frames[0]).astype(int); blk = np.kron(~grid, np.ones((8, 8), bool)); ov[blk] = ov[blk] // 2 + [100, 0, 0]
Image.fromarray(ov.astype(np.uint8)).save(OUT / "apercu" / "collisions.png")

# contrôle : la recomposition non élargie doit reproduire la carte de la planche
test = np.zeros((H0, W0, 3), float)
t0 = np.zeros((H0, W0, 4)); t0[TY:, :, :3] = ter; t0[TY:, :, 3] = (~eq(ter, SHEET_BG)) * 255
s0 = np.zeros((H0, W0, 4)); s0[:85, :, :3] = sky_blk; s0[85:, :, :3] = sky_blk[-1]; s0[..., 3] = 255
u0 = np.zeros((H0, W0, 4)); y, x = sun_pos[8]; fm = ~eq(suns[8], FRAME_BG); u0[y:y + 31, x:x + 96][fm] = np.concatenate([suns[8], np.full((31, 96, 1), 255)], 2)[fm]
for a in (s0, u0, t0):
    m = a[..., 3:4] / 255.0; test = test * (1 - m) + a[..., :3] * m
recomp = float((test.astype(int) == comp).all(2).mean())
refc = set(map(tuple, src.reshape(-1, 3).tolist()))
cols = lambda a: set(map(tuple, a[a[..., 3] > 0][:, :3].astype(int).tolist()))
checks = {n_: {"taille": [a.shape[1], a.shape[0]], "div8": a.shape[0] % 8 == 0 and a.shape[1] % 8 == 0,
               "alpha_binaire": bool(np.isin(a[..., 3], [0, 255]).all()), "couleurs_hors_planche": len(cols(a) - refc)} for n_, a in LAYERS}
checks["soleil"] = {"frames": 12, "ms": SUN_MS, "positions": sun_pos, "couleurs_hors_planche": len(set().union(*map(cols, sun_frames)) - refc)}
checks["recomposition_reference_pct"] = round(recomp * 100, 2)
checks["cases_marchables"] = int(grid.sum())
manifest = {"reference": {"file": REF.name, "sha256": hashlib.sha256(REF.read_bytes()).hexdigest(), "ripper": "SparkuG23"},
            "canvas": [W, H], "grille": 8, "prefixe_import": PFX, "ordre_calques": [n_ for n_, _ in LAYERS],
            "layout": {"elargissement_px": 64, "bandes_dupliquees_x": [L_BAND, R_BAND], "chemin": "droit, sud -> nord, recentré"},
            "soleil": {"frames": [f"{PFX}01_soleil_f{i:02d}.png" for i in range(12)], "ms": SUN_MS, "note": "ordre de la planche (ligne par ligne) ; cadence choisie"},
            "collisions_8px": grid.astype(int).tolist(), "controles": checks}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1, default=int))
with zipfile.ZipFile(OUT.parent / "summit_coucher_v5_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(OUT.parent))
    z.write(__file__, "summit_coucher_v5/source/build.py")
print(json.dumps(checks, ensure_ascii=False, default=int))
