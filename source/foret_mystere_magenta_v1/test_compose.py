"""Tests des livrables Forêt Mystère magenta V1.
Lancer : .venv/bin/python -m unittest discover -s source/foret_mystere_magenta_v1 -p 'test_*.py'"""
import hashlib, json, sys, unittest
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
OUT = R / "renders" / "foret_mystere_magenta_v1"
sys.path.insert(0, str(R / "source" / "controle_qualite_pixel"))
import gate  # noqa: E402


class ForetMystereMagentaV1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = json.loads((OUT / "manifest.json").read_text())
        cls.layers = [np.array(Image.open(OUT / f)) for f in cls.m["calques"]]
        ref = np.array(Image.open(HERE / "refs" / "reference_mystifying_forest.png").convert("RGB"))
        cls.pal = {tuple(c) for c in np.unique(ref.reshape(-1, 3), axis=0)}

    def test_gate_pass(self):
        self.assertTrue(gate.zone_checks(OUT)["pass"])

    def test_grille_8px_et_alignement(self):
        for a in self.layers:
            self.assertEqual(a.shape, (592, 440, 4))
        self.assertEqual((592 % 8, 440 % 8), (0, 0))
        self.assertTrue((self.layers[0][..., 3] == 255).all(), "sol plein")

    def test_palette_exacte_de_la_reference(self):
        for f, a in zip(self.m["calques"], self.layers):
            vis = a[a[..., 3] > 0][:, :3]
            cols = {tuple(c) for c in np.unique(vis, axis=0)}
            self.assertFalse(cols - self.pal, f"{f}: couleurs hors palette Mystifying")
            self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255}, f"{f}: alpha non binaire")

    def test_composite_empilement_exact(self):
        st = Image.new("RGBA", (440, 592))
        for a in self.layers:
            st.alpha_composite(Image.fromarray(a))
        self.assertTrue(np.array_equal(np.array(st), np.array(Image.open(OUT / "composite.png"))))

    def test_couloir_sud_nord_libre(self):
        # entrée nord et arrivée sud non couvertes par rochers/troncs/canopées
        for a in self.layers[2:]:
            self.assertEqual(int(a[0:40, 285:325, 3].max()), 0, "entrée nord obstruée")
            self.assertEqual(int(a[560:592, 205:235, 3].max()), 0, "arrivée sud obstruée")

    def test_provenance_bruts(self):
        for name, h in self.m["bruts_sha256"].items():
            self.assertEqual(hashlib.sha256((HERE / "bruts" / name).read_bytes()).hexdigest(), h)
        self.assertIn("GÉNÉRÉ", self.m["pixels"])


if __name__ == "__main__":
    unittest.main()
