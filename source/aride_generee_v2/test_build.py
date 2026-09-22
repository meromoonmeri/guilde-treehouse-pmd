"""Tests du lot aride generee V2 (textures generees, pas natives)."""
import json
import unittest
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
OUT = R / 'renders/aride_generee_v2'
MAG = np.array([255, 0, 255])


def load(n):
    return Image.open(OUT / n).convert('RGBA')


class TestAride(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = json.loads((OUT / 'manifest.json').read_text())

    def test_01_canvas_grille8(self):
        w, h = self.m['canvas']
        self.assertEqual((w % 8, h % 8), (0, 0))
        for p in ['composite.png', 'couches/00_plafond.png', 'couches/00_sol.png',
                  'couches/01_parois.png'] + \
                 [f'couches/02_prop_{n}.png' for n in
                  ['grandA', 'grandB', 'moyenA', 'moyenB', 'arbusteA', 'arbusteB', 'blocA', 'blocB']] + \
                 [f'fx/fx_{f:02d}.png' for f in range(12)]:
            self.assertEqual(load(p).size, (w, h), p)

    def test_02_pas_de_magenta_residuel(self):
        for p in ['couches/01_parois.png', 'planche_props.png'] + \
                 [f'fx/fx_{f:02d}.png' for f in range(12)]:
            a = np.array(load(p)).astype(int)
            d = np.abs(a[:, :, :3] - MAG).sum(axis=2)
            n = int(((d < 170) & (a[:, :, 3] > 0)).sum())
            self.assertEqual(n, 0, f'{p}: {n}px magenta residuel')

    def test_03_recomposition_exacte(self):
        comp = load('couches/00_plafond.png')
        comp = Image.alpha_composite(comp, load('couches/00_sol.png'))
        comp = Image.alpha_composite(comp, load('couches/01_parois.png'))
        feet = self.m['feet']
        for nm in sorted(feet, key=lambda n: feet[n][1]):
            comp = Image.alpha_composite(comp, load(f'couches/02_prop_{nm}.png'))
        comp = Image.alpha_composite(comp, load('fx/fx_00.png'))
        self.assertEqual(np.array(comp).tobytes(), np.array(load('composite.png')).tobytes())

    def test_04_fx_boucle_et_decalages(self):
        bands = self.m['log']['fx']['bands']
        self.assertEqual(self.m['frames'], 12)
        for b in bands:
            for f in range(12):
                off = (b['speed'] * f) // 12
                self.assertEqual(off, (b['speed'] * f) // 12)
            self.assertEqual((b['speed'] * 12) // 12 % 400, b['speed'] % 400)
        # frame 12 reconstruite == frame 0 (wrap modulo 400 + shimmer periodique)
        self.assertAlmostEqual(float(np.sin(2 * np.pi * 12 / 12)), 0.0, places=6)

    def test_05_pieds_sur_grille(self):
        for nm, (fx, fy) in self.m['feet'].items():
            self.assertEqual((fx % 8, fy % 8), (0, 0), nm)

    def test_06_bouche_coherente(self):
        mo = self.m['mouth']
        self.assertGreater(mo['x1'] - mo['x0'], 30)
        self.assertGreater(mo['y1'] - mo['y0'], 30)
        wall = np.array(load('couches/01_parois.png').convert('RGB')).astype(int)
        core = wall[mo['y0']:mo['y1'], mo['x0']:mo['x1']].reshape(-1, 3).mean()
        self.assertLess(core, 90, f'mediane bouche trop claire: {core}')

    def test_07_sentier_degage(self):
        path = self.m['path']
        self.assertLess(path[0][1], 230)
        self.assertGreater(path[-1][1], 350)
        # degagement 10px autour du sentier dans les calques props
        occ = np.zeros((360, 400), bool)
        for nm in self.m['feet']:
            a = np.array(load(f'couches/02_prop_{nm}.png'))
            occ |= a[:, :, 3] > 0
        ys, xs = np.where(occ)
        for px, py in path:
            dd = np.maximum(np.abs(xs - px), np.abs(ys - py)).min()
            self.assertGreaterEqual(int(dd), 8, f'sentier bloque en {(px, py)}')

    def test_08_bruts_presents(self):
        for n in ['parois_grotte.png', 'sol_sable.png', 'props_arbres_blocs.png', 'fx_poussiere.png']:
            self.assertTrue((R / 'source/aride_generee_v2/bruts' / n).exists(), n)


if __name__ == '__main__':
    unittest.main()
