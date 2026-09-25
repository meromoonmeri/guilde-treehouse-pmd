"""Mont Thunder V7 — nouvelle falaise générée (chemin droit, bordures) + brume électrostatique en contrebas.

Guides générés : generation/falaise_guide.png (ciel/vide magenta), generation/brume_guide.png.
Réduits en BOX, quantifiés au pas de 8. Ciel, nuages et éclairs bleus repris de V6.
"""
import json, hashlib, pathlib, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V6 = ROOT / "renders" / "mont_thunder_orage_v6"
OUT = ROOT / "renders" / "mont_thunder_orage_v7"
PFX = "MTTHUNDER_V7_"
W, H = 304, 456

def box(img, w, h): return np.array(img.convert("RGB").resize((w, h), Image.BOX)).astype(int)
def quant(rgb, n, mask=None):
    q = Image.fromarray(rgb.astype(np.uint8)).quantize(colors=n, method=Image.Quantize.MEDIANCUT)
    pal = np.array(q.getpalette()[:3 * n]).reshape(n, 3) // 8 * 8
    return pal[np.array(q)]

# ---------- terrain ----------
g = Image.open(HERE / "generation" / "falaise_guide.png")
big = np.array(g.convert("RGB")).astype(int)
magb = (big[..., 0] > 190) & (big[..., 1] < 90) & (big[..., 2] > 190)
mag = np.array(Image.fromarray((magb * 255).astype(np.uint8)).resize((W, H), Image.BOX)) > 110
ts = box(g, W, H)
tq = quant(np.where(mag[..., None], 0, ts), 24)
terr = np.zeros((H, W, 4), np.uint8); terr[..., :3] = tq; terr[..., 3] = (~mag) * 255
terr[nd.binary_opening(~mag, iterations=1) == 0, 3] = 0  # pixels isolés

# ---------- brume électrostatique ----------
bg = Image.open(HERE / "generation" / "brume_guide.png")
BW = 2 * W; BH = int(round(bg.height * BW / bg.width))
bs = box(bg, BW, BH)
cyan = (bs[..., 1] > 150) & (bs[..., 2] > 170) & (bs[..., 0] < 140)
body = bs.copy()
idx = nd.distance_transform_edt(cyan, return_distances=False, return_indices=True)
body[cyan] = bs[idx[0][cyan], idx[1][cyan]]  # brume sans étincelles (voisin le plus proche)
bq = quant(body, 10)
brume = np.zeros((BH, BW, 4), np.uint8); brume[..., :3] = bq; brume[..., 3] = 255
lab, n = nd.label(cyan, np.ones((3, 3)))
rng = np.random.default_rng(11); group = rng.integers(0, 4, n + 1)
SP = [(96, 232, 248), (168, 248, 248), (64, 168, 232)]
def sparks(f):  # 4 groupes, chacun allumé 2 frames sur 8, couleur tournante
    a = np.zeros((BH, BW, 4), np.uint8)
    for gi in range(4):
        ph = (f - 2 * gi) % 8
        if ph < 2:
            m = cyan & (group[lab] == gi); a[m, :3] = SP[ph]; a[m, 3] = 255
        elif ph == 2:
            m = cyan & (group[lab] == gi); a[m, :3] = SP[2]; a[m, 3] = 255
    return a
NSP, SPMS = 8, 90
BR_Y, BR_SPEED = 112, -4
def band_at(band, t, y0):
    off = int(round(-BR_SPEED * t / 1000)) % BW
    b = np.roll(band, -off, axis=1)[:, :W]
    a = np.zeros((H, W, 4), np.uint8)
    reps = int(np.ceil((H - y0) / BH)) + 1
    tall = np.concatenate([b] * reps, 0)[:H - y0]
    a[y0:] = tall; return a

# ---------- ciel, nuages, éclairs de V6 ----------
m6 = json.load(open(V6 / "manifest.json"))
sky6 = np.array(Image.open(V6 / "calques" / "00_ciel.png").convert("RGBA"))
sky = np.zeros((H, W, 4), np.uint8); sky[:sky6.shape[0]] = sky6; sky[sky6.shape[0]:] = sky6[-1]
cl6 = np.array(Image.open(V6 / "nuages" / "MTTHUNDER_V6_01_nuages_bande_608.png").convert("RGBA"))
CL_Y = m6["nuages"]["y"] - 12
def clouds_at(t, lv):
    off = int(round(6 * t / 1000)) % cl6.shape[1]
    b = np.roll(cl6, -off, axis=1)[:, :W].copy()
    tt = lv / 5 * 0.55; b[..., :3] = ((b[..., :3] * (1 - tt) + np.array([176, 208, 248]) * tt) // 8 * 8).astype(np.uint8)
    a = np.zeros((H, W, 4), np.uint8); y0 = CL_Y; h = min(b.shape[0] + y0, H)
    a[:h] = b[-y0:-y0 + h]; return a
raw = []
for f in m6["timeline"]:
    e = np.array(Image.open(V6 / "eclairs" / f["eclair"]).convert("RGBA"))
    raw.append([e, f["nuages_flash"], f["ms"]])
# éclairs replacés dans la brume en contrebas : chaque impact déplacé là où il est le plus visible
void = (terr[..., 3] == 0) & (np.arange(H)[:, None] > BR_Y + 20)
groups, cur = [], []
for i, (e, lv, ms) in enumerate(raw):
    if (e[..., 3] > 0).any(): cur.append(i)
    elif cur and ms > 200: groups.append(cur); cur = []
if cur: groups.append(cur)
shift = {}
used = []
for gi in groups:
    u = np.zeros(raw[0][0].shape[:2], bool)
    for i in gi: u |= raw[i][0][..., 3] > 0
    ys, xs = np.where(u); y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    m = u[y0:y1, x0:x1]; best = None
    for Y in range(BR_Y + 20, H - (y1 - y0), 4):
        for X in range(0, W - (x1 - x0), 2):
            if any(abs(Y - a) < 70 and abs(X - b) < 30 for a, b in used): continue
            v = void[Y:Y + y1 - y0, X:X + x1 - x0][m].mean()
            if best is None or v > best[0]: best = (v, Y, X)
    used.append(best[1:])
    for i in gi: shift[i] = (y0, x0, y1, x1, best[1], best[2])
TL = []
for i, (e, lv, ms) in enumerate(raw):
    ee = np.zeros((H, W, 4), np.uint8)
    for j in (i, i - 1, i - 2, i - 3, i - 4, i - 5):  # frames vides dans un impact : même décalage
        if j in shift: break
    if (e[..., 3] > 0).any() and i in shift:
        y0, x0, y1, x1, Y, X = shift[i]; ee[Y:Y + y1 - y0, X:X + x1 - x0] = e[y0:y1, x0:x1]
    TL.append((ee, lv, ms))
CYCLE = sum(m for *_, m in TL)

# ---------- collisions : sol clair plat (dessus de falaise + chemin) ----------
tc = terr[..., :3].astype(int); L = tc.mean(2)
flat = (terr[..., 3] > 0) & (L >= 80)
lab2, n2 = nd.label(nd.binary_closing(flat, iterations=2))
walk = nd.binary_erosion(lab2 == (np.argmax(nd.sum(flat, lab2, range(1, n2 + 1))) + 1), iterations=2)
grid = walk.reshape(H // 8, 8, W // 8, 8).mean(axis=(1, 3)) > 0.8

# ---------- sorties ----------
for d in ["calques", "brume", "eclairs", "import_png_8px", "apercu"]: (OUT / d).mkdir(parents=True, exist_ok=True)
def save(a, p):
    a = a.copy(); a[a[..., 3] == 0, :3] = 0; Image.fromarray(a.astype(np.uint8), "RGBA").save(p, optimize=True)
LAYERS = [("00_ciel", sky), ("01_nuages", clouds_at(0, 0)), ("02_brume", band_at(brume, 0, BR_Y)),
          ("03_brume_etincelles", band_at(sparks(0), 0, BR_Y)), ("04_eclairs", None), ("05_terrain", terr)]
for n_, a in LAYERS:
    if a is not None: save(a, OUT / "calques" / f"{n_}.png"); save(a, OUT / "import_png_8px" / f"{PFX}{n_}.png")
save(brume, OUT / "brume" / f"{PFX}02_brume_bande_{BW}x{BH}.png")
for f in range(NSP): save(sparks(f), OUT / "brume" / f"{PFX}03_etincelles_bande_f{f}.png")
timeline = []
for i, (a, lv, ms) in enumerate(TL):
    fn = f"{PFX}04_eclairs_f{i:02d}.png"; save(a, OUT / "eclairs" / fn); timeline.append({"eclair": fn, "nuages_flash": lv, "ms": ms})
def at(t):
    r = t % CYCLE
    for a, lv, ms in TL:
        if r < ms: return a, lv
        r -= ms
def compose(t):
    e, lv = at(t); img = np.zeros((H, W, 3), float)
    for a in (sky, clouds_at(t, lv), band_at(brume, t, BR_Y), band_at(sparks(int(t // SPMS) % NSP), t, BR_Y), e, terr):
        m = a[..., 3:4] / 255.0; img = img * (1 - m) + a[..., :3] * m
    return Image.fromarray(img.astype(np.uint8))
ts = list(range(0, CYCLE, 50)); frames = [compose(t) for t in ts]
frames[0].save(OUT / "apercu" / "animation.gif", save_all=True, append_images=frames[1:], duration=50, loop=0)
frames[0].save(OUT / "apercu" / "scene_statique.png")
pk = max(range(len(ts)), key=lambda i: at(ts[i])[1] * 10000 + (at(ts[i])[0][..., 3] > 0).sum()); frames[pk].save(OUT / "apercu" / "scene_eclair.png")
ov = np.array(frames[0]).astype(int); blk = np.kron(~grid, np.ones((8, 8), bool)); ov[blk] = ov[blk] // 2 + [100, 0, 0]
Image.fromarray(ov.astype(np.uint8)).save(OUT / "apercu" / "collisions.png")
checks = {"taille": [W, H], "div8": W % 8 == 0 and H % 8 == 0, "terrain_couleurs": len(set(map(tuple, tq[~mag].tolist()))),
          "alpha_binaire": bool(np.isin(terr[..., 3], [0, 255]).all()), "brume_opaque": True, "etincelles_composantes": int(n),
          "cases_marchables": int(grid.sum()), "cycle_eclairs_ms": CYCLE, "eclairs_positions": used}
manifest = {"guides_generes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE / "generation").glob("*_guide.png"))},
            "canvas": [W, H], "grille": 8, "prefixe_import": PFX, "ordre_calques": [n_ for n_, _ in LAYERS],
            "brume": {"bande": f"brume/{PFX}02_brume_bande_{BW}x{BH}.png", "RepeatX": True, "RepeatY": True, "vitesse_px_s": BR_SPEED, "y": BR_Y},
            "etincelles": {"frames": [f"brume/{PFX}03_etincelles_bande_f{f}.png" for f in range(NSP)], "ms": SPMS, "suit_la_brume": True},
            "nuages": {"source": "V6", "y": CL_Y, "vitesse_px_s": -6}, "timeline": timeline,
            "collisions_8px": grid.astype(int).tolist(), "controles": checks}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1, default=int))
with zipfile.ZipFile(OUT.parent / "mont_thunder_orage_v7_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(OUT.parent))
    z.write(__file__, "mont_thunder_orage_v7/source/build.py")
print(json.dumps(checks, ensure_ascii=False))
