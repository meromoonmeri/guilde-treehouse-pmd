"""Mont Thunder — sommet orageux V6.

Terrain : layout V5 (112438 élargi 64 px, chemin droit), recoloré en roche gris/noir
par remappage de palette (texture et ordre des teintes conservés, aucun pixel redessiné).
Ciel et nuages : guides générés dans la DA PMD (generation/), réduits et quantifiés.
Éclairs : formes canoniques de la planche 5394 (6/4 frames de croissance), recolorées en bleu.
"""
import json, hashlib, pathlib, zipfile
import numpy as np
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "renders" / "mont_thunder_orage_v6"
PFX = "MTTHUNDER_V6_"
V5 = ROOT / "renders" / "summit_coucher_v5" / "calques" / "02_terrain.png"
terr5 = np.array(Image.open(V5).convert("RGBA"))
SKY_ADD = 40  # ciel agrandi : terrain descendu de 40 px (5 cases)
terr = np.zeros((terr5.shape[0] + SKY_ADD, terr5.shape[1], 4), np.uint8); terr[SKY_ADD:] = terr5
H, W = terr.shape[:2]

# ---------- terrain gris/noir : remappage de palette par luminance ----------
cols = sorted(set(map(tuple, terr[terr[..., 3] > 0][:, :3].tolist())), key=lambda c: 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2])
def grey(c):
    L = 0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2]
    g = 10 + (L / 255.0) ** 1.7 * 185
    return (int(g * 0.97) // 8 * 8, int(g * 0.99) // 8 * 8, int(min(255, g * 1.04)) // 8 * 8)  # pas de 8 (style GBA)
REMAP = {c: grey(c) for c in cols}
tg = terr.copy()
for c, n in REMAP.items():
    tg[np.all(terr[..., :3] == c, axis=2) & (terr[..., 3] > 0), :3] = n

# ---------- ciel généré : bandes horizontales ----------
sky_g = np.array(Image.open(HERE / "generation" / "ciel_guide.png").convert("RGB"))
col = sky_g[:, sky_g.shape[1] // 2]
rows = np.array([col[int(y * (len(col) - 1) / (H - 1))] for y in range(H)])
rows = (rows // 8) * 8
sky = np.zeros((H, W, 4), np.uint8); sky[..., :3] = rows[:, None, :]; sky[..., 3] = 255

# ---------- nuages générés : bande 2W sans raccord, quantifiée ----------
cg = Image.open(HERE / "generation" / "nuages_guide.png").convert("RGB")
CW = 2 * W; CH = int(round(cg.height * CW / cg.width))
cs = np.array(cg.resize((CW, CH), Image.BOX)).astype(int)
mag = (cs[..., 0] > 190) & (cs[..., 1] < 100) & (cs[..., 2] > 190)
qi = Image.fromarray(cs.astype(np.uint8)).quantize(colors=10, method=Image.Quantize.MEDIANCUT)
pal = np.array(qi.getpalette()[:30]).reshape(10, 3) // 8 * 8
qidx = np.array(qi)
clouds = np.zeros((CH, CW, 4), np.uint8); clouds[..., :3] = pal[qidx]; clouds[..., 3] = (~mag) * 255
magp = [i for i in range(10) if (np.abs(pal[i] - [248, 0, 248]).sum() < 120)]
for i in magp: clouds[qidx == i, 3] = 0
CL_Y = -int(CH * 0.25)   # le haut de la bande déborde un peu du cadre
CL_SPEED = -6            # px/s, période 2W/6 s
FLASH_LV = 4
def flash(a, lv):  # éclaircissement bleuté par pas de palette (niveau 0 = normal)
    b = a.copy(); t = lv / (FLASH_LV + 1) * 0.55
    b[..., :3] = ((a[..., :3] * (1 - t) + np.array([176, 208, 248]) * t) // 8 * 8).astype(np.uint8)
    return b

# ---------- éclairs bleus (formes canoniques 5394) ----------
sheet = np.array(Image.open(ROOT / "5394.png").convert("RGB")).astype(int)
BLUE = {(248, 248, 136): (216, 240, 248), (232, 224, 120): (120, 184, 248), (208, 200, 112): (56, 104, 224)}
def crop(y0, y1, x0, x1):
    s = sheet[y0:y1, x0:x1]; a = np.zeros(s.shape[:2] + (4,), np.uint8)
    for c, b in BLUE.items():
        m = np.all(s == c, axis=2); a[m, :3] = b; a[m, 3] = 255
    return a
BOLTS = {"A": [(614, 619), (624, 629), (633, 643), (648, 659), (664, 675), (679, 690)], "B": [(617, 622), (624, 629), (634, 644), (648, 659), (666, 677), (686, 697)],
         "C": [(555, 559), (562, 568), (570, 579), (584, 590)], "D": [(555, 559), (563, 569), (572, 581), (584, 590)]}
BY = {"A": (131, 173), "B": (177, 219), "C": (227, 254), "D": (267, 294)}
LV = {6: [2, 4, 4, 3, 2, 1], 4: [2, 4, 3, 1]}
def strike(k, cx, cy, mir):
    out = []
    for x0, x1 in BOLTS[k]:
        b = crop(BY[k][0], BY[k][1], x0, x1)
        if mir: b = b[:, ::-1]
        f = np.zeros((H, W, 4), np.uint8); m = b[..., 3] > 0
        f[cy:cy + b.shape[0], cx:cx + b.shape[1]][m] = b[m]; out.append(f)
    return out, LV[len(out)]
EMPTY = np.zeros((H, W, 4), np.uint8)
PLAN = [("A", 60, 30, False), ("C", 200, 40, False), ("B", 236, 26, True), ("D", 110, 40, True), ("A", 170, 30, True), ("C", 30, 42, False)]
TL = []
for k, cx, cy, mir in PLAN:
    TL.append((EMPTY, 0, 1100))
    fr, lv = strike(k, cx, cy, mir)
    TL += [(f, l, 50) for f, l in zip(fr, lv)]
    TL += [(fr[-1], 1, 50), (EMPTY, 2, 50), (fr[-1], 1, 50), (EMPTY, 0, 50)]  # rebond de l'arc
CYCLE = sum(m for *_, m in TL)

# ---------- collisions (reprises de V5) ----------
m5 = json.load(open(ROOT / "renders" / "summit_coucher_v5" / "manifest.json"))
grid = [[0] * (W // 8) for _ in range(SKY_ADD // 8)] + m5["collisions_8px"]

# ---------- sorties ----------
for d in ["calques", "nuages", "eclairs", "import_png_8px", "apercu"]: (OUT / d).mkdir(parents=True, exist_ok=True)
def save(a, p):
    a = a.copy(); a[a[..., 3] == 0, :3] = 0; Image.fromarray(a.astype(np.uint8), "RGBA").save(p, optimize=True)
def cloud_frame(t, lv):
    off = int(round(-CL_SPEED * t / 1000)) % CW
    band = flash(np.roll(clouds, -off, axis=1)[:, :W], lv)
    a = np.zeros((H, W, 4), np.uint8); y0 = CL_Y
    a[max(0, y0):y0 + CH] = band[max(0, -y0):max(0, -y0) + min(H, y0 + CH) - max(0, y0)]
    return a
LAYERS = [("00_ciel", sky), ("01_nuages", cloud_frame(0, 0)), ("02_eclairs", None), ("03_terrain", tg)]
for n_, a in LAYERS:
    if a is not None: save(a, OUT / "calques" / f"{n_}.png"); save(a, OUT / "import_png_8px" / f"{PFX}{n_}.png")
save(clouds, OUT / "nuages" / f"{PFX}01_nuages_bande_{CW}.png")
for lv in range(FLASH_LV + 1): save(flash(clouds, lv), OUT / "nuages" / f"{PFX}01_nuages_bande_flash{lv}.png")
timeline = []
for i, (a, lv, ms) in enumerate(TL):
    fn = f"{PFX}02_eclairs_f{i:02d}.png"; save(a, OUT / "eclairs" / fn); timeline.append({"eclair": fn, "nuages_flash": lv, "ms": ms})
def at(t):
    r = t % CYCLE
    for a, lv, ms in TL:
        if r < ms: return a, lv
        r -= ms
def compose(t):
    e, lv = at(t); img = np.zeros((H, W, 3), float)
    for a in (flash(sky, max(0, lv - 1)), cloud_frame(t, lv), e, tg):
        m = a[..., 3:4] / 255.0; img = img * (1 - m) + a[..., :3] * m
    return Image.fromarray(img.astype(np.uint8))
ts = list(range(0, CYCLE, 50)); frames = [compose(t) for t in ts]
frames[0].save(OUT / "apercu" / "animation.gif", save_all=True, append_images=frames[1:], duration=50, loop=0)
frames[0].save(OUT / "apercu" / "scene_statique.png")
pk = max(range(len(ts)), key=lambda i: at(ts[i])[1] * 10000 + (at(ts[i])[0][..., 3] > 0).sum()); frames[pk].save(OUT / "apercu" / "scene_eclair.png")
v5 = Image.open(ROOT / "renders" / "summit_coucher_v5" / "apercu" / "scene_statique.png").convert("RGB")
cmp_ = Image.new("RGB", (W * 2 + 8, H)); cmp_.paste(v5, (0, 0)); cmp_.paste(frames[pk], (W + 8, 0)); cmp_.save(OUT / "apercu" / "v5_vs_v6.png")

checks = {"taille": [W, H], "div8": W % 8 == 0 and H % 8 == 0, "terrain_couleurs_remappees": len(REMAP),
          "terrain_forme_identique_v5": bool((tg[..., 3] == terr[..., 3]).all()),
          "nuages_bande": [CW, CH], "eclairs_frames": len(TL), "cycle_ms": CYCLE}
manifest = {"sources": {"terrain_v5": str(V5.relative_to(ROOT)), "planche_eclairs": "5394.png",
                        "guides_generes": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE / "generation").glob("*_guide.png"))}},
            "canvas": [W, H], "grille": 8, "prefixe_import": PFX, "ordre_calques": [n_ for n_, _ in LAYERS],
            "terrain_remap": {",".join(map(str, k)): list(v) for k, v in REMAP.items()},
            "nuages": {"bande": f"nuages/{PFX}01_nuages_bande_{CW}.png", "RepeatX": True, "vitesse_px_s": CL_SPEED, "y": CL_Y, "flash_niveaux": FLASH_LV + 1},
            "eclairs": {"couleurs": {",".join(map(str, k)): list(v) for k, v in BLUE.items()}, "positions": PLAN},
            "timeline": timeline, "collisions_8px": grid, "controles": checks}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1, default=int))
with zipfile.ZipFile(OUT.parent / "mont_thunder_orage_v6_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(OUT.parent))
    z.write(__file__, "mont_thunder_orage_v6/source/build.py")
print(json.dumps(checks, ensure_ascii=False))
