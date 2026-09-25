"""Mt. Thunder (PMD Rouge, salle du boss) -> arène orageuse multicalque V1.

Layout légèrement différent de la référence (plateau élargi de 32 px, décalé,
décors redistribués), pixels et palette 100 % issus de la référence.
Nuages et éclairs sur leurs propres calques animés.
"""
import json, hashlib, pathlib, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "renders" / "mt_thunder_orage_v1"
REF = HERE / "reference_mt_thunder.png"
W, H = 432, 352
DARK = (64, 56, 64)
PFX = "MTTHUNDER_V1_"

src = np.array(Image.open(REF).convert("RGB")).astype(np.int16)
scene, sheet = src[:H], src[H:]
R, G, B = scene[..., 0], scene[..., 1], scene[..., 2]
neutral = (abs(R - B) <= 16) & (abs(R - G) <= 16)
black = scene.sum(2) == 0
dark = np.all(scene == DARK, axis=2)

# ---------- plateau (sol + falaises) ----------
pl = nd.binary_fill_holes(~neutral & ~black)
lab, n = nd.label(pl)
pl = lab == (np.argmax(nd.sum(pl, lab, range(1, n + 1))) + 1)
pl = nd.binary_fill_holes(pl)

sand = pl & (R >= 216) & (B <= 168) & (G >= 200)
lab, n = nd.label(sand)
sand = lab == (np.argmax(nd.sum(sand, lab, range(1, n + 1))) + 1)
holes = nd.binary_fill_holes(sand) & ~sand
dlab, dn = nd.label(holes, np.ones((3, 3)))
decos = []
plat = scene.copy()
for i, sl in enumerate(nd.find_objects(dlab)):
    m = dlab[sl] == i + 1
    if m.sum() < 6:
        continue  # trait de texture du sable, pas un décor
    y0, x0 = sl[0].start, sl[1].start
    rgba = np.zeros(m.shape + (4,), np.uint8)
    rgba[..., :3] = scene[sl]; rgba[..., 3] = m * 255
    decos.append({"x": int(x0), "y": int(y0), "img": rgba, "px": int(m.sum())})
    # comblement : sable natif pris 24 px à gauche/droite (texture d'origine)
    for yy, xx in zip(*np.where(m)):
        Y, X = yy + y0, xx + x0
        for dx in (-24, 24, -48, 48, -16, 16):
            if 0 <= X + dx < W and sand[Y, X + dx]:
                plat[Y, X] = scene[Y, X + dx]; break

# prolongement vertical sous la bande de nuages avant (révélée par le défilement)
Y0 = 288
ext = pl.copy()
for y in range(Y0, 340):
    sy = Y0 - 16 + (y - Y0) % 16
    ext[y] = pl[sy]; plat[y] = plat[sy] if y >= Y0 else plat[y]
pl = ext

# élargissement : duplication d'une bande centrale 32 px de sable pur, recadrage
def widen(arr):
    w = np.concatenate([arr[:, :232], arr[:, 200:232], arr[:, 232:]], axis=1)
    return w[:, 16:16 + W]
plat_w, pl_w = widen(plat), widen(pl)
sand_w = widen(sand | holes)
plateau = np.zeros((H, W, 4), np.uint8)
plateau[..., :3] = plat_w; plateau[..., 3] = pl_w * 255

# décors redistribués : miroir horizontal de leur POSITION (sprites non retournés)
details = np.zeros((H, W, 4), np.uint8)
placed = []
for d in decos:
    h, w = d["img"].shape[:2]
    nx = W - (d["x"] + 16) - w  # position symétrique dans le nouveau repère
    nx = max(0, min(W - w, nx)); ny = d["y"]
    ok = bool(sand_w[ny:ny + h, nx:nx + w][d["img"][..., 3] > 0].all())
    if not ok:
        nx = d["x"] - 16 + (16 if d["x"] >= 216 else 0)  # repli : position d'origine décalée
    a = d["img"][..., 3] > 0
    details[ny:ny + h, nx:nx + w][a] = d["img"][a]
    placed.append({"from": [d["x"], d["y"]], "to": [int(nx), int(ny)], "size": [w, h], "px": d["px"]})

# ---------- ciel ----------
ciel = np.zeros((H, W, 4), np.uint8); ciel[..., :3] = DARK; ciel[..., 3] = 255

# ---------- nuages ----------
lum = scene[..., 0]
clouds_src = scene.copy()
orig_pl = nd.binary_fill_holes(lab.astype(bool)) if False else None
hidden = ~(neutral) | black  # pixels non-nuage : plateau (et coins noirs)
# comblement derrière le plateau : ping-pong fixe des colonnes libres de bord
L, Rt = 55, 377
def pingpong(k, n):
    k %= 2 * n
    return k if k < n else 2 * n - 1 - k
for x in range(W):
    if x < L or x >= Rt:
        continue
    sx = L - 1 - pingpong(x - L, L) if x < 216 else Rt + pingpong(Rt - 1 - x + (432 - Rt), 432 - Rt) if False else (L - 1 - pingpong(x - L, L) if x < 216 else W - 1 - pingpong(x - Rt, W - Rt))
    col = hidden[:, x]
    clouds_src[col, x] = scene[col, sx]
# coins noirs : remplis depuis les colonnes voisines
for x in list(range(48)) + list(range(W - 48, W)):
    sx = 48 + (47 - x) if x < 48 else W - 49 - (x - (W - 48))
    col = black[:, x]
    clouds_src[col, x] = scene[col, sx]
cR = clouds_src[..., 0]
cdark = np.all(clouds_src == DARK, axis=2)
white = ~cdark & (cR >= 216) & (np.arange(H)[:, None] >= 280)
wl, _ = nd.label(white)
front = np.isin(wl, np.unique(wl[-1][wl[-1] > 0]))  # bande blanche reliée au bas de carte
back = ~cdark & ~front
def layer(mask):
    a = np.zeros((H, W, 4), np.uint8); a[..., :3] = clouds_src; a[..., 3] = mask * 255
    return a
def seamless(a):  # bande 2W sans raccord : original + miroir (RepeatX)
    return np.concatenate([a, a[:, ::-1]], axis=1)
nuages_arr, nuages_av = seamless(layer(back)), seamless(layer(front))
SPEED_BACK, SPEED_FRONT = -8, -16  # px/s ; périodes 108 s et 54 s sur 864 px

# ---------- éclairs (planche : Normal / Fading) ----------
def comp(y0, y1, x0, x1, color):
    sub = sheet[y0 - H:y1 - H, x0:x1]
    return np.all(sub == color, axis=2)
BOLTS = {1: comp(372, 443, 121, 129, (240, 240, 0)), 2: comp(372, 436, 169, 185, (240, 240, 0)),
         3: comp(372, 498, 219, 243, (240, 240, 0)), 4: comp(372, 475, 284, 307, (240, 240, 0))}
FLASH = comp(393, 401, 15, 55, (240, 240, 128))
PAL = {"normal": {"bolt": (240, 240, 0), "flash": (240, 240, 128)},
       "fading": {"bolt": (160, 152, 32), "flash": (184, 176, 120)}}
# côté gauche tel que la planche ; côté droit = miroir (note de la planche)
TOP = 44
POS = {1: 24, 2: 12, 3: 8, 4: 14}
def bolt_frame(k, side, state):
    f = np.zeros((H, W, 4), np.uint8)
    m = BOLTS[k]; fm = FLASH
    if side == "R":
        m = m[:, ::-1]; fm = fm[:, ::-1]
    h, w = m.shape
    x = POS[k] if side == "L" else W - POS[k] - w
    f[TOP:TOP + h, x:x + w][m] = PAL[state]["bolt"] + (255,)
    fx = x + w // 2 - fm.shape[1] // 2; fx = max(0, min(W - fm.shape[1], fx))
    f[TOP - 6:TOP + 2, fx:fx + fm.shape[1]][fm] = PAL[state]["flash"] + (255,)
    return f
EMPTY = np.zeros((H, W, 4), np.uint8)
seq = []  # (image, ms) : cadence choisie, pas la cadence GBA officielle
for k, side in [(1, "L"), (3, "R"), (2, "L"), (4, "R"), (3, "L"), (1, "R")]:
    seq += [(EMPTY, 900), (bolt_frame(k, side, "normal"), 67), (bolt_frame(k, side, "fading"), 67),
            (bolt_frame(k, side, "normal"), 67), (bolt_frame(k, side, "fading"), 133)]

# ---------- collisions 8 px ----------
walk = nd.binary_erosion(sand_w, iterations=4) & (np.arange(H)[:, None] < 296)
grid = walk.reshape(H // 8, 8, W // 8, 8).all(axis=(1, 3))

# ---------- sorties ----------
for d in ["calques", "eclairs", "import_png_8px", "apercu"]:
    (OUT / d).mkdir(parents=True, exist_ok=True)
def save(a, p):
    a = a.copy(); a[a[..., 3] == 0, :3] = 0
    Image.fromarray(a.astype(np.uint8), "RGBA").save(p, optimize=True)
LAYERS = [("00_ciel", ciel), ("01_nuages_arriere", nuages_arr), ("02_eclairs", None),
          ("03_plateau", plateau), ("04_details", details), ("05_nuages_avant", nuages_av)]
for name, a in LAYERS:
    if a is not None:
        save(a, OUT / "calques" / f"{name}.png")
        save(a, OUT / "import_png_8px" / f"{PFX}{name}.png")
eclair_meta = []
for i, (a, ms) in enumerate(seq):
    p = f"{PFX}02_eclairs_f{i:02d}.png"; save(a, OUT / "eclairs" / p)
    eclair_meta.append({"file": p, "ms": ms})

def compose(t_ms, eclair):
    img = ciel.astype(float).copy()
    def over(dst, a):
        m = a[..., 3:4] / 255.0; dst[..., :3] = dst[..., :3] * (1 - m) + a[..., :3] * m
    def scroll(strip, speed):
        off = int(round(-speed * t_ms / 1000)) % strip.shape[1]
        return np.roll(strip, -off, axis=1)[:, :W]
    over(img, scroll(nuages_arr, SPEED_BACK)); over(img, eclair)
    over(img, plateau); over(img, details); over(img, scroll(nuages_av, SPEED_FRONT))
    return Image.fromarray(img[..., :3].astype(np.uint8))
compose(0, EMPTY).save(OUT / "apercu" / "scene_statique.png")
frames, durs, t = [], [], 0
for a, ms in seq:
    step = 100 if ms > 100 else ms
    left = ms
    while left > 0:
        d = min(step, left); frames.append(compose(t, a)); durs.append(d); t += d; left -= d
frames[0].save(OUT / "apercu" / "animation.gif", save_all=True, append_images=frames[1:], duration=durs, loop=0)
ref = Image.fromarray(scene.astype(np.uint8)); new = frames[0]
cmp_ = Image.new("RGB", (W * 2 + 8, H), (0, 0, 0)); cmp_.paste(ref, (0, 0)); cmp_.paste(new, (W + 8, 0))
cmp_.save(OUT / "apercu" / "reference_vs_v1.png")
col = compose(0, EMPTY).convert("RGBA"); ov = np.array(col)
ov[np.kron(~grid, np.ones((8, 8), bool))] = (ov[np.kron(~grid, np.ones((8, 8), bool))] // 2) + np.array([100, 0, 0, 127], np.uint8)
Image.fromarray(ov).convert("RGB").save(OUT / "apercu" / "collisions.png")

# ---------- contrôles ----------
ref_colors = set(map(tuple, src.reshape(-1, 3)))
checks = {}
for name, a in LAYERS:
    if a is None: continue
    c = set(map(tuple, a[a[..., 3] > 0][:, :3].astype(int)))
    checks[name] = {"size": list(a.shape[1::-1]), "div8": a.shape[0] % 8 == 0 and a.shape[1] % 8 == 0,
                    "alpha_binaire": bool(np.isin(a[..., 3], [0, 255]).all()),
                    "couleurs_hors_reference": len(c - ref_colors)}
ec = set()
for a, _ in seq: ec |= set(map(tuple, a[a[..., 3] > 0][:, :3].astype(int)))
checks["02_eclairs"] = {"couleurs": sorted(map(list, ec)), "couleurs_hors_reference": len(ec - ref_colors), "frames": len(seq), "cycle_ms": sum(m for _, m in seq)}
diff = float((np.array(frames[0]) != scene.astype(np.uint8)).any(2).mean())
checks["layout_different_de_reference_pct"] = round(diff * 100, 1)
manifest = {
    "reference": {"file": REF.name, "sha256": hashlib.sha256(REF.read_bytes()).hexdigest()},
    "canvas": [W, H], "grille": 8, "prefixe_import": PFX,
    "ordre_calques": [n for n, _ in LAYERS],
    "nuages": {"01_nuages_arriere": {"largeur_bande": 2 * W, "RepeatX": True, "vitesse_px_s": SPEED_BACK, "periode_s": 2 * W / abs(SPEED_BACK)},
               "05_nuages_avant": {"largeur_bande": 2 * W, "RepeatX": True, "vitesse_px_s": SPEED_FRONT, "periode_s": 2 * W / abs(SPEED_FRONT)}},
    "eclairs": {"calque": "02_eclairs", "frames": eclair_meta, "palette": {k: {kk: list(vv) for kk, vv in v.items()} for k, v in PAL.items()},
                "note": "Éclairs 1-4 et Flash de la planche ; côté droit = miroir (indiqué par la planche). Séquence/cadence : choix artistique."},
    "layout": {"elargissement_px": 32, "bande_dupliquee_x": [200, 232], "decalage_x": -16, "decors": placed,
               "prolongement_plateau_sous_nuages_avant_y": [Y0, 340]},
    "collisions_8px": grid.astype(int).tolist(),
    "controles": checks,
}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1, default=int))
with zipfile.ZipFile(OUT.parent / "mt_thunder_orage_v1_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(OUT.parent))
    z.write(__file__, "mt_thunder_orage_v1/source/build.py")
print(json.dumps(checks, ensure_ascii=False, indent=1, default=int))
