"""Tests dédiés — Thunder Meadow falaise + arène V1 (TMA1, 4:3).
.venv/bin/python -m unittest source.thunder_meadow_arene_v1.test_build -v
Contrôles d'images, de couleurs canoniques, de boucles et d'accès : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, json, unittest
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/thunder_meadow_arene_v1'
S = R / '.cache/thunder_meadow_arene_v1/thunder_meadow_arene'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
REF = np.array(Image.open(R / 'Rescue_Team_Friend_Area_-_Thunder_Meadow.png').convert('RGB'))
SHEET = np.array(Image.open(HERE / 'bruts/ref_5394.png').convert('RGB'))


def load(p):
    return np.array(Image.open(p).convert('RGBA'))


def expand(L):
    return [load(O / L['file'])] if L['phases'] == 1 else [load(O / L['file'].replace('fNN', f'f{t:02d}')) for t in range(L['phases'])]


BY = {Path(L['file']).stem.replace('_fNN', '').split('_', 2)[2]: (L, expand(L)) for L in M['layers']}


def colors(frames):
    return {tuple(int(v) for v in c) for a in frames for c in np.unique(a[a[..., 3] == 255][:, :3], axis=0)}


class Build(unittest.TestCase):
    def test_raw_hashes(self):
        for r in M['raw_inputs']:
            self.assertEqual(hashlib.sha256((R / r['file']).read_bytes()).hexdigest(), r['sha256'])
        self.assertEqual(hashlib.sha256((HERE / 'bruts/ref_5394.png').read_bytes()).hexdigest(), M['references']['planche']['sha256'])

    def test_sizes_alpha(self):
        for k, (L, fr) in BY.items():
            for a in fr:
                self.assertEqual(a.shape, (H, W, 4), k)
                self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255}, k)

    def test_fond_couvre_tout_et_flash_canonique(self):
        L, fr = BY['fond_nuages']
        flash = [tuple(c) for row in M['flash']['palette_niveaux'] for c in row]
        native = {tuple(int(v) for v in SHEET[57 + 9 * r + 3, 519 + 9 * c + 3]) for r in range(6) for c in range(8)}
        self.assertEqual(set(flash), native)
        for t, a in enumerate(fr):
            self.assertTrue((a[..., 3] == 255).all())
            lv = M['flash']['sequence'][t]
            self.assertTrue(colors([a]) <= {tuple(c) for c in M['flash']['palette_niveaux'][lv]}, t)
        self.assertEqual(len({a.tobytes() for a in fr}), 6)

    def test_couleurs_canoniques_du_rip(self):
        rip = {tuple(int(v) for v in c) for c in REF.reshape(-1, 3)}
        for k in ('prairie', 'falaises', 'ilots', 'pierres'):
            self.assertTrue(colors(BY[k][1]) <= rip, k)

    def test_etincelles_natives(self):
        native = {tuple(int(v) for v in c) for c in SHEET[125:400, 470:710].reshape(-1, 3)}
        self.assertTrue(colors(BY['etincelles'][1]) <= native)

    def test_foudre_derriere_falaise_et_boucle(self):
        land = np.zeros((H, W), bool)
        for k in ('ilots', 'falaises', 'prairie', 'chemin', 'arene', 'pierres', 'arbre'):
            land |= BY[k][1][0][..., 3] == 255
        for k in ('foudre', 'etincelles'):
            L, fr = BY[k]
            self.assertEqual((L['phases'], L['ticks']), (48, 5))
            for a in fr:
                self.assertFalse((a[..., 3] == 255)[land].any(), k)
        self.assertTrue(any(a[..., 3].any() for a in BY['foudre'][1]))
        self.assertFalse(BY['foudre'][1][0][..., 3].any())

    def test_calques_multiples_couverture(self):
        cov = BY['fond_nuages'][1][0][..., 3] == 255
        self.assertTrue(cov.all())
        self.assertGreaterEqual(len([k for k in BY if BY[k][0]['phases'] == 1]), 7)

    def test_access_arene(self):
        a = M['access']
        self.assertTrue(a['path_found_16x16'])
        self.assertGreaterEqual(a['entry_px'][1], H - 16); self.assertLess(a['arene_centre_px'][1], 200)
        doc = json.loads((S / f"Data/Ground/{M['pmdo']['asset']}.rsground").read_text())['Object']
        self.assertEqual(sum(c['Tags'] for col in doc['obstacles'] for c in col), a['blocked_cells'])
        self.assertFalse(M['pmdo']['runtime_tested']); self.assertFalse(M['art_approved'])


if __name__ == '__main__':
    unittest.main()
