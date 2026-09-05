"""Contrôles de la reconstruction des couloirs : matière, plans, accès et exports."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image
from scipy.ndimage import label, distance_transform_edt

from verify_tile_formats import image, same, aseprite, tiled

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "tilesheets"
NAMES = ["00_fond_immersion", "01_soubassement", "02_feuillage_arriere", "03_parquet",
         "04_murs_fond", "05_murs_retours", "06_ombres_contact", "07_reflets_seuils",
         "08_spirales", "09_ombres_objets", "10_objets", "11_ecorce_racines_avant", "12_feuillage_avant"]


def verify():
    m = json.loads((KIT / "kit.json").read_text())
    provenance = json.loads((ROOT / "source/hallways/provenance.json").read_text())
    assert m["architecture"]["version"] == 2 and m["architecture"]["calques"] == 13
    assert len(m["modules"]) == 9
    for file, sha in provenance["preserves_sha256"].items():
        assert hashlib.sha256((ROOT / file).read_bytes()).hexdigest() == sha, f"Hors périmètre modifié : {file}"
    # Mesurer le matériau réellement exporté, hors du cadre du panneau.
    wall_file = KIT / "architecture/pieces/murs_fond/000_jour.png"
    a = np.array(image(wall_file))[9:-9, 9:-9, :3].astype(float).mean(axis=2)
    gx, gy = float(abs(np.diff(a, axis=1)).mean()), float(abs(np.diff(a, axis=0)).mean())
    f = np.array(image(KIT / "parquet/parquet_jour.png"))[:32, :32, :3].astype(float).mean(axis=2)
    fx, fy = float(abs(np.diff(f, axis=1)).mean()), float(abs(np.diff(f, axis=0)).mean())
    assert gx > gy * 1.5 and fy > fx * 2, "Le mur et le parquet doivent avoir des orientations de fibres distinctes"
    report = {"version_architecture": 2, "calques_par_module": 13,
              "fichiers_hors_perimetre_intacts": len(provenance["preserves_sha256"]),
              "matiere_murale_distincte": {"gradient_x_mur": gx, "gradient_y_mur": gy,
                                          "gradient_x_parquet": fx, "gradient_y_parquet": fy}, "modules": []}
    edges = {mode: {d: [] for d in ["N", "E", "S", "O"]} for mode in ["jour", "nuit"]}
    for module in m["modules"]:
        assert module["version_architecture"] == 2
        assert [c["id"] for c in module["calques"]] == NAMES
        w, h = module["dimensions"]
        folder = KIT / "modules" / module["id"]
        floor = np.array(Image.open(folder / "sol_praticable.png")) > 0
        assert floor.shape == (h, w) and floor.any()
        assert label(floor)[1] == 1, "Plancher déconnecté"
        core, core_count = label(floor & (distance_transform_edt(floor) >= 16))
        declared = {e["direction"] for e in module["acces"]}
        for direction, strip in {"N": floor[0], "S": floor[-1], "E": floor[:, -1], "O": floor[:, 0]}.items():
            assert bool(strip.any()) == (direction in declared), "Accès manquant ou sortie fantôme"
        guard = np.zeros(floor.shape, bool)
        labels_at_exits = []
        for exit in module["acces"]:
            d = exit["direction"]
            strip = {"N": floor[0], "S": floor[-1], "E": floor[:, -1], "O": floor[:, 0]}[d]
            indices = np.flatnonzero(strip)
            assert len(indices) == exit["largeur_px"] == 96 and (np.diff(indices) == 1).all()
            lo, hi = int(indices[0]), int(indices[-1]) + 1
            assert [lo, hi] == exit["intervalle_px"]
            center = (lo + hi) // 2
            assert center % 32 == 16, "Phase de raccord incompatible"
            if d in ["N", "S"]:
                assert exit["ancrage_px"][0] == center
                probe = (center, 20 if d == "N" else h - 21)
                if d == "N": guard[:40, lo:hi] = True
                else: guard[-40:, lo:hi] = True
            else:
                assert exit["ancrage_px"][1] == center
                probe = (20 if d == "O" else w - 21, center)
                if d == "O": guard[lo:hi, :40] = True
                else: guard[lo:hi, -40:] = True
            value = int(core[probe[1], probe[0]])
            assert value != 0, "Pas de dégagement de 16 px autour du repère d'accès"
            labels_at_exits.append(value)
        assert len(set(labels_at_exits)) == 1, "Les accès ne partagent pas le même noyau praticable"
        alphas, lights = [], []
        nonempty = None
        for mode, files in module["fichiers"].items():
            assert len(files["calques"]) == 13
            assert {p.stem for p in (folder / "calques" / mode).glob("*.png")} == set(NAMES), "Calques de l'ancienne version restants"
            layers = [image(KIT / file) for file in files["calques"]]
            assert all(im.size == (w, h) for im in layers)
            nonempty = [bool(im.getbbox()) for im in layers]
            for i in [0, 1, 2, 3, 6, 7, 11, 12]:
                assert nonempty[i], (module["id"], "calque requis vide", NAMES[i])
            assert nonempty[4] or nonempty[5], "Aucun panneau mural"
            arrays = [np.array(im) for im in layers]
            assert np.array_equal(arrays[0][:, :, 3] > 0, ~floor), "Le fond doit être évidé sous le parquet"
            assert np.array_equal(arrays[3][:, :, 3] > 0, floor), "Le calque sol ne correspond pas au plan"
            wall = (arrays[4][:, :, 3] > 0) | (arrays[5][:, :, 3] > 0)
            assert not wall[floor].any(), "Un panneau remplit le sol"
            if module["id"] in ["couloir_horizontal", "palier_baies"]:
                assert label(wall)[1] == 1, "Fente entre les panneaux d'un même mur"
            for i in [6, 7, 8]:
                assert not (arrays[i][:, :, 3] > 0)[~floor].any(), "Ombre/reflet/motif hors du plancher"
            for i in [1, 2, 4, 5, 11, 12]:
                assert not (arrays[i][:, :, 3] > 0)[guard].any(), "Décor bloquant l'extrémité d'un passage"
            if module["famille"] == "couloir":
                assert not any(nonempty[i] for i in [8, 9, 10]), "Couloir encombré d'objets"
            full = Image.new("RGBA", (w, h))
            transparent = Image.new("RGBA", (w, h))
            for i, im in enumerate(layers):
                full.alpha_composite(im)
                if i: transparent.alpha_composite(im)
            target = image(KIT / files["png"])
            same(full, target, "Recomposition des 13 PNG")
            same(transparent, image(KIT / files["transparent"]), "Version sans fond")
            same(tiled(KIT / files["tiled"]), target, "Recomposition Tiled")
            aseprite(KIT / files["aseprite"], 13, target)
            assert (np.array(target)[:, :, 3] == 255).all()
            alphas.append(np.array(transparent)[:, :, 3] > 0)
            lights.append(int(arrays[7][:, :, 3].max()))
            for e in module["acces"]:
                lo, hi = e["intervalle_px"]
                d = e["direction"]
                edge = {"N": arrays[3][0, lo:hi], "S": arrays[3][-1, lo:hi],
                        "O": arrays[3][lo:hi, 0], "E": arrays[3][lo:hi, -1]}[d]
                edges[mode][d].append(edge)
        assert np.array_equal(*alphas), "Silhouette jour/nuit différente"
        assert 0 < lights[1] < lights[0], "Reflets non atténués la nuit"
        report["modules"].append({"id": module["id"], "calques": 13, "sol_connecte": True,
                                   "acces": len(module["acces"]), "degagement_probe_px": 16,
                                   "fond_evide": True, "murs_distincts_du_sol": True,
                                   "bordures_2_plans": True, "PNG_Aseprite_Tiled": "identiques",
                                   "calques_non_vides": sum(nonempty)})
    # Raccord des sols, pas promesse d'égalité de tous les pixels décoratifs du bord.
    for mode in edges:
        for a in edges[mode]["E"]:
            for b in edges[mode]["O"]:
                assert np.array_equal(a, b), "Discontinuité du parquet est-ouest"
        reference = np.array(image(KIT / "parquet" / f"parquet_{mode}.png"))[:32, :32]
        for a in edges[mode]["N"]:
            assert np.array_equal(a, np.tile(reference[0], (3, 1)))
        for a in edges[mode]["S"]:
            assert np.array_equal(a, np.tile(reference[-1], (3, 1)))
    report["raccords_sols"] = "E/O identiques ; joints N/S à phase cohérente ; axes congrus à 16 modulo 32"
    report["limites"] = "Validation des formats par code. Ni application Aseprite/Tiled, ni moteur exécuté. Les décors de raccord restent ajustables."
    (KIT / "controle_hallways.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(f"PASS couloirs : 9 modules × 13 plans, accès dégagés, fond évidé, murs distincts, bordures séparées ; {len(provenance['preserves_sha256'])} fichiers préservés.")
    return report


if __name__ == "__main__":
    verify()
