"""Tests du lot aride generee V1 : couches, FX, boucle, chemin."""
import json
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import label

R = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).parent))
from fx import N, PHASES, AMPS, wisp_dx, grain_dx, grain_dy  # noqa: E402

OUT = R / "renders/aride_generee_v1"
MAGENTA = np.array([255, 0, 255])


def load(name):
    return np.array(Image.open(OUT / name).convert("RGBA"))


def pink_opaque(a):
    d = np.abs(a[:, :, :3].astype(int) - MAGENTA).sum(axis=2)
    return (d < 120) & (a[:, :, 3] > 0)


class TestAride(unittest.TestCase):
    def test_bruts(self):
        man = json.loads((OUT / "manifest.json").read_text())
        self.assertEqual(man["scene"], [408, 288])
        for b, meta in man["bruts"].items():
            p = R / "source/aride_generee_v1/bruts" / b
            self.assertTrue(p.exists(), b)
            with Image.open(p) as im:
                self.assertEqual(im.size, (1224, 864), b)
            import hashlib
            self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),
                             meta["sha256"], b)

    def test_dimensions_grille(self):
        for f in ["L00_sol.png", "L01_parois.png", "L02_props.png",
                  "L03_bouche.png", "composite.png",
                  *[f"fx/frame_{i:02d}.png" for i in range(N)]]:
            a = load(f)
            self.assertEqual(a.shape, (288, 408, 4), f)
            self.assertEqual(a.shape[0] % 8, 0)
            self.assertEqual(a.shape[1] % 8, 0)

    def test_zero_magenta(self):
        files = ["L00_sol.png", "L01_parois.png", "L02_props.png",
                 "L03_bouche.png", "composite.png",
                 *[f"fx/frame_{i:02d}.png" for i in range(N)]]
        files += [f"props/{n}.png" for n in
                  ["arbre0", "arbre1", "arbre2", "arbre3", "bloc0", "bloc1"]]
        files += ["fx/voile0.png", "fx/voile1.png", "fx/voile2.png",
                  *[f"fx/grain_{k}.png" for k in range(4)]]
        for f in files:
            a = np.array(Image.open(OUT / f).convert("RGBA"))
            self.assertEqual(int(pink_opaque(a).sum()), 0, f)

    def test_rgb_zero_sous_alpha(self):
        for f in ["L01_parois.png", "L02_props.png", "L03_bouche.png",
                  *[f"fx/frame_{i:02d}.png" for i in range(N)]]:
            a = load(f)
            tr = a[:, :, 3] == 0
            self.assertEqual(int(a[tr][:, :3].sum()), 0, f)

    def test_bouche(self):
        man = json.loads((OUT / "manifest.json").read_text())
        x0, y0, x1, y1 = man["bouche_bbox"]
        self.assertTrue(100 < x0 < x1 < 310 and y0 < 100)
        l01, l03 = load("L01_parois.png"), load("L03_bouche.png")
        ref = load("L01_parois_avec_bouche_REF.png")
        m3 = l03[:, :, 3] > 0
        # le trou de L01 == exactement les pixels de L03
        hole = (ref[:, :, 3] > 0) & (l01[:, :, 3] == 0)
        self.assertTrue(np.array_equal(hole, m3))
        # recomposition RGB exacte vs REF
        m1 = l01[:, :, 3] > 0
        self.assertTrue(np.array_equal(l01[m1], ref[m1]))
        self.assertTrue(np.array_equal(l03[m3], ref[m3]))

    def test_props(self):
        man = json.loads((OUT / "manifest.json").read_text())
        self.assertEqual(len(man["props_composantes"]), 6)
        l01 = load("L01_parois.png")
        l03 = load("L03_bouche.png")
        x0, y0, x1, y1 = man["bouche_bbox"]
        names = ["arbre0", "arbre1", "arbre2", "arbre3", "bloc0", "bloc1"]
        for n in names:
            spr = np.array(Image.open(OUT / "props" / f"{n}.png").convert("RGBA"))
            m = spr[:, :, 3] > 0
            self.assertGreater(int(m.sum()), 200, n)
            dx, dy = man["placements"][n]
            h, w = m.shape
            self.assertGreaterEqual(dx, 0)
            self.assertGreaterEqual(dy, 0)
            self.assertLessEqual(dx + w, 408)
            self.assertLessEqual(dy + h, 288)
            # pas sur la bouche (+8 px de marge)
            self.assertTrue(dx + w < x0 - 8 or dx > x1 + 8 or
                            dy + h < y0 - 8 or dy > y1 + 8, n)
            # majoritairement sur le sable, pas dans la roche
            rock = (l01[dy:dy + h, dx:dx + w, 3] > 0) & m
            self.assertLess(rock.sum() / m.sum(), 0.25, n)
        # aucun pixel de prop dans la bouche
        l02 = load("L02_props.png")
        self.assertEqual(int(l02[y0:y1 + 1, x0:x1 + 1, 3].sum()), 0)

    def test_fx_boucle(self):
        for ph, amp in zip(PHASES, AMPS):
            for i in range(N):
                self.assertEqual(wisp_dx(i, ph, amp), wisp_dx(i + N, ph, amp))
        for k in range(4):
            for i in range(N):
                self.assertEqual(grain_dx(i, k), grain_dx(i + N, k))
                self.assertEqual(grain_dy(i, k), grain_dy(i + N, k))

    def test_fx_couleurs_des_sprites(self):
        pal = set()
        for f in ["fx/voile0.png", "fx/voile1.png", "fx/voile2.png",
                  *[f"fx/grain_{k}.png" for k in range(4)]]:
            a = np.array(Image.open(OUT / f).convert("RGBA"))
            m = a[:, :, 3] > 0
            for px in a[m][:, :3]:
                pal.add(tuple(px))
        for i in range(N):
            a = load(f"fx/frame_{i:02d}.png")
            m = a[:, :, 3] > 0
            cols = set(map(tuple, a[m][:, :3]))
            self.assertTrue(cols <= pal, f"frame {i}: {cols - pal}")
        # alpha des voiles : 0 ou 150 uniquement
        for f in ["fx/voile0.png", "fx/voile1.png", "fx/voile2.png"]:
            a = np.array(Image.open(OUT / f).convert("RGBA"))
            self.assertTrue(set(np.unique(a[:, :, 3])) <= {0, 150}, f)

    def test_recomposition(self):
        comp = load("composite.png")
        acc = load("L00_sol.png").copy()
        for f in ["L01_parois.png", "L03_bouche.png", "L02_props.png"]:
            lay = load(f)
            m = lay[:, :, 3:4] > 0
            acc = np.where(m, lay, acc)
        self.assertTrue(np.array_equal(acc, comp))

    def test_chemin_sud_bouche(self):
        l01, l03, l02 = (load("L01_parois.png"), load("L03_bouche.png"),
                         load("L02_props.png"))
        walk = (l01[:, :, 3] == 0) & (l03[:, :, 3] == 0) & (l02[:, :, 3] == 0)
        lab, _ = label(walk)
        start, goal = lab[282, 205], lab[100, 205]
        self.assertGreater(start, 0)
        self.assertEqual(start, goal, "pas de chemin sud -> bouche")
        # largeur minimale du corridor : le run contenant x=205 fait >= 24 px
        for y in range(100, 283, 4):
            row = walk[y]
            if not row[205]:
                continue
            x0 = 205
            while x0 > 0 and row[x0 - 1]:
                x0 -= 1
            x1 = 205
            while x1 < 407 and row[x1 + 1]:
                x1 += 1
            self.assertGreaterEqual(x1 - x0, 24, f"ligne {y}")


if __name__ == "__main__":
    unittest.main()
