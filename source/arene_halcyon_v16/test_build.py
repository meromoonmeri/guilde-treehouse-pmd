import unittest, json, hashlib
import numpy as np
from PIL import Image
from . import build as b

class HalcyonV16Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.terrain = np.array(Image.open(b.O / 'couches/terrain_fixe.png'))
        cls.frames = [np.array(Image.open(b.O / 'couches/aurore' / f'AuroreV16_{f:02d}.png')) for f in range(b.T)]

    def test_provenance_bruts(self):
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertEqual(hashlib.sha256(b.BRUT_T.read_bytes()).hexdigest(), m['bruts_sha256']['terrain'])
        self.assertEqual(hashlib.sha256(b.BRUT_B.read_bytes()).hexdigest(), m['bruts_sha256']['boreale'])

    def test_sans_trou_central(self):
        # bord sombre du cratere V15 = 5471 px dans la zone centrale ; V16 doit etre < 600
        z = self.terrain[430:670, 230:700]
        lum = z[:, :, :3].astype(float).mean(axis=2)
        sombres = int(((lum < 120) & (z[:, :, 3] > 128)).sum())
        self.assertLess(sombres, 600, 'le trou central est encore present')
        opaques = self.terrain[self.terrain[:, :, 3] > 128][:, :3].astype(int)
        magenta_res = (opaques[:, 0] > 200) & (opaques[:, 2] > 200) & (opaques[:, 1] < 90)
        self.assertEqual(int(magenta_res.sum()), 0, 'magenta residuel opaque')
        self.assertEqual(int(self.terrain[:50, :, 3].max()), 0)

    def test_10_frames_uniformes_halcyon(self):
        self.assertEqual(len(self.frames), 10)
        for f in self.frames:
            self.assertEqual(f.shape, (256, 768, 4))
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertTrue(m['halcyon']['position_multiple_de_8'])
        self.assertEqual(m['halcyon']['duree_ms_uniforme'], 130)
        self.assertEqual(m['halcyon']['frames_nommage_uniforme'], 'AuroreV16_00..09.png')

    def test_ondulation_et_boucle_parfaite(self):
        m0 = self.frames[0][:, :, 3] > 128
        for f in self.frames[1:]:
            mf = f[:, :, 3] > 128
            inter = (mf & m0).sum(); union = (mf | m0).sum()
            self.assertGreater(inter / union, 0.30, 'silhouette trop differente')
        diffs = [np.mean(self.frames[i][:, :, 3] != self.frames[(i + 1) % 10][:, :, 3]) for i in range(10)]
        self.assertTrue(all(d > 0.02 for d in diffs), 'pas d ondulation')
        d97 = np.mean(self.frames[9][:, :, 3] != self.frames[0][:, :, 3])
        self.assertLess(d97, 0.18, 'frame 10 trop loin de frame 1 : boucle ouverte')

    def test_style_reference_et_sans_magenta_cuit(self):
        # aucun magenta opaque dans le calque aurore
        op = self.frames[0][self.frames[0][:, :, 3] > 128][:, :3].astype(int)
        mag = (op[:, 0] > 200) & (op[:, 2] > 200) & (op[:, 1] < 90)
        self.assertLess(mag.mean(), 0.02, 'magenta cuit dans le calque aurore')
        # coeur magenta + liseres cyan presents (style reference)
        cy = (op[:, 1] > op[:, 0] + 40).mean()
        mg = ((op[:, 0] > op[:, 1] + 40) & (op[:, 2] > op[:, 1])).mean()
        self.assertGreater(cy, 0.05)
        self.assertGreater(mg, 0.10)

    def test_scene_recomposee(self):
        ciel = np.array(Image.open(b.O / 'couches/ciel_fixe.png'))
        et = np.array(Image.open(b.O / 'couches/etoiles_fixes.png'))
        s = Image.fromarray(ciel, 'RGBA').copy()
        s.alpha_composite(Image.fromarray(et, 'RGBA'))
        s.alpha_composite(Image.fromarray(self.frames[3], 'RGBA'), (b.POS_X, b.POS_Y))
        s.alpha_composite(Image.fromarray(self.terrain, 'RGBA'))
        np.testing.assert_array_equal(np.array(s), np.array(Image.open(b.O / 'scene/scene_03.png')))

    def test_webp_gif(self):
        with Image.open(b.O / 'aurore_ondulation_10frames.webp') as im:
            self.assertEqual(im.n_frames, 10)
        total = 0
        with Image.open(b.O / 'review/scene_ondulation.gif') as im:
            self.assertEqual(im.n_frames, 10)
            for i in range(10):
                im.seek(i); total += im.info.get('duration', 0)
        self.assertEqual(total, 1300)

if __name__ == '__main__':
    unittest.main()
