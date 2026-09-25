"""Zone D06P11 V9 (falaise régénérée style ROM d06p11a, écume de contour façon PMD Sky, soleil blanc tramé façon Sky)
Zone D06P11 V8 (dérivé V7 : fragment flottant retiré, marches/bouche de grotte marchables, écume animée générée au pied des falaises)
Zone D06P11 V7 — carte agrandie 544x640 : chemin et terrasses plus vastes, mer visible des deux côtés.
Terrain étendu au générateur (falaise_etendue.png), palette ROM. Soleil animé généré (soleil_frames.png, 6 frames).
Fond (ciel, étoiles, lune+halo, nuages, mer ROM) repris de V5 par mode et élargi."""
import json, shutil, pathlib, zipfile, numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parents[1]; G = HERE / "generation"
V6R = ROOT / "renders" / "zone_d06p11_v6"; V2 = ROOT / "renders" / "zone_d06p11_v2"
OUT = ROOT / "renders" / "zone_d06p11_v9"; PFX = "D06P11_V9_"
m5 = json.load(open(V6R / "manifest.json")); W0, H0 = m5["canvas"]; HOR = m5["horizon_y"]
W, H = 544, 640; VW, VH = 320, 240
LD = lambda p: np.array(Image.open(p).convert("RGBA")).astype(int)
def is_mag(a): return (a[..., 0] > 170) & (a[..., 1] < 110) & (a[..., 2] > 170)
def q8(a): return (np.clip(a, 0, 248) // 8 * 8).astype(int)
def snap(a, pal):
    d = ((a[..., None, :].astype(np.int32) - pal[None, None].astype(np.int32)) ** 2).sum(-1); return pal[d.argmin(-1)]
# ---------- terrain ----------
g = np.array(Image.open(G / "falaise_style_d06p11a.png").convert("RGB").resize((W, H), Image.BOX)).astype(int)
mg = np.pad(is_mag(g), 4, mode="edge"); mg = nd.binary_opening(nd.binary_closing(mg, np.ones((3, 3))), np.ones((2, 2)))[4:-4, 4:-4]
t2 = LD(V2 / "calques" / "04_terrain.png"); PAL = np.unique(t2[t2[..., 3] > 0][:, :3], axis=0)
rgb = snap(g, PAL); terr = np.zeros((H, W, 4), int); terr[..., :3] = rgb; terr[..., 3] = np.where(mg, 0, 255)
hsv = np.array(Image.fromarray(rgb.astype(np.uint8)).convert("HSV")).astype(int)
sand = nd.binary_opening((~mg) & (rgb.sum(-1) > 430) & (hsv[..., 1] < 135), np.ones((3, 3)))
cells = sand.reshape(H // 8, 8, W // 8, 8).mean((1, 3)) > .55
solid = (~mg).reshape(H // 8, 8, W // 8, 8).all((1, 3))
lab, n = nd.label(cells); sz = np.bincount(lab.ravel()); sz[0] = 0
walk = np.isin(lab, np.nonzero(sz >= 20)[0])
# relie terrasses / marches : fermeture 5x5 limitée au terrain plein
walk = (walk | (nd.binary_closing(walk, np.ones((5, 5))) & solid))
# V8 : marches + bouche de grotte (coordonnées du guide 960x1120 : x410-560, y420-515) -> marchables (warp à poser en jeu)
FX, FY = W / 960, H / 1120
walk[int(420 * FY) // 8:int(515 * FY) // 8 + 1, int(410 * FX) // 8:int(560 * FX) // 8 + 1] = True
lab, n = nd.label(walk); sz = np.bincount(lab.ravel()); sz[0] = 0; walk = lab == sz.argmax(); col = (~walk).astype(int)
# V9 : layout identique à V8, la roche claire régénérée fausse la détection du sable -> grille de collision V8 reprise telle quelle
col = np.array(json.load(open(ROOT / "renders" / "zone_d06p11_v8" / "manifest.json"))["collisions_8px"]); walk = col == 0
GRADE = {"jour": ([1, 1, 1.], [0, 0, 0.]), "crepuscule": ([1.0, .74, .68], [18, 4, 16.]), "nuit": ([.42, .5, .78], [4, 8, 24.])}
def grade(a, mode):
    mul, add = map(np.array, GRADE[mode]); b = a.copy(); b[..., :3] = q8(a[..., :3] * mul + add); return b
# ---------- soleil blanc façon PMD Sky : disque blanc + halo tramé en damier (réf generation/ref_soleil_blanc_sky_x4.png) ----------
SUN_S = 44; SUN = []
yy, xx = np.mgrid[:SUN_S, :SUN_S] - (SUN_S - 1) / 2; rr = np.hypot(yy, xx); chk = ((yy + xx + SUN_S) % 2 == 0)
for k in range(6):
    p = .5 + .5 * np.sin(2 * np.pi * k / 6); core = 8.5; h1 = 12 + 2 * p; h2 = 16 + 3 * p; h3 = 19.5 + 2 * p
    r_ = np.zeros((SUN_S, SUN_S, 3), int); m_ = np.zeros((SUN_S, SUN_S), bool)
    for lim, colr, dith in ((h3, (200, 240, 248), True), (h2, (224, 248, 248), False), (h1, (248, 248, 248), True), (core + 1, (248, 248, 248), False)):
        z = (rr <= lim) & (chk if dith else True); r_[z] = colr; m_ |= z
    SUN.append((r_, m_))
NSUN, FLS = len(SUN), 8
# ---------- lune animée générée (9 frames en grille 3x3) ----------
MOON_S = 44
lg = np.array(Image.open(G / "lune_frames.png").convert("RGB")).astype(int)
lmg = ~is_mag(lg); lmg = nd.binary_closing(lmg, np.ones((5, 5)))
llb, _ = nd.label(lmg)
lobjs = [s for s in nd.find_objects(llb) if (llb[s] == lmg[s]).sum() > 2000 and (lmg[s]).sum() > 2000]
lobjs = [s for i, s in enumerate(nd.find_objects(llb)) if (llb[s] == i + 1).sum() > 2000]
lobjs.sort(key=lambda s: (s[0].start // 340, s[1].start))
MOON = []
for s in lobjs:
    m = lmg[s]; h, w = m.shape
    crop = lg[s].copy(); crop[~m] = 0
    f = MOON_S / max(h, w)
    r_ = np.array(Image.fromarray(crop.astype(np.uint8)).resize((max(1, int(w * f)), max(1, int(h * f))), Image.BOX)).astype(int)
    m_ = np.array(Image.fromarray((m * 255).astype(np.uint8)).resize((r_.shape[1], r_.shape[0]), Image.BOX)) > 120
    o = np.zeros((MOON_S, MOON_S, 4), int)
    y0, x0 = (MOON_S - r_.shape[0]) // 2, (MOON_S - r_.shape[1]) // 2
    o[y0:y0 + r_.shape[0], x0:x0 + r_.shape[1], :3] = q8(r_); o[y0:y0 + r_.shape[0], x0:x0 + r_.shape[1], 3] = m_ * 255
    MOON.append(o)
NMOON, FLAL = len(MOON), 8
FOAM=[None]*16
NFOAM, FLF = 16, 6
# ---------- placement des astres : trouée de ciel la plus large, visible depuis une caméra au bord ----------
free = (terr[..., 3] == 0)
def place(side_left, rad):
    best = None
    xs = range(rad + 4, VW - rad - 4) if side_left else range(W - VW + rad + 4, W - rad - 4)
    for cx in xs[::4]:
        for cy in range(rad + 6, HOR - rad - 20, 4):
            if free[cy - rad - 2:cy + rad + 3, cx - rad - 2:cx + rad + 3].all():
                sc = -abs(cy - 40) - (abs(cx - (60 if side_left else W - 60)) * .3)
                if best is None or sc > best[0]: best = (sc, cx, cy)
    return best[1:] if best else None
def foam_frames():
    """Écume de contour façon PMD Sky (arène plage) : lavis clair collé à la roche + ligne blanche qui respire,
    puis un anneau tramé qui s'éloigne et s'efface. Boucle exacte sur 16 phases."""
    sea = (terr[..., 3] == 0); sea[:HOR + 2] = False
    rock = terr[..., 3] > 0; d = nd.distance_transform_edt(~rock)
    Y, X = np.mgrid[:H, :W]; ph = 2 * np.pi * (Y / 46.0 + np.sin(X / 13.0) * .15)
    wob = np.sin(X / 5.0 + Y / 7.0) * .8; chk = (X + Y) % 2 == 0; out = []
    for k in range(16):
        t = 2 * np.pi * k / 16; r = 3.2 + 2.2 * (.5 + .5 * np.sin(t + ph)) + wob
        o = np.zeros((H, W, 4), int)
        wash = sea & (d < r + 4); o[wash] = [120, 208, 248, 150]
        lite = sea & (d < r); o[lite] = [184, 232, 248, 230]
        line = sea & (np.abs(d - r) < 1.1); o[line] = [248, 248, 248, 255]
        fr = ((k / 16) + (Y / 46.0) % 1) % 1; ring = 5 + 12 * fr
        rg = sea & (np.abs(d - ring - wob) < .8) & chk & (fr < .75); o[rg] = [232, 248, 248, 255]
        o[:HOR + 2] = 0; out.append(o)
    return out
FOAMF = foam_frames(); FSITES = []

SUNPOS = place(True, SUN_S // 2); MOONPOS = place(False, MOON_S // 2 - 1)
if OUT.exists(): shutil.rmtree(OUT)
def save(a, p):
    p.parent.mkdir(parents=True, exist_ok=True); a = a.copy().astype(np.uint8); a[a[..., 3] == 0, :3] = 0; Image.fromarray(a, "RGBA").save(p, optimize=True)
def widen_sea(a):   # mer V5 (384x448, période horizontale 96 px) -> 544x640
    per = a[:, :96]; o = np.concatenate([per] * (W // 96 + 1), 1)[:, :W]
    out = np.zeros((H, W, 4), int); out[:H0] = o
    blk = o[H0 - 96:H0]
    for y in range(H0, H, 96): out[y:min(H, y + 96)] = blk[:min(96, H - y)]
    return out
man = {"prefixe_import": PFX, "canvas": [W, H], "viewport_pmdo": [VW, VH], "horizon_y": HOR, "collisions_8px": col.tolist(), "modes": {}}
checks = {"cases_marchables": int(walk.sum()), "soleil_frames": NSUN, "lune_frames": NMOON, "ecume_frames": NFOAM, "soleil_centre": SUNPOS, "lune_centre": MOONPOS}
for mode, d5 in m5["modes"].items():
    D = OUT / mode
    sky5 = LD(V6R / d5["calques"]["00_ciel"]); rows = sky5[:, 0]
    sky = np.zeros((H, W, 4), int); sky[:, :] = rows[:H0][:, None] if H <= H0 else np.concatenate([rows, np.repeat(rows[-1:], H - H0, 0)])[:, None]; sky[..., 3] = 255
    # étoiles V5 élargies (copie décalée pour la bande droite)
    ST = []
    for f in d5["etoiles"]["frames"]:
        e = LD(V6R / f); o = np.zeros((H, W, 4), int); o[:H0, :W0] = e; o[:H0, W0:] = e[:, 100:100 + W - W0]; ST.append(o)
    AS = []
    if mode == "nuit":
        cx, cy = MOONPOS; h = MOON_S // 2
        for o_ in MOON:
            o = np.zeros((H, W, 4), int); o[cy - h:cy - h + MOON_S, cx - h:cx - h + MOON_S] = o_; o[HOR:] = 0; AS.append(o)
        FLA = FLAL
    else:
        for (r_, m_) in SUN:
            o = np.zeros((H, W, 4), int); cx, cy = SUNPOS; h = SUN_S // 2
            sub = o[cy - h:cy - h + SUN_S, cx - h:cx - h + SUN_S]; col_ = r_ if mode == "jour" else q8(r_ * [1, .8, .62] + [8, 0, 0])
            sub[m_, :3] = col_[m_]; sub[m_, 3] = 255; o[HOR:] = 0; AS.append(o)
        FLA = FLS
    for i in range(len(ST)): ST[i][:, :, 3] *= (ST[i][..., 3] > 0)
    nu = LD(V6R / d5["nuages"]["bande"]); ny = d5["nuages"]["y"]; bw = nu.shape[1]
    FO = [grade(o, mode) for o in FOAMF]
    mer = [widen_sea(LD(V6R / f)) for f in d5["mer_bpa"]["frames"]]; pal = [widen_sea(LD(V6R / f)) for f in d5["mer_palette"]["frames"]]
    ter = grade(terr, mode)
    save(sky, D / "calques" / "00_ciel.png"); save(ter, D / "calques" / "05_terrain.png"); save(nu, D / "nuages" / f"{PFX}{mode}_03_nuages_bande_{bw}.png")
    for i, a in enumerate(ST): save(a, D / "etoiles" / f"{PFX}{mode}_01_etoiles_f{i:02d}.png")
    for i, a in enumerate(AS): save(a, D / "astre" / f"{PFX}{mode}_02_astre_f{i:02d}.png")
    for i, a in enumerate(mer): save(a, D / "mer_bpa" / f"{PFX}{mode}_04_mer_bpa_f{i:02d}.png")
    for i, a in enumerate(FO): save(a, D / "ecume" / f"{PFX}{mode}_04c_ecume_f{i:02d}.png")
    for i, a in enumerate(pal): save(a, D / "mer_palette" / f"{PFX}{mode}_04b_mer_palette_f{i:02d}.png")
    for n_, a in [("00_ciel", sky), ("01_etoiles", ST[0]), ("02_astre", AS[0]), ("05_terrain", ter)]: save(a, OUT / "import_png_8px" / f"{PFX}{mode}_{n_}.png")
    def comp(t):
        fr = int(t * 60 / 1000); img = np.zeros((H, W, 3)); off = int(round(4 * t / 1000)) % bw
        cl = np.zeros((H, W, 4)); rep = np.concatenate([nu] * (W // bw + 2), 1); cl[ny:ny + nu.shape[0]] = rep[:, off:off + W]
        for a in (sky, ST[(fr // 8) % len(ST)], AS[(fr // FLA) % len(AS)], cl, mer[(fr // 10) % 10], pal[(fr // 5) % len(pal)], FO[(fr // FLF) % NFOAM], ter):
            k = a[..., 3:4] / 255; img = img * (1 - k) + a[..., :3] * k
        return Image.fromarray(img.astype(np.uint8))
    FR = [comp(t) for t in range(0, 3200, 67)]
    (D / "apercu").mkdir(parents=True, exist_ok=True)
    FR[0].save(D / "apercu" / "animation.gif", save_all=True, append_images=FR[1:], duration=67, loop=0); FR[0].save(D / "apercu" / "scene_statique.png")
    ax = (SUNPOS if mode != "nuit" else MOONPOS)[0]; camx = 0 if ax < W / 2 else W - VW
    vp = [f.crop((camx, 0, camx + VW, VH)).resize((VW * 2, VH * 2), Image.NEAREST) for f in FR]
    vp[0].save(D / "apercu" / "viewport_pmdo_bord.gif", save_all=True, append_images=vp[1:], duration=67, loop=0); vp[0].save(D / "apercu" / "viewport_pmdo_bord.png")
    man["modes"][mode] = {"ordre_calques": ["00_ciel", "01_etoiles", "02_astre", "03_nuages", "04_mer_bpa", "04b_mer_palette", "04c_ecume", "05_terrain"],
        "calques": {"00_ciel": f"{mode}/calques/00_ciel.png", "05_terrain": f"{mode}/calques/05_terrain.png"},
        "etoiles": {"frames": [f"{mode}/etoiles/{PFX}{mode}_01_etoiles_f{i:02d}.png" for i in range(len(ST))], "FrameLength_60fps": 8, "ms": 133.3},
        "astre": {"frames": [f"{mode}/astre/{PFX}{mode}_02_astre_f{i:02d}.png" for i in range(len(AS))], "FrameLength_60fps": FLA, "ms": round(FLA * 1000 / 60, 1),
                  "centre": list(SUNPOS if mode != "nuit" else MOONPOS), "frames_source": ("lune_rom_v02p06a_generee" if mode == "nuit" else "soleil_blanc_trame_sky")},
        "nuages": {"bande": f"{mode}/nuages/{PFX}{mode}_03_nuages_bande_{bw}.png", "y": ny, "RepeatX": True, "vitesse_px_s": -4},
        "mer_bpa": {"frames": [f"{mode}/mer_bpa/{PFX}{mode}_04_mer_bpa_f{i:02d}.png" for i in range(10)], "FrameLength_60fps": 10, "ms": 166.7},
        "ecume": {"frames": [f"{mode}/ecume/{PFX}{mode}_04c_ecume_f{i:02d}.png" for i in range(NFOAM)], "FrameLength_60fps": FLF, "ms": 100.0, "source": "procedurale, contour de la roche, style ecume Sky (arenapmdskybeach)", "boucle": "16 phases exactes"},
        "mer_palette": {"frames": [f"{mode}/mer_palette/{PFX}{mode}_04b_mer_palette_f{i:02d}.png" for i in range(len(pal))], "FrameLength_60fps": 5, "ms": 83.3}}
ims = [Image.open(OUT / m / "apercu" / "scene_statique.png") for m in ("jour", "crepuscule", "nuit")]
tri = Image.new("RGB", (W * 3 + 16, H), (16, 16, 16))
for i, im in enumerate(ims): tri.paste(im, (i * (W + 8), 0))
(OUT / "apercu").mkdir(exist_ok=True); tri.save(OUT / "apercu" / "jour_crepuscule_nuit.png")
ov = np.array(ims[0]).astype(float); ck = np.kron(col, np.ones((8, 8)))[..., None] > 0
Image.fromarray((ov * np.where(ck, .55, 1) + np.where(ck, [110, 0, 0], 0)).clip(0, 255).astype(np.uint8)).save(OUT / "apercu" / "collisions.png")
man["controles"] = checks; (OUT / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1, default=int))
with zipfile.ZipFile(OUT.parent / "zone_d06p11_v9_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(OUT.parent))
    z.write(__file__, "zone_d06p11_v9/source/build.py")
print(json.dumps(checks, default=int))
