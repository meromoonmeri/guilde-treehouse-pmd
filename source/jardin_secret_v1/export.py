"""Exporte le Jardin secret v1 : calques PNG 8 px jour/nuit, compositions, ORA, provenance,
manifeste, vérifications et galerie HTML."""
from __future__ import annotations

import hashlib
import io
import json
import sys
import zipfile
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "source" / "cote_v4_abyss"))
import layout as L  # noqa: E402
from compose import compose, composite  # noqa: E402
from night import night  # noqa: E402

OUT = ROOT / "renders" / "jardin_secret_v1"
PREFIX = "JSEC_V1_"
LABELS = {
    "01_sol": "Sol : sous-bois, frange de feuilles, pelouse, haies, tapis 4 bandes (synthèse de la référence)",
    "02_fleurs": "Fleurs (sprites de la référence, sous le joueur)",
    "03_rochers": "Rochers (sprites de la référence, ombres portées incluses)",
    "04_souche": "Souche-sanctuaire à escalier (position d'origine)",
    "05_arbres_troncs": "Arbres : troncs et ombres au sol (sous le joueur)",
    "06_arbres_cimes": "Arbres : cimes (au-dessus du joueur)",
    "07_rayon": "Rayon de lumière (position d'origine, au-dessus du joueur)",
    "08_feuillage_avant": "Feuillage immersif d'avant-plan (frange sombre de la référence)",
}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save_ora(path: Path, layers: dict, comp: np.ndarray):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("mimetype", "image/openraster", compress_type=zipfile.ZIP_STORED)
        stack = [f'<image w="{L.W}" h="{L.H}"><stack>']
        for k in sorted(layers, reverse=True):
            stack.append(f'<layer name="{PREFIX}{k}" src="data/{k}.png" x="0" y="0" visibility="visible"/>')
        stack.append("</stack></image>")
        z.writestr("stack.xml", "\n".join(stack))
        for k, a in layers.items():
            b = io.BytesIO()
            Image.fromarray(a).save(b, "PNG")
            z.writestr(f"data/{k}.png", b.getvalue())
        b = io.BytesIO()
        Image.fromarray(comp).save(b, "PNG")
        z.writestr("mergedimage.png", b.getvalue())
        t = Image.fromarray(comp)
        t.thumbnail((256, 256))
        b = io.BytesIO()
        t.save(b, "PNG")
        z.writestr("Thumbnails/thumbnail.png", b.getvalue())


def walk_check(cls_t, layers):
    """Chemin sud → pied de l'escalier de la souche sur le sol praticable
    (pelouse + tapis, hors rochers et troncs), marge de 8 px (gabarit d'un Pokémon)."""
    from scipy import ndimage as ndi
    walk = cls_t >= 1
    walk &= layers["03_rochers"][..., 3] == 0
    walk &= layers["05_arbres_troncs"][..., 3] == 0
    walk &= layers["04_souche"][..., 3] == 0
    walk = ndi.binary_erosion(walk, np.ones((9, 9)), border_value=1)
    start = [(L.H - 1, x) for x in range(L.W) if walk[L.H - 1, x]]
    ys, xs = np.nonzero(layers["04_souche"][..., 3])
    goal_y = int(ys.max()) + 6
    gx = int(np.median(xs[ys > ys.max() - 12]))
    seen = np.zeros_like(walk)
    dq = deque(start)
    for p in start:
        seen[p] = True
    while dq:
        y, x = dq.popleft()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ny, nx = y + dy, x + dx
            if 0 <= ny < L.H and 0 <= nx < L.W and walk[ny, nx] and not seen[ny, nx]:
                seen[ny, nx] = True
                dq.append((ny, nx))
    reach = bool(seen[max(0, goal_y - 6):goal_y + 6, gx - 6:gx + 6].any())
    return {"entree_sud_px": len(start), "but": [gx, goal_y], "atteint": reach,
            "zone_praticable_px": int(seen.sum())}


def export():
    layers, srcs, placements, warnings, refrgba = compose()
    (OUT / "calques").mkdir(parents=True, exist_ok=True)
    (OUT / "nuit").mkdir(parents=True, exist_ok=True)
    keys = sorted(layers)
    night_layers = {k: np.array(night(Image.fromarray(v))) for k, v in layers.items()}
    files = {}
    for k in keys:
        pj = OUT / "calques" / f"{PREFIX}{k}.png"
        pn = OUT / "nuit" / f"{PREFIX}{k}_nuit.png"
        Image.fromarray(layers[k]).save(pj)
        Image.fromarray(night_layers[k]).save(pn)
        files[k] = {"jour": str(pj.relative_to(ROOT)), "nuit": str(pn.relative_to(ROOT)),
                    "sha256_jour": sha(pj), "sha256_nuit": sha(pn), "role": LABELS[k],
                    "pixels_opaques": int((layers[k][..., 3] > 0).sum())}
    comp = composite(layers, keys)
    compn = composite(night_layers, keys)
    Image.fromarray(comp).save(OUT / f"{PREFIX}composition_jour.png")
    Image.fromarray(compn).save(OUT / f"{PREFIX}composition_nuit.png")
    # sans avant-plan (pour voir le sol sous le feuillage)
    Image.fromarray(composite(layers, [k for k in keys if k != "08_feuillage_avant"])).save(
        OUT / f"{PREFIX}composition_sans_feuillage.png")
    save_ora(OUT / f"{PREFIX}jour.ora", layers, comp)
    save_ora(OUT / f"{PREFIX}nuit.ora", night_layers, compn)
    np.savez_compressed(OUT / f"{PREFIX}provenance_src_yx.npz", **{k: v.astype(np.int16) for k, v in srcs.items()})

    # ---------------- vérifications ----------------
    ref = refrgba
    checks = {}
    checks["dimensions_816x1152_grille_8px"] = all(
        a.shape[:2] == (L.H, L.W) for a in layers.values()) and L.W % 8 == 0 and L.H % 8 == 0
    checks["alpha_binaire"] = all(set(np.unique(a[..., 3]).tolist()) <= {0, 255} for a in layers.values())
    checks["sol_entierement_opaque"] = bool((layers["01_sol"][..., 3] == 255).all())
    exact = {}
    for k, a in layers.items():
        m = a[..., 3] > 0
        s = srcs[k]
        ok_src = bool((s[m] >= 0).all())
        sy, sx = s[m][:, 0], s[m][:, 1]
        eq = bool(ok_src and (ref[sy, sx] == a[m]).all())
        exact[k] = eq
    checks["chaque_pixel_opaque_egal_a_son_pixel_source"] = exact
    ref_cols = set(map(tuple, ref[..., :3].reshape(-1, 3).tolist()))
    new_cols = set()
    for a in layers.values():
        m = a[..., 3] > 0
        new_cols |= set(map(tuple, a[m][:, :3].tolist()))
    checks["aucune_couleur_hors_reference_jour"] = len(new_cols - ref_cols) == 0
    checks["recomposition_exacte"] = bool((composite(layers, keys) == comp).all())
    checks["nuit_egale_filtre_abyss_des_calques"] = all(
        (np.array(night(Image.fromarray(layers[k]))) == night_layers[k]).all() for k in keys)
    names = [Path(f["jour"]).name for f in files.values()] + [Path(f["nuit"]).name for f in files.values()]
    checks["noms_de_fichiers_uniques"] = len(names) == len(set(names))
    sol = np.load(HERE / "travail" / "sol.npz")
    checks["parcours_sud_vers_sanctuaire"] = walk_check(sol["cls"], layers)
    checks["placements_sur_pelouse"] = not warnings
    all_pass = (checks["dimensions_816x1152_grille_8px"] and checks["alpha_binaire"]
                and checks["sol_entierement_opaque"] and all(exact.values())
                and checks["aucune_couleur_hors_reference_jour"] and checks["recomposition_exacte"]
                and checks["nuit_egale_filtre_abyss_des_calques"] and checks["noms_de_fichiers_uniques"]
                and checks["parcours_sud_vers_sanctuaire"]["atteint"] and checks["placements_sur_pelouse"])
    checks["all_pass"] = bool(all_pass)
    (OUT / "verification.json").write_text(json.dumps(checks, indent=1, ensure_ascii=False))

    manifest = {
        "id": "jardin_secret_v1",
        "taille_px": [L.W, L.H], "grille_px": 8, "cellules": [L.W // 8, L.H // 8],
        "reference": {"fichier": "secretgarden.png", "taille": [408, 408],
                      "sha256": sha(ROOT / "secretgarden.png")},
        "methode": ("Synthèse guidée par patchs (image quilting + texture transfer) depuis la seule "
                    "référence : chaque pixel est copié d'un pixel source (provenance_src_yx.npz, "
                    "coordonnées y,x dans secretgarden.png) ; coupes minimales, aucun mélange, "
                    "aucune couleur créée. Objets détourés puis translatés. Module rayon/souche/"
                    "prairie reposé à l'identique (décalage +204,0)."),
        "ordre_calques_bas_vers_haut": [f"{PREFIX}{k}" for k in keys],
        "calques": files,
        "placements": placements,
        "nuit": "filtre Abyss exact (source/cote_v4_abyss/night.py), une seule fois, par calque",
        "import_pmdo": "PNG to Tileset, taille de tuile 8 px ; collisions et warps à dessiner dans l'éditeur",
        "limites": [
            "Pixels = référence PMD Sky ; la géométrie du jardin est nouvelle (pas un décor officiel).",
            "Les bords de pelouse orientés sud n'existent pas dans la référence : ils sont placés sous le feuillage d'avant-plan.",
            "Aucun test dans PMDO (ni rendu moteur, ni collisions).",
            "Rayon statique comme la référence (pas d'animation inventée).",
        ],
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False))
    return checks, files


if __name__ == "__main__":
    checks, files = export()
    print(json.dumps({k: v for k, v in checks.items() if k != "chaque_pixel_opaque_egal_a_son_pixel_source"},
                     indent=1, ensure_ascii=False))
    print("exact:", checks["chaque_pixel_opaque_egal_a_son_pixel_source"])
