"""10 tests du lot aride finale magenta V3."""
import json
import unittest
import zipfile
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
OUT = R / 'renders' / 'aride_finale_magenta_v3'
LAYERS = ['L00_sol', 'L01_chemin', 'L02_cliff', 'L03_roches', 'L04_arbres', 'L05_ombres']


def pal_native():
    a = np.array(Image.open(R / 'entrancearidedungeonpmdsky.png').convert('RGB')).reshape(-1, 3)
    return {tuple(c) for c in np.unique(a, axis=0)}


class T(unittest.TestCase):
    def test_01_tailles_grille(self):
        for k in LAYERS + ['composite']:
            im = Image.open(OUT / f'{k}.png')
            self.assertEqual(im.size, (408, 288), k)
            self.assertEqual(im.mode, 'RGBA', k)

    def test_02_zero_magenta(self):
        for k in LAYERS:
            a = np.array(Image.open(OUT / f'{k}.png')).astype(int)
            op = a[:, :, 3] > 0
            mag = (a[:, :, 0] > 200) & (a[:, :, 2] > 200) & (a[:, :, 1] < 120) & op
            self.assertEqual(int(mag.sum()), 0, k)

    def test_03_palette_native(self):
        pal = pal_native()
        self.assertEqual(len(pal), 99)
        for k in LAYERS:
            a = np.array(Image.open(OUT / f'{k}.png'))
            op = a[:, :, 3] > 0
            cols = {tuple(c) for c in np.unique(a[:, :, :3][op].reshape(-1, 3), axis=0)}
            self.assertTrue(cols <= pal, f'{k}: {len(cols - pal)} couleurs hors palette')

    def test_04_rgb_zero_sous_alpha(self):
        for k in LAYERS:
            a = np.array(Image.open(OUT / f'{k}.png'))
            tr = a[:, :, 3] == 0
            self.assertEqual(int(a[:, :, :3][tr].sum()), 0, k)

    def test_05_recomposition_exacte(self):
        man = json.loads((OUT / 'manifest.json').read_text())
        base = Image.open(OUT / f"{man['ordre'][0]}.png")
        for k in man['ordre'][1:]:
            base.alpha_composite(Image.open(OUT / f'{k}.png'))
        ref = Image.open(OUT / 'composite.png')
        self.assertTrue(np.array_equal(np.array(base), np.array(ref)))

    def test_06_bouche(self):
        man = json.loads((OUT / 'manifest.json').read_text())
        x0, y0, x1, y1 = man['bouche_bbox']
        a = np.array(Image.open(OUT / 'L02_cliff.png')).astype(int)
        zone = a[y0:y1, x0:x1]
        lum = zone[:, :, :3].sum(axis=2)
        dark = ((lum < 200) & (zone[:, :, 3] > 0)).sum()
        self.assertGreater(dark, 300)
        self.assertLess(y0, 140)  # bouche au nord

    def test_07_acces_sud_bouche(self):
        from build import flood, mouth_door
        L00 = np.array(Image.open(OUT / 'L00_sol.png'))
        L02 = np.array(Image.open(OUT / 'L02_cliff.png'))
        man = json.loads((OUT / 'manifest.json').read_text())
        walk = (L00[:, :, 3] > 0) & ~((L02[:, :, 3] > 0) & ~mouth_door(L02, man['bouche_bbox']))
        seen = flood(walk, (204, 284))
        gx = (man['bouche_bbox'][0] + man['bouche_bbox'][2]) // 2
        self.assertTrue(seen[man['bouche_bbox'][3] + 2, gx])
        # corridor minimal : au moins 40 px de large a y=150
        self.assertGreaterEqual(int(walk[150].sum()), 40)

    def test_08_sprites_au_sol_hors_bouche(self):
        man = json.loads((OUT / 'manifest.json').read_text())
        L02 = np.array(Image.open(OUT / 'L02_cliff.png'))[:, :, 3] > 0
        L00 = np.array(Image.open(OUT / 'L00_sol.png'))[:, :, 3] > 0
        x0, y0, x1, y1 = man['bouche_bbox']
        for k in ['L03_roches', 'L04_arbres']:
            a = np.array(Image.open(OUT / f'{k}.png'))[:, :, 3] > 0
            self.assertFalse(a[y0:y1, x0:x1].any(), f'{k} sur la bouche')
        # pieds des 4 arbres et 2 blocs sur du sable (pas sur la roche)
        for name, (x, y) in man['placements'].items():
            if name.startswith('caillou'):
                continue
            spr = np.array(Image.open(OUT / 'sprites' / f'{name}.png'))[:, :, 3] > 0
            fy = min(y + spr.shape[0] - 1, 287)
            fx = min(max(x + spr.shape[1] // 2, 0), 407)
            self.assertTrue(L00[fy, fx], f'{name} pied hors sol')

    def test_09_sprites_fichiers(self):
        files = list((OUT / 'sprites').glob('*.png'))
        self.assertGreaterEqual(len(files), 12)
        for f in files:
            a = np.array(Image.open(f))
            self.assertGreater(int((a[:, :, 3] > 0).sum()), 0, f.name)

    def test_10_pack_complet(self):
        ora = OUT / 'aride_finale_magenta_v3.ora'
        self.assertTrue(ora.exists())
        zf = zipfile.ZipFile(ora)
        self.assertIn('stack.xml', zf.namelist())
        lay = [n for n in zf.namelist() if n.startswith('data/layer')]
        self.assertEqual(len(lay), 6)
        zp = R / 'renders' / 'aride_finale_magenta_v3_pack.zip'
        self.assertTrue(zp.exists())
        names = zipfile.ZipFile(zp).namelist()
        for k in LAYERS:
            self.assertTrue(any(k in n for n in names), k)


if __name__ == '__main__':
    unittest.main()
