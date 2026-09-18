import unittest, json, hashlib
import numpy as np
from PIL import Image
from . import build as b

class CielPmdskyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref = np.array(Image.open(b.REF_PATH).convert('RGB'))
        cls.ciel = [np.array(Image.open(b.O / 'ciel/frames' / f'CielPmdskyV7_{t:03d}.png')) for t in range(b.T)]
        cls.ov = [np.array(Image.open(b.O / 'overlay/frames' / f'OverlayPmdskyV7_{t:03d}.png')) for t in range(b.T)]
        cls.mnorm = b.modulations()

    def test_frame0_est_la_reference_exacte(self):
        np.testing.assert_array_equal(self.ciel[0], self.ref)

    def test_aucun_deplacement_hors_zone_aurore(self):
        for t in range(b.T):
            diff = np.any(self.ciel[t] != self.ref, axis=2)
            lignes = np.where(diff.any(axis=1))[0]
            self.assertTrue(lignes.size == 0 or lignes.max() < b.H_REGION, f'frame {t}')

    def test_etoiles_et_bas_inchanges(self):
        lum = self.ref.astype(float).mean(axis=2)
        sat = self.ref.max(axis=2) - self.ref.min(axis=2)
        etoiles = (sat < 40) & (lum > 170)
        for t in range(b.T):
            np.testing.assert_array_equal(self.ciel[t][etoiles], self.ref[etoiles])

    def test_modulation_subtile_sans_teinte(self):
        self.assertEqual(len(self.mnorm), b.T)
        self.assertTrue(all(np.isfinite(m).all() for m in self.mnorm))
        self.assertAlmostEqual(max(np.abs(m).max() for m in self.mnorm), 1.0, places=6)
        for t in range(b.T):
            d = self.ciel[t].astype(int) - self.ref.astype(int)
            rapports = []
            m = (d != 0) & (self.ref > 0)
            if m.any():
                rapports = np.abs(d[m]) / self.ref[m]
                self.assertLess(np.percentile(rapports, 99.9), 0.35, f'frame {t}')

    def test_boucle_fermee(self):
        self.assertTrue(np.all(self.mnorm[0] == 0))
        th = 2 * np.pi * np.arange(b.T + 1) / b.T
        u = 0.5 * (np.cos(th) - 1.0)
        self.assertAlmostEqual(u[0], u[-1], places=12)

    def test_24_frames_et_webp_fidele(self):
        self.assertEqual(len(self.ciel), 24)
        with Image.open(b.O / 'ciel/ciel_boreal_anime.webp') as im:
            self.assertEqual(im.n_frames, 24)
            for t in (0, 7, 15, 23):
                im.seek(t)
                np.testing.assert_array_equal(np.array(im.convert('RGB')), self.ciel[t])

    def test_overlay_pose_fixe_et_fond_fondu(self):
        self.assertEqual(self.ov[0].shape, (314, 528, 4))
        self.assertEqual(self.ov[0][313, :, 3].max(), 0)
        z0 = self.ov[0][:, :, 3] > 128
        for t in range(1, b.T):
            z = self.ov[t][:, :, 3] > 128
            inter = (z & z0).sum(); union = (z | z0).sum()
            self.assertGreater(inter / max(1, union), 0.80, f'frame {t}')

    def test_overlay_anime_sans_translation(self):
        for t in range(b.T):
            z = (self.ov[t][:, :, 3] > 40)
            z0 = (self.ov[0][:, :, 3] > 40)
            self.assertLess(abs(int(z.sum()) - int(z0.sum())) / max(1, int(z0.sum())), 0.25)

    def test_gif_boucle_24(self):
        total = 0
        with Image.open(b.O / 'review/ciel_anime.gif') as im:
            self.assertEqual(im.n_frames, 24)
            for i in range(24):
                im.seek(i); total += im.info.get('duration', 0)
        self.assertEqual(total, 2880)

    def test_calques_V3_intacts_et_scene_recomposee(self):
        for p in (b.O / 'calques').glob('*.png'):
            self.assertEqual(p.read_bytes(), (b.V3 / 'calques' / p.name).read_bytes())
        ciel_merged = Image.open(b.V3 / 'calques/AreneLargeV3_00_ciel_genere.png').convert('RGBA')
        ciel_merged.alpha_composite(Image.open(b.V3 / 'calques/AreneLargeV3_00b_etoiles.png').convert('RGBA'))
        terrain = Image.open(b.V3 / 'review/terrain_detoure.png').convert('RGBA')
        recomposee = b.scene_composee(0, ciel_merged, terrain, [Image.fromarray(a) for a in self.ov])
        np.testing.assert_array_equal(np.array(Image.open(b.O / 'review/scene_000.png').convert('RGBA')), np.array(recomposee))

    def test_overlay_unique_sans_wrap(self):
        self.assertEqual(self.ov[0].shape[1], 528)
        self.assertEqual(self.ov[0][:, 0, 3].max(), 0)
        self.assertEqual(self.ov[0][:, 527, 3].max(), 0)
        self.assertLessEqual(528 + 120, 768)
        self.assertGreaterEqual(120, 24)

    def test_manifest_et_provenance(self):
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertEqual(m['frames'], 24)
        self.assertEqual(m['cycle_s'], 2.88)
        self.assertEqual(hashlib.sha256(b.REF_PATH.read_bytes()).hexdigest(), m['reference_sha256'])
        self.assertIn('aucun wrap', m['methode'])
        self.assertIn('INCONNU', m['cycle_officiel'])

if __name__ == '__main__':
    unittest.main()
