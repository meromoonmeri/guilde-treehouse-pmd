import unittest, json, hashlib
import numpy as np
from PIL import Image
from . import build as b

class GuideCouchesV13Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ciel = np.array(Image.open(b.O / 'couches/ciel_fixe.png'))
        cls.etoiles = np.array(Image.open(b.O / 'couches/etoiles_fixes.png'))
        cls.terrain = np.array(Image.open(b.O / 'couches/terrain_fixe.png'))
        cls.frames = [np.array(Image.open(b.O / 'couches/aurore' / f'AuroreGuideV13_frame_{f:02d}.png')) for f in range(b.T)]

    def test_guide_copie(self):
        self.assertEqual((b.O / 'guide/layout_guide.png').read_bytes(), b.GUIDE.read_bytes())

    def test_calques_disjoints_recomposent_le_guide(self):
        guide = np.array(Image.open(b.GUIDE).convert('RGB'))
        masques = [(c[:, :, 3] > 0) for c in (self.ciel, self.etoiles, self.terrain, self.frames[0])]
        tous = np.zeros(masques[0].shape, bool)
        for m in masques:
            self.assertTrue(not (tous & m).any(), 'chevauchement de calques')
            tous |= m
        self.assertTrue(tous.all())
        recompose = np.zeros_like(guide)
        for c in (self.ciel, self.etoiles, self.frames[0], self.terrain):
            recompose[c[:, :, 3] > 0] = c[:, :, :3][c[:, :, 3] > 0]
        np.testing.assert_array_equal(recompose, guide)

    def test_frame0_egale_aurore_du_guide(self):
        guide = np.array(Image.open(b.GUIDE).convert('RGB'))
        np.testing.assert_array_equal(self.frames[0][:, :, :3][self.frames[0][:, :, 3] > 0], guide[self.frames[0][:, :, 3] > 0])

    def test_8_frames_cycling_geometrie_identique(self):
        self.assertEqual(len(self.frames), 8)
        a0 = self.frames[0][:, :, 3] > 0
        for f in self.frames[1:]:
            np.testing.assert_array_equal(f[:, :, 3] > 0, a0)
        # frame 8 = frame 0 (periode 4 | 8)
        np.testing.assert_array_equal(self.frames[0], self.frames[0])
        diffs = [np.mean(np.any(self.frames[i][:, :, :3] != self.frames[(i + 1) % 8][:, :, :3], axis=2)) for i in range(8)]
        self.assertTrue(all(d > 0.005 for d in diffs), 'pas de cycling')

    def test_aurore_independante_du_ciel(self):
        # le ciel et les etoiles ne contiennent aucun pixel de l'aurore (satures)
        sat_au = self.frames[0][:, :, :3].max(axis=2).astype(int) - self.frames[0][:, :, :3].min(axis=2).astype(int)
        au = self.frames[0][:, :, 3] > 0
        self.assertEqual(int((self.ciel[:, :, 3] > 0)[au].sum()), 0)
        self.assertEqual(int((self.etoiles[:, :, 3] > 0)[au].sum()), 0)
        self.assertGreater(int(sat_au[au].max()), 80)

    def test_scene_recomposee(self):
        s = Image.fromarray(self.ciel, 'RGBA').copy()
        s.alpha_composite(Image.fromarray(self.etoiles, 'RGBA'))
        s.alpha_composite(Image.fromarray(self.frames[2], 'RGBA'))
        s.alpha_composite(Image.fromarray(self.terrain, 'RGBA'))
        np.testing.assert_array_equal(np.array(s), np.array(Image.open(b.O / 'scene/scene_02.png')))

    def test_webp_gif(self):
        with Image.open(b.O / 'aurore_palette_cycle_8frames.webp') as im:
            self.assertEqual(im.n_frames, 8)
        total = 0
        with Image.open(b.O / 'review/scene_guide_animee.gif') as im:
            self.assertEqual(im.n_frames, 8)
            for i in range(8):
                im.seek(i); total += im.info.get('duration', 0)
        self.assertEqual(total, 960)

    def test_manifest(self):
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertTrue(m['frame0_egale_guide'])
        self.assertEqual(hashlib.sha256(b.GUIDE.read_bytes()).hexdigest(), m['guide']['sha256'])

if __name__ == '__main__':
    unittest.main()
