import unittest, json, hashlib
import numpy as np
from PIL import Image
from . import build as b

class PaletteCyclingV12Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames = [np.array(Image.open(b.O / 'couches' / f'PaletteCycleV12_frame_{f:02d}.png')) for f in range(b.T)]

    def test_provenance(self):
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertEqual(hashlib.sha256(b.BRUT.read_bytes()).hexdigest(), m['brut_sha256'])

    def test_8_calques_768x256(self):
        self.assertEqual(len(self.frames), 8)
        for f in self.frames:
            self.assertEqual(f.shape, (256, 768, 4))

    def test_silhouette_identique(self):
        alpha0 = self.frames[0][:, :, 3] > 128
        for f in self.frames[1:]:
            alpha = f[:, :, 3] > 128
            inter = (alpha & alpha0).sum(); union = (alpha | alpha0).sum()
            self.assertGreater(inter / union, 0.999)

    def test_couleurs_avancent(self):
        voisins = [np.mean(np.any(self.frames[i][:, :, :3] != self.frames[(i + 1) % 8][:, :, :3], axis=2) & (self.frames[i][:, :, 3] > 128)) for i in range(8)]
        self.assertTrue(all(v > 0.02 for v in voisins), 'couleurs identiques : pas de cycling')

    def test_boucle_fermee(self):
        d07 = np.mean(np.any(self.frames[7][:, :, :3] != self.frames[0][:, :, :3], axis=2) & (self.frames[0][:, :, 3] > 128))
        self.assertLess(d07, 0.35, 'frame 8 trop loin de frame 1 : boucle ouverte')

    def test_sans_ciel_borne(self):
        f = self.frames[0]
        self.assertEqual(int(f[:, :4, 3].max()), 0)
        self.assertEqual(int(f[:, -4:, 3].max()), 0)
        self.assertEqual(int(f[:6, :, 3].max()), 0)

    def test_scene_et_contexte(self):
        for nom, src in {'ciel_genere': b.V8 / 'AreneLargeV3_00_ciel_genere.png', 'etoiles': b.V8 / 'AreneLargeV3_00b_etoiles.png',
                         'glace_laterale': b.V8 / 'V8_glace_laterale_arriere_plan.png', 'terrain': b.V8 / 'AreneLargeV3_02_sol_visible.png'}.items():
            self.assertEqual((b.O / 'contexte' / f'{nom}.png').read_bytes(), src.read_bytes())

    def test_assets_indexes_moteur(self):
        """Assets moteur : UNE image indexee + 8 palettes rejouent exactement les 8 calques."""
        alpha = np.array(Image.open(b.O / 'onde_alpha.png'))
        pim = Image.open(b.O / 'onde_indexee.png')
        self.assertEqual(pim.mode, 'P')
        idx = np.array(pim)
        self.assertEqual(idx.shape, (256, 768))
        self.assertEqual(alpha.shape, (256, 768))
        self.assertEqual(set(np.unique(idx).tolist()) - {0, 1, 2, 3, 4, 5, 6, 7, 8}, set())
        palettes = json.loads((b.O / 'palettes_8frames.json').read_text())['frames']
        self.assertEqual(len(palettes), b.T)
        for f in range(b.T):
            pal = [v for c in palettes[f] for v in c]
            pim.putpalette(pal + [0] * (3 * (256 - len(palettes[f]))))
            got = np.zeros((256, 768, 4), 'uint8')
            got[:, :, :3] = np.array(pim.convert('RGB'))
            got[:, :, 3] = alpha
            got[alpha == 0] = 0
            self.assertTrue(np.array_equal(got, self.frames[f]), f'frame {f} hors decodage indexe')
            self.assertTrue(np.array_equal(alpha, self.frames[f][:, :, 3]), f'alpha {f} modifie')
        # le cycling tourne : les rampes reviennent a leur depart apres 4 frames, corps sombre fixe
        self.assertEqual(palettes[0][:4], palettes[4][:4])
        self.assertEqual(palettes[0][4:8], palettes[4][4:8])
        self.assertNotEqual(palettes[0][:4], palettes[1][:4])
        self.assertEqual({tuple(p[8]) for p in palettes}, {(18, 14, 52)})

    def test_webp_gif(self):
        with Image.open(b.O / 'palette_cycling_8frames.webp') as im:
            self.assertEqual(im.n_frames, 8)
        total = 0
        with Image.open(b.O / 'review/palette_cycling.gif') as im:
            self.assertEqual(im.n_frames, 8)
            for i in range(8):
                im.seek(i); total += im.info.get('duration', 0)
        self.assertEqual(total, 960)

    def test_manifest(self):
        m = json.loads((b.O / 'manifest.json').read_text())
        self.assertEqual(m['frames'], 8)
        self.assertTrue(m['sans_ciel'])
        self.assertFalse(m['wrap'])

if __name__ == '__main__':
    unittest.main()
