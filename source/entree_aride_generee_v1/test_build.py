"""Tests dedies entree aride V1 : decoupe, couches, ORA, corridor. Pas de runtime PMDO."""
import json
import unittest
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

from .build import LAYERS, O, R, SRC, W, H, detourage_magenta

LIDS = [lid for lid, _ in LAYERS]


def couche(lid):
    return np.array(Image.open(O / "couches" / f"EntreeArideV1_{lid}.png").convert("RGBA"))


class TestEntreeAride(unittest.TestCase):
    def test_01_dimensions_grille8(self):
        for lid in LIDS:
            im = Image.open(O / "couches" / f"EntreeArideV1_{lid}.png")
            self.assertEqual(im.size, (W, H), lid)
        self.assertEqual(W % 8, 0)
        self.assertEqual(H % 8, 0)
        self.assertEqual(
            Image.open(O / "scene/scene_complete.png").size, (W, H))

    def test_02_zero_magenta_residuel(self):
        for lid in LIDS[1:]:
            a = couche(lid).astype(float)
            d = np.linalg.norm(a[:, :, :3] - np.array([255., 0., 255.]), axis=2)
            self.assertEqual(int(((d < 40) & (a[:, :, 3] > 0)).sum()), 0, lid)

    def test_03_alpha_binaire_rgb_nuls(self):
        for lid in LIDS:
            a = couche(lid)
            self.assertTrue(set(np.unique(a[:, :, 3])) <= {0, 255}, lid)
            sous = a[a[:, :, 3] == 0][:, :3]
            self.assertEqual(int(sous.sum()), 0, lid)
        sol = couche("01_sol")
        self.assertEqual(int((sol[:, :, 3] == 0).sum()), 0)  # sol opaque

    def test_04_partition_exacte_du_relief(self):
        brut = Image.open(SRC / "generation/brut_relief_magenta.png").convert("RGB")
        rel = np.array(brut.resize((W, H), Image.Resampling.LANCZOS)).astype(float)
        opaque, _d = detourage_magenta(rel)
        union = np.zeros_like(opaque)
        for lid in LIDS[1:]:
            m = couche(lid)[:, :, 3] > 0
            self.assertEqual(int((union & m).sum()), 0, f"chevauchement {lid}")
            union |= m
        self.assertTrue(np.array_equal(union, opaque), "union != relief detoure")
        # RGB identiques au brut normalise sur chaque couche
        ref = rel.astype("uint8")
        for lid in LIDS[1:]:
            a = couche(lid)
            m = a[:, :, 3] > 0
            self.assertTrue(np.array_equal(a[m][:, :3], ref[m]), f"RGB modifies {lid}")

    def test_05_recomposition_scene(self):
        scene = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for lid in LIDS:
            scene.alpha_composite(Image.open(O / "couches" / f"EntreeArideV1_{lid}.png"))
        att = Image.open(O / "scene/scene_complete.png").convert("RGBA")
        self.assertTrue(np.array_equal(np.array(scene), np.array(att)))

    def test_06_grotte_nord_centre(self):
        m = couche("03_bouche_grotte")[:, :, 3] > 0
        self.assertGreater(int(m.sum()), 400)
        ys, xs = np.where(m)
        cx, cy = float(xs.mean()), float(ys.mean())
        self.assertTrue(150 < cx < 258, cx)
        self.assertLess(cy, H / 2)
        self.assertLess(int(ys.min()), 70)

    def test_07_corridor_sud_grotte_16px(self):
        man = json.loads((O / "manifest.json").read_text(encoding="utf-8"))
        cor = man["corridor_sud_nord"]
        self.assertGreaterEqual(cor["largeur"], 16, cor)
        relief = np.zeros((H, W), bool)
        for lid in LIDS[1:]:
            relief |= couche(lid)[:, :, 3] > 0
        bande = relief[cor["y_haut"]:cor["y_bas"], cor["x0"]:cor["x1"] + 1]
        self.assertEqual(int(bande.sum()), 0)

    def test_08_ora_valide_6_calques(self):
        p = O / "EntreeArideV1.ora"
        with zipfile.ZipFile(p) as z:
            self.assertEqual(z.namelist()[0], "mimetype")
            self.assertEqual(z.read("mimetype"), b"image/openraster")
            root = ET.fromstring(z.read("stack.xml"))
            self.assertEqual(root.get("w"), str(W))
            self.assertEqual(root.get("h"), str(H))
            layers = root.findall(".//layer")
            self.assertEqual(len(layers), 6)
            for lay in layers:
                im = Image.open(z.open(lay.get("src")))
                self.assertEqual(im.size, (W, H))

    def test_09_viewer_embarque_6_calques(self):
        html = (R / "apercu_entree_aride_v1.html").read_text(encoding="utf-8")
        self.assertEqual(html.count("data:image/png;base64,"), 6)
        for lid in LIDS:
            self.assertIn(lid, html)

    def test_10_manifest_coherent(self):
        man = json.loads((O / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(man["taille"], [W, H])
        self.assertEqual(len(man["calques"]), 6)
        self.assertEqual(man["runtime_PMDO"], "NON TESTE")
        self.assertFalse(man["art_approuve"])
        # reference originale intacte
        ref = SRC / "references/reference_originale.png"
        self.assertTrue(ref.exists())
        import hashlib
        self.assertEqual(man["sha256"][ref.name],
                         hashlib.sha256(ref.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
