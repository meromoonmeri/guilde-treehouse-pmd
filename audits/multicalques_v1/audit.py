"""Audit qualité des livrables multicalques (mesures objectives, pas un jugement artistique)."""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
TARGETS = [
    "renders/froggy_forest_dungeon_entry_multicalque",
    "renders/crooked_cavern_waterfall_v2",
    "renders/generator_multicalque_v2/maison_interieure",
    "renders/generator_multicalque_v3/maison_interieure",
    "renders/generator_multicalque_final/maison_interieure",
    "renders/generator_zones_duo_v1",
    "renders/network_zones_multicalques_v1",
    "renders/network_zones_multicalques_v2",
    "renders/network_zones_multicalques_v3",
    "renders/network_zones_multicalques_v4",
]
BASELINES = [  # références canoniques natives pour étalonner les seuils
    "source/amp_plains_fleurie_v1/references/vast_steppe_composition.png",
    "source/antre_harmonie_v3/references/altere_composition.png",
]

def metrics(p):
    im = Image.open(p).convert("RGBA"); a = np.asarray(im).astype(np.int32)
    h, w = a.shape[:2]; al = a[..., 3]; rgb = a[..., :3]
    vis = al > 0; nvis = int(vis.sum()) or 1
    semi = int(((al > 0) & (al < 255)).sum())
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    magenta = vis & (r > 150) & (b > 150) & (g < 110) & (np.abs(r - b) < 90)
    pinkfringe = vis & (r - g > 70) & (b - g > 70)
    op = rgb[al == 255]
    ncol = len(np.unique(op[:, 0] * 65536 + op[:, 1] * 256 + op[:, 2])) if len(op) else 0
    # proportion de pixels égaux à leur voisin de droite (aplats typiques du pixel art)
    same = (np.all(a[:, 1:] == a[:, :-1], axis=2) & vis[:, 1:]).sum() / max(1, vis[:, 1:].sum())
    # grains d'alpha isolés : pixel visible entouré de 4 transparents (ou l'inverse)
    pad = np.pad(vis, 1)
    nb = pad[:-2, 1:-1].astype(int) + pad[2:, 1:-1] + pad[1:-1, :-2] + pad[1:-1, 2:]
    specks = int((vis & (nb == 0)).sum() + (~vis & (nb == 4)).sum())
    return dict(file=str(p.relative_to(ROOT)), size=[w, h], grid8=(w % 8 == 0 and h % 8 == 0),
                visible_pct=round(100 * nvis / (w * h), 1),
                semi_alpha_pct=round(100 * semi / nvis, 2),
                magenta_px=int(magenta.sum()), pink_fringe_px=int(pinkfringe.sum()),
                opaque_colors=ncol, flat_neighbour_pct=round(100 * float(same), 1),
                alpha_specks=specks)

def overlap(files):
    """Pixels opaques recouverts par plusieurs calques d'une même zone."""
    ims = [np.asarray(Image.open(f).convert("RGBA"))[..., 3] > 200 for f in files]
    if len({i.shape for i in ims}) != 1: return None
    cnt = np.sum(ims, axis=0)
    return round(100 * float((cnt > 1).sum()) / cnt.size, 1)

out = {"baselines": [metrics(ROOT / b) for b in BASELINES], "targets": []}
for t in TARGETS:
    d = ROOT / t
    groups = {}
    for p in sorted(d.rglob("*.png")):
        if "animation" in p.parts and not p.name.startswith("00"): continue
        groups.setdefault(p.parent, []).append(p)
    for parent, files in groups.items():
        layers = [f for f in files if f.name[:2].isdigit() and "phase" not in f.name]
        out["targets"].append(dict(zone=str(parent.relative_to(ROOT)),
                                   layers=[metrics(f) for f in files],
                                   layer_overlap_pct=overlap(layers) if len(layers) > 1 else None))
(Path(__file__).parent / "mesures.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
print("BASELINES"); [print(" ", m) for m in out["baselines"]]
