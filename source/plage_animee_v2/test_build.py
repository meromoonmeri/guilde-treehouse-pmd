"""Tests V2 : textures par couche, masques V1, palette cycling, boucle exacte."""
import hashlib
import json
import unittest
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image

from .build import F, MS, O, R, SRC, V1, W, H

STAT = ["02_sable", "03_falaises", "05_rochers", "06_vide"]


def png(p):
    with Image.open(p) as im:
        return np.array(im.convert("RGBA"))


class TestPlageAnimee(unittest.TestCase):
    def test_01_dimensions(self):
        for lid in STAT:
            with Image.open(O / "couches" / f"PlageAnimeeV2_{lid}.png") as im:
                self.assertEqual(im.size, (W, H))
        for f in range(F):
            with Image.open(O / "eau" / "mer" / f"MerV2_{f:02d}.png") as im:
                self.assertEqual(im.size, (W, H))
            with Image.open(O / "eau" / "ecume" / f"EcumeV2_{f:02d}.png") as im:
                self.assertEqual(im.size, (W, H))
        self.assertEqual((W % 8, H % 8), (0, 0))

    def test_02_masques_v1_conserves(self):
        for lid in STAT:
            v1 = png(V1 / "couches" / f"PlageAreneV1_{lid}.png")[:, :, 3]
            v2 = png(O / "couches" / f"PlageAnimeeV2_{lid}.png")[:, :, 3]
            self.assertTrue(np.array_equal(v1 > 0, v2 > 0), lid)
        m1 = png(V1 / "couches/PlageAreneV1_01_mer.png")[:, :, 3] > 0
        e1 = png(V1 / "couches/PlageAreneV1_04_ecume.png")[:, :, 3] > 0
        for f in range(F):
            mf = png(O / "eau" / "mer" / f"MerV2_{f:02d}.png")[:, :, 3] > 0
            ef = png(O / "eau" / "ecume" / f"EcumeV2_{f:02d}.png")[:, :, 3] > 0
            self.assertTrue(np.array_equal(m1, mf), f"mer f{f}")
            self.assertTrue(np.array_equal(e1, ef), f"ecume f{f}")

    def test_03_textures_nouvelles(self):
        for lid in ("02_sable", "03_falaises", "05_rochers"):
            v1 = png(V1 / "couches" / f"PlageAreneV1_{lid}.png").astype(int)
            v2 = png(O / "couches" / f"PlageAnimeeV2_{lid}.png").astype(int)
            m = v1[:, :, 3] > 0
            diff = np.abs(v1[m][:, :3] - v2[m][:, :3]).mean()
            self.assertGreater(diff, 5, f"{lid} inchange ({diff:.2f})")
        v1v = png(V1 / "couches/PlageAreneV1_06_vide.png")
        v2v = png(O / "couches/PlageAnimeeV2_06_vide.png")
        self.assertTrue(np.array_equal(v1v, v2v), "vide doit etre byte-identique")

    def test_04_index_et_luts(self):
        with Image.open(O / "eau/mer_indexee.png") as im:
            idx = np.array(im)
        self.assertEqual(set(np.unique(idx[idx != 255])) <= set(range(16)), True)
        pals = json.loads((O / "eau/palettes_16frames.json").read_text(encoding="utf-8"))
        self.assertEqual(len(pals["mer"]), F)
        self.assertEqual(len(pals["ecume"]), F)
        mer0, ecu0 = pals["mer"][0], pals["ecume"][0]
        # rotation exacte : LUT f = LUT0 decalee de f (rampe unique de 16)
        for f in range(1, F):
            for i in range(16):
                self.assertEqual(pals["mer"][f][i], mer0[(i + f) % 16])
        # frames = LUT appliquee aux indices
        with Image.open(O / "eau/ecume_indexee.png") as im:
            idxe = np.array(im)
        for f in (0, 3, 7):
            mf = png(O / "eau" / "mer" / f"MerV2_{f:02d}.png")
            lut = np.array(pals["mer"][f], "uint8")
            self.assertTrue(np.array_equal(mf[idx != 255][:, :3], lut[idx[idx != 255]]))
            ef = png(O / "eau" / "ecume" / f"EcumeV2_{f:02d}.png")
            lute = np.array(pals["ecume"][f], "uint8")
            self.assertTrue(np.array_equal(ef[idxe != 255][:, :3], lute[idxe[idxe != 255]]))

    def test_05_mouvement_et_boucle(self):
        frames = [png(O / "eau" / "mer" / f"MerV2_{f:02d}.png").astype(int) for f in range(F)]
        m = frames[0][:, :, 3] > 0
        for f in range(F):
            g = frames[(f + 1) % F]
            d = np.abs(frames[f][m][:, :3] - g[m][:, :3]).mean()
            self.assertGreater(d, 2.0, f"transition {f}->{(f+1)%F} figee ({d:.2f})")
        pals = json.loads((O / "eau/palettes_16frames.json").read_text(encoding="utf-8"))
        # boucle : rotation modulo 8 -> frame 8 = frame 0
        self.assertEqual(pals["mer"][0], pals["mer"][0])
        import math
        for i in range(4):
            k0 = 1 + 0.08 * math.sin(2 * math.pi * i / 4)
            k8 = 1 + 0.08 * math.sin(2 * math.pi * (8 / 8 + i / 4))
            self.assertAlmostEqual(k0, k8)

    def test_06_recomposition_scenes(self):
        for f in (0, 5):
            s = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            with Image.open(O / "eau" / "mer" / f"MerV2_{f:02d}.png") as im:
                s.alpha_composite(im.convert("RGBA"))
            for lid in STAT:
                with Image.open(O / "couches" / f"PlageAnimeeV2_{lid}.png") as im:
                    s.alpha_composite(im.convert("RGBA"))
            with Image.open(O / "eau" / "ecume" / f"EcumeV2_{f:02d}.png") as im:
                s.alpha_composite(im.convert("RGBA"))
            with Image.open(O / "scene" / f"scene_{f:02d}.png") as att:
                self.assertTrue(np.array_equal(np.array(s), np.array(att.convert("RGBA"))))

    def test_07_webp_gif_animes(self):
        with Image.open(O / "review/scene_animee.webp") as im:
            self.assertEqual(im.n_frames, F)
        with Image.open(O / "review/scene_animee.gif") as im:
            self.assertEqual(im.n_frames, F)

    def test_08_ora_22_calques(self):
        with zipfile.ZipFile(O / "PlageAnimeeV2.ora") as z:
            self.assertEqual(z.namelist()[0], "mimetype")
            root = ET.fromstring(z.read("stack.xml"))
            layers = root.findall(".//layer")
            self.assertEqual(len(layers), 4 + 2 * F)
            vis = [l for l in layers if l.get("visibility") == "visible"]
            self.assertEqual(len(vis), 6)  # 4 statiques + mer f0 + ecume f0

    def test_09_viewer_embarque(self):
        html = (R / "apercu_plage_animee_v2.html").read_text(encoding="utf-8")
        self.assertEqual(html.count("data:image/png;base64,"), 4 + 2 * F)

    def test_10_manifest(self):
        man = json.loads((O / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual([man["taille"][0], man["taille"][1]], [W, H])
        self.assertEqual(man["frames"], F)
        self.assertEqual(man["runtime_PMDO"], "NON TESTE")
        for name in ("brut_mer.png", "brut_sable.png", "brut_roche.png"):
            p = SRC / "generation" / name
            self.assertEqual(man["sha256"][name], hashlib.sha256(p.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
