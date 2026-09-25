"""V12 : falaise = V10 pixel pour pixel, SAUF la zone du second chemin (rangées 40-51, colonnes 20-47 en cases 8 px)
reprise de la falaise recalculée avec le chemin ouvert. Sol = exactement les cases de sable V10 (+ cases ouvertes)."""
import json, pathlib, numpy as np
from PIL import Image
HERE = pathlib.Path(__file__).resolve().parent; ROOT = HERE.parents[1]; G = HERE / "generation"; T = 8
v10 = np.array(Image.open(ROOT / "source/zone_d06p11_v10/generation/terrain_canonique.png")).astype(int)
new = np.array(Image.open(G / "calque_falaise.png")).astype(int)
meta = json.load(open(G / "falaise_meta.json")); cls = np.array(meta["cls"])
rom = np.array(Image.open(ROOT / "source/zone_d06p11_v1/source_rom/d06p11a_f0.png").convert("RGB")).astype(int)
prov10 = json.load(open(ROOT / "source/zone_d06p11_v10/generation/provenance_tuiles.json"))
# case de sable V10 = tuile posée identique à une tuile de sable ROM (même source que V10)
from scipy import ndimage as nd
RH, RW = rom.shape[0] // T, rom.shape[1] // T
tl = rom[:RH * T, :RW * T].reshape(RH, T, RW, T, 3).transpose(0, 2, 1, 3, 4)
m = tl.mean((2, 3)); sd = tl.std((2, 3)).mean(-1); lum = m.mean(-1); blue = m[..., 2] > m[..., 0] + 20
s0 = (~blue) & (sd < 14) & (lum > 150); lab, _ = nd.label(s0); sz = np.bincount(lab.ravel()); sz[0] = 0; sand = lab == sz.argmax()
CH, CW = v10.shape[0] // T, v10.shape[1] // T
sand10 = np.zeros((CH, CW), bool)
for k, (r, c) in prov10["tuiles"].items():
    j, i = map(int, k.split(",")); sand10[j, i] = sand[r, c]
ROI = (slice(40, 52), slice(20, 48))
roi_px = np.zeros(v10.shape[:2], bool); roi_px[ROI[0].start * T:ROI[0].stop * T, ROI[1].start * T:ROI[1].stop * T] = True
fal = v10.copy(); fal[roi_px] = new[roi_px]
cells = sand10.copy(); cells[ROI] = (cls[ROI] == "sable")
Image.fromarray(fal.astype(np.uint8), "RGBA").save(G / "calque_falaise.png")
meta["cls_sol_v12"] = cells.astype(int).tolist(); meta["roi_second_chemin_cases"] = [40, 52, 20, 48]
# collisions : V10 hors ROI, recalculées dans la ROI
c10 = np.array(prov10["collisions_8px"]); col = c10.copy(); col[ROI] = np.where(cls[ROI] == "sable", 0, c10[ROI] & 1)
col[ROI] = np.where(cells[ROI], 0, 1); meta["collisions_8px"] = col.tolist()
(G / "falaise_meta.json").write_text(json.dumps(meta))
d = (np.abs(fal - v10).sum(-1) > 0); print("pixels falaise modifiés vs V10 :", int(d.sum()), "tous dans ROI :", bool((d & ~roi_px).sum() == 0), "cases sol :", int(cells.sum()))
