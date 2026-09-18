import unittest, json, hashlib
import numpy as np
from PIL import Image
from . import build as b

class GuideCouchesV14Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ciel = np.array(Image.open(b.O / 'couches/ciel_fixe.png'))
        cls.etoiles = np.array(Image.open(b.O / 'couches/etoiles_fixes.png'))
        cls.terrain = np.array(Image.open(b.O / 'couches/terrain_fixe.png'))
        cls.frames = [np.array(Image.open(b.O / 'couches/aurore' / f'AuroreEleganteV14_frame_{f:02d}.png')) for f in range(b.T)]
        cls.guide = np.array(Image.open(b.GUIDE).convert('RGB'))

    def test_guide_copie(self):
        self.assertEqual((b.O / 'guide/layout_guide.png').read_bytes(), b.GUIDE.read_bytes())

    def test_calques_disjoints_recomposent_exactement(self):
        masques = [(c[:, :, 3] > 0) for c in (self.ciel, self.etoiles, self.terrain, self.frames[0])]
        tous = np.zeros(masques[0].shape, bool)
        for m in masques:
            self.assertTrue(not (tous & m).any())
            tous |= m
        self.assertTrue(tous.all())
        rec = np.zeros_like(self.guide)
        for c in (self.ciel, self.etoiles, self.frames[0], self.terrain):
            k = c[:, :, 3] > 0
            rec[k] = c[:, :, :3][k]
        np.testing.assert_array_equal(rec, self.guide)

    def test_cristaux_sombres_dans_terrain(self):
        lum = self.guide.astype(float).mean(axis=2)
        sat = self.guide.max(axis=2).astype(int) - self.guide.min(axis=2).astype(int)
        au = self.frames[0][:, :, 3] > 0
        sombres = au & (lum < 55) & (sat > 80)
        self.assertEqual(int(sombres.sum()), 0, 'cristaux sombres encore dans l aurore')

    def test_frame0_couleurs_exactes(self):
        k = self.frames[0][:, :, 3] > 0
        np.testing.assert_array_equal(self.frames[0][:, :, :3][k], self.guide[k])

    def test_15_frames_geometrie_fixe_boucle(self):
        self.assertEqual(len(self.frames), 15)
        m0 = self.frames[0][:, :, 3] > 0
        for f in self.frames[1:]:
            np.testing.assert_array_equal(f[:, :, 3] > 0, m0)
        # design et texture : les differences de teintes sont en place (toutes frames differentes)
        diffs = [np.mean(np.abs(self.frames[i][:, :, :3].astype(int) - self.frames[(i + 1) % 15][:, :, :3].astype(int))[m0]) for i in range(15)]
        self.assertTrue(all(d > 0.5 for d in diffs), 'frames identiques')

    def test_mouvement_harmonieux_progressif(self):
        # pas adjacent petit (interpolation douce) et bien plus petit qu un grand saut
        m0 = self.frames[0][:, :, 3] > 0
        pas = np.mean(np.abs(self.frames[3][:, :, :3].astype(int) - self.frames[4][:, :, :3].astype(int))[m0])
        saut = np.mean(np.abs(self.frames[0][:, :, :3].astype(int) - self.frames[7][:, :, :3].astype(int))[m0])
        self.assertLess(pas, saut / 2)
        self.assertLess(pas, 10.0)

    def test_aurore_independante(self):
        au = self.frames[0][:, :, 3] > 0
        self.assertEqual(int((self.ciel[:, :, 3] > 0)[au].sum()), 0)
        self.assertEqual(int((self.etoiles[:, :, 3] > 0)[au].sum()), 0)

    def test_scene_recomposee(self):
        s = Image.fromarray(self.ciel, 'RGBA').copy()
        s.alpha_composite(Image.fromarray(self.etoiles, 'RGBA'))
        s.alpha_composite(Image.fromarray(self.frames[5], 'RGBA'))
        s.alpha_composite(Image.fromarray(self.terrain, 'RGBA'))
        np.testing.assert_array_equal(np.array(s), np.array(Image.open(b.O / 'scene/scene_05.png')))

    def test_webp_gif_manifest(self):
        with Image.open(b.O / 'aurore_elegante_15frames.webp') as im:
            self.assertEqual(im.n_frames, 15)
        total = 0
        with Image.open(b.O / 'review/scene_15frames.gif') as im:
            self.assertEqual(im.n_frames, 15)
            for i in range(15):
                im.seek(i); total += im.info.get('duration', 0)
        self.assertEqual(total, 1800)
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertEqual(hashlib.sha256(b.GUIDE.read_bytes()).hexdigest(), m['guide']['sha256'])

if __name__ == '__main__':
    unittest.main()
