"""Zone D06P11 V5 — astres visibles dans le viewport PMDO (320x240) aux bords, halo animé, étoiles scintillantes.
Dérivé de V4 (terrain, mer, nuages). Corrige aussi le liseré opaque au bord du terrain V4."""
import json, shutil, pathlib, zipfile, numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parents[1]
V4 = ROOT / "renders" / "zone_d06p11_v4"; G4 = ROOT / "source" / "zone_d06p11_v4" / "generation"
OUT = ROOT / "renders" / "zone_d06p11_v5"; PFX = "D06P11_V5_"
m4 = json.load(open(V4 / "manifest.json")); W, H = m4["canvas"]; HOR = m4["horizon_y"]; VW, VH = 320, 240
LD = lambda p: np.array(Image.open(p).convert("RGBA")).astype(int)
def is_mag(a): return (a[..., 0] > 170) & (a[..., 1] < 110) & (a[..., 2] > 170)
# --- alpha terrain recalculé (morphologie avec bord répliqué -> plus de liseré) ---
g = np.array(Image.open(G4 / "falaise_majestueuse.png").convert("RGB").resize((W, H), Image.BOX)).astype(int)
mg = np.pad(is_mag(g), 4, mode="edge"); mg = nd.binary_opening(nd.binary_closing(mg, np.ones((3, 3))), np.ones((2, 2)))[4:-4, 4:-4]
ALPHA = np.where(mg, 0, 255)
NF, FL = 8, 8   # 8 frames x 8 f (133 ms) pour halo et scintillement
def q8(a): return (np.clip(a, 0, 248) // 8 * 8).astype(int)
def sprite(path, size, pick="largest"):
    im = np.array(Image.open(path).convert("RGB")).astype(int); lum = im.sum(-1)
    br = lum > np.percentile(lum, 99.3); lb, n = nd.label(br); s = nd.find_objects(lb)
    i = int(np.argmax([(lb[x] == k + 1).sum() for k, x in enumerate(s)])); sl = s[i]
    y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop; r = max(y1 - y0, x1 - x0); cy, cx = (y0 + y1) // 2, (x0 + x1) // 2
    crop = im[max(0, cy - r // 2):cy + r // 2 + 1, max(0, cx - r // 2):cx + r // 2 + 1]
    rgb = np.array(Image.fromarray(crop.astype(np.uint8)).resize((size, size), Image.BOX)).astype(int)
    yy, xx = np.mgrid[:size, :size]; m = (yy - size / 2 + .5) ** 2 + (xx - size / 2 + .5) ** 2 <= (size / 2) ** 2
    return q8(rgb), m
def disc_sprite(size, core, rim):
    yy, xx = np.mgrid[:size, :size]; d = np.hypot(yy - size / 2 + .5, xx - size / 2 + .5) / (size / 2)
    rgb = np.where((d < .7)[..., None], core, rim); return q8(rgb + 0), d <= 1
ASTRE = {  # mode -> (sprite rgb, masque, centre, couleur halo)
    "nuit": (*sprite(G4 / "ciel_nuit.png", 22), (338, 40), np.array([200, 208, 232])),
    "crepuscule": (*sprite(G4 / "ciel_crepuscule.png", 26), (44, 44), np.array([248, 176, 88])),
    "jour": (*disc_sprite(24, np.array([248, 248, 224]), np.array([248, 232, 160])), (44, 34), np.array([248, 248, 216])),
}
def visible(cx, cy, r):   # visible depuis au moins une position caméra bornée à la carte ?
    ok = False
    for camx in (0, W - VW):
        if camx <= cx - r and cx + r < camx + VW and cy + r < VH: ok = True
    return ok
def star_list(sky):
    base = np.median(sky[:HOR, :, :3], axis=1)
    diff = np.abs(sky[:HOR, :, :3] - base[:, None]).sum(-1) > 40
    ys, xs = np.nonzero(diff); return base, list(zip(ys, xs, [sky[y, x, :3] for y, x in zip(ys, xs)]))
if OUT.exists(): shutil.rmtree(OUT)
man = {"prefixe_import": PFX, "canvas": [W, H], "viewport_pmdo": [VW, VH], "horizon_y": HOR, "collisions_8px": m4["collisions_8px"], "modes": {}}
def save(a, p):
    p.parent.mkdir(parents=True, exist_ok=True); a = a.copy().astype(np.uint8); a[a[..., 3] == 0, :3] = 0; Image.fromarray(a, "RGBA").save(p, optimize=True)
checks = {}
for mode, d4 in m4["modes"].items():
    D = OUT / mode; sky4 = LD(V4 / d4["calques"]["00_ciel"])
    base, stars = star_list(sky4)
    sky = np.zeros((H, W, 4), int); sky[:HOR, :, :3] = q8(base)[:, None]; sky[HOR:, :, :3] = q8(base[-1]); sky[..., 3] = 255
    rgb, msk, (cx, cy), hc = ASTRE[mode]; s = msk.shape[0]; r = s // 2
    # étoiles (hors zone de l'astre) : 1 calque animé, phase par étoile
    ST = [np.zeros((H, W, 4), int) for _ in range(NF)]; rng = np.random.default_rng(7)
    LEV = np.array([1, 1, .75, .45, .15, .45, .75, 1])
    nst = 0
    for (y, x, c) in stars:
        if (y - cy) ** 2 + (x - cx) ** 2 < (r + 8) ** 2: continue
        ph = rng.integers(NF); nst += 1
        for f in range(NF):
            lv = LEV[(f + ph) % NF]; ST[f][y, x, :3] = q8(base[y] + (c - base[y]) * lv); ST[f][y, x, 3] = 255
    # astre + halo pulsé (anneaux tramés, alpha binaire)
    AS = [np.zeros((H, W, 4), int) for _ in range(NF)]
    yy, xx = np.mgrid[:H, :W]; dist = np.hypot(yy - cy, xx - cx); bay = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16
    B = np.tile(bay, (H // 4 + 1, W // 4 + 1))[:H, :W]
    for f in range(NF):
        pulse = .5 + .5 * np.cos(2 * np.pi * f / NF)          # 1 -> 0 -> 1
        reach = r + 3 + 4 * pulse
        t = np.clip(1 - (dist - r) / (reach - r), 0, 1) * (.55 + .35 * pulse)
        ring = (dist >= r) & (dist < reach) & (t > B) & (yy < HOR)
        a = AS[f]; a[ring, :3] = q8(sky[ring, :3] * .45 + hc * .55); a[ring, 3] = 255
        Y0, X0 = cy - r, cx - r; sub = a[Y0:Y0 + s, X0:X0 + s]
        # coeur : scintillement léger (1 pas de palette plus clair sur les frames de pointe)
        core = q8(rgb + (8 if pulse > .8 else 0)); sub[msk, :3] = core[msk]; sub[msk, 3] = 255
        a[yy >= HOR] = 0   # l'astre passe derrière l'horizon (mer)
    vis_px = int(((AS[0][..., 3] > 0) & (ALPHA == 0)).sum()); tot = int((AS[0][..., 3] > 0).sum())
    checks[mode] = {"astre_centre": [cx, cy], "visible_viewport_bord": visible(cx, cy, r + 7), "astre_px_non_masques": f"{vis_px}/{tot}", "etoiles": nst}
    # terrain / mer / nuages V4 (terrain avec alpha corrigé)
    ter = LD(V4 / d4["calques"]["04_terrain"]); ter[..., 3] = ALPHA
    if (ter[..., 3] > 0).any():
        holes = (ALPHA > 0) & (LD(V4 / d4["calques"]["04_terrain"])[..., 3] == 0)
        ter[holes, :3] = LD(V4 / "jour" / "calques" / "04_terrain.png")[holes, :3]  # jamais atteint en pratique
    nu = LD(V4 / d4["nuages"]["bande"]); mer = [LD(V4 / f) for f in d4["mer_bpa"]["frames"]]; pal = [LD(V4 / f) for f in d4["mer_palette"]["frames"]]
    save(sky, D / "calques" / "00_ciel.png"); save(ter, D / "calques" / "05_terrain.png"); save(nu, D / "nuages" / f"{PFX}{mode}_03_nuages_bande_{nu.shape[1]}.png")
    for f in range(NF):
        save(ST[f], D / "etoiles" / f"{PFX}{mode}_01_etoiles_f{f:02d}.png"); save(AS[f], D / "astre" / f"{PFX}{mode}_02_astre_f{f:02d}.png")
    for i, a in enumerate(mer): save(a, D / "mer_bpa" / f"{PFX}{mode}_04_mer_bpa_f{i:02d}.png")
    for i, a in enumerate(pal): save(a, D / "mer_palette" / f"{PFX}{mode}_04b_mer_palette_f{i:02d}.png")
    for n_, a in [("00_ciel", sky), ("01_etoiles", ST[0]), ("02_astre", AS[0]), ("05_terrain", ter)]: save(a, OUT / "import_png_8px" / f"{PFX}{mode}_{n_}.png")
    ny = d4["nuages"]["y"]; bw = nu.shape[1]
    def comp(t, camx=None):
        fr = int(t * 60 / 1000); img = np.zeros((H, W, 3)); off = int(round(4 * t / 1000)) % bw
        cl = np.zeros((H, W, 4)); rep = np.concatenate([nu] * (W // bw + 2), 1); cl[ny:ny + nu.shape[0]] = rep[:, off:off + W]
        for a in (sky, ST[(fr // FL) % NF], AS[(fr // FL) % NF], cl, mer[(fr // 10) % 10], pal[(fr // 5) % len(pal)], ter):
            k = a[..., 3:4] / 255; img = img * (1 - k) + a[..., :3] * k
        return Image.fromarray(img.astype(np.uint8))
    FR = [comp(t) for t in range(0, 4267, 67)]
    (D / "apercu").mkdir(parents=True, exist_ok=True)
    FR[0].save(D / "apercu" / "animation.gif", save_all=True, append_images=FR[1:], duration=67, loop=0); FR[0].save(D / "apercu" / "scene_statique.png")
    camx = 0 if cx < W / 2 else W - VW
    vp = [f.crop((camx, 0, camx + VW, VH)).resize((VW * 2, VH * 2), Image.NEAREST) for f in FR]
    vp[0].save(D / "apercu" / "viewport_pmdo_bord.gif", save_all=True, append_images=vp[1:], duration=67, loop=0); vp[0].save(D / "apercu" / "viewport_pmdo_bord.png")
    man["modes"][mode] = {"ordre_calques": ["00_ciel", "01_etoiles", "02_astre", "03_nuages", "04_mer_bpa", "04b_mer_palette", "05_terrain"],
        "calques": {"00_ciel": f"{mode}/calques/00_ciel.png", "05_terrain": f"{mode}/calques/05_terrain.png"},
        "etoiles": {"frames": [f"{mode}/etoiles/{PFX}{mode}_01_etoiles_f{f:02d}.png" for f in range(NF)], "FrameLength_60fps": FL, "ms": round(FL * 1000 / 60, 1)},
        "astre": {"frames": [f"{mode}/astre/{PFX}{mode}_02_astre_f{f:02d}.png" for f in range(NF)], "FrameLength_60fps": FL, "ms": round(FL * 1000 / 60, 1), "centre": [cx, cy]},
        "nuages": {"bande": f"{mode}/nuages/{PFX}{mode}_03_nuages_bande_{bw}.png", "y": ny, "RepeatX": True, "vitesse_px_s": -4},
        "mer_bpa": {"frames": [f"{mode}/mer_bpa/{PFX}{mode}_04_mer_bpa_f{i:02d}.png" for i in range(10)], "FrameLength_60fps": 10, "ms": 166.7},
        "mer_palette": {"frames": [f"{mode}/mer_palette/{PFX}{mode}_04b_mer_palette_f{i:02d}.png" for i in range(len(pal))], "FrameLength_60fps": 5, "ms": 83.3}}
vps = [Image.open(OUT / m / "apercu" / "viewport_pmdo_bord.png") for m in ("jour", "crepuscule", "nuit")]
tri = Image.new("RGB", (VW * 2 * 3 + 16, VH * 2), (16, 16, 16))
for i, im in enumerate(vps): tri.paste(im, (i * (VW * 2 + 8), 0))
(OUT / "apercu").mkdir(exist_ok=True); tri.save(OUT / "apercu" / "viewport_bords_3_modes.png")
man["controles"] = checks; (OUT / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1, default=int))
with zipfile.ZipFile(OUT.parent / "zone_d06p11_v5_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(OUT.parent))
    z.write(__file__, "zone_d06p11_v5/source/build.py")
print(json.dumps(checks, default=int))
