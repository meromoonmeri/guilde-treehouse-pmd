"""Audit en lecture seule des assets existants, sans lancer le générateur ni le build.

Usage, depuis la racine du dépôt :
  python rapports/audit_interieurs_guilde/relever_mesures.py > mesures.json

Dépendances : celles de source/requirements.txt.
La sortie standard est le seul résultat ; aucun asset n'est modifié.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import platform
import subprocess

from PIL import Image
import cv2
import numpy as np
from scipy.ndimage import binary_fill_holes

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = json.loads((ROOT / "kit.json").read_text(encoding="utf-8"))


def rgba(path):
    with Image.open(ROOT / path) as image:
        return np.array(image.convert("RGBA"))


def file_counts(folder):
    return dict(Counter(p.suffix for p in (ROOT / folder).rglob("*") if p.is_file()))


def compare(a, b):
    delta = np.abs(a.astype(np.int16) - b.astype(np.int16))
    return {
        "pixels_differents": int(np.count_nonzero(delta.max(axis=2))),
        "ecart_max_par_canal": int(delta.max()),
        "pixels_alpha_differents": int(np.count_nonzero(delta[:, :, 3])),
    }


def audit():
    rooms = []
    counts = {folder: file_counts(folder) for folder in (
        "salles", "calques", "source", "sprites", "exterieur",
        "fenetres_exterieur", "tiled", "apercus"
    )}
    originals = []
    for path in sorted((ROOT / "source/natives").glob("*.png")):
        with Image.open(path) as image:
            a = np.array(image.convert("RGBA"))
            originals.append({
                "fichier": str(path.relative_to(ROOT)),
                "dimensions": list(image.size),
                "mode_png": image.mode,
                "couleurs_rgba_utilisees": int(len(np.unique(a.reshape(-1, 4), axis=0))),
                "cles_metadonnees_pillow": list(image.info),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            })
    for room in MANIFEST["salles"]:
        base = rgba(room["fichiers"]["jour"]["base"])
        night = rgba(room["fichiers"]["nuit"]["base"])
        alpha = base[:, :, 3] > 0
        with Image.open(ROOT / "fenetres_exterieur" / room["id"] / "masque.png") as image:
            window_mask = np.array(image) > 0
        omitted = binary_fill_holes(alpha) & ~alpha & ~window_mask
        n, _, components, _ = cv2.connectedComponentsWithStats(omitted.astype("uint8"), 8)
        red, green, blue = [base[:, :, i].astype(np.int16) for i in range(3)]
        # Signal de contrôle seulement : ce seuil ne prouve pas une contamination.
        pink = (red > green + 25) & (blue > green + 12) & (blue > red * .42) & alpha
        layers = []
        for layer in MANIFEST["calques"]:
            path = f"calques/{room['dossier']}/jour/{layer['id']}.png"
            a = rgba(path)
            layers.append({"id": layer["id"], "pixels_alpha_non_nuls": int(np.count_nonzero(a[:, :, 3]))})
        lum_day = (base[:, :, :3] @ np.array([.2126, .7152, .0722]))[alpha].mean()
        lum_night = (night[:, :, :3] @ np.array([.2126, .7152, .0722]))[alpha].mean()
        rooms.append({
            "id": room["id"], "nom": room["nom"], "dossier": room["dossier"],
            "dimensions": room["dimensions"], "acces": room["acces"],
            "groupes_fenetres": len(room["fenetres"]),
            "pixels_ouvertures_fenetres": int(window_mask.sum()),
            "alpha_base_jour_nuit_identique": bool(np.array_equal(base[:, :, 3], night[:, :, 3])),
            "valeurs_alpha_base_jour": np.unique(base[:, :, 3]).tolist(),
            "luminance_codee_moyenne_jour": round(float(lum_day), 2),
            "luminance_codee_moyenne_nuit": round(float(lum_night), 2),
            "pixels_roses_signales_par_seuil": int(pink.sum()),
            "trous_internes_hors_masque_paysage": {
                "pixels": int(omitted.sum()), "composantes": int(n - 1),
                "boites_xywh_et_aires": components[1:].tolist(),
            },
            "calques_jour": layers,
        })
    by_id = {r["id"]: r for r in MANIFEST["salles"]}
    duplicates = []
    for first, second, flip in [("05", "07", True), ("05", "11", True), ("08", "10", True), ("07", "11", False)]:
        entry = {"source": first, "cible": second, "miroir_horizontal": flip, "bases": {}}
        for mode in ["jour", "nuit"]:
            a = rgba(by_id[first]["fichiers"][mode]["base"])
            b = rgba(by_id[second]["fichiers"][mode]["base"])
            entry["bases"][mode] = compare(a[:, ::-1] if flip else a, b)
        duplicates.append(entry)
    sprite_manifest = json.loads((ROOT / "sprites/decorations.json").read_text(encoding="utf-8"))
    rules = json.loads((ROOT / "source/regles_acces.json").read_text(encoding="utf-8"))
    return {
        "revision": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "environnement": {"python": platform.python_version(), "pillow": Image.__version__, "numpy": np.__version__, "opencv": cv2.__version__},
        "comptages_par_extension": counts,
        "images_natives": originals,
        "salles": rooms,
        "comparaisons_reutilisation": duplicates,
        "banque_sprites": {"total": len(sprite_manifest["sprites"]), "groupes": dict(Counter(s["groupe"] for s in sprite_manifest["sprites"]))},
        "guides_non_retrouves": [p for p in rules["guides"].values() if not (ROOT / p).exists() and not (ROOT / "source" / p).exists()],
        "prudence": "Le seuil de pixels roses est un indicateur, pas une preuve automatique de défaut. La luminance indiquée est une moyenne pondérée des canaux sRGB codés, non une mesure photométrique linéaire.",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2))
