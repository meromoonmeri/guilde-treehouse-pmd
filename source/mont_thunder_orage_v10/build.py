"""Mont Thunder V10 — dérivé de V9.
- Sommet uniforme : le gravier clair du chemin (112/112/112, 112/120/120, 104/104/104) est remappé
  sur le gris du sommet (88/88/96) dans la zone praticable uniquement.
- Contrebas : brouillard indexé assorti à la roche, animé en PALETTE CYCLING (mouvement léger, inorganique).
- Nuages fins : bande 608 px recomposée en wrap parfait (traînées coupées au bord retirées, placement modulo),
  vitesse 4 px/s -> boucle exacte 152 s.
- Ciel et éclairs bleus : V9. Volutes V9 retirées (remplacées par le cycling).
"""
import json, pathlib, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parents[1]
V9 = ROOT / "renders" / "mont_thunder_orage_v9"; OUT = ROOT / "renders" / "mont_thunder_orage_v10"; PFX = "MTTHUNDER_V10_"
L = lambda p: np.array(Image.open(p).convert("RGBA"))
m9 = json.load(open(V9 / "manifest.json"))
terr = L(V9 / "calques" / "05_terrain.png"); sky = L(V9 / "calques" / "00_ciel.png")
H, W = terr.shape[:2]
BR_Y = m9["volutes"]["instances"] and None
# ---------- sommet uniforme ----------
g = np.array(m9["collisions_8px"]); wk = nd.binary_dilation(np.kron(g, np.ones((8, 8), int)).astype(bool)[:H, :W], iterations=3)
rgb = terr[..., :3].astype(int); n_fix = 0
for c in [(112, 112, 112), (112, 120, 120), (104, 104, 104)]:
    m = (rgb == c).all(-1) & wk & (terr[..., 3] > 0); n_fix += int(m.sum()); terr[m, :3] = (88, 88, 96)
# ---------- brouillard palette cycling ----------
b9 = L(V9 / "calques" / "02_brume_statique.png"); BR_Y = int(np.argmax(b9[..., 3].max(1) > 0))
RAMP = np.array([(24, 24, 32), (32, 32, 40), (40, 40, 48), (56, 56, 64), (72, 72, 80), (88, 88, 96),
                 (72, 72, 80), (56, 56, 64), (40, 40, 48), (32, 32, 40)])  # aller-retour : pas de saut
N = len(RAMP)
rng = np.random.default_rng(10)
def pnoise(h, w, cx, cy):  # bruit lisse périodique en x (tuile horizontale), étiré en largeur
    z = rng.random((cy, cx)); z = np.concatenate([z, z[:, :3]], 1)
    return np.array(Image.fromarray((z * 255).astype(np.uint8)).resize((w * (cx + 3) // cx, h), Image.BICUBIC))[:, :w] / 255.0
FH = H - BR_Y
y = np.arange(FH)[:, None]
field = 0.55 * pnoise(FH, W, 6, 10) + 0.3 * pnoise(FH, W, 12, 22) + 0.15 * pnoise(FH, W, 19, 40) + y / 90.0
# nappes horizontales quantifiées en paliers, tramage Bayer 2x2 sur les frontières
bay = np.array([[0, 2], [3, 1]]) / 4.0; bayer = np.tile(bay, (FH // 2 + 1, W // 2 + 1))[:FH, :W]
IDX = (np.floor(field * 7 + bayer * 0.9).astype(int)) % N
NF, MS = N * 2, 140  # 2 sous-pas par couleur : chaque frame décale une moitié des paliers -> glissement doux
def fog_at(f):
    shift = f // 2 + ((IDX % 2) * (f % 2))
    a = np.zeros((H, W, 4), np.uint8); a[BR_Y:, :, :3] = RAMP[(IDX + shift) % N]; a[BR_Y:, :, 3] = 255; return a
FOG = [fog_at(f) for f in range(NF)]
assert (FOG[0] == fog_at(NF)).all()
# ---------- nuages fins : wrap parfait ----------
band9 = L(V9 / "nuages" / "MTTHUNDER_V9_01_nuages_fins_bande_608.png"); BWd = band9.shape[1]
lab, n = nd.label(band9[..., 3] > 0, np.ones((3, 3))); band = np.zeros_like(band9); kept = 0
for i, sl in enumerate(nd.find_objects(lab)):
    if sl[1].start == 0 or sl[1].stop == BWd: continue  # traînée coupée par le bord du guide
    m = lab[sl] == i + 1; ys, xs = np.nonzero(m); kept += 1
    X = (xs + sl[1].start + 37 * i) % BWd; Y = ys + sl[0].start  # redistribution modulo : aucune couture
    band[Y, X] = band9[sl][ys, xs]
CL_SPEED = 4; CL_PERIOD_S = BWd / CL_SPEED
seam = int(((band[:, 0, 3] > 0) != (band[:, -1, 3] > 0)).sum())
def clouds_at(t):
    off = int(round(CL_SPEED * t / 1000)) % BWd; a = np.zeros((H, W, 4), np.uint8)
    b = np.roll(band, -off, 1)[:, :W]; a[:b.shape[0]] = b[:H]; return a
# ---------- éclairs V9 ----------
TL = [(L(V9 / "eclairs" / f["eclair"]), f["ms"]) for f in m9["timeline"]]; CYCLE = sum(ms for _, ms in TL)
# ---------- sorties ----------
for d in ["calques", "nuages", "brouillard", "eclairs", "import_png_8px", "apercu"]: (OUT / d).mkdir(parents=True, exist_ok=True)
def save(a, p): a = a.copy(); a[a[..., 3] == 0, :3] = 0; Image.fromarray(a, "RGBA").save(p, optimize=True)
LAYERS = [("00_ciel", sky), ("01_nuages_fins", clouds_at(0)), ("02_brouillard_cycling", FOG[0]), ("04_eclairs", None), ("05_terrain", terr)]
for n_, a in LAYERS:
    if a is not None: save(a, OUT / "calques" / f"{n_}.png"); save(a, OUT / "import_png_8px" / f"{PFX}{n_}.png")
save(band, OUT / "nuages" / f"{PFX}01_nuages_fins_bande_{BWd}.png")
for f, a in enumerate(FOG): save(a, OUT / "brouillard" / f"{PFX}02_brouillard_f{f:02d}.png")
# index + rampe pour un vrai cycling moteur
Image.fromarray(np.pad(IDX, ((BR_Y, 0), (0, 0))).astype(np.uint8) * 20).save(OUT / "brouillard" / f"{PFX}02_brouillard_index_x20.png")
timeline = []
for i, (a, ms) in enumerate(TL):
    fn = f"{PFX}04_eclairs_f{i:02d}.png"; save(a, OUT / "eclairs" / fn); timeline.append({"eclair": fn, "ms": ms})
def ecl(t):
    r = t % CYCLE
    for a, ms in TL:
        if r < ms: return a
        r -= ms
def compose(t):
    img = np.zeros((H, W, 3), float)
    for a in (sky, clouds_at(t), FOG[int(t // MS) % NF], ecl(t), terr):
        m = a[..., 3:4] / 255.0; img = img * (1 - m) + a[..., :3] * m
    return Image.fromarray(img.astype(np.uint8))
ts = list(range(0, NF * MS * 3, 70)); frames = [compose(t) for t in ts]
frames[0].save(OUT / "apercu" / "animation.gif", save_all=True, append_images=frames[1:], duration=70, loop=0)
frames[0].save(OUT / "apercu" / "scene_statique.png")
checks = {"taille": [W, H], "pixels_chemin_remappes": n_fix, "brouillard_frames": NF, "brouillard_ms": MS, "rampe": N,
          "nuages_trainees": kept, "nuages_couture_px": seam, "nuages_boucle_s": CL_PERIOD_S, "cycle_eclairs_ms": CYCLE}
manifest = {"canvas": [W, H], "grille": 8, "prefixe_import": PFX, "ordre_calques": [n_ for n_, _ in LAYERS],
            "nuages_fins": {"bande": f"nuages/{PFX}01_nuages_fins_bande_{BWd}.png", "RepeatX": True, "vitesse_px_s": -CL_SPEED, "boucle_s": CL_PERIOD_S},
            "brouillard": {"frames": [f"brouillard/{PFX}02_brouillard_f{f:02d}.png" for f in range(NF)], "ms": MS, "y": BR_Y,
                           "rampe_cycling": RAMP.tolist(), "index": f"brouillard/{PFX}02_brouillard_index_x20.png"},
            "timeline": timeline, "collisions_8px": m9["collisions_8px"], "controles": checks}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1, default=int))
with zipfile.ZipFile(OUT.parent / "mont_thunder_orage_v10_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(OUT.parent))
    z.write(__file__, "mont_thunder_orage_v10/source/build.py")
print(json.dumps(checks))
