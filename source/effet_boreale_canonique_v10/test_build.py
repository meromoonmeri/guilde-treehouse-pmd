import unittest, json, hashlib
import numpy as np
from PIL import Image
from scipy import ndimage
from . import build as b

class EffetBorealeCanoniqueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.effet = np.array(Image.open(b.O / 'effet_canonique_extrait.png'))
        cls.couches = [np.array(Image.open(b.O / 'couches' / f'EffetBorealeV10_frame_{t:02d}.png')) for t in range(b.T)]

    def test_texture_canonique_recuperee(self):
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertEqual(hashlib.sha256(b.CANONIQUE.read_bytes()).hexdigest(), m['texture']['sha256'])

    def test_extrait_sans_ciel_sans_etoiles(self):
        self.assertEqual(self.effet.shape, (288, 528, 4))
        self.assertGreater((self.effet[:, :, 3] > 0).sum(), 40000)
        # aucun ciel bake : sous le seuil de luminosite le ciel canonique (lum~21) n'apparait pas opaque
        opaques = self.effet[self.effet[:, :, 3] > 200][:, :3].astype(float)
        self.assertGreater((opaques.mean(axis=1) > 60).mean(), 0.75, 'trop de pixels sombres opaques (ciel bake ?)')
        # aucune etoile residuelle : point visible peu sature loin d'un ruban sature
        sat = self.effet[:, :, :3].max(axis=2).astype(int) - self.effet[:, :, :3].min(axis=2).astype(int)
        noyau = (self.effet[:, :, 3] >= 100) & (sat >= 70)
        dist = ndimage.distance_transform_edt(~noyau)
        self.assertEqual(int(((self.effet[:, :, 3] >= 100) & (sat < 50) & (dist > 10)).sum()), 0)
        # bas du calque : fondu progressif vers zero (nuages/pics exclus, pas de coupe brutale)
        self.assertEqual(int(self.effet[-2:, :, 3].max()), 0)
        self.assertLess(int(self.effet[274:280, :, 3].max()), 240)
        self.assertGreater(int(self.effet[258:264, :, 3].max()), 200)

    def test_10_couches(self):
        self.assertEqual(len(self.couches), 10)
        for c in self.couches:
            self.assertEqual(c.shape, (288, 528, 4))

    def test_onde_transversale_colonne_par_colonne(self):
        for t in (1, 4, 7):
            for x in range(0, 528, 11):
                d = int(round(b.decalage(x, t) * b.enveloppe(x)))
                col_e = self.effet[:, x, :]
                col_f = self.couches[t][:, x, :]
                if d > 0:
                    np.testing.assert_array_equal(col_f[d:], col_e[:288 - d])
                    np.testing.assert_array_equal(col_f[:d], np.zeros((d, 4), 'uint8'))
                elif d < 0:
                    np.testing.assert_array_equal(col_f[:288 + d], col_e[-d:])
                    np.testing.assert_array_equal(col_f[288 + d:], np.zeros((-d, 4), 'uint8'))
                else:
                    np.testing.assert_array_equal(col_f, col_e)

    def test_boucle_exacte(self):
        f10 = np.array(b.couche_deplacee(Image.fromarray(self.effet), 10))
        f0 = np.array(b.couche_deplacee(Image.fromarray(self.effet), 0))
        np.testing.assert_array_equal(f10, f0)
        np.testing.assert_array_equal(f0, self.couches[0])

    def test_aucune_translation_de_masse(self):
        centres = []
        for c in self.couches:
            w = c[:, :, 3].astype(float)
            centres.append((w.sum(axis=0) * np.arange(528)).sum() / w.sum())
        self.assertLess(np.std(centres), 1.0)

    def test_scene_recomposee_et_contexte_intacts(self):
        for nom, src in {'ciel_genere': b.V8 / 'AreneLargeV3_00_ciel_genere.png', 'etoiles': b.V8 / 'AreneLargeV3_00b_etoiles.png',
                         'glace_laterale': b.V8 / 'V8_glace_laterale_arriere_plan.png', 'terrain': b.V8 / 'AreneLargeV3_02_sol_visible.png'}.items():
            self.assertEqual((b.O / 'contexte' / f'{nom}.png').read_bytes(), src.read_bytes())
        ciel = Image.open(b.O / 'contexte/ciel_genere.png').convert('RGBA')
        ciel.alpha_composite(Image.open(b.O / 'contexte/etoiles.png').convert('RGBA'))
        rec = b.scene_composee(3, ciel, [Image.fromarray(c) for c in self.couches],
                               Image.open(b.O / 'contexte/glace_laterale.png').convert('RGBA'),
                               Image.open(b.O / 'contexte/terrain.png').convert('RGBA'))
        np.testing.assert_array_equal(np.array(Image.open(b.O / 'scene/scene_03.png').convert('RGBA')), np.array(rec))

    def test_webp_et_gifs(self):
        with Image.open(b.O / 'effet_boreale_canonique_10frames.webp') as im:
            self.assertEqual(im.n_frames, 10)
            for t in (0, 3, 7, 9):
                im.seek(t)
                a = np.array(im.convert('RGBA')); a[a[:, :, 3] == 0] = 0
                np.testing.assert_array_equal(a, self.couches[t])
        for g in (b.O / 'review/scene_effet_gif.gif', b.O / 'review/effet_seul.gif'):
            total = 0
            with Image.open(g) as im:
                self.assertEqual(im.n_frames, 10)
                for i in range(10):
                    im.seek(i); total += im.info.get('duration', 0)
            self.assertEqual(total, 1600)

    def test_manifest(self):
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertEqual(m['onde']['frames'], 10)
        self.assertIn('vertical', m['onde']['physique'])
        self.assertFalse(m['wrap'])
        self.assertIn('recuperee', m['texture']['source'])

if __name__ == '__main__':
    unittest.main()
