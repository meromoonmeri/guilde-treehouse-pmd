"""Tests des livrables Crooked Cavern × Apple Woods V1.
Lancer : .venv/bin/python -m unittest discover -s source/crooked_applewoods_v1 -p 'test_*.py'"""
import hashlib, json, sys, unittest
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
OUT = R / "renders" / "crooked_applewoods_v1"
sys.path.insert(0, str(R / "source" / "controle_qualite_pixel"))
sys.path.insert(0, str(HERE))
import gate  # noqa: E402
from pixels_lib import palette_of  # noqa: E402


class CrookedAppleV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = json.loads((OUT / "manifest.json").read_text())
        cls.layers = [np.array(Image.open(OUT / f)) for f in cls.m["calques"]]
        pal = np.concatenate([palette_of(HERE / "refs" / "reference_apple_woods.png"),
                              palette_of(HERE / "refs" / "reference_crooked_cavern.png")])
        cls.pal = {tuple(int(v) for v in c) for c in pal}

    def test_gate_pass(self):
        self.assertTrue(gate.zone_checks(OUT)["pass"])

    def test_grille_8px_et_alignement(self):
        for a in self.layers:
            self.assertEqual(a.shape, (432, 464, 4))
        self.assertTrue((self.layers[0][..., 3] == 255).all(), "sol plein")

    def test_palettes_exactes_des_references(self):
        for f, a in zip(self.m["calques"], self.layers):
            cols = {tuple(int(v) for v in c) for c in np.unique(a[a[..., 3] > 0][:, :3], axis=0)}
            self.assertFalse(cols - self.pal, f"{f}: couleurs hors palettes Crooked/Apple Woods")
            self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255}, f"{f}: alpha non binaire")

    def test_composite_empilement_exact(self):
        st = Image.new("RGBA", (464, 432))
        for a in self.layers:
            st.alpha_composite(Image.fromarray(a))
        self.assertTrue(np.array_equal(np.array(st), np.array(Image.open(OUT / "composite.png"))))

    def test_couloir_sud_nord_libre(self):
        # devant la grotte et à l'arrivée sud : ni rocher, ni tronc, ni canopée
        for a in self.layers[3:]:
            self.assertEqual(int(a[125:150, 275:315, 3].max()), 0, "parvis de la grotte obstrué")
            self.assertEqual(int(a[400:432, 270:320, 3].max()), 0, "arrivée sud obstruée")
        self.assertEqual(int(self.layers[1][176:432, 200:360, 3].max()), 0, "falaise sur le chemin")

    def test_grotte_sombre_au_nord(self):
        z = self.layers[1][60:110, 275:320]
        self.assertTrue((z[..., 3] == 255).all())
        self.assertLess(float(z[..., :3].mean()), 70, "bouche de grotte absente")

    def test_provenance_bruts(self):
        for name, h in self.m["bruts_sha256"].items():
            self.assertEqual(hashlib.sha256((HERE / "bruts" / name).read_bytes()).hexdigest(), h)
        self.assertIn("GÉNÉRÉ", self.m["pixels"])


if __name__ == "__main__":
    unittest.main()
