import unittest, json, hashlib
import numpy as np
from PIL import Image
from . import build as b

class OndeBorealeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.master = np.array(Image.open(b.O / 'rideau_master_extrait.png'))
        cls.couches = [np.array(Image.open(b.O / 'couches' / f'OndeBorealeV9_frame_{t:02d}.png')) for t in range(b.T)]

    def test_master_extrait_propre(self):
        self.assertEqual(self.master.shape, (256, 768, 4))
        self.assertGreater((self.master[:, :, 3] > 128).sum(), 40000)
        semi = (self.master[:, :, 3] > 60) & (self.master[:, :, 3] < 200)
        rgb = self.master[:, :, :3].astype(float)
        pale = semi & (rgb.mean(axis=2) > 170) & ((rgb.max(axis=2) - rgb.min(axis=2)) < 60)
        self.assertLess(int(pale.sum()), 2000, 'voile/gris parasite')

    def test_10_couches_768x256(self):
        self.assertEqual(len(self.couches), 10)
        for c in self.couches:
            self.assertEqual(c.shape, (256, 768, 4))

    def test_onde_transversale_pure_colonne_par_colonne(self):
        """Physique : chaque colonne x de la frame t = colonne x du master decalee de round(decalage)."""
        for t in (1, 4, 7):
            for x in range(0, 768, 13):
                d = int(round(b.decalage(x, t) * b.amplitude(x)))
                col_m = self.master[:, x, :]
                col_f = self.couches[t][:, x, :]
                if d > 0:
                    np.testing.assert_array_equal(col_f[d:], col_m[:256 - d])
                    np.testing.assert_array_equal(col_f[:d], np.zeros((d, 4), 'uint8'))
                elif d < 0:
                    np.testing.assert_array_equal(col_f[:256 + d], col_m[-d:])
                    np.testing.assert_array_equal(col_f[256 + d:], np.zeros((-d, 4), 'uint8'))
                else:
                    np.testing.assert_array_equal(col_f, col_m)

    def test_boucle_exacte_frame10_egale_frame0(self):
        f10 = b.couche_deplacee(Image.fromarray(self.master), 10)
        f0 = b.couche_deplacee(Image.fromarray(self.master), 0)
        np.testing.assert_array_equal(np.array(f10), np.array(f0))
        np.testing.assert_array_equal(np.array(f0), self.couches[0])

    def test_aucune_translation_horizontale_de_masse(self):
        centres = []
        for c in self.couches:
            w = c[:, :, 3].astype(float)
            centres.append((w.sum(axis=0) * np.arange(768)).sum() / w.sum())
        self.assertLess(np.std(centres), 1.0)

    def test_couverture_sur_toute_la_largeur(self):
        for c in self.couches:
            colonnes = np.where((c[:, :, 3] > 40).any(axis=0))[0]
            self.assertLessEqual(colonnes.min(), 2)
            self.assertGreaterEqual(colonnes.max(), 765)

    def test_scene_recomposee_exactement(self):
        ciel = Image.open(b.O / 'contexte/ciel_genere.png').convert('RGBA')
        ciel.alpha_composite(Image.open(b.O / 'contexte/etoiles.png').convert('RGBA'))
        glace = Image.open(b.O / 'contexte/glace_laterale.png').convert('RGBA')
        terrain = Image.open(b.O / 'contexte/terrain.png').convert('RGBA')
        rec = b.scene_composee(3, ciel, [Image.fromarray(c) for c in self.couches], glace, terrain)
        np.testing.assert_array_equal(np.array(Image.open(b.O / 'scene/scene_03.png').convert('RGBA')), np.array(rec))

    def test_contexte_byte_identique(self):
        paires = {'ciel_genere': b.V8 / 'AreneLargeV3_00_ciel_genere.png', 'etoiles': b.V8 / 'AreneLargeV3_00b_etoiles.png',
                  'glace_laterale': b.V8 / 'V8_glace_laterale_arriere_plan.png', 'terrain': b.V8 / 'AreneLargeV3_02_sol_visible.png'}
        for nom, src in paires.items():
            self.assertEqual((b.O / 'contexte' / f'{nom}.png').read_bytes(), src.read_bytes())

    def test_webp_et_gifs(self):
        with Image.open(b.O / 'onde_boreale_10frames.webp') as im:
            self.assertEqual(im.n_frames, 10)
            im.seek(6)
            a = np.array(im.convert('RGBA')); a[a[:, :, 3] == 0] = 0
            np.testing.assert_array_equal(a, self.couches[6])
        for g in (b.O / 'review/scene_onde_gif.gif', b.O / 'review/aurore_seule.gif'):
            total = 0
            with Image.open(g) as im:
                self.assertEqual(im.n_frames, 10)
                for i in range(10):
                    im.seek(i); total += im.info.get('duration', 0)
            self.assertEqual(total, 1600)

    def test_manifest(self):
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertEqual(hashlib.sha256(b.BRUT.read_bytes()).hexdigest(), m['master']['brut_sha256'])
        self.assertEqual(m['onde']['frames'], 10)
        self.assertIn('vertical', m['onde']['physique'])
        self.assertFalse(m['wrap'])

if __name__ == '__main__':
    unittest.main()
