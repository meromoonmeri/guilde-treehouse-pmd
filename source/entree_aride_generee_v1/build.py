"""Entree aride generee V1 — methode rendus generes (pas de mosaique native).

Bruts : relief complet sur magenta + sol sableux complet (generateur, guides par
la reference entrancearidedungeonpmdsky.png 408x288).
Normalisation uniforme /3 isotrope, alpha par inondation magenta + seuil serre,
6 calques, ORA, scene, planche de revision, viewer autonome, manifeste.

Dessins GENERES references PMD, pas des pixels natifs certifies.
"""
from pathlib import Path
import base64
import hashlib
import io
import json
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image
from scipy import ndimage

R = Path(__file__).resolve().parents[2]
SRC = Path(__file__).resolve().parent
O = R / "renders/entree_aride_generee_v1"
W, H = 408, 288  # cible = reference, grille 8 px (51 x 36)

LAYERS = [
    ("01_sol", "Sol sableux complet"),
    ("02_falaise", "Falaise ocre"),
    ("03_bouche_grotte", "Bouche de grotte"),
    ("04_arbres_morts", "Arbres morts"),
    ("05_cailloux", "Cailloux isoles"),
    ("06_ombres", "Ombres et speckles"),
]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def detourage_magenta(rgb: np.ndarray):
    """Fond magenta par inondation depuis les bords + seuil serre global.

    Pas de fill_holes : les trous magenta interieurs sont le sol manquant,
    ils doivent rester transparents (lecon V9/V16).
    """
    d = np.linalg.norm(rgb.astype(float) - np.array([255.0, 0.0, 255.0]), axis=2)
    cand = d < 130
    bord = np.zeros_like(cand)
    bord[0, :] = bord[-1, :] = bord[:, 0] = bord[:, -1] = True
    fond = ndimage.binary_propagation(bord & cand, mask=cand)
    fond = fond | (d < 40)
    r, g, b = rgb.transpose(2, 0, 1)
    magish = (r > g * 1.05) & (b > g * 1.05)
    fond = fond | (ndimage.binary_dilation(fond, iterations=1) & magish)
    return ~fond, d  # opaque, distances


def construire():
    (O / "couches").mkdir(parents=True, exist_ok=True)
    (O / "scene").mkdir(parents=True, exist_ok=True)
    (O / "review").mkdir(parents=True, exist_ok=True)

    brut_relief = Image.open(SRC / "generation/brut_relief_magenta.png").convert("RGB")
    brut_sol = Image.open(SRC / "generation/brut_sol.png").convert("RGB")
    # Normalisation uniforme isotrope /3 (1224x864 -> 408x288), jamais anisotrope.
    rel = np.array(brut_relief.resize((W, H), Image.Resampling.LANCZOS)).astype(float)
    sol = brut_sol.resize((W, H), Image.Resampling.LANCZOS).convert("RGBA")

    opaque, dist = detourage_magenta(rel)
    r, g, b = rel.transpose(2, 0, 1)
    lum = rel.mean(axis=2)
    mx = rel.max(axis=2)
    mn = rel.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)

    # --- grotte : plus grande composante sombre, attendue au nord centre ---
    sombre = opaque & (lum < 35)
    lab_s, n_s = ndimage.label(sombre)
    tailles_s = ndimage.sum(sombre, lab_s, range(1, n_s + 1)) if n_s else []
    k_grotte = 1 + int(np.argmax(tailles_s))
    grotte = lab_s == k_grotte
    ys, xs = np.where(grotte)
    grotte_bbox = [int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())]

    # --- arbres vs ombres : gris reconnectes (dilatation 1 px) ---
    gris = opaque & (sat < 0.25) & (lum > 40) & (lum < 170)
    gris_dil = ndimage.binary_dilation(gris, iterations=1)
    lab_g, n_g = ndimage.label(gris_dil)
    arbres = np.zeros_like(opaque)
    ombres = np.zeros_like(opaque)
    for k in range(1, n_g + 1):
        comp = lab_g == k
        if int((gris & comp).sum()) >= 30:
            arbres |= gris & comp
        else:
            ombres |= gris & comp
    ombres |= sombre & ~grotte  # micro-sombres hors grotte (crevasses)

    # --- cailloux : composantes isolees non grises ---
    lab_o, n_o = ndimage.label(opaque)
    bords = set(np.unique(np.concatenate([lab_o[0, :], lab_o[-1, :], lab_o[:, 0], lab_o[:, -1]]))) - {0}
    cailloux = np.zeros_like(opaque)
    n_cailloux = 0
    for k in range(1, n_o + 1):
        if k in bords:
            continue
        comp = lab_o == k
        if (comp & grotte).any():
            continue
        frac_gris = (comp & (gris | ombres)).sum() / comp.sum()
        if frac_gris > 0.5:
            ombres |= comp & ~grotte & ~arbres
        else:
            cailloux |= comp & ~grotte & ~arbres
            n_cailloux += 1

    # Partition stricte par priorite : grotte > arbres > cailloux > ombres.
    ombres &= ~grotte & ~arbres & ~cailloux
    falaise = opaque & ~grotte & ~arbres & ~ombres & ~cailloux

    masks = {"01_sol": None, "02_falaise": falaise, "03_bouche_grotte": grotte,
             "04_arbres_morts": arbres, "05_cailloux": cailloux, "06_ombres": ombres}

    couches = {}
    couches["01_sol"] = sol
    for lid, _label in LAYERS[1:]:
        m = masks[lid]
        rgba = np.dstack([rel.astype("uint8"), np.where(m, 255, 0).astype("uint8")])
        rgba[~m] = 0  # RGB nuls sous alpha 0
        couches[lid] = Image.fromarray(rgba, "RGBA")

    for lid, _label in LAYERS:
        couches[lid].save(O / "couches" / f"EntreeArideV1_{lid}.png")

    # --- scene recomposee ---
    scene = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for lid, _label in LAYERS:
        scene.alpha_composite(couches[lid])
    scene.save(O / "scene" / "scene_complete.png")

    # --- planche de revision : 6 calques sur damier + scene ---
    dam = Image.new("RGB", (W, H), (64, 64, 64))
    px = dam.load()
    for y in range(H):
        for x in range(W):
            if (x // 8 + y // 8) % 2:
                px[x, y] = (96, 96, 96)
    vignettes = []
    for lid, _label in LAYERS:
        v = dam.copy()
        v.paste(couches[lid], (0, 0), couches[lid])
        vignettes.append(v)
    vignettes.append(scene.convert("RGB"))
    planche = Image.new("RGB", (W * 4, H * 2), (32, 32, 32))
    for i, v in enumerate(vignettes[:8]):
        planche.paste(v, ((i % 4) * W, (i // 4) * H))
    planche.save(O / "review" / "planche_calques.png")

    # --- ORA editable ---
    ora_path = O / "EntreeArideV1.ora"
    root = ET.Element("image", {"w": str(W), "h": str(H), "name": ora_path.stem})
    stack = ET.SubElement(root, "stack")
    with zipfile.ZipFile(ora_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "image/openraster", compress_type=zipfile.ZIP_STORED)
        for i, (lid, label) in reversed(list(enumerate(LAYERS))):
            fn = f"data/layer{i}.png"
            ET.SubElement(stack, "layer", {"name": f"{lid} — {label}", "src": fn,
                                           "x": "0", "y": "0", "opacity": "1.0",
                                           "visibility": "visible", "composite-op": "svg:src-over"})
            buf = io.BytesIO()
            couches[lid].save(buf, format="PNG")
            z.writestr(fn, buf.getvalue())
        z.writestr("stack.xml", ET.tostring(root, encoding="utf-8", xml_declaration=True))
        buf = io.BytesIO()
        scene.save(buf, format="PNG")
        z.writestr("mergedimage.png", buf.getvalue())

    # --- corridor sud -> grotte : plus large bande verticale degagee ---
    # Le cadre bas de la bouche (2-3 px sous le vide sombre) est le seuil :
    # le corridor va du sud jusqu'au seuil, puis la bouche est l'entree.
    relief_alpha = opaque
    y_seuil = grotte_bbox[3] + 12
    libres = [x for x in range(W) if not relief_alpha[y_seuil:H, x].any()]
    # plus long segment contigu qui chevauche la bouche
    best, cur = [], []
    for i, x in enumerate(libres):
        if i == 0 or x == libres[i - 1] + 1:
            cur.append(x)
        else:
            if (cur[0] <= grotte_bbox[2] and cur[-1] >= grotte_bbox[0]
                    and len(cur) > len(best)):
                best = cur
            cur = [x]
    if cur and (cur[0] <= grotte_bbox[2] and cur[-1] >= grotte_bbox[0]
                and len(cur) > len(best)):
        best = cur
    assert best, "aucun corridor face a la grotte"
    corridor = {"x0": int(best[0]), "x1": int(best[-1]), "largeur": len(best),
                "y_haut": y_seuil, "y_bas": H,
                "note": "degage jusqu'au seuil ; la bouche (vide sombre) est l'entree"}

    # --- viewer autonome ---
    def uri(im: Image.Image) -> str:
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    donnees = {"largeur": W, "hauteur": H,
               "calques": [{"id": lid, "label": label, "uri": uri(couches[lid])}
                           for lid, label in LAYERS]}
    gabarit = (SRC / "viewer.html").read_text(encoding="utf-8")
    (R / "apercu_entree_aride_v1.html").write_text(
        gabarit.replace("__DATA__", json.dumps(donnees)), encoding="utf-8")

    manifest = {
        "id": "entree_aride_generee_v1",
        "reference": "entrancearidedungeonpmdsky.png (408x288, conservee intacte)",
        "taille": [W, H], "grille_px": 8, "cases": [W // 8, H // 8],
        "methode": "rendu genere reference PMD sur magenta -> detourage -> 6 calques ; "
                   "PAS des pixels natifs, PAS une mosaique de bouts de maps",
        "calques": [{"id": lid, "label": label,
                     "fichier": f"couches/EntreeArideV1_{lid}.png",
                     "pixels": int((np.array(couches[lid])[:, :, 3] > 0).sum())}
                    for lid, label in LAYERS],
        "grotte_bbox": grotte_bbox, "cailloux_isoles": n_cailloux,
        "corridor_sud_nord": corridor,
        "orientation": "arrivee SUD, grotte au NORD ; corridor indicatif, pas une collision moteur",
        "sha256": {p.name: sha256(p) for p in
                   [SRC / "generation/brut_relief_magenta.png", SRC / "generation/brut_sol.png",
                    SRC / "references/reference_originale.png"]},
        "runtime_PMDO": "NON TESTE", "art_approuve": False,
    }
    (O / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    print(f"entree aride V1 : scene {W}x{H}, grotte {grotte_bbox}, "
          f"corridor x {corridor['x0']}-{corridor['x1']} ({corridor['largeur']} px), "
          f"cailloux {n_cailloux}")


if __name__ == "__main__":
    construire()
