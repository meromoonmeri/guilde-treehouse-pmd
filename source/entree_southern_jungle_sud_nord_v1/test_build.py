"""Tests dédiés — Entrée Southern Jungle sud -> nord V1 (ESJ1, 4:3 vaste).
.venv/bin/python -m unittest source.entree_southern_jungle_sud_nord_v1.test_build -v
Contrôles d'images, de palettes, de fidélité au rip, de boucles et d'accès : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, json, unittest
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_southern_jungle_sud_nord_v1'
S = R / '.cache/entree_southern_jungle_sud_nord_v1/entree_southern_jungle_sud_nord'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']


def load(p):
    return np.array(Image.open(p).convert('RGBA'))


def expand(L):
    return [load(O / L['file'])] if L['phases'] == 1 else [load(O / L['file'].replace('fNN', f'f{t:02d}')) for t in range(L['phases'])]


BY = {Path(L['file']).stem.replace('_fNN', '').split('_', 2)[2]: (L, expand(L)) for L in M['layers']}


class Build(unittest.TestCase):
    def test_raw_hashes_and_reference(self):
        for r in M['raw_inputs']:
            self.assertEqual(hashlib.sha256((R / r['file']).read_bytes()).hexdigest(), r['sha256'])
        self.assertEqual(M['reference_da']['file'], 'Southern_Jungle_exit_S.png')
        self.assertTrue(all('Southern_Jungle_exit_S.png' in g['images'] or 'decor_magenta' in g['images'][0] for g in M['generation']))

    def test_sizes_alpha_no_magenta(self):
        for k, (L, fr) in BY.items():
            for a in fr:
                self.assertEqual(a.shape, (H, W, 4), k)
                self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255}, k)
                r, g, b = [a[..., i].astype(int) for i in range(3)]
                self.assertFalse(((a[..., 3] == 255) & (r > 180) & (b > 150) & (g < 120)).any(), k)

    def test_full_coverage(self):
        cov = np.zeros((H, W), bool)
        for k in ('eau', 'sol_complet', 'herbe', 'sable', 'rochers', 'jungle', 'grotte'):
            cov |= BY[k][1][0][..., 3] == 255
        self.assertTrue(cov.all())

    def test_fidelite_rip(self):
        f = M['fidelite_rip']['calques_finaux']
        self.assertLess(f['sable']['distance_rip'], 20); self.assertLess(f['herbe']['distance_rip'], 20)
        self.assertLess(f['feuillage']['distance_rip'], 35)

    def test_animations_own_layers_and_loop(self):
        self.assertEqual([(BY[k][0]['phases'], BY[k][0]['ticks']) for k in ('eau', 'scintillements', 'papillons')],
                         [(4, 10), (4, 10), (48, 5)])
        for k in ('eau', 'scintillements', 'papillons'):
            L = BY[k][0]; self.assertEqual(M['scene_loop_ticks'] % (L['phases'] * L['ticks']), 0)
        pap = BY['papillons'][1]
        self.assertTrue(all(a[..., 3].any() for a in pap))
        self.assertGreater(len({a.tobytes() for a in pap}), 40)

    def test_water_without_light_rim(self):
        eau = BY['eau'][1]; land = np.zeros((H, W), bool)
        for k in ('herbe', 'sable', 'rochers', 'jungle', 'grotte'):
            land |= BY[k][1][0][..., 3] == 255
        cols = {tuple(c) for a in eau for c in np.unique(a[a[..., 3] == 255][:, :3], axis=0)}
        self.assertLessEqual(len(cols), 6)
        self.assertGreater(int((eau[0][..., 3] == 255).sum() - ((eau[0][..., 3] == 255) & land).sum()), 3000)

    def test_access(self):
        a = M['access']
        self.assertTrue(a['path_found_16x16'])
        self.assertGreaterEqual(a['entry_px'][1], H - 16); self.assertLess(a['threshold_px'][1], 200)

    def test_ground(self):
        doc = json.loads((S / f"Data/Ground/{M['pmdo']['asset']}.rsground").read_text())['Object']
        self.assertEqual(len(doc['Layers']), len(M['layers']) + 1)
        self.assertEqual(sum(c['Tags'] for col in doc['obstacles'] for c in col), M['access']['blocked_cells'])
        self.assertFalse(M['pmdo']['runtime_tested']); self.assertFalse(M['art_approved'])


if __name__ == '__main__':
    unittest.main()
