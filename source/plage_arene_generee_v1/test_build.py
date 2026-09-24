"""Tests dedies plage V1 : partition pleine page, couches, ORA, ouverture sud."""
import hashlib
import json
import unittest
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from PIL import Image

from .build import LAYERS, O, R, SRC, W, H, normaliser, sculpter_ouverture_sud

LIDS = [lid for lid, _ in LAYERS]


def couche(lid):
    with Image.open(O / "couches" / f"PlageAreneV1_{lid}.png") as im:
        return np.array(im.convert("RGBA"))


class TestPlageArene(unittest.TestCase):
    def test_01_dimensions_grille8(self):
        for lid in LIDS:
            with Image.open(O / "couches" / f"PlageAreneV1_{lid}.png") as im:
                self.assertEqual(im.size, (W, H), lid)
        self.assertEqual(W % 8, 0)
        self.assertEqual(H % 8, 0)
        with Image.open(O / "scene/scene_complete.png") as im:
            self.assertEqual(im.size, (W, H))

    def test_02_alpha_binaire_rgb_nuls(self):
        for lid in LIDS:
            a = couche(lid)
            self.assertTrue(set(np.unique(a[:, :, 3])) <= {0, 255}, lid)
            self.assertEqual(int(a[a[:, :, 3] == 0][:, :3].sum()), 0, lid)

    def test_03_partition_pleine_page_exacte(self):
        union = np.zeros((H, W), bool)
        for lid in LIDS:
            m = couche(lid)[:, :, 3] > 0
            self.assertEqual(int((union & m).sum()), 0, f"chevauchement {lid}")
            union |= m
        self.assertTrue(union.all(), "trous dans la partition")

    def test_04_rgb_intacts_sauf_ouverture(self):
        with Image.open(SRC / "generation/brut_scene.png") as b:
            a = normaliser(b.convert("RGB"))
        _out, ouv = sculpter_ouverture_sud(a)
        ret = np.zeros((H, W), bool)
        # re-derive : pixels retouches = zone ou scene != brut normalise
        with Image.open(O / "scene/scene_complete.png") as s:
            scene = np.array(s.convert("RGBA"))[:, :, :3].astype(int)
        diff = (np.abs(scene - a.astype(int)).sum(axis=2) > 0)
        self.assertEqual(int(diff.sum()), ouv["pixels_retouches"])
        self.assertGreater(ouv["pixels_retouches"], 100)
        # hors retouche : chaque couche reprend le RGB du brut
        ref = a.astype("uint8")
        for lid in LIDS:
            c = couche(lid)
            m = (c[:, :, 3] > 0) & ~diff
            self.assertTrue(np.array_equal(c[m][:, :3], ref[m]), f"RGB modifies {lid}")

    def test_05_recomposition_scene(self):
        scene = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for lid in LIDS:
            with Image.open(O / "couches" / f"PlageAreneV1_{lid}.png") as im:
                scene.alpha_composite(im.convert("RGBA"))
        with Image.open(O / "scene/scene_complete.png") as att:
            self.assertTrue(np.array_equal(np.array(scene), np.array(att.convert("RGBA"))))

    def test_06_masses_coherentes(self):
        pix = {lid: int((couche(lid)[:, :, 3] > 0).sum()) for lid in LIDS}
        for lid, mini in [("01_mer", 10000), ("02_sable", 10000), ("03_falaises", 30000),
                          ("04_ecume", 2000), ("05_rochers", 200), ("06_vide", 1000)]:
            self.assertGreater(pix[lid], mini, f"{lid}={pix[lid]}")
        # mer sur les cotes, vide en haut, sable au centre-sud
        mer = couche("01_mer")[:, :, 3] > 0
        self.assertGreater(mer[:, :60].sum(), 3000)
        self.assertGreater(mer[:, -60:].sum(), 3000)
        vide = couche("06_vide")[:, :, 3] > 0
        self.assertGreater(vide[:120, :].sum(), 500)
        sable = couche("02_sable")[:, :, 3] > 0
        self.assertGreater(sable[300:, 150:306].sum(), 5000)

    def test_07_ouverture_sud_sable(self):
        man = json.loads((O / "manifest.json").read_text(encoding="utf-8"))
        ouv = man["ouverture_sud"]
        self.assertGreaterEqual(ouv["colonnes_sans_falaise_420_480"], 40, ouv)
        self.assertGreater(ouv["pixels_retouches"], 100)
        sable = couche("02_sable")[:, :, 3] > 0
        # le bord sud de l'ouverture est praticable (sable)
        bas = sable[H - 1, ouv["x0"]:ouv["x1"]]
        self.assertGreaterEqual(int(bas.sum()), 32, "bord sud bouche")
        # la zone retouchee est 100 % sable (retrouvee par difference au brut)
        with Image.open(SRC / "generation/brut_scene.png") as b:
            a = normaliser(b.convert("RGB"))
        with Image.open(O / "scene/scene_complete.png") as s:
            scene = np.array(s.convert("RGBA"))[:, :, :3].astype(int)
        diff = (np.abs(scene - a.astype(int)).sum(axis=2) > 0)
        self.assertTrue(sable[diff].all(), "retouche non sable")
        # l'entonnoir rejoint le sable de l'arene en haut
        self.assertGreater(sable[385:400, 216:240].sum(), 200, "entonnoir bouche en haut")

    def test_08_rochers_isoles(self):
        man = json.loads((O / "manifest.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(man["rochers_isoles"], 3)
        self.assertLessEqual(man["rochers_isoles"], 40)
        m = couche("05_rochers")[:, :, 3] > 0
        self.assertFalse(m[0, :].any() or m[-1, :].any() or m[:, 0].any() or m[:, -1].any())
        # aucun pan de muraille : chaque rocher < 1500 px et >= 12 px
        from scipy import ndimage as ndi
        lab, n = ndi.label(m)
        tailles = ndi.sum(m, lab, range(1, n + 1))
        for t in tailles:
            self.assertLess(t, 1500)
            self.assertGreaterEqual(t, 12)

    def test_09_ora_valide_6_calques(self):
        with zipfile.ZipFile(O / "PlageAreneV1.ora") as z:
            self.assertEqual(z.namelist()[0], "mimetype")
            self.assertEqual(z.read("mimetype"), b"image/openraster")
            root = ET.fromstring(z.read("stack.xml"))
            self.assertEqual(root.get("w"), str(W))
            self.assertEqual(root.get("h"), str(H))
            layers = root.findall(".//layer")
            self.assertEqual(len(layers), 6)
            for lay in layers:
                with z.open(lay.get("src")) as f:
                    with Image.open(f) as im:
                        self.assertEqual(im.size, (W, H))

    def test_10_viewer_manifest(self):
        html = (R / "apercu_plage_arene_v1.html").read_text(encoding="utf-8")
        self.assertEqual(html.count("data:image/png;base64,"), 6)
        for lid in LIDS:
            self.assertIn(lid, html)
        man = json.loads((O / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(man["taille"], [W, H])
        self.assertEqual(len(man["calques"]), 6)
        self.assertEqual(man["runtime_PMDO"], "NON TESTE")
        self.assertFalse(man["art_approuve"])
        ref = SRC / "references/reference_originale.png"
        self.assertEqual(man["sha256"][ref.name],
                         hashlib.sha256(ref.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
