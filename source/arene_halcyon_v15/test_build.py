import unittest, json, hashlib
import numpy as np
from PIL import Image
from . import build as b

class HalcyonV15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.terrain = np.array(Image.open(b.O / 'couches/terrain_fixe.png'))
        cls.frames = [np.array(Image.open(b.O / 'couches/aurore' / f'AuroreV15_{f:02d}.png')) for f in range(b.T)]

    def test_provenance_bruts(self):
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertEqual(hashlib.sha256(b.BRUT_T.read_bytes()).hexdigest(), m['bruts_sha256']['terrain'])
        self.assertEqual(hashlib.sha256(b.BRUT_B.read_bytes()).hexdigest(), m['bruts_sha256']['boreale'])

    def test_methode_canonique_terrain(self):
        self.assertEqual(self.terrain.shape, (1152, 928, 4))
        # pas un seul pixel magenta opaque residuel (bande retiree, pointes de pics conservees)
        opaques = self.terrain[self.terrain[:, :, 3] > 128][:, :3].astype(int)
        magenta_res = (opaques[:, 0] > 200) & (opaques[:, 2] > 200) & (opaques[:, 1] < 90)
        self.assertEqual(int(magenta_res.sum()), 0)
        self.assertEqual(int(self.terrain[:50, :, 3].max()), 0)
        self.assertGreater((self.terrain[500:1000, :, 3] > 0).sum(), 100000)

    def test_halcyon_frames_uniformes(self):
        self.assertEqual(len(self.frames), 8)
        for f in self.frames:
            self.assertEqual(f.shape, (256, 768, 4))
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertTrue(m['halcyon']['position_multiple_de_8'])
        self.assertEqual(m['halcyon']['duree_ms_uniforme'], 150)

    def test_ondulation_reelle(self):
        m0 = self.frames[0][:, :, 3] > 128
        # les poses different mais restent le meme rideau (IoU elevee)
        for f in self.frames[1:]:
            mf = f[:, :, 3] > 128
            inter = (mf & m0).sum(); union = (mf | m0).sum()
            self.assertGreater(inter / union, 0.55)
        diffs = [np.mean(self.frames[i][:, :, 3] != self.frames[(i + 1) % 8][:, :, 3]) for i in range(8)]
        self.assertTrue(all(d > 0.02 for d in diffs), 'pas d ondulation')

    def test_sans_ciel_dans_le_calque(self):
        f = self.frames[0]
        self.assertEqual(int(f[:, :4, 3].max()), 0)
        self.assertEqual(int(f[:, -4:, 3].max()), 0)
        self.assertEqual(int(f[:6, :, 3].max()), 0)

    def test_scene_recomposee(self):
        ciel = np.array(Image.open(b.O / 'couches/ciel_fixe.png'))
        et = np.array(Image.open(b.O / 'couches/etoiles_fixes.png'))
        s = Image.fromarray(ciel, 'RGBA').copy()
        s.alpha_composite(Image.fromarray(et, 'RGBA'))
        s.alpha_composite(Image.fromarray(self.frames[2], 'RGBA'), (b.POS_X, b.POS_Y))
        s.alpha_composite(Image.fromarray(self.terrain, 'RGBA'))
        np.testing.assert_array_equal(np.array(s), np.array(Image.open(b.O / 'scene/scene_02.png')))

    def test_webp_gif(self):
        with Image.open(b.O / 'aurore_ondulation_8frames.webp') as im:
            self.assertEqual(im.n_frames, 8)
        total = 0
        with Image.open(b.O / 'review/scene_ondulation.gif') as im:
            self.assertEqual(im.n_frames, 8)
            for i in range(8):
                im.seek(i); total += im.info.get('duration', 0)
        self.assertEqual(total, 1200)

    def test_manifest(self):
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertFalse(m['halcyon']['pas_de_wrap'] is False)
        self.assertEqual(m['halcyon']['frames_nommage_uniforme'], 'AuroreV15_00..07.png')

if __name__ == '__main__':
    unittest.main()
