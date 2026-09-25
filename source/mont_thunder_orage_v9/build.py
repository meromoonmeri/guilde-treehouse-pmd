"""Mont Thunder V9 — ciel, nuages fins et brume régénérés, palette commune à tous les calques.

- Terrain et éclairs bleus : V8 (inchangés).
- Ciel (bandes) + nuages fins extraits du même guide généré ; nuages en dérive lente.
- Brume du contrebas : guide généré, STATIQUE.
- Volutes : quelques sprites générés qui dérivent dans le vide et s'éclairent aux impacts.
- Toutes les couleurs générées sont ramenées sur une palette commune (terrain + 16 teintes).
"""
import json, hashlib, pathlib, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V8 = ROOT / "renders" / "mont_thunder_orage_v8"
OUT = ROOT / "renders" / "mont_thunder_orage_v9"
PFX = "MTTHUNDER_V9_"
G = HERE / "generation"
terr8 = np.array(Image.open(V8 / "calques" / "05_terrain.png").convert("RGBA"))
SKY_ADD = 32  # ciel agrandi de 32 px (4 cases) : les nuages fins ont la place de se lire
terr = np.zeros((terr8.shape[0] + SKY_ADD, terr8.shape[1], 4), np.uint8); terr[SKY_ADD:] = terr8
H, W = terr.shape[:2]
m8 = json.load(open(V8 / "manifest.json"))
BR_Y = m8["brume"]["y"] + SKY_ADD

def box(p, w, h): return np.array(Image.open(p).convert("RGB").resize((w, h), Image.BOX)).astype(int)
def is_mag(a): return (a[..., 0] > 190) & (a[..., 1] < 100) & (a[..., 2] > 190)

# ---------- ciel + nuages fins ----------
cg = Image.open(G / "ciel_guide.png"); sw = 2 * W; sh = int(round(cg.height * sw / cg.width))
cs = box(G / "ciel_guide.png", sw, sh)
bandc = np.median(cs, axis=1)                       # couleur de bande par ligne
dev = np.abs(cs - bandc[:, None, :]).sum(2) > 24    # nuages = écart à la bande
dev = nd.binary_opening(dev, np.ones((1, 2)))
SKY_H = BR_Y + 40
rows = np.array([bandc[int(y * (sh - 1) / (SKY_H - 1))] for y in range(SKY_H)])
# ---------- brume statique ----------
bgp = Image.open(G / "brume_guide.png"); BW = 2 * W; BH = int(round(bgp.height * BW / bgp.width))
bs = box(G / "brume_guide.png", BW, BH)
# ---------- volutes ----------
vg = np.array(Image.open(G / "volutes_guide.png").convert("RGB")).astype(int)
vm = ~is_mag(vg); lab, n = nd.label(vm)
SCALE = 0.11
wisps = []
for i, sl in enumerate(nd.find_objects(lab)):
    m = lab[sl] == i + 1
    if m.sum() < 2000: continue
    h, w = m.shape; nh, nw = max(4, int(h * SCALE)), max(6, int(w * SCALE))
    rgb = np.array(Image.fromarray(vg[sl].astype(np.uint8)).resize((nw, nh), Image.BOX)).astype(int)
    mm = np.array(Image.fromarray((m * 255).astype(np.uint8)).resize((nw, nh), Image.BOX)) > 140
    wisps.append((rgb, mm))

# ---------- palette commune ----------
tcols = np.array(sorted(set(map(tuple, terr[terr[..., 3] > 0][:, :3].tolist()))))
pool = np.concatenate([rows.reshape(-1, 3), cs[dev].reshape(-1, 3), bs.reshape(-1, 3)] + [r[m] for r, m in wisps]).astype(np.uint8)
q = Image.fromarray(pool[None]).quantize(colors=16, method=Image.Quantize.MEDIANCUT)
gen_pal = np.array(q.getpalette()[:48]).reshape(16, 3) // 8 * 8
PAL = np.unique(np.concatenate([tcols, gen_pal]), axis=0).astype(int)
def snap(a):
    d = ((a[..., None, :].astype(np.int32) - PAL[None].astype(np.int32)) ** 2).sum(-1)
    return PAL[d.argmin(-1)]

sky = np.zeros((H, W, 4), np.uint8); sr = snap(rows[:, None, :])[:, 0]
sky[:SKY_H, :, :3] = sr[:, None]; sky[SKY_H:, :, :3] = sr[-1]; sky[..., 3] = 255
cl_band = np.zeros((sh, sw, 4), np.uint8); cl_band[..., :3] = snap(cs); cl_band[..., 3] = dev * 255
CL_SPEED = -3
# nuages fins : chaque traînée est gardée intacte mais rapprochée verticalement dans le ciel visible
cl2 = np.zeros((64, sw, 4), np.uint8)
lab_c, n_c = nd.label(dev, np.ones((3, 3)))
y_min = min(sl[0].start for sl in nd.find_objects(lab_c))
for i, sl in enumerate(nd.find_objects(lab_c)):
    m = lab_c[sl] == i + 1
    ny = 4 + int((sl[0].start - y_min) * 0.28)
    h = min(m.shape[0], 64 - ny)
    if h <= 0: continue
    dst = cl2[ny:ny + h, sl[1]]; mm = m[:h]
    dst[mm] = cl_band[sl][:h][mm]
cl_band = cl2
CL_CROP = 0
brume = np.zeros((H, W, 4), np.uint8)
bq = snap(bs); reps = int(np.ceil((H - BR_Y) / BH)) + 1
brume[BR_Y:, :, :3] = np.concatenate([bq] * reps, 0)[:H - BR_Y, :W]; brume[BR_Y:, :, 3] = 255
wisps = [(snap(r), m) for r, m in wisps]

# ---------- éclairs V8 + volutes mobiles ----------
TL = []
for f in m8["timeline"]:
    e8 = np.array(Image.open(V8 / "eclairs" / f["eclair"]).convert("RGBA")); e = np.zeros((H, W, 4), np.uint8); e[SKY_ADD:] = e8
    TL.append((e, f["nuages_flash"], f["ms"]))
CYCLE = sum(m for *_, m in TL)
void = (terr[..., 3] == 0) & (np.arange(H)[:, None] > BR_Y + 16)
def lighter(rgb, k):
    out = rgb.copy()
    for _ in range(k):
        L = PAL.mean(1); cur = out
        d = ((cur[..., None, :] - PAL[None]) ** 2).sum(-1); idx = d.argmin(-1)
        # couleur de palette immédiatement plus claire et de teinte proche
        cand = np.where(L[None, None, :] > L[idx][..., None] + 4, ((PAL[None, None] - cur[..., None, :]) ** 2).sum(-1), 1e9)
        out = PAL[cand.argmin(-1)]
    return out
# trajectoires : chaque volute oscille dans une poche de vide, période = cycle des éclairs
pockets = []
lab2, n2 = nd.label(void)
for i, sl in enumerate(sorted(nd.find_objects(lab2), key=lambda s: -(s[0].stop - s[0].start) * (s[1].stop - s[1].start))[:2]):
    pockets.append(sl)
INST = []
rng = np.random.default_rng(5)
for k in range(6):
    sl = pockets[k % len(pockets)]
    y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
    INST.append({"w": k % len(wisps), "cy": int(y0 + (y1 - y0) * (0.18 + 0.3 * (k // 2))), "cx": int((x0 + x1) / 2),
                 "ax": int(rng.integers(6, 14)), "ay": int(rng.integers(3, 8)), "ph": float(rng.random())})
WMS = 150; NW = CYCLE // WMS
def flash_at(t):
    r = t % CYCLE
    for a, lv, ms in TL:
        if r < ms: return lv
        r -= ms
    return 0
def wisps_at(f):
    t = f * WMS; lv = flash_at(t); a = np.zeros((H, W, 4), np.uint8)
    for it in INST:
        rgb, m = wisps[it["w"]]
        rgb = lighter(rgb, 3 if lv >= 3 else (2 if lv >= 1 else 1))
        ph = 2 * np.pi * (f / NW + it["ph"])
        cx = int(round(it["cx"] + it["ax"] * np.sin(ph))); cy = int(round(it["cy"] + it["ay"] * np.sin(2 * ph)))
        h, w = m.shape; ys, xs = cy - h // 2, cx - w // 2
        for yy in range(h):
            for xx in range(w):
                Y, X = ys + yy, xs + xx
                if m[yy, xx] and 0 <= Y < H and 0 <= X < W: a[Y, X, :3] = rgb[yy, xx]; a[Y, X, 3] = 255
    return a
WF = [wisps_at(f) for f in range(NW)]

# ---------- sorties ----------
for d in ["calques", "nuages", "volutes", "eclairs", "import_png_8px", "apercu"]: (OUT / d).mkdir(parents=True, exist_ok=True)
def save(a, p):
    a = a.copy(); a[a[..., 3] == 0, :3] = 0; Image.fromarray(a.astype(np.uint8), "RGBA").save(p, optimize=True)
def clouds_at(t):
    off = int(round(-CL_SPEED * t / 1000)) % sw
    b = np.roll(cl_band, -off, axis=1)[:, :W][CL_CROP:]; a = np.zeros((H, W, 4), np.uint8); a[:b.shape[0]] = b[:H]; return a
LAYERS = [("00_ciel", sky), ("01_nuages_fins", clouds_at(0)), ("02_brume_statique", brume), ("03_volutes", WF[0]), ("04_eclairs", None), ("05_terrain", terr)]
for n_, a in LAYERS:
    if a is not None: save(a, OUT / "calques" / f"{n_}.png"); save(a, OUT / "import_png_8px" / f"{PFX}{n_}.png")
save(cl_band, OUT / "nuages" / f"{PFX}01_nuages_fins_bande_{sw}.png")
for f, a in enumerate(WF): save(a, OUT / "volutes" / f"{PFX}03_volutes_f{f:02d}.png")
timeline = []
for i, (a, lv, ms) in enumerate(TL):
    fn = f"{PFX}04_eclairs_f{i:02d}.png"; save(a, OUT / "eclairs" / fn); timeline.append({"eclair": fn, "flash": lv, "ms": ms})
def at(t):
    r = t % CYCLE
    for a, lv, ms in TL:
        if r < ms: return a, lv
        r -= ms
def compose(t):
    e, lv = at(t); img = np.zeros((H, W, 3), float)
    for a in (sky, clouds_at(t), brume, WF[int(t // WMS) % NW], e, terr):
        m = a[..., 3:4] / 255.0; img = img * (1 - m) + a[..., :3] * m
    return Image.fromarray(img.astype(np.uint8))
ts = list(range(0, CYCLE, 50)); frames = [compose(t) for t in ts]
frames[0].save(OUT / "apercu" / "animation.gif", save_all=True, append_images=frames[1:], duration=50, loop=0)
frames[0].save(OUT / "apercu" / "scene_statique.png")
pk = max(range(len(ts)), key=lambda i: at(ts[i])[1] * 10000 + (at(ts[i])[0][..., 3] > 0).sum()); frames[pk].save(OUT / "apercu" / "scene_eclair.png")
cols = lambda a: set(map(tuple, a[a[..., 3] > 0][:, :3].astype(int).tolist()))
allc = set().union(*[cols(a) for n_, a in LAYERS if a is not None and n_ != "05_terrain"], cols(cl_band), *map(cols, WF))
checks = {"taille": [W, H], "palette_commune": len(PAL), "couleurs_generees_hors_palette": len(allc - set(map(tuple, PAL.tolist()))),
          "brume_statique": True, "volutes": len(INST), "volutes_frames": NW, "cycle_ms": CYCLE}
manifest = {"guides_generes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(G.glob("*_guide.png"))},
            "canvas": [W, H], "grille": 8, "prefixe_import": PFX, "ordre_calques": [n_ for n_, _ in LAYERS],
            "palette_commune": PAL.tolist(),
            "nuages_fins": {"bande": f"nuages/{PFX}01_nuages_fins_bande_{sw}.png", "RepeatX": True, "vitesse_px_s": CL_SPEED},
            "volutes": {"frames": [f"volutes/{PFX}03_volutes_f{f:02d}.png" for f in range(NW)], "ms": WMS, "instances": INST,
                        "note": "oscillation lente dans les poches de vide, éclaircissement 1-2 pas aux impacts (synchro timeline)"},
            "timeline": timeline, "collisions_8px": [[0] * (W // 8)] * (SKY_ADD // 8) + m8["collisions_8px"], "controles": checks}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1, default=int))
with zipfile.ZipFile(OUT.parent / "mont_thunder_orage_v9_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(OUT.parent))
    z.write(__file__, "mont_thunder_orage_v9/source/build.py")
print(json.dumps(checks, ensure_ascii=False))
