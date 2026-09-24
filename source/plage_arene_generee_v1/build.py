"""Plage / arene cotiere V1 — methode rendus generes (pas de mosaique native).

Brut : composition complete pleine page generee, guidee par arenapmdskybeach.png.
Normalisation uniforme isotrope, ouverture sud sculptee par clonage vertical du
sable du brut (documente), decoupe couleur en partition stricte, 6 calques,
ORA, scene, planche, viewer, manifeste.

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
O = R / "renders/plage_arene_generee_v1"
W, H = 456, 480  # cible = reference, grille 8 px (57 x 60)

LAYERS = [
    ("01_mer", "Mer"),
    ("02_sable", "Sable de l'arene"),
    ("03_falaises", "Falaises rouges et mousse"),
    ("04_ecume", "Ecume et eclats blancs"),
    ("05_rochers", "Rochers isoles"),
    ("06_vide", "Vide hors terrain"),
]


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def normaliser(brut: Image.Image) -> np.ndarray:
    s = max(W / brut.width, H / brut.height)
    tmp = brut.resize((round(brut.width * s), round(brut.height * s)), Image.Resampling.LANCZOS)
    x0 = (tmp.width - W) // 2
    y0 = (tmp.height - H) // 2
    return np.array(tmp.crop((x0, y0, x0 + W, y0 + H))).astype(float)


def sculpter_ouverture_sud(a: np.ndarray) -> tuple[np.ndarray, dict]:
    """Ouvre une arrivee sud dans la barriere rocheuse du bas.

    Pour chaque colonne de l'ouverture : les pixels sous le dernier sable
    sont remplaces par le sable pris juste au-dessus (decalage vertical,
    pixels du brut uniquement). Bords en escalier elargi vers le sud.
    """
    r, g, b = a.transpose(2, 0, 1)
    # Masque sable strict (meme regle que la decoupe finale) pour ne cloner
    # que des pixels qui resteront du sable apres classification.
    lum = a.mean(axis=2)
    mx = a.max(axis=2)
    mn = a.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    vide0 = lum < 45
    ecume0 = (~vide0) & (lum > 195) & (sat < 0.4)
    mer0 = (~vide0) & (~ecume0) & (b > r + 10) & (b > 70)
    sable0 = ((~vide0) & (~ecume0) & (~mer0) & (r > 150) & (g > 130)
              & (r > b + 15) & (sat < 0.55))
    out = a.copy()
    retouche = np.zeros((H, W), bool)
    cx = W // 2
    # Entonnoir vers le sud : le brut ferme l'arene par un monticule rocheux
    # (~y400-445 au centre). On l'ouvre en entonnoir elargi vers le sud.
    for x in range(cx - 24, cx + 24):
        d = abs(x - cx + (0.5 if x < cx else -0.5))
        yA = 395 if d < 16 else (405 if d < 20 else 415)
        # Fin du sable contigu depuis l'arene (galets <= 5 px toleres).
        col = sable0[:, x]
        yb, zeros = 380, 0
        for y in range(381, H):
            if col[y]:
                yb, zeros = y, 0
            else:
                zeros += 1
                if zeros >= 6:
                    break
        pool = [yy for yy in range(max(0, yb - 70), yb + 1) if col[yy]]
        if len(pool) < 10:
            continue
        i = 0
        for y in range(max(yA, yb + 1), H):
            out[y, x] = a[pool[i % len(pool)], x]
            retouche[y, x] = True
            i += 1
        # Si le sable contigu descendait deja sous yA (pas de monticule dans
        # cette colonne), rien a retoucher au-dessus de yb : le test de zone
        # retouchee 100 % sable reste valide dans tous les cas.
    info = {"x0": cx - 24, "x1": cx + 24, "pixels_retouches": int(retouche.sum()),
            "methode": "ouverture du monticule sud : pavage cyclique du sable "
                       "strict du brut, entonnoir 16/20/24 px depuis y395/405/415"}
    return out, info


def construire():
    (O / "couches").mkdir(parents=True, exist_ok=True)
    (O / "scene").mkdir(parents=True, exist_ok=True)
    (O / "review").mkdir(parents=True, exist_ok=True)

    brut = Image.open(SRC / "generation/brut_scene.png").convert("RGB")
    a = normaliser(brut)
    a, ouv = sculpter_ouverture_sud(a)

    r, g, b = a.transpose(2, 0, 1)
    lum = a.mean(axis=2)
    mx = a.max(axis=2)
    mn = a.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)

    vide = lum < 45
    ecume = (~vide) & (lum > 195) & (sat < 0.4)
    mer = (~vide) & (~ecume) & (b > r + 10) & (b > 70)
    sable = (~vide) & (~ecume) & (~mer) & (r > 150) & (g > 130) & (r > b + 15) & (sat < 0.55)
    rouge = (~vide) & (~ecume) & (~mer) & (~sable) & (r > 100) & (r > b + 25)
    vert = (~vide) & (~ecume) & (~mer) & (~sable) & (~rouge) & (g > r) & (g > b) & (g > 80)
    # Roche candidate : rouge + mousse + crevasses sombres.
    reste = ~(vide | ecume | mer | sable | rouge | vert)
    cand_roche = rouge | vert | reste
    # Reflets bleus enfermes dans la roche -> falaise (pas des trous de mer).
    # Seules les poches < 600 px sont absorbees ; une vraie poche d'eau garde
    # sa classification (controle visuel + test de taille).
    poches = ndimage.binary_fill_holes(cand_roche) & ~cand_roche
    poches &= ~(sable | ecume | vide)
    lab_p, n_p = ndimage.label(poches)
    absorbe = np.zeros_like(vide)
    for k in range(1, n_p + 1):
        if (lab_p == k).sum() < 600:
            absorbe |= lab_p == k
    mer &= ~absorbe
    cand_roche |= absorbe

    # Falaises vs rochers : les massifs sont fragmentes par la mer et l'ecume,
    # la taille seule ne suffit pas. Un rocher est petit (< 2500 px), ne touche
    # aucun bord, sans roche ni vide dans un rayon de 16 px, et entoure a 90 %
    # de sable/mer/ecume. Les dents du nord (vide proche) et les pans de mur
    # (roche proche) restent des falaises.
    # Micro-nettoyage : les speckles < 12 px (grains de sable rougeatres,
    # crevasses sombres) sont rendus a la classe voisine avant le tri,
    # pour ne pas fausser le test de proximite des vrais rochers.
    def micro_nettoyage(masque):
        lab_m, n_m = ndimage.label(masque)
        for k in range(1, n_m + 1):
            if (lab_m == k).sum() >= 12:
                continue
            comp = lab_m == k
            rim = ndimage.binary_dilation(comp, iterations=3) & ~comp
            votes = [((rim & sable).sum(), "s"), ((rim & mer).sum(), "m"),
                     ((rim & ecume).sum(), "e"), ((rim & cand_roche).sum(), "r"),
                     ((rim & vide).sum(), "v")]
            yield comp, max(votes)[1]

    for comp, maj in list(micro_nettoyage(cand_roche)):
        if maj == "s":
            sable |= comp
        elif maj == "m":
            mer |= comp
        elif maj == "e":
            ecume |= comp
        else:
            continue  # roche ou vide proche : gardee dans la roche
        cand_roche &= ~comp
    for comp, maj in list(micro_nettoyage(vide)):
        if maj in ("s", "m", "e"):
            if maj == "s":
                sable |= comp
            elif maj == "m":
                mer |= comp
            else:
                ecume |= comp
            vide &= ~comp
        elif maj == "r":
            cand_roche |= comp
            vide &= ~comp
        # sinon : gardee dans le vide

    # Murs par propagation : les pans sont fragmentes mais restent proches
    # (<= 16 px) les uns des autres, tandis que les blocs isoles (y compris
    # en champ de blocs) sont loin de tout mur. Graines : bords, massifs
    # >= 2500 px, dents proches du vide >= 300 px.
    lab, n = ndimage.label(cand_roche)
    bords = set(np.unique(np.concatenate([lab[0, :], lab[-1, :], lab[:, 0], lab[:, -1]]))) - {0}
    mur = np.zeros(n + 1, bool)
    for k in range(1, n + 1):
        comp = lab == k
        taille = int(comp.sum())
        if k in bords or taille >= 2500:
            mur[k] = True
            continue
        if taille >= 300:
            anneau = ndimage.binary_dilation(comp, iterations=16) & ~comp
            if (anneau & vide).any():
                mur[k] = True
    while True:
        murs = np.isin(lab, np.where(mur)[0])
        dil = ndimage.binary_dilation(murs, iterations=16)
        ajout = False
        for k in range(1, n + 1):
            if not mur[k] and (dil & (lab == k)).any():
                mur[k] = True
                ajout = True
        if not ajout:
            break
    murs = np.isin(lab, np.where(mur)[0])
    # Rochers : hors murs, 12 a 1500 px, sans vide proche, ecrasante
    # majorite de sable/mer/ecume autour.
    rochers = np.zeros_like(vide)
    for k in range(1, n + 1):
        if mur[k]:
            continue
        comp = lab == k
        taille = int(comp.sum())
        if taille < 12 or taille >= 1500:
            continue
        anneau = ndimage.binary_dilation(comp, iterations=16) & ~comp
        if (anneau & vide).any():
            continue
        if (anneau & (sable | mer | ecume)).sum() < 0.9 * anneau.sum():
            continue
        rochers |= comp
    # Note : les candidats rochers a teinte sableuse sont des monticules
    # ombres (relief obstacle), pas du sable plat : ils restent dans
    # 05_rochers comme objets deplacables. (Un correctif de teinte les
    # renvoyait au sable a tort ; abandonne apres controle.)
    n_rochers = ndimage.label(rochers)[1]
    falaise = cand_roche & ~rochers

    masks = {"01_mer": mer, "02_sable": sable, "03_falaises": falaise,
             "04_ecume": ecume, "05_rochers": rochers, "06_vide": vide}
    assert sum(m.sum() for m in masks.values()) == W * H, "partition non exhaustive"

    couches = {}
    ref8 = a.astype("uint8")
    for lid, _ in LAYERS:
        m = masks[lid]
        rgba = np.dstack([ref8, np.where(m, 255, 0).astype("uint8")])
        rgba[~m] = 0
        couches[lid] = Image.fromarray(rgba, "RGBA")
        couches[lid].save(O / "couches" / f"PlageAreneV1_{lid}.png")

    scene = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for lid, _ in LAYERS:
        scene.alpha_composite(couches[lid])
    scene.save(O / "scene" / "scene_complete.png")

    dam = Image.new("RGB", (W, H), (64, 64, 64))
    px = dam.load()
    for y in range(H):
        for x in range(W):
            if (x // 8 + y // 8) % 2:
                px[x, y] = (96, 96, 96)
    vignettes = []
    for lid, _ in LAYERS:
        v = dam.copy()
        v.paste(couches[lid], (0, 0), couches[lid])
        vignettes.append(v)
    vignettes.append(scene.convert("RGB"))
    planche = Image.new("RGB", (W * 4, H * 2), (32, 32, 32))
    for i, v in enumerate(vignettes[:8]):
        planche.paste(v, ((i % 4) * W, (i // 4) * H))
    planche.save(O / "review" / "planche_calques.png")

    ora_path = O / "PlageAreneV1.ora"
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

    # Acces sud : l'ouverture doit etre sans falaise jusqu'a l'arene.
    # (Galets/coquillages sur calques separes = deplacables dans l'editeur.)
    col_ok = [x for x in range(ouv["x0"], ouv["x1"]) if not falaise[420:H, x].any()]

    def uri(im: Image.Image) -> str:
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    donnees = {"largeur": W, "hauteur": H,
               "calques": [{"id": lid, "label": label, "uri": uri(couches[lid])}
                           for lid, label in LAYERS]}
    gabarit = (SRC / "viewer.html").read_text(encoding="utf-8")
    (R / "apercu_plage_arene_v1.html").write_text(
        gabarit.replace("__DATA__", json.dumps(donnees)), encoding="utf-8")

    manifest = {
        "id": "plage_arene_generee_v1",
        "reference": "arenapmdskybeach.png (456x480, conservee intacte)",
        "taille": [W, H], "grille_px": 8, "cases": [W // 8, H // 8],
        "methode": "composition generee reference PMD pleine page -> ouverture sud "
                   "sculptee (clonage sable du brut) -> 6 calques ; PAS des pixels natifs",
        "calques": [{"id": lid, "label": label,
                     "fichier": f"couches/PlageAreneV1_{lid}.png",
                     "pixels": int((np.array(couches[lid])[:, :, 3] > 0).sum())}
                    for lid, label in LAYERS],
        "ouverture_sud": {**ouv, "colonnes_sans_falaise_420_480": len(col_ok)},
        "rochers_isoles": n_rochers,
        "orientation": "arrivee SUD (ouverture sculptee), perspective mer au NORD ; "
                       "indicatif, pas une collision moteur",
        "sha256": {p.name: sha256(p) for p in
                   [SRC / "generation/brut_scene.png", SRC / "references/reference_originale.png"]},
        "runtime_PMDO": "NON TESTE", "art_approuve": False,
    }
    (O / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                     encoding="utf-8")
    print(f"plage V1 : scene {W}x{H}, rochers {n_rochers}, "
          f"ouverture sud retouchee {ouv['pixels_retouches']} px, "
          f"colonnes sans falaise {len(col_ok)}/{ouv['x1'] - ouv['x0']}")


if __name__ == "__main__":
    construire()
