"""Zone D06P11 V4 — entrée majestueuse (montagne rocheuse régénérée), nuages régénérés en boucle parfaite,
modes jour / crépuscule / nuit (ciels générés, étalonnage palette du terrain, de la mer et des nuages).
Fond mer : animations ROM de la V2 (BPA 10x10 f, palette 7x5 f)."""
import json, pathlib, zipfile, numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parents[1]; G = HERE / "generation"
V2 = ROOT / "renders" / "zone_d06p11_v2"; OUT = ROOT / "renders" / "zone_d06p11_v4"; PFX = "D06P11_V4_"
m2 = json.load(open(V2 / "manifest.json")); W, H = m2["canvas"]; HOR = 168
LD = lambda p: np.array(Image.open(p).convert("RGBA")).astype(int)
def is_mag(a): return (a[..., 0] > 170) & (a[..., 1] < 110) & (a[..., 2] > 170)
# ---------- terrain ----------
g = np.array(Image.open(G / "falaise_majestueuse.png").convert("RGB").resize((W, H), Image.BOX)).astype(int)
mag = nd.binary_opening(nd.binary_closing(is_mag(g), np.ones((3, 3))), np.ones((2, 2)))
t2 = LD(V2 / "calques" / "04_terrain.png"); PAL = np.unique(t2[t2[..., 3] > 0][:, :3], axis=0)
def snap(a, pal):
    d = ((a[..., None, :].astype(np.int32) - pal[None, None].astype(np.int32)) ** 2).sum(-1); return pal[d.argmin(-1)]
rgb = snap(g, PAL); terr = np.zeros((H, W, 4), int); terr[..., :3] = rgb; terr[..., 3] = np.where(mag, 0, 255)
hsv = np.array(Image.fromarray(rgb.astype(np.uint8)).convert("HSV")).astype(int)
sand = nd.binary_opening((~mag) & (rgb.sum(-1) > 500) & (hsv[..., 1] < 120), np.ones((3, 3)))
cells = sand.reshape(H // 8, 8, W // 8, 8).mean((1, 3)) > .6
lab, n = nd.label(cells); sz = np.bincount(lab.ravel()); sz[0] = 0; walk = lab == sz.argmax(); col = (~walk).astype(int)
# ---------- nuages générés : bande coupée entre deux colonnes vides -> boucle parfaite ----------
ro = np.array(Image.open(G / "nuages_roule_couture_centre.png").convert("RGB")).astype(int)   # guide roulé d'une demi-largeur
rp = np.array(Image.open(G / "nuages_couture_reparee.png").convert("RGB").resize((ro.shape[1], ro.shape[0]), Image.LANCZOS)).astype(int)
Wg = ro.shape[1]; c0, c1 = int(Wg * .4), int(Wg * .6)
# raccord : dans la bande centrale on prend la réparation ; coutures internes posées sur la colonne la plus proche
def best_cut(lo, hi): return lo + int(np.argmin([np.abs(ro[:, x] - rp[:, x]).sum() for x in range(lo, hi)]))
c0 = best_cut(int(Wg * .35), int(Wg * .45)); c1 = best_cut(int(Wg * .55), int(Wg * .65))
fixed = ro.copy(); fixed[:, c0:c1] = rp[:, c0:c1]
CH = 104; cw = int(round(Wg * CH / ro.shape[0])); c = np.array(Image.fromarray(fixed.astype(np.uint8)).resize((cw, CH), Image.BOX)).astype(int)
cm = nd.binary_opening(~is_mag(c), np.ones((2, 2)))
x1, x2 = 0, cw
band = np.zeros((CH, cw, 4), int); band[..., :3] = c; band[..., 3] = cm * 255
bw = band.shape[1]; CPAL = np.array(Image.fromarray(c[:, x1:x2][cm[:, x1:x2]][None].astype(np.uint8)).quantize(12).getpalette()[:36]).reshape(12, 3) // 8 * 8
band[..., :3] = np.where(band[..., 3:] > 0, snap(band[..., :3], CPAL), 0)
seam_ok = float(np.abs(band[:, 0, 3] - band[:, -1, 3]).mean() / 255)  # écart alpha entre la 1re et la dernière colonne (bords = colonnes voisines du guide)
CL_SPEED = 4
# ---------- ciels ----------
def sky_from(path, horizon_frac):
    im = np.array(Image.open(path).convert("RGB")).astype(int); h0, w0 = im.shape[:2]
    yh = int(h0 * horizon_frac); src = im[:yh]
    k = W / w0; top = max(0, yh - int(HOR / k)); src = src[top:]
    # bandes : médiane par rangée, rééchantillonnée
    rows = np.median(src, axis=1); ys = np.linspace(0, len(rows) - 1, HOR).astype(int); out = np.repeat(rows[ys][:, None], W, 1)
    # astres (étoiles, lune, soleil) : composantes claires reposées à l'échelle
    lum = src.sum(-1); bright = lum > np.median(lum, axis=1, keepdims=True) + 90
    lb, nb = nd.label(bright)
    for i, s in enumerate(nd.find_objects(lb)):
        m = lb[s] == i + 1; hh, ww = m.shape
        if m.sum() > 60:   # lune / soleil : réduit en conservant la forme
            nh, nw = max(3, int(hh * k)), max(3, int(ww * k))
            pr = np.array(Image.fromarray(src[s].astype(np.uint8)).resize((nw, nh), Image.BOX)).astype(int)
            pm = np.array(Image.fromarray((m * 255).astype(np.uint8)).resize((nw, nh), Image.BOX)) > 110
            Y, X = int(s[0].start * k), int(s[1].start * k)
            reg = out[Y:Y+nh, X:X+nw]; pm = pm[:reg.shape[0], :reg.shape[1]]; reg[pm] = pr[:reg.shape[0], :reg.shape[1]][pm]
        else:              # étoile : 1 px (2 px si grande)
            Y, X = int((s[0].start + hh / 2) * k * len(ys) / HOR * HOR / len(ys)), int((s[1].start + ww / 2) * k)
            Y = min(HOR - 1, int((s[0].start + hh / 2) * (HOR - 1) / (len(rows) - 1))) if len(rows) > 1 else 0
            X = min(W - 1, X); out[Y, X] = src[s][m].max(0)
            if m.sum() > 6 and X + 1 < W: out[Y, X + 1] = out[Y, X]
    a = np.zeros((H, W, 4), int); a[:HOR, :, :3] = out // 8 * 8; a[..., 3] = 255; a[HOR:, :, :3] = out[-1] // 8 * 8; return a
sky_day = LD(V2 / "calques" / "00_ciel.png")
SKY = {"jour": sky_day, "crepuscule": sky_from(G / "ciel_crepuscule.png", 0.93), "nuit": sky_from(G / "ciel_nuit.png", 0.62)}
# ---------- étalonnage par mode (sur couleurs, quantifié 8) ----------
GRADE = {"jour": (np.array([1, 1, 1.]), np.array([0, 0, 0.])),
         "crepuscule": (np.array([1.0, .74, .68]), np.array([18, 4, 16.])),
         "nuit": (np.array([.42, .5, .78]), np.array([4, 8, 24.]))}
def grade(a, mode):
    mul, add = GRADE[mode]; b = a.copy(); b[..., :3] = np.clip(a[..., :3] * mul + add, 0, 248) // 8 * 8; return b
A = m2["animations"]; mer = [LD(V2 / f) for f in A["02_mer_bpa"]["frames"]]; pal = [LD(V2 / f) for f in A["03_mer_palette"]["frames"]]
# ---------- sorties ----------
def save(a, p):
    p.parent.mkdir(parents=True, exist_ok=True); a = a.copy().astype(np.uint8); a[a[..., 3] == 0, :3] = 0; Image.fromarray(a, "RGBA").save(p, optimize=True)
def clouds_at(b, t):
    off = int(round(CL_SPEED * t / 1000)) % bw; rep = np.concatenate([b] * (W // bw + 2), 1)
    a = np.zeros((H, W, 4), int); a[HOR - CH:HOR] = rep[:, off:off + W]; return a
manifest = {"prefixe_import": PFX, "canvas": [W, H], "grille": 8, "horizon_y": HOR, "modes": {}, "collisions_8px": col.tolist(),
            "guides_generes": sorted(p.name for p in G.glob("*.png") if not p.name.startswith("ref"))}
for mode in ("jour", "crepuscule", "nuit"):
    D = OUT / mode; sky = SKY[mode]; T_ = grade(terr, mode); B_ = grade(band, mode)
    if mode == "crepuscule": B_[..., :3] = np.clip(B_[..., :3] * [1.05, .85, .9] + [20, 0, 10], 0, 248) // 8 * 8
    MER = [grade(a, mode) for a in mer]; PL = [grade(a, mode) for a in pal]
    lay = {"00_ciel": sky, "01_nuages": clouds_at(B_, 0), "02_mer_bpa": MER[0], "03_mer_palette": PL[0], "04_terrain": T_}
    for n_, a in lay.items(): save(a, D / "calques" / f"{n_}.png"); save(a, OUT / "import_png_8px" / f"{PFX}{mode}_{n_}.png")
    save(B_, D / "nuages" / f"{PFX}{mode}_01_nuages_bande_{bw}.png")
    for i, a in enumerate(MER): save(a, D / "mer_bpa" / f"{PFX}{mode}_02_mer_bpa_f{i:02d}.png")
    for i, a in enumerate(PL): save(a, D / "mer_palette" / f"{PFX}{mode}_03_mer_palette_f{i:02d}.png")
    def comp(t):
        fr = int(t * 60 / 1000); img = np.zeros((H, W, 3))
        for a in (sky, clouds_at(B_, t), MER[(fr // 10) % 10], PL[(fr // 5) % len(PL)], T_):
            k = a[..., 3:4] / 255; img = img * (1 - k) + a[..., :3] * k
        return Image.fromarray(img.astype(np.uint8))
    FR = [comp(t) for t in range(0, 5000, 83)]
    (D / "apercu").mkdir(parents=True, exist_ok=True)
    FR[0].save(D / "apercu" / "animation.gif", save_all=True, append_images=FR[1:], duration=83, loop=0); FR[0].save(D / "apercu" / "scene_statique.png")
    manifest["modes"][mode] = {"calques": {n_: f"{mode}/calques/{n_}.png" for n_ in lay},
        "nuages": {"bande": f"{mode}/nuages/{PFX}{mode}_01_nuages_bande_{bw}.png", "y": HOR - CH, "RepeatX": True, "vitesse_px_s": -CL_SPEED, "boucle_s": bw / CL_SPEED},
        "mer_bpa": {"frames": [f"{mode}/mer_bpa/{PFX}{mode}_02_mer_bpa_f{i:02d}.png" for i in range(10)], "FrameLength_60fps": 10, "ms": 166.7},
        "mer_palette": {"frames": [f"{mode}/mer_palette/{PFX}{mode}_03_mer_palette_f{i:02d}.png" for i in range(len(PL))], "FrameLength_60fps": 5, "ms": 83.3}}
ims = [Image.open(OUT / m / "apercu" / "scene_statique.png") for m in ("jour", "crepuscule", "nuit")]
tri = Image.new("RGB", (W * 3 + 16, H), (16, 16, 16))
for i, im in enumerate(ims): tri.paste(im, (i * (W + 8), 0))
(OUT / "apercu").mkdir(exist_ok=True); tri.save(OUT / "apercu" / "jour_crepuscule_nuit.png")
ov = np.array(ims[0]).astype(float); ck = np.kron(col, np.ones((8, 8)))[..., None] > 0
Image.fromarray((ov * np.where(ck, .55, 1) + np.where(ck, [110, 0, 0], 0)).clip(0, 255).astype(np.uint8)).save(OUT / "apercu" / "collisions.png")
manifest["controles"] = {"cases_marchables": int(walk.sum()), "zones_connexes": 1, "nuages_bande_px": bw, "nuages_hauteur": CH,
                         "nuages_ecart_bords_alpha": seam_ok, "terrain_couleurs": int(len(np.unique(rgb.reshape(-1, 3), axis=0)))}
(OUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1))
with zipfile.ZipFile(OUT.parent / "zone_d06p11_v4_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(OUT.parent))
    z.write(__file__, "zone_d06p11_v4/source/build.py")
print(json.dumps(manifest["controles"]))
