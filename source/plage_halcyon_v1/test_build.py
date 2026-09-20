import unittest, json, hashlib
import numpy as np
from PIL import Image
from scipy import ndimage
from . import build as b

class PlageHalcyonV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.terrain = np.array(Image.open(b.O / 'couches/terrain_fixe.png'))
        cls.frames = [np.array(Image.open(b.O / 'couches/eau' / f'EauLumiereV1_{f:02d}.png')) for f in range(b.T)]
        cls.fond = np.array(Image.open(b.O / 'couches/fond_fixe.png'))
        cls.man = json.loads((b.O / 'manifest.json').read_text())

    def test_provenance_bruts(self):
        self.assertEqual(hashlib.sha256(b.BRUT_T.read_bytes()).hexdigest(), self.man['bruts_sha256']['terrain'])
        self.assertEqual(hashlib.sha256(b.BRUT_E.read_bytes()).hexdigest(), self.man['bruts_sha256']['eau'])

    def test_terrain_nettoye(self):
        self.assertEqual(self.terrain.shape, (1152, 928, 4))
        # bande magenta du haut retiree : transparence en tete
        self.assertEqual(int(self.terrain[:36, :, 3].max()), 0)
        opaques = self.terrain[self.terrain[:, :, 3] > 128][:, :3].astype(int)
        magenta = (opaques[:, 0] > 200) & (opaques[:, 2] > 200) & (opaques[:, 1] < 90)
        self.assertEqual(int(magenta.sum()), 0, 'magenta residuel opaque dans le terrain')
        # sable central continu : pas de cratere sombre. Les petits rochers poses sur le
        # sable (comme la reference) sont legitimes : on refuse un grand composant sombre
        # connexe (cratere V15 = 5471 px d'un bloc).
        z = self.terrain[560:980, 360:560]
        lum = z[:, :, :3].astype(float).mean(axis=2)
        sombres = (lum < 120) & (z[:, :, 3] > 128)
        lab, n = ndimage.label(sombres)
        plus_gros = max(ndimage.sum(sombres, lab, range(1, n + 1)), default=0)
        self.assertLess(plus_gros, 2000, 'cratere sombre au centre du sable')
        self.assertLess(int(sombres.sum()), 3000)

    def test_10_frames_uniformes_halcyon(self):
        self.assertEqual(len(self.frames), 10)
        for f in self.frames:
            self.assertEqual(f.shape, (256, 928, 4))
        h = self.man['halcyon']
        self.assertTrue(h['position_multiple_de_8'])
        self.assertEqual(h['duree_ms_uniforme'], 140)
        self.assertEqual(h['frames_nommage_uniforme'], 'EauLumiereV1_00..09.png')
        self.assertTrue(h['pas_de_wrap'])

    def test_scintillement_et_boucle_fermee(self):
        masks = [f[:, :, 3] > 128 for f in self.frames]
        def sd(a, c): return float(np.mean(a ^ c))
        diffs = [sd(masks[i], masks[(i + 1) % 10]) for i in range(10)]
        self.assertTrue(all(0.003 < d for d in diffs), 'pas de scintillement entre frames')
        self.assertTrue(all(d < 0.20 for d in diffs), 'saut trop violent quelque part')
        # boucle : la frame 10 est un demi-pas de la frame 1 (fondu 50 %)
        self.assertLess(diffs[9], min(diffs[:5]) * 1.5, 'la fermeture de boucle n est pas un demi-pas')
        for i in range(10):
            a, c = masks[i], masks[(i + 1) % 10]
            self.assertGreater((a & c).sum() / max(1, (a | c).sum()), 0.10, f'IoU frame {i}')

    def test_trainees_restreintes_a_leau(self):
        # les frames sont locales a la bande (256 px) : l'animation ne modifie la scene
        # QUE dans les lignes [POS_Y, POS_Y+256)
        y0 = self.man['bande_eau']['y']
        base = Image.fromarray(self.fond, 'RGBA').copy()
        base.alpha_composite(Image.fromarray(self.terrain, 'RGBA'))
        base = np.array(base)
        s0 = np.array(Image.open(b.O / 'scene' / 'scene_00.png'))
        different = (base != s0).any(axis=2)
        hors_bande = different.copy()
        hors_bande[y0:y0 + b.CASE_H, :] = False
        self.assertEqual(int(hors_bande.sum()), 0, 'animation hors de la bande d eau')
        self.assertGreater(int(different.sum()), 500, 'aucune trace visible dans la bande')
        # aucun magenta cuit
        op = self.frames[0][self.frames[0][:, :, 3] > 128][:, :3].astype(int)
        mag = (op[:, 0] > 200) & (op[:, 2] > 200) & (op[:, 1] < 90)
        self.assertLess(mag.mean(), 0.02, 'magenta cuit dans le calque eau')
        alpha = self.frames[3][:, :, 3] > 128
        self.assertGreater(alpha.sum(), 500, 'calque eau presque vide')

    def test_couverture_eau(self):
        self.assertGreater(self.man['bande_eau']['couverture_eau_totale'], 0.70,
                           'la bande ne couvre pas les grands bassins')

    def test_scene_recomposee(self):
        px, py = self.man['halcyon']['eau_position']
        for f in (0, 3, 6, 9):
            s = Image.fromarray(self.fond, 'RGBA').copy()
            s.alpha_composite(Image.fromarray(self.terrain, 'RGBA'))
            s.alpha_composite(Image.fromarray(self.frames[f], 'RGBA'), (px, py))
            np.testing.assert_array_equal(np.array(s), np.array(Image.open(b.O / 'scene' / f'scene_{f:02d}.png')))

    def test_fond_crique(self):
        np.testing.assert_array_equal(self.fond[:, :, :3], np.full((1152, 928, 3), b.FOND, 'uint8'))
        self.assertEqual(int(self.fond[:, :, 3].min()), 255)

    def test_webp_gif(self):
        with Image.open(b.O / 'eau_scintillement_10frames.webp') as im:
            self.assertEqual(im.n_frames, 10)
        total = 0
        with Image.open(b.O / 'review/scene_scintillement.gif') as im:
            self.assertEqual(im.n_frames, 10)
            for i in range(10):
                im.seek(i); total += im.info.get('duration', 0)
        self.assertEqual(total, 1400)

if __name__ == '__main__':
    unittest.main()
