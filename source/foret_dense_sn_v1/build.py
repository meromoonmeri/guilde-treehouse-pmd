"""Construit FDENSE_V1 — entrée de forêt dense, arrivée sud → entrée de donjon au nord.

Usage : .venv/bin/python source/foret_dense_sn_v1/build.py
Écrit renders/foret_dense_sn_v1/ (calques, composite, ORA, provenance, manifest, planche)
et apercu_foret_dense_sn_v1.html à la racine.

Méthode hybride (choix utilisateur) :
  * sol, ombre, chemin, parois = pixels exacts de D24P11A / D24P31A (provenance au pixel) ;
  * fleurs et petits buissons = sprites canoniques exacts des mêmes références ;
  * arbres géants, entrée, rochers = générés sur magenta puis retouchés 1:1 (pixelize.py) dans les
    sous-palettes exactes des références — ce ne sont PAS des pixels natifs.
"""
from __future__ import annotations

import hashlib
import io
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import labels as LB  # noqa: E402
import layout as LY  # noqa: E402
import pixelize as PX  # noqa: E402
import sprites as SP  # noqa: E402
import strips as ST  # noqa: E402
import synth as SY  # noqa: E402
from pmdsynth import check_provenance  # noqa: E402

ROOT = HERE.parents[1]
OUT = ROOT / "renders" / "foret_dense_sn_v1"
PREFIX = "FDENSE_V1_"
H, W = LY.H, LY.W
GEN_BASE = 100  # id de provenance des sprites générés : 100 + k

LAYERS = [
    ("01_sol", "Herbe au soleil — quilting de D24P11A (pixels exacts)"),
    ("02_ombres", "Antichambre sombre — herbe d'ombre de D24P31A, liseré guidé par distance (pixels exacts, opaques)"),
    ("03_chemin", "Chemin de terre — segments rigides de D24P11A, coupes minimales (pixels exacts)"),
    ("04_vegetation_basse", "Fleurs D24P11A + petits buissons D24P31A (sprites canoniques exacts)"),
    ("05_rochers", "Rochers — générés sur magenta puis retouchés 1:1 palette des références"),
    ("06_parois_foret", "Parois d'arbres — bande périodique exacte de D24P31A (192 lignes, raccord canonique)"),
    ("07_troncs_racines", "Troncs, racines et touffes des arbres géants — générés puis retouchés 1:1"),
    ("08_entree", "Entrée du donjon (troncs, tunnel, pierres, fleurs) — générée puis retouchée 1:1"),
    ("09_canopees", "Canopées des arbres géants et de l'entrée (au-dessus du joueur) — générées puis retouchées 1:1"),
]

# placements (coin haut-gauche) des sprites générés et canoniques
TREE_POS = {"arbre_ouest": (36, 356), "arbre_est": (300, 548)}
ENTRANCE_POS = (LY.ENTRANCE_BOX[0], LY.ENTRANCE_BOX[1])
ROCK_POS = {"rocher_0": (324, 342), "rocher_2": (166, 574), "rocher_3": (318, 432)}  # bas-centre
# sprites canoniques retenus (les plus propres) : fleurs D24P11A n° 0, 2, 4 ; buissons D24P31A n° 0, 1
FLOWER_POS = [(196, 300, 0), (340, 262, 4), (180, 500, 4), (338, 560, 2), (206, 612, 2), (362, 396, 0),
              (166, 236, 2), (300, 232, 0), (190, 404, 0), (346, 468, 4), (292, 640, 2), (214, 548, 4)]
BUSH_POS = [(212, 380, 0), (316, 516, 1), (226, 652, 1), (330, 206, 1), (180, 280, 0), (358, 610, 0)]


class Layer:
    def __init__(self, name):
        self.name = name
        self.rgb = np.zeros((H, W, 3), np.int16)
        self.a = np.zeros((H, W), bool)
        self.prov = np.full((H, W, 3), -1, np.int32)

    def paste(self, rgb, alpha, x0, y0, prov=None, sid=None):
        h, w = alpha.shape
        ys, xs = np.nonzero(alpha)
        ty, tx = ys + y0, xs + x0
        ok = (ty >= 0) & (ty < H) & (tx >= 0) & (tx < W)
        ys, xs, ty, tx = ys[ok], xs[ok], ty[ok], tx[ok]
        self.rgb[ty, tx] = rgb[ys, xs]
        self.a[ty, tx] = True
        if prov is not None:
            self.prov[ty, tx] = prov[ys, xs]
        elif sid is not None:
            self.prov[ty, tx, 0] = sid
            self.prov[ty, tx, 1] = ys
            self.prov[ty, tx, 2] = xs

    def rgba(self):
        out = np.zeros((H, W, 4), np.uint8)
        out[..., :3] = np.where(self.a[..., None], self.rgb, 0).astype(np.uint8)
        out[..., 3] = self.a * 255
        return out


def side_component(mask, side):
    cc, _ = ndi.label(mask)
    ids = np.unique(cc[:, 0] if side == "ouest" else cc[:, -1])
    return np.isin(cc, ids[ids > 0])


def path_valid_rows(R, pa, margin=14):
    valid = np.zeros(R.A.shape[0], bool)
    for y in range(R.A.shape[0]):
        xs = np.nonzero(pa[y])[0]
        if len(xs) == 0:
            continue
        lo, hi = max(0, xs.min() - margin), min(R.A.shape[1] - 1, xs.max() + margin)
        valid[y] = np.isin(R.la[y, lo:hi + 1], [LB.HERBE, LB.CHEMIN]).all()
    return valid


def write_ora(path: Path, layers: list[tuple[str, np.ndarray]], composite: np.ndarray):
    def png_bytes(a):
        b = io.BytesIO()
        Image.fromarray(a).save(b, "PNG", optimize=True)
        return b.getvalue()
    stack = ['<?xml version="1.0" encoding="UTF-8"?>',
             f'<image version="0.0.3" w="{W}" h="{H}"><stack>']
    for name, _ in reversed(layers):
        stack.append(f'<layer name="{name}" src="data/{name}.png" x="0" y="0" opacity="1.0" visibility="visible"/>')
    stack.append("</stack></image>")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "image/openraster", compress_type=zipfile.ZIP_STORED)
        z.writestr("stack.xml", "\n".join(stack), compress_type=zipfile.ZIP_DEFLATED)
        for name, a in layers:
            z.writestr(f"data/{name}.png", png_bytes(a), compress_type=zipfile.ZIP_DEFLATED)
        z.writestr("mergedimage.png", png_bytes(composite), compress_type=zipfile.ZIP_DEFLATED)
        th = Image.fromarray(composite)
        th.thumbnail((256, 256), Image.NEAREST)
        b = io.BytesIO(); th.save(b, "PNG")
        z.writestr("Thumbnails/thumbnail.png", b.getvalue(), compress_type=zipfile.ZIP_DEFLATED)


def build(verbose=True):
    log = print if verbose else (lambda *a, **k: None)
    R = SY.Refs()
    lay = LY.build_layout()
    OUT.mkdir(parents=True, exist_ok=True)

    log("1/7 sol (quilting herbe D24P11A)…")
    L, pL = SY.synth_ground(R, seed=1)
    log("2/7 parois périodiques exactes D24P31A…")
    wall_rgb = np.zeros((H, W, 3), np.int16)
    wall_prov = np.full((H, W, 3), -1, np.int32)
    wall_a = np.zeros((H, W), bool)
    for side, (dx, ph) in LY.WALLS.items():
        out, prov = ST.periodic_wall(R.B, side, H, W, dx, ph)
        wm = side_component(R.label_of(prov) == LB.MUR, side)
        wall_rgb[wm] = out[wm]
        wall_prov[wm] = prov[wm]
        wall_a |= wm
    log("3/7 antichambre sombre (herbe d'ombre D24P31A)…")
    dark_t = lay["shade"] > 0.5
    S, pS, _ = SY.synth_shade_shape(R, L, pL, dark_t, wall_a, seed=2)
    log("4/7 chemin par segments D24P11A…")
    pa = LB.path_mask_A(R.la)
    valid = path_valid_rows(R, pa)
    mt = np.array([14 if lay["shade"][min(y, H - 1), int(lay["path_cx"][min(y, H)])] < 0.2 else 3
                   for y in range(H)])
    P, pP, placed = ST.path_strips(R.A, pa, valid, S, pS, lay["path_cx"], lay["path_hr"], 150, mt,
                                   seg_h=32, ov=12, w_shape=120.0, seed=5)
    for name, img, prov in (("sol", L, pL), ("ombre", S, pS), ("chemin", P, pP)):
        bad = check_provenance(img, prov, R.rgb)
        assert bad == 0, f"provenance {name}: {bad} px faux"

    log("5/7 sprites (retouche 1:1 des générés, canoniques exacts)…")
    subpal, _ = PX.ref_subpalettes()
    gen = SP.generated_sprites(subpal)
    flowers = SP.canonical_flowers(R.A, R.la)
    bushes = SP.canonical_bushes(R.B, R.lb)

    log("6/7 calques…")
    Ls = {n: Layer(n) for n, _ in LAYERS}
    Ls["01_sol"].rgb[:] = L; Ls["01_sol"].a[:] = True; Ls["01_sol"].prov[:] = pL
    m = (S != L).any(-1)
    Ls["02_ombres"].paste(S, m, 0, 0, prov=pS)
    m = (P != S).any(-1)
    Ls["03_chemin"].paste(P, m, 0, 0, prov=pP)
    veg = Ls["04_vegetation_basse"]
    for cx, cy, k in FLOWER_POS:
        f = flowers[k]
        h, w = f.shape
        veg.paste(f.rgb, f.alpha, cx - w // 2, cy - h // 2, prov=f.prov)
    for cx, cy, k in BUSH_POS:
        b = bushes[k]
        h, w = b.shape
        veg.paste(b.rgb, b.alpha, cx - w // 2, cy - h // 2, prov=b.prov)
    gen_ids = {}
    for k, name in enumerate(sorted(gen)):
        gen_ids[name] = GEN_BASE + k
    for name, (bx, by) in ROCK_POS.items():
        s = gen[name]
        h, w = s.shape
        Ls["05_rochers"].paste(s.rgb, s.alpha, bx - w // 2, by - h, sid=gen_ids[name])
    Ls["06_parois_foret"].paste(wall_rgb, wall_a, 0, 0, prov=wall_prov)
    for name, (x0, y0) in TREE_POS.items():
        s = gen[name]
        Ls["07_troncs_racines"].paste(s.rgb, s.alpha & ~s.split, x0, y0, sid=gen_ids[name])
        Ls["09_canopees"].paste(s.rgb, s.alpha & s.split, x0, y0, sid=gen_ids[name])
    e = gen["entree"]
    eh = min(e.shape[0], LY.ENTRANCE_BOX[3] - LY.ENTRANCE_BOX[1])
    ea = e.alpha.copy(); ea[eh:] = False
    Ls["08_entree"].paste(e.rgb, ea & ~e.split, *ENTRANCE_POS, sid=gen_ids["entree"])
    Ls["09_canopees"].paste(e.rgb, ea & e.split, *ENTRANCE_POS, sid=gen_ids["entree"])

    log("7/7 exports…")
    comp = np.zeros((H, W, 3), np.int16)
    for n, _ in LAYERS:
        l = Ls[n]
        comp[l.a] = l.rgb[l.a]
    comp_rgba = np.zeros((H, W, 4), np.uint8); comp_rgba[..., :3] = comp; comp_rgba[..., 3] = 255
    files = []
    for n, desc in LAYERS:
        p = OUT / f"{PREFIX}{n}.png"
        Image.fromarray(Ls[n].rgba()).save(p, optimize=True)
        files.append(p)
    Image.fromarray(comp_rgba).save(OUT / f"{PREFIX}composite.png", optimize=True)
    Image.fromarray(comp.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(
        OUT / f"{PREFIX}apercu_x2_revue.png", optimize=True)
    write_ora(OUT / f"{PREFIX}calques.ora", [(f"{PREFIX}{n}", Ls[n].rgba()) for n, _ in LAYERS], comp_rgba)
    np.savez_compressed(OUT / f"{PREFIX}provenance.npz",
                        **{n: Ls[n].prov for n, _ in LAYERS}, **{f"{n}_alpha": Ls[n].a for n, _ in LAYERS})
    # planche des sprites retouchés (revue)
    sheet_items = [gen[k] for k in ("arbre_ouest", "arbre_est", "entree")] + \
                  [gen[k] for k in sorted(gen) if k.startswith("rocher")]
    sw = sum(s.shape[1] + 8 for s in sheet_items) + 8
    sh = max(s.shape[0] for s in sheet_items) + 16
    sheet = np.zeros((sh, sw, 4), np.uint8)
    x = 8
    for s in sheet_items:
        h, w = s.shape
        sheet[8:8 + h, x:x + w, :3][s.alpha] = s.rgb[s.alpha]
        sheet[8:8 + h, x:x + w, 3][s.alpha] = 255
        x += w + 8
    Image.fromarray(sheet).save(OUT / "PLANCHE_SPRITES_RETOUCHES_revue.png", optimize=True)

    # manifest
    def stats(l):
        op = l.rgb[l.a]
        n_col = len(np.unique(op.reshape(-1, 3), axis=0)) if len(op) else 0
        src = l.prov[..., 0][l.a]
        return {"pixels_visibles": int(l.a.sum()), "couleurs": n_col,
                "px_D24P11A": int((src == 0).sum()), "px_D24P31A": int((src == 1).sum()),
                "px_generes_retouches": int((src >= GEN_BASE).sum())}
    ref_union = set(map(tuple, np.concatenate([R.A.reshape(-1, 3), R.B.reshape(-1, 3)]).tolist()))
    comp_cols = set(map(tuple, comp.reshape(-1, 3).tolist()))
    manifest = {
        "nom": "FDENSE_V1 — entrée de forêt dense sud → nord",
        "taille": [W, H], "grille": 8, "prefixe_import": PREFIX,
        "references": {"0": "D24P11A (large.D24P11A.gif…) → source/foret_dense_sn_v1/refs/D24P11A.png",
                       "1": "D24P31A (large.D24P31A.gif…) → source/foret_dense_sn_v1/refs/D24P31A.png"},
        "provenance_ids": {"0": "D24P11A (y, x)", "1": "D24P31A (y, x)",
                           **{str(v): f"généré retouché : {k} (y, x dans le sprite retouché)" for k, v in gen_ids.items()}},
        "calques": [{"fichier": f"{PREFIX}{n}.png", "role": d, **stats(Ls[n])} for n, d in LAYERS],
        "composite": f"{PREFIX}composite.png",
        "couleurs_composite": len(comp_cols),
        "couleurs_hors_palette_references": len(comp_cols - ref_union),
        "parois": {"bandes": {k: {"colonnes_source": list(v[0]), "ligne_depart": v[1], "periode": ST.PERIOD}
                              for k, v in ST.WALL_STRIPS.items()},
                   "decalage_phase": LY.WALLS},
        "chemin_segments": [{"y_cible": int(a), "y_source": int(b), "dx": int(c)} for a, b, c in placed],
        "generes": {k: {"brut": "bruts/" + (SP.GENERATED["rochers"][0] if k.startswith("rocher") else SP.GENERATED[k][0]),
                        "id": gen_ids[k], "taille_retouchee": list(gen[k].shape), "origine": gen[k].origin}
                    for k in gen},
        "placements": {"arbres": TREE_POS, "entree": ENTRANCE_POS, "rochers_bas_centre": ROCK_POS,
                       "fleurs": FLOWER_POS, "buissons": BUSH_POS},
        "non_fait": ["test en jeu PMDO", "collisions / warps / gameplay", "animation"],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False, default=str))
    log("écrit :", OUT)
    return Ls, comp, manifest


def pack():
    """FDENSE_V1_pack.zip : calques, composite, ORA, manifest, README, galerie."""
    import viewer
    html = viewer.write()
    names = [f"{PREFIX}{n}.png" for n, _ in LAYERS] + [f"{PREFIX}composite.png", f"{PREFIX}calques.ora",
                                                       "manifest.json", "README.md"]
    with zipfile.ZipFile(OUT / f"{PREFIX}pack.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for n in names:
            z.write(OUT / n, f"foret_dense_sn_v1/{n}")
        z.write(html, f"foret_dense_sn_v1/{html.name}")
    return OUT / f"{PREFIX}pack.zip"


if __name__ == "__main__":
    build()
    print("pack :", pack())
