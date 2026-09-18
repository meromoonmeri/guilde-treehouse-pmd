import unittest, json, hashlib
import numpy as np
from PIL import Image
from . import build as b

class OndulationGlaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.poses = [np.array(Image.open(b.O / 'aurore/poses' / f'pose_{i:02d}.png')) for i in range(b.POSES)]
        cls.frames = [np.array(Image.open(b.O / 'aurore/frames' / f'AuroreOndulationV8_{t:03d}.png')) for t in range(b.T)]
        cls.gl = np.array(Image.open(b.O / 'calques/V8_glace_laterale_arriere_plan.png'))

    def test_8_poses_extraites_du_brut(self):
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertEqual(hashlib.sha256(b.BRUT_AURORE.read_bytes()).hexdigest(), m['aurore']['brut_sha256'])
        self.assertEqual(hashlib.sha256(b.BRUT_GLACE.read_bytes()).hexdigest(), m['glace']['brut_sha256'])
        for p in self.poses:
            self.assertEqual(p.shape, (256, 768, 4))
        self.assertTrue(all(np.any(p[:, :, 3] > 200) for p in self.poses))

    def test_poses_ondulent_sans_translation(self):
        g = [np.where((p[:, :, 3] > 128).any(axis=0))[0] for p in self.poses]
        self.assertTrue(all(len(x) > 700 for x in g))
        centres = [x.mean() for x in g]
        self.assertLess(max(centres) - min(centres), 60)

    def test_frames_fondus_premultiplies(self):
        self.assertEqual(len(self.frames), 32)
        for t in (0, 2, 9, 17, 25, 31):
            k, frac = t // 4, (t % 4) / 4
            p0, p1 = self.poses[k], self.poses[(k + 1) % 8]
            a = self.frames[t][:, :, 3].astype(float)
            cible = (1 - frac) * p0[:, :, 3] + frac * p1[:, :, 3]
            np.testing.assert_allclose(a, cible, atol=1.5)

    def test_boucle_fermee_32(self):
        np.testing.assert_array_equal(self.frames[0], np.array(Image.open(b.O / 'aurore/frames/AuroreOndulationV8_000.png')))
        # frame 32 = frame 0 : le dernier fondu pose7->pose0 (s=3) vaut 25 % pose 7 + 75 % pose 0,
        # tres proche de la frame 0 (pose 0 pure) : la boucle se referme en 32 etapes
        p7, p0 = self.poses[7].astype(float), self.poses[0].astype(float)
        a = self.frames[31][:, :, 3].astype(float)
        np.testing.assert_allclose(a, 0.25 * p7[:, :, 3] + 0.75 * p0[:, :, 3], atol=1.5)
        rgb = self.frames[31][:, :, :3].astype(float)
        denom = (0.25 * p7[:, :, 3] + 0.75 * p0[:, :, 3])[:, :, None]
        cible = (0.25 * p7[:, :, :3] * p7[:, :, 3:4] + 0.75 * p0[:, :, :3] * p0[:, :, 3:4]) / np.maximum(denom, 1e-6)
        masque = self.frames[31][:, :, 3] > 0
        np.testing.assert_allclose(rgb[masque], cible[masque], atol=1.5)

    def test_glace_remplit_les_cotes(self):
        # colonnes exterieures opaques en bas de couche (parois), vide en haut (ciel)
        self.assertGreater((self.gl[:120, :, 3] > 0).sum(), 0)
        bas_gauche = self.gl[300:512, :100, 3]
        bas_droite = self.gl[300:512, -100:, 3]
        self.assertGreater(np.mean(bas_gauche > 128), 0.9)
        self.assertGreater(np.mean(bas_droite > 128), 0.9)
        haut = self.gl[:40, 100:668, 3]
        self.assertLess(np.mean(haut > 0), 0.25)

    def test_scene_recomposee_exactement(self):
        ciel = Image.open(b.V3 / 'calques/AreneLargeV3_00_ciel_genere.png').convert('RGBA')
        ciel.alpha_composite(Image.open(b.V3 / 'calques/AreneLargeV3_00b_etoiles.png').convert('RGBA'))
        terrain = Image.open(b.V3 / 'review/terrain_detoure.png').convert('RGBA')
        recomposee = b.scene_composee(8, ciel, [Image.fromarray(f) for f in self.frames], Image.fromarray(self.gl), terrain)
        np.testing.assert_array_equal(np.array(Image.open(b.O / 'review/scene_008.png').convert('RGBA')), np.array(recomposee))

    def test_calques_V3_intacts(self):
        for p in (b.O / 'calques').glob('*.png'):
            if p.name != 'V8_glace_laterale_arriere_plan.png':
                self.assertEqual(p.read_bytes(), (b.V3 / 'calques' / p.name).read_bytes())

    def test_webp_32_fidele(self):
        with Image.open(b.O / 'aurore/ondulation_32frames.webp') as im:
            self.assertEqual(im.n_frames, 32)
            for t in (0, 5, 12, 27, 31):
                im.seek(t)
                a = np.array(im.convert('RGBA')); a[a[:, :, 3] == 0] = 0
                np.testing.assert_array_equal(a, self.frames[t])

    def test_gif_32_frames_boucle(self):
        total = 0
        with Image.open(b.O / 'review/scene_ondulation_glace.gif') as im:
            self.assertEqual(im.n_frames, 32)
            for i in range(32):
                im.seek(i); total += im.info.get('duration', 0)
        # le format GIF encode des centisecondes : 125 ms sont arrondies a 120 ms (cycle GIF 3,84 s)
        self.assertEqual(total, 3840)

    def test_manifest_complet(self):
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertEqual(m['aurore']['etapes'], 32)
        self.assertEqual(m['aurore']['cycle_s'], 4.0)
        self.assertFalse(m['wrap'])
        self.assertIn('pas de translation horizontale', m['aurore']['methode'])

if __name__ == '__main__':
    unittest.main()
