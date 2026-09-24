"""Composition finale de la Forêt Mystère (méthode calques générés sur magenta).

Entrées : calques générés (bruts/) -> process.py -> pixels/ (1:1, palette canonique).
Sortie  : renders/foret_mystere_magenta_v1/ — 5 calques PNG alignés 440x592 (grille 8 px),
          composite = empilement exact, manifeste des placements.
Usage   : .venv/bin/python source/foret_mystere_magenta_v1/compose.py
"""
from pathlib import Path
import hashlib
import json
import sys

import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
sys.path.insert(0, str(HERE))
from process import to_pixels  # noqa: E402

OUT = R / "renders" / "foret_mystere_magenta_v1"
W, H = 440, 592
CROP = (3, 3)  # recadrage du sol 447x599 -> 440x592
PREFIX = "ForetMystereMagentaV1_"

# Placements (id du sprite dans son calque généré, x, y) en coordonnées finales.
TREES = [  # groupes d'arbres du calque 02
    (5, -44, 72),     # colonne gauche
    (1, 44, -6),      # massif nord-ouest, borde l'entrée
    (6, 334, 128),    # colonne droite
    (2, 326, -8),     # massif nord-est, borde l'entrée
]
ROCKS = [
    (20, 236, 66), (9, 332, 104), (14, 132, 186), (5, 206, 150), (16, 300, 222),
    (17, 176, 318), (21, 252, 296), (19, 86, 470), (15, 318, 492), (22, 118, 552), (8, 240, 560),
    (4, 262, 118),
]
# Rampe de verts EXACTS de la référence (sombre -> clair) pour les herbes hautes générées en sarcelle.
RAMPE_HERBES = [(31, 63, 55), (39, 87, 63), (39, 103, 71), (47, 111, 79), (63, 135, 87), (79, 159, 103)]
GRASS = [
    (13, -10, 508), (11, 322, 502), (16, 104, 244), (12, 352, 262), (15, 62, 372),
    (6, 262, 498), (8, 146, 520), (3, 238, 20), (10, 16, 60),
]


def sprites(rgba):
    a = rgba[..., 3] > 0
    lab, n = nd.label(a, structure=np.ones((3, 3)))
    out = {}
    for i, sl in enumerate(nd.find_objects(lab), 1):
        m = lab[sl] == i
        if m.sum() < 30:
            continue
        s = rgba[sl].copy()
        s[~m] = 0
        out[i] = dict(rgba=s, box=[sl[1].start, sl[0].start, sl[1].stop, sl[0].stop])
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
    """Feuillage (canopée, devant le joueur) / bois (troncs, racines, derrière le joueur)."""
    rgb = spr[..., :3].astype(int)
    vis = spr[..., 3] > 0
    leaf = vis & (rgb[..., 1] >= rgb[..., 0] + 30) & (rgb[..., 1] >= rgb[..., 2])
    lab, n = nd.label(leaf)
    if n:
        sizes = nd.sum(leaf, lab, range(1, n + 1))
        leaf = np.isin(lab, np.flatnonzero(sizes >= 150) + 1)  # lianes fines -> restent au bois
    # reboucher seulement les petits trous du feuillage (reflets, ombres) ; les troncs restent du bois
    holes = vis & ~leaf
    lab, n = nd.label(holes)
    if n:
        sizes = nd.sum(holes, lab, range(1, n + 1))
        leaf |= np.isin(lab, np.flatnonzero(sizes < 40) + 1)
    canopy, wood = spr.copy(), spr.copy()
    canopy[~leaf] = 0
    wood[leaf] = 0
    return canopy, wood


def merge_rare(layer, min_count=4):
    """Fusionne les couleurs d'un calque vues sur < min_count px vers la couleur fréquente la
    plus proche du même calque (toutes restent des couleurs exactes de la palette)."""
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


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    B = HERE / "bruts"
    sol, st_sol = to_pixels(B / "01_sol.png", keyed=False)
    arb, st_arb = to_pixels(B / "02_arbres_magenta.png")
    roc, st_roc = to_pixels(B / "03_rochers_magenta.png")
    her, st_her = to_pixels(B / "04_herbes_hautes_magenta.png", ramp=RAMPE_HERBES)
    cx, cy = CROP
    sol = sol[cy:cy + H, cx:cx + W].copy()
    assert sol.shape[:2] == (H, W) and (sol[..., 3] == 255).all()

    L = {k: np.zeros((H, W, 4), np.uint8) for k in
         ("02_herbes_hautes", "03_rochers", "04_troncs_racines", "05_canopees_devant_joueur")}
    placements = []
    S_arb, S_roc, S_her = sprites(arb), sprites(roc), sprites(her)
    for sid, x, y in GRASS:
        paste(L["02_herbes_hautes"], S_her[sid]["rgba"], x, y)
        placements.append(dict(calque="02_herbes_hautes", sprite=sid, source="04_herbes_hautes_magenta.png",
                               boite_source_1x=S_her[sid]["box"], position=[x, y]))
    for sid, x, y in sorted(ROCKS, key=lambda r: r[2] + S_roc[r[0]]["rgba"].shape[0]):
        paste(L["03_rochers"], S_roc[sid]["rgba"], x, y)
        placements.append(dict(calque="03_rochers", sprite=sid, source="03_rochers_magenta.png",
                               boite_source_1x=S_roc[sid]["box"], position=[x, y]))
    for sid, x, y in TREES:
        canopy, wood = split_tree(S_arb[sid]["rgba"])
        paste(L["04_troncs_racines"], wood, x, y)
        paste(L["05_canopees_devant_joueur"], canopy, x, y)
        placements.append(dict(calque="04+05", sprite=sid, source="02_arbres_magenta.png",
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
    man = dict(
        titre="Forêt Mystère — entrée de donjon sud → nord (calques générés sur magenta)",
        taille=[W, H], grille_px=8, import_pmdo="PNG to Tileset, tuiles de 8 px",
        reference=dict(fichier="Mystifying_Forest_entrance_TDS.png",
                       sha256=hashlib.sha256((HERE / "refs" / "reference_mystifying_forest.png").read_bytes()).hexdigest()),
        methode=[
            "4 générations indépendantes depuis la référence : sol plein cadre, arbres, rochers, herbes hautes sur magenta.",
            "Clé magenta explicite (teinte + frange), alpha binaire.",
            "Faux pixels 2 px du générateur -> grille 1:1 par vote majoritaire (phase détectée), sans LANCZOS/BILINEAR.",
            "Herbes hautes : modelé du brut conservé par rampe de luminance sur 6 verts exacts de la référence.",
            "Toutes les couleurs ramenées à la palette exacte de la référence (118 couleurs, plus proche voisin Lab).",
            "Couleurs vues sur < 4 px d'un calque de sprites fusionnées vers la couleur fréquente la plus proche du calque.",
            "Composition manuelle des sprites ; arbres séparés en canopée (devant) et bois (derrière) par couleur.",
        ],
        pixels="Dessin GÉNÉRÉ dans la palette canonique : ce ne sont pas des tuiles natives extraites.",
        bruts_sha256={f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(B.glob("0[1-4]_*.png"))},
        calques=files, ordre_empilement=files,
        entree_nord_approx=[304, 20], arrivee_sud_approx=[222, H - 8],
        generations={"sol": st_sol, "arbres": st_arb, "rochers": st_roc, "herbes": st_her},
        placements=placements,
        limites=["Collisions, warps et occlusion à configurer dans PMDO ; non testés.",
                 "Art non encore validé par l'utilisateur."],
    )
    (OUT / "manifest.json").write_text(json.dumps(man, indent=1, ensure_ascii=False))
    write_html(files)
    print("ok", files)


def write_html(files):
    rows = "\n".join(
        f'<label><input type="checkbox" checked data-i="{i}"> {f.split(PREFIX)[1][:-4]}</label>'
        for i, f in enumerate(files))
    imgs = "\n".join(f'<img src="{f}" id="l{i}" style="z-index:{i}">' for i, f in enumerate(files))
    (OUT / "apercu_calques.html").write_text(f"""<!doctype html><meta charset="utf-8">
<title>Forêt Mystère — calques</title>
<style>body{{background:#1b1f1d;color:#ddd;font:14px sans-serif;display:flex;gap:20px;padding:16px}}
#m{{position:relative;width:{W*2}px;height:{H*2}px;flex:none}}
#m img{{position:absolute;left:0;top:0;width:{W*2}px;height:{H*2}px;image-rendering:pixelated}}
#g{{position:absolute;inset:0;z-index:99;display:none;background-size:16px 16px;
background-image:linear-gradient(#fff3 1px,transparent 1px),linear-gradient(90deg,#fff3 1px,transparent 1px)}}
label{{display:block;margin:6px 0}}p{{max-width:340px;color:#aaa}}</style>
<div id="m">{imgs}<div id="g"></div></div>
<div><h3>Calques (ordre d'empilement)</h3>{rows}
<label><input type="checkbox" id="gc"> grille 8 px</label>
<p>Zoom ×2, pixels nets. Arrivée au sud, entrée du donjon au nord. Pixels GÉNÉRÉS depuis la
référence Mystifying Forest, ramenés à sa palette exacte ; composés par l'agent. Voir manifest.json.</p></div>
<script>document.querySelectorAll('[data-i]').forEach(c=>c.onchange=()=>
document.getElementById('l'+c.dataset.i).style.display=c.checked?'':'none');
gc.onchange=()=>g.style.display=gc.checked?'block':'none';</script>
""")


if __name__ == "__main__":
    main()
