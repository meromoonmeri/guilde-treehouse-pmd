"""Vérifie les pixels, grilles, raccords et formats du kit modulaire."""
from pathlib import Path
from PIL import Image
import hashlib
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "tilesheets"


from verify_tile_formats import image, same, aseprite, tiled


def verify():
    m = json.loads((KIT / "kit.json").read_text())
    source = json.loads((ROOT / "source/tilesheets/provenance.json").read_text())
    for path, expected in source["salles_preservees_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected, f"Salle antérieure modifiée : {path}"
    assert m["grille_px"] == 32 and len(m["objets"]) == 20 and len(m["modules"]) == 9
    assert len({o["id"] for o in m["objets"]}) == 20
    assert m["spirales"]["motifs"] == 16
    report = {"grille": 32, "objets": 20, "motifs_spirales": 16, "salles_existantes_intactes": True, "modules": []}
    for mode in m["palettes"]:
        sheet = np.array(image(KIT / "parquet" / f"parquet_{mode}.png"))
        assert sheet.shape == (128, 256, 4) and (sheet[:, :, 3] == 255).all()
        horizontal = [sheet[i // 8 * 32:i // 8 * 32 + 32, i % 8 * 32:i % 8 * 32 + 32] for i in range(16)]
        vertical = [sheet[i // 8 * 32:i // 8 * 32 + 32, i % 8 * 32:i % 8 * 32 + 32] for i in range(16, 32)]
        for a in horizontal:
            for b in horizontal:
                assert np.array_equal(a[:, -1], b[:, 0]), "Raccord latéral de parquet"
                assert np.array_equal(a[0], b[0]) and np.array_equal(a[-1], b[-1]), "Phase des joints"
        for a in vertical:
            for b in vertical:
                assert np.array_equal(a[-1], b[0]), "Raccord longitudinal du parquet vertical"
        spirals = image(KIT / "spirales" / f"spirales_{mode}.png")
        a = np.array(spirals)
        assert spirals.size == (256, 256) and 0 < a[:, :, 3].max() < 255
        assert np.count_nonzero(a[:, :, 3]) < 256 * 256 * .2
        for i in range(16):
            individual = image(KIT / "spirales/individuelles" / f"spirale_{i + 1:02d}_{mode}.png")
            sx, sy = i % 4 * 64, i // 4 * 64
            same(individual, spirals.crop((sx, sy, sx + 64, sy + 64)), "Motif mal rangé")
        obj_atlas = image(KIT / "objets" / f"objets_{mode}.png")
        obj_shadow = image(KIT / "objets" / f"ombres_{mode}.png")
        assert obj_atlas.size == obj_shadow.size == (384, 480)
        for obj in m["objets"]:
            im = image(KIT / obj["fichiers"][mode]["png"])
            shadow = image(KIT / obj["fichiers"][mode]["ombre"])
            assert list(im.size) == obj["taille"] and im.size == shadow.size
            assert im.width % 8 == im.height % 8 == 0
            pixels = np.array(im)
            assert set(np.unique(pixels[:, :, 3])) <= {0, 255} and (pixels[:, :, 3] == 255).any()
            r, g, b = [pixels[:, :, k].astype(int) for k in range(3)]
            assert not ((r > 220) & (b > 220) & (g < 50) & (pixels[:, :, 3] > 0)).any(), "Fond magenta résiduel"
            x, y, w, h = obj["rect_atlas"]
            tile = obj_atlas.crop((x, y, x + w, y + h))
            target = Image.new("RGBA", (96, 96))
            target.alpha_composite(im, (48 - obj["pivot"][0], 88 - obj["pivot"][1]))
            same(tile, target, "Objet coupé ou décalé dans la planche")
        composed = obj_shadow.copy()
        composed.alpha_composite(obj_atlas)
        aseprite(KIT / "objets" / f"objets_{mode}.aseprite", 2, composed)
        aseprite(KIT / "parquet" / f"parquet_et_spirales_{mode}.aseprite", 2)
    from verify_hallways import verify as verify_hallways
    hallway_report = verify_hallways()
    report["modules"] = hallway_report["modules"]
    report["architecture_version"] = 2
    report["calques_par_module"] = 13
    report["raccords_sols"] = hallway_report["raccords_sols"]
    report["parquet_bords_communs"] = True
    report["spirales_sans_parquet"] = True
    report["limite"] = "Formats relus par code, sans ouverture dans l'interface Aseprite/Tiled. Les modules ne sont pas intégrés à un moteur."
    (KIT / "controle_qualite.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("PASS : 20 objets, 32 parquets, 16 spirales transparentes ; 18 modules PNG/Aseprite/Tiled identiques ; raccords et salles initiales préservés.")


if __name__ == "__main__":
    verify()
