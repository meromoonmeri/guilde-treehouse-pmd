import unittest, json, hashlib
import numpy as np
from PIL import Image
from . import build as b

class BorealeSuiteV11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.poses = [np.array(Image.open(b.O / 'poses' / f'pose_{i:02d}.png')) for i in range(b.POSES)]
        cls.couches = [np.array(Image.open(b.O / 'couches' / f'BorealeSuiteV11_frame_{t:02d}.png')) for t in range(b.T)]

    def test_provenance_planche_generee(self):
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertEqual(hashlib.sha256(b.BRUT.read_bytes()).hexdigest(), m['planche']['brut_sha256'])
        self.assertEqual(m['planche']['poses_dessinees'], 8)
        self.assertIn('canonique', m['planche']['generee_avec'][0])
        self.assertIn('harmonisation', m['planche']['generee_avec'][1])

    def test_8_poses_16_etapes(self):
        self.assertEqual(len(self.poses), 8)
        self.assertEqual(len(self.couches), 16)
        for c in self.couches:
            self.assertEqual(c.shape, (300, 768, 4))

    def test_positions_verrouillees_subtilite(self):
        boites = []
        for p in self.poses:
            ys, xs = np.where(p[:, :, 3] > 128)
            boites.append((xs.min(), ys.min(), xs.max(), ys.max()))
        for axe in range(4):
            coords = [b_[axe] for b_ in boites]
            self.assertLess(max(coords) - min(coords), 18, 'rubans redeplaces entre poses')
        # les poses different quand meme (shimmer/coeurs)
        canevas = [b.canevas_pose(p) for p in self.poses]
        diffs = [np.abs(np.array(canevas[i])[:, :, 3].astype(int) - np.array(canevas[(i + 1) % 8])[:, :, 3].astype(int)).mean() for i in range(8)]
        self.assertGreater(max(diffs), 0.5)

    def test_fondus_50_pourcent(self):
        for etape in (1, 5, 9, 13):
            k = etape // 2
            A = np.array(b.canevas_pose(self.poses[k])).astype(float)
            B = np.array(b.canevas_pose(self.poses[(k + 1) % 8])).astype(float)
            cible = (A[:, :, 3] + B[:, :, 3]) / 2
            np.testing.assert_allclose(self.couches[etape][:, :, 3].astype(float), cible, atol=2)

    def test_boucle_exacte_16(self):
        canevas = [b.canevas_pose(p) for p in self.poses]
        frames = b.frames_suite(canevas)
        np.testing.assert_array_equal(np.array(frames[16 % 16]), self.couches[0])
        np.testing.assert_array_equal(np.array(frames[0]), self.couches[0])

    def test_bords_propres_sans_fond_magenta(self):
        for c in [self.couches[0]] + self.couches[1:16:5]:
            self.assertEqual(int(c[:, :3, 3].max()), 0)
            self.assertEqual(int(c[:, -3:, 3].max()), 0)
            opaques = c[c[:, :, 3] == 255][:, :3].astype(float)
            d = np.linalg.norm(opaques - np.array([255.0, 0.0, 255.0]), axis=1)
            self.assertLess((d < 30).mean(), 0.02, 'magenta de fond opaque residuel')

    def test_scene_recomposee_et_contexte_intacts(self):
        for nom, src in {'ciel_genere': b.V8 / 'AreneLargeV3_00_ciel_genere.png', 'etoiles': b.V8 / 'AreneLargeV3_00b_etoiles.png',
                         'glace_laterale': b.V8 / 'V8_glace_laterale_arriere_plan.png', 'terrain': b.V8 / 'AreneLargeV3_02_sol_visible.png'}.items():
            self.assertEqual((b.O / 'contexte' / f'{nom}.png').read_bytes(), src.read_bytes())
        ciel = Image.open(b.O / 'contexte/ciel_genere.png').convert('RGBA')
        ciel.alpha_composite(Image.open(b.O / 'contexte/etoiles.png').convert('RGBA'))
        rec = b.scene_composee(4, ciel, [Image.fromarray(c) for c in self.couches],
                               Image.open(b.O / 'contexte/glace_laterale.png').convert('RGBA'),
                               Image.open(b.O / 'contexte/terrain.png').convert('RGBA'))
        np.testing.assert_array_equal(np.array(Image.open(b.O / 'scene/scene_04.png').convert('RGBA')), np.array(rec))

    def test_webp_et_gifs(self):
        with Image.open(b.O / 'boreale_suite_16frames.webp') as im:
            self.assertEqual(im.n_frames, 16)
            for t in (0, 4, 9, 15):
                im.seek(t)
                a = np.array(im.convert('RGBA')); a[a[:, :, 3] == 0] = 0
                np.testing.assert_array_equal(a, self.couches[t])
        for g in (b.O / 'review/scene_suite_gif.gif', b.O / 'review/suite_seule.gif'):
            total = 0
            with Image.open(g) as im:
                self.assertEqual(im.n_frames, 16)
                for i in range(16):
                    im.seek(i); total += im.info.get('duration', 0)
            self.assertEqual(total, 1920)

    def test_manifest(self):
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertEqual(m['suite']['etapes'], 16)
        self.assertEqual(m['suite']['cycle_s'], 1.92)
        self.assertFalse(m['wrap'])

if __name__ == '__main__':
    unittest.main()
