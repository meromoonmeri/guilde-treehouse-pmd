"""Composition : entrée de Crooked Cavern (grès moussu) dans la forêt d'Apple Woods, arrivée sud -> grotte au nord.

Entrées : pixels/ (produit par convert.py depuis bruts/, palettes canoniques des deux références).
Sortie  : renders/crooked_applewoods_v1/ — 6 calques alignés 464x432 (grille 8 px), composite exact,
          manifeste, aperçu HTML.
Usage   : .venv/bin/python source/crooked_applewoods_v1/compose.py
"""
from pathlib import Path
import hashlib
import json

import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
PX = HERE / "pixels"
OUT = R / "renders" / "crooked_applewoods_v1"
W, H = 464, 432
PREFIX = "CrookedAppleV1_"
SOL_CROP = (0, 0)          # coin haut-gauche du recadrage du sol 595x439
FALAISE_POS = (-10, 0)     # bouche de la grotte au-dessus de la clairière

# (id du sprite dans sa feuille, x, y) en coordonnées de la carte
ARBRES = [
    (5, 92, 146),     # buisson rond dans l'arche, à gauche
    (1, -52, 222),    # pommier ouest
    (3, 382, 226),    # pommier est
    (2, 28, 318),     # pommier sud-ouest
    (6, 388, 342),    # buisson sud-est
]
ROCHERS = [
    (1, 204, 112), (3, 334, 150), (5, 180, 262), (13, 364, 252),
    (10, 250, 190), (14, 300, 212), (18, 226, 178), (17, 282, 330), (20, 250, 404), (21, 330, 372),
]
VEGETATION = [
    (2, 8, 232), (3, 186, 350), (9, 362, 300), (16, 168, 396),
    (4, 226, 252), (6, 338, 262), (12, 214, 330), (13, 352, 350), (14, 204, 410), (19, 172, 206), (5, 360, 410),
    (22, 150, 300),
]


def sprites(rgba):
    """Sprites = composantes regroupées par proximité (pétales détachés rattachés à leur fleur)."""
    a = rgba[..., 3] > 0
    lab, _ = nd.label(nd.binary_dilation(a, iterations=1), structure=np.ones((3, 3)))
    lab = lab * a
    out = {}
    raw, _ = nd.label(a, structure=np.ones((3, 3)))
    # numérotation = plus petit id de composante brute contenu (stable avec l'inventaire)
    for g in np.unique(lab[lab > 0]):
        m = lab == g
        ys, xs = np.nonzero(m)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        s = rgba[y0:y1, x0:x1].copy()
        s[~m[y0:y1, x0:x1]] = 0
        sid = int(raw[m].min())
        out[sid] = dict(rgba=s, box=[int(x0), int(y0), int(x1), int(y1)])
    return out


def paste(layer, spr, x, y):
    h, w = spr.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    sub = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    m = sub[..., 3] > 0
    layer[y0:y1, x0:x1][m] = sub[m]


def split_tree(spr):
    """Feuillage (devant le joueur) / tronc et racines (derrière)."""
    rgb = spr[..., :3].astype(int)
    vis = spr[..., 3] > 0
    leaf = vis & (rgb[..., 1] >= rgb[..., 0] + 30) & (rgb[..., 1] >= rgb[..., 2])
    lab, n = nd.label(leaf)
    if n:
        sizes = nd.sum(leaf, lab, range(1, n + 1))
        leaf = np.isin(lab, np.flatnonzero(sizes >= 150) + 1)
    # bois = zones non vertes qui descendent dans le bas du sprite (tronc, racines) ;
    # pommes, branches et ombres enfermées dans la couronne -> canopée
    other = vis & ~leaf
    lab, n = nd.label(other, structure=np.ones((3, 3)))
    h = spr.shape[0]
    for i, sl in enumerate(nd.find_objects(lab), 1):
        if sl[0].stop <= 0.72 * h:
            leaf |= lab == i
    canopy, wood = spr.copy(), spr.copy()
    canopy[~leaf] = 0
    wood[leaf] = 0
    return canopy, wood


def merge_rare(layer, min_count=4):
    vis = layer[..., 3] > 0
    px = layer[vis][:, :3].astype(int)
    if not len(px):
        return layer
    u, inv, c = np.unique(px, axis=0, return_inverse=True, return_counts=True)
    keep = u[c >= min_count]
    for i in np.flatnonzero(c < min_count):
        u[i] = keep[((keep - u[i]) ** 2).sum(1).argmin()]
    out = layer.copy()
    out[vis, :3] = u[inv.ravel()].astype(np.uint8)
    return out


def load(name):
    return np.array(Image.open(PX / name).convert("RGBA"))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    sol = load("01_sol.png")
    cx, cy = SOL_CROP
    sol = sol[cy:cy + H, cx:cx + W].copy()
    assert sol.shape[:2] == (H, W) and (sol[..., 3] == 255).all()

    L = {k: np.zeros((H, W, 4), np.uint8) for k in
         ("02_falaise_grotte", "03_vegetation_basse", "04_rochers", "05_troncs_racines", "06_canopees_devant_joueur")}
    paste(L["02_falaise_grotte"], load("02_falaise.png"), *FALAISE_POS)
    placements = [dict(calque="02_falaise_grotte", source="02_falaise_magenta.png", position=list(FALAISE_POS))]
    S_arb, S_roc, S_veg = sprites(load("03_arbres.png")), sprites(load("04_rochers.png")), sprites(load("05_vegetation.png"))

    def by_bottom(lst, S):
        return sorted(lst, key=lambda t: t[2] + S[t[0]]["rgba"].shape[0])

    for sid, x, y in by_bottom(VEGETATION, S_veg):
        paste(L["03_vegetation_basse"], S_veg[sid]["rgba"], x, y)
        placements.append(dict(calque="03_vegetation_basse", sprite=sid, source="05_vegetation_magenta.png",
                               boite_source_1x=S_veg[sid]["box"], position=[x, y]))
    for sid, x, y in by_bottom(ROCHERS, S_roc):
        paste(L["04_rochers"], S_roc[sid]["rgba"], x, y)
        placements.append(dict(calque="04_rochers", sprite=sid, source="04_rochers_magenta.png",
                               boite_source_1x=S_roc[sid]["box"], position=[x, y]))
    for sid, x, y in by_bottom(ARBRES, S_arb):
        canopy, wood = split_tree(S_arb[sid]["rgba"])
        paste(L["05_troncs_racines"], wood, x, y)
        paste(L["06_canopees_devant_joueur"], canopy, x, y)
        placements.append(dict(calque="05+06", sprite=sid, source="03_arbres_magenta.png",
                               boite_source_1x=S_arb[sid]["box"], position=[x, y]))

    layers = {"01_sol": sol, **{k: merge_rare(v) for k, v in L.items()}}
    comp = Image.new("RGBA", (W, H))
    files = []
    for name in sorted(layers):
        fn = f"{PREFIX}{name}.png"
        Image.fromarray(layers[name]).save(OUT / fn)
        comp.alpha_composite(Image.fromarray(layers[name]))
        files.append(fn)
    comp.save(OUT / "composite.png")
    comp.resize((W * 2, H * 2), Image.NEAREST).save(OUT / "apercu_x2_NE_PAS_IMPORTER.png")
    stats = json.loads((PX / "stats.json").read_text())
    man = dict(
        titre="Entrée de Crooked Cavern dans la forêt d'Apple Woods — arrivée sud, grotte au nord",
        taille=[W, H], grille_px=8, import_pmdo="PNG to Tileset, tuiles de 8 px",
        references={p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE / "refs").glob("*.png"))},
        references_origine={"reference_apple_woods.png": "Apple_Woods_entrance_TDS.png (racine du dépôt)",
                            "reference_crooked_cavern.png": "source/cote_v5_expeditions/audit/Halcyon__crooked_cavern_entrance_composition.png"},
        methode=[
            "5 générations indépendantes depuis les références : sol plein cadre (Apple Woods), falaise + grotte "
            "(Crooked Cavern, mousse et lierre), pommiers/buissons, rochers moussus, petite végétation — objets sur magenta.",
            "Clé magenta explicite (teinte + frange, vert < 100/130 pour épargner les pétales roses), alpha binaire.",
            "Grille des faux pixels estimée par axe (pas 2, 3 ou fractionnaire 2,867 / 5,733) ; chaque cellule prend "
            "la couleur majoritaire : inversion de l'agrandissement du générateur, sans LANCZOS/BILINEAR/NEAREST.",
            "Couleurs ramenées aux palettes exactes : Apple Woods (145) pour sol, arbres, végétation ; Crooked Cavern "
            "(453) + verts Apple Woods pour falaise et rochers moussus. Plus proche voisin Lab.",
            "Couleurs vues sur < 4 px d'un calque de sprites fusionnées vers la couleur fréquente la plus proche.",
            "Composition manuelle par l'agent ; arbres séparés en canopée (devant) et bois (derrière) par couleur.",
        ],
        pixels="Dessin GÉNÉRÉ dans les palettes canoniques : ce ne sont pas des tuiles natives extraites.",
        bruts_sha256={f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted((HERE / "bruts").glob("*.png"))},
        conversion=stats,
        calques=files, ordre_empilement=files,
        entree_grotte_approx=[297, 118], arrivee_sud_approx=[297, H - 8],
        placements=placements,
        limites=["Collisions, warps et occlusion à configurer dans PMDO ; non testés.",
                 "Art non encore validé par l'utilisateur."],
    )
    (OUT / "manifest.json").write_text(json.dumps(man, indent=1, ensure_ascii=False))
    write_html(files)
    print("ok", files)


def write_html(files):
    rows = "\n".join(f'<label><input type="checkbox" checked data-i="{i}"> {f.split(PREFIX)[1][:-4]}</label>'
                     for i, f in enumerate(files))
    imgs = "\n".join(f'<img src="{f}" id="l{i}" style="z-index:{i}">' for i, f in enumerate(files))
    (OUT / "apercu_calques.html").write_text(f"""<!doctype html><meta charset="utf-8">
<title>Crooked Cavern × Apple Woods — calques</title>
<style>body{{background:#1b1f1d;color:#ddd;font:14px sans-serif;display:flex;gap:20px;padding:16px}}
#m{{position:relative;width:{W*2}px;height:{H*2}px;flex:none}}
#m img{{position:absolute;left:0;top:0;width:{W*2}px;height:{H*2}px;image-rendering:pixelated}}
#g{{position:absolute;inset:0;z-index:99;display:none;background-size:16px 16px;
background-image:linear-gradient(#fff3 1px,transparent 1px),linear-gradient(90deg,#fff3 1px,transparent 1px)}}
label{{display:block;margin:6px 0}}p{{max-width:340px;color:#aaa}}</style>
<div id="m">{imgs}<div id="g"></div></div>
<div><h3>Calques (ordre d'empilement)</h3>{rows}
<label><input type="checkbox" id="gc"> grille 8 px</label>
<p>Zoom ×2. Arrivée au sud, entrée de Crooked Cavern au nord. Pixels GÉNÉRÉS depuis les références
Crooked Cavern et Apple Woods, ramenés à leurs palettes exactes ; composés par l'agent. Voir manifest.json.</p></div>
<script>document.querySelectorAll('[data-i]').forEach(c=>c.onchange=()=>
document.getElementById('l'+c.dataset.i).style.display=c.checked?'':'none');
gc.onchange=()=>g.style.display=gc.checked?'block':'none';</script>
""")


if __name__ == "__main__":
    main()
