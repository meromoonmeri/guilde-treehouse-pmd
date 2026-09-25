"""Zone D06P11 V3 — falaise/montagne/grotte régénérées au générateur (composition), ramenées sur la palette ROM
de d06p11a (roche réchauffée V2 + sable ROM). Fond (ciel, nuages wrap, mer BPA, palette) repris de la V2."""
import json, shutil, pathlib, zipfile, numpy as np
from PIL import Image
from scipy import ndimage as nd
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parents[1]
V2 = ROOT / "renders" / "zone_d06p11_v2"; OUT = ROOT / "renders" / "zone_d06p11_v3"; PFX = "D06P11_V3_"
m2 = json.load(open(V2 / "manifest.json")); W, H = m2["canvas"]
g = np.array(Image.open(HERE / "generation" / "falaise_guide.png").convert("RGB").resize((W, H), Image.BOX)).astype(int)
mag = (g[..., 0] > 170) & (g[..., 1] < 110) & (g[..., 2] > 170)
mag = nd.binary_opening(nd.binary_closing(mag, np.ones((3, 3))), np.ones((2, 2)))
t2 = np.array(Image.open(V2 / "calques" / "04_terrain.png").convert("RGBA")).astype(int)
PAL = np.unique(t2[t2[..., 3] > 0][:, :3], axis=0)
d = ((g[..., None, :] - PAL[None, None]) ** 2).sum(-1); rgb = PAL[d.argmin(-1)]
terr = np.zeros((H, W, 4), np.uint8); terr[..., :3] = rgb; terr[..., 3] = np.where(mag, 0, 255)
# sable = couleurs claires peu contrastées (plages ROM) -> collision 8 px
hsv = np.array(Image.fromarray(rgb.astype(np.uint8)).convert("HSV")).astype(int)
sand = (~mag) & (rgb.sum(-1) > 520) & (hsv[..., 1] < 110)
sand = nd.binary_opening(sand, np.ones((3, 3)))
cells = sand.reshape(H // 8, 8, W // 8, 8).mean((1, 3)) > .6
lab, n = nd.label(cells); sz = np.bincount(lab.ravel()); sz[0] = 0; walk = lab == sz.argmax()
col = (~walk).astype(int)
shutil.rmtree(OUT, ignore_errors=True); shutil.copytree(V2, OUT)
for p in list(OUT.rglob("*D06P11_V2_*")): p.rename(p.with_name(p.name.replace("D06P11_V2_", PFX)))
Image.fromarray(terr, "RGBA").save(OUT / "calques" / "04_terrain.png"); Image.fromarray(terr, "RGBA").save(OUT / "import_png_8px" / f"{PFX}04_terrain.png")
m = json.loads(json.dumps(m2).replace("D06P11_V2_", PFX)); m["prefixe_import"] = PFX
m["terrain"] = {"guide_genere": "source/zone_d06p11_v3/generation/falaise_guide.png", "palette_rom_couleurs": len(PAL), "alpha": "binaire"}
m["collisions_8px"] = col.tolist(); m["controles"].update({"cases_marchables": int(walk.sum()), "zones_marchables_connexes": 1, "pixels_inventes": "terrain généré (composition), couleurs ROM"})
(OUT / "manifest.json").write_text(json.dumps(m, ensure_ascii=False, indent=1))
L = {n: np.array(Image.open(OUT / "calques" / f"{n}.png").convert("RGBA")).astype(float) for n in m["ordre_calques"]}
band = np.array(Image.open(OUT / m["nuages"]["bande"]).convert("RGBA")).astype(float)
A = m["animations"]; mer = [np.array(Image.open(OUT / f).convert("RGBA")).astype(float) for f in A["02_mer_bpa"]["frames"]]
pal = [np.array(Image.open(OUT / f).convert("RGBA")).astype(float) for f in A["03_mer_palette"]["frames"]]
def comp(t):
    fr = int(t * 60 / 1000); off = int(round(4 * t / 1000)) % band.shape[1]; cl = np.zeros_like(L["00_ciel"]); cl[:band.shape[0]] = np.roll(band, -off, 1)[:, :W]
    img = np.zeros((H, W, 3))
    for a in (L["00_ciel"], cl, mer[(fr // 10) % 10], pal[(fr // 5) % len(pal)], terr.astype(float)):
        k = a[..., 3:4] / 255; img = img * (1 - k) + a[..., :3] * k
    return Image.fromarray(img.astype(np.uint8))
FR = [comp(t) for t in range(0, 6000, 83)]
FR[0].save(OUT / "apercu" / "animation.gif", save_all=True, append_images=FR[1:], duration=83, loop=0); FR[0].save(OUT / "apercu" / "scene_statique.png")
ov = np.array(FR[0]).astype(float); ck = np.kron(col, np.ones((8, 8)))[..., None] > 0
Image.fromarray((ov * np.where(ck, .55, 1) + np.where(ck, [110, 0, 0], 0)).clip(0, 255).astype(np.uint8)).save(OUT / "apercu" / "collisions.png")
with zipfile.ZipFile(OUT.parent / "zone_d06p11_v3_pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.rglob("*")):
        if p.is_file(): z.write(p, p.relative_to(OUT.parent))
    z.write(__file__, "zone_d06p11_v3/source/build.py")
print(json.dumps(m["controles"], ensure_ascii=False))
