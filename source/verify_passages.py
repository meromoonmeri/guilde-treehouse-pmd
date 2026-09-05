"""Contrôles géométriques supplémentaires des corrections PMD.

Ne remplace pas verify_pmd.py (formats) ni verify_browser.py (aperçu).
Les zones de transition sont des repères d'intégration, pas des collisions moteur.
"""
from pathlib import Path
import hashlib
import json
import numpy as np
import cv2
from PIL import Image
from scipy.ndimage import binary_fill_holes, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source/passages"


def rgba(path):
    return np.array(Image.open(path).convert("RGBA"))


def verify():
    manifest = json.loads((ROOT / "kit.json").read_text())
    definitions = json.loads((SOURCE / "definitions.json").read_text())["salles"]
    provenance = json.loads((SOURCE / "provenance.json").read_text())
    for path, expected in provenance["natifs_originaux_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, f"Natif d'origine modifié : {path}"
    report = {"natifs_originaux_intacts": True, "salles": []}
    count = 0
    for room in manifest["salles"]:
        rid = room["id"]
        w, h = room["dimensions"]
        semantic = np.array(Image.open(SOURCE / "masques" / f"{rid}.png"))
        reference = rgba(SOURCE / "bases" / f"{rid}.png")
        original_alpha = reference[:, :, 3] > 0
        assert np.array_equal(semantic > 0, original_alpha), (rid, "couverture des masques")
        floor = semantic == 1
        # La connectivité et l'épaisseur se testent sur le SOL, pas sur l'alpha
        # global qui comprend aussi les murs et ne prouve pas un passage libre.
        _, regions = cv2.connectedComponents(floor.astype("uint8"), connectivity=4)
        cx, cy = w // 2, round(h * .65)
        main = regions[cy, cx]
        assert main != 0, (rid, "sol central absent")
        padded = np.pad(floor, 1, mode="constant", constant_values=False)
        clearance = distance_transform_edt(padded)[1:-1, 1:-1]
        points = []
        for p in definitions[rid]["passages"]:
            x, y = p["point_sol"]
            assert regions[y, x] == main, (rid, p["id"], "accès coupé du sol principal")
            assert clearance[y, x] >= 8, (rid, p["id"], "bande de sol trop étroite au point de contrôle")
            if p["type"] in ["passage_lateral", "passage_sud"]:
                if p["orientation"] == "E":
                    assert floor[y, -1]
                elif p["orientation"] == "O":
                    assert floor[y, 0]
                else:
                    assert floor[-1, x]
            points.append({"id": p["id"], "sol_connecte": True, "degagement_px": float(clearance[y, x])})
            count += 1
        hole = np.array(Image.open(ROOT / "fenetres_exterieur" / rid / "masque.png")) > 0
        assert np.array_equal(binary_fill_holes(original_alpha) & ~original_alpha, hole), (rid, "petit trou de fenêtre oublié")
        light_peaks = {}
        alphas = []
        for mode in ["jour", "nuit"]:
            base = rgba(ROOT / room["fichiers"][mode]["base"])
            alpha = base[:, :, 3] > 0
            alphas.append(alpha)
            assert np.array_equal(alpha, original_alpha), (rid, mode, "silhouette déplacée")
            path = ROOT / "calques" / room["dossier"] / mode
            shadow = rgba(path / "08_ombres_acces.png")
            light = rgba(path / "09_eclairage_fixe.png")
            assert shadow[:, :, 3].any() and light[:, :, 3].any(), (rid, mode, "calque de contact ou lumière vide")
            effects = (shadow[:, :, 3] > 0) | (light[:, :, 3] > 0)
            assert not effects[~alpha].any(), (rid, mode, "effet hors décor ou dans une fenêtre")
            assert not effects[hole].any()
            # Pas de filtre global : la base artistique doit rester exacte en dehors
            # des petits effets des accès. La palette nocturne est le grade déclaré.
            expected = reference.copy()
            if mode == "nuit":
                expected[:, :, :3] = np.rint(expected[:, :, :3] * [.36, .34, .43] + [9, 10, 19]).clip(0, 255).astype("uint8")
                expected[~alpha] = 0
            assert np.array_equal(base[~effects], expected[~effects]), (rid, mode, "modification hors éclairage local")
            for p in definitions[rid]["passages"]:
                x, y = p["point_sol"]
                assert shadow[max(0, y - 2):y + 3, max(0, x - 2):x + 3, 3].max() <= 4, (rid, mode, p["id"], "centre du passage barré par l'ombre")
            light_peaks[mode] = int(light[:, :, 3].max())
        assert np.array_equal(*alphas)
        assert light_peaks["nuit"] < light_peaks["jour"]
        for guide in [SOURCE / "masques" / f"{rid}.png", SOURCE / "masques" / f"{rid}_retouches.png"]:
            assert guide.exists()
        report["salles"].append({"id": rid, "passages": points, "petits_trous_couverts": True,
                                  "alpha_jour_nuit_identique": True, "lumiere_nuit_attenuee": True,
                                  "effets_uniquement_locaux": True})
    report["reperes_verifies"] = count
    report["limite"] = "Contrôle d'assets : aucune collision, transition ou animation n'est installée dans un moteur de jeu."
    (ROOT / "controle_passages.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"PASS : {count} repères connectés, ouvertures fines complètes, centres dégagés, lumière nuit atténuée, natifs intacts.")
    return report


if __name__ == "__main__":
    verify()
