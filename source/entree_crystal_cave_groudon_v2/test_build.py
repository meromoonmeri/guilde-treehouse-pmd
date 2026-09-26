"""Tests dédiés — ECC2 : grotte de cristal ECC1 + VFX colonnes de flamme (arrivée de Groudon).
.venv/bin/python -m unittest source.entree_crystal_cave_groudon_v2.test_build -v
Contrôles d'images, de formats, de palette et de projet : PAS un test du moteur PMDO (script init.lua non testé).
"""
from pathlib import Path
import hashlib, json, unittest, zipfile
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_crystal_cave_groudon_v2'
B = R / 'renders/entree_crystal_cave_sud_nord_v1'
S = R / '.cache/entree_crystal_cave_groudon_v2/entree_crystal_cave_groudon'
M = json.loads((O / 'manifest.json').read_text())
ASSET = M['pmdo']['asset']


def frames(root, L):
    n = L['phases']
    fs = [L['file']] if n == 1 else [L['file'].replace('fNN', f'f{t:02d}') for t in range(n)]
    return [root / f for f in fs]


EVT = [L for L in M['layers'] if L.get('evenement')]
BASE = [L for L in M['layers'] if not L.get('evenement')]
FL = next(L for L in EVT if 'colonnes_flamme' in L['file'])


class Build(unittest.TestCase):
    def test_raw_hash(self):
        for r in M['raw_inputs']:
            self.assertEqual(hashlib.sha256((R / r['file']).read_bytes()).hexdigest(), r['sha256'])
        self.assertEqual(M['generation'][0]['images'], ['Dark_Crater_Pit_TDS.png'])

    def test_base_layers_identical_to_ecc1(self):
        BM = json.loads((B / 'manifest.json').read_text())
        self.assertEqual(len(BASE), len(BM['layers']))
        for L, BL in zip(BASE, BM['layers']):
            self.assertEqual((L['phases'], L['ticks']), (BL['phases'], BL['ticks']))
            for a, b in zip(frames(O, L), frames(B, BL)):
                self.assertEqual(a.read_bytes(), b.read_bytes(), a.name)

    def test_event_layers(self):
        self.assertEqual(len(EVT), 3)
        for L in EVT:
            self.assertEqual((L['phases'], L['ticks']), (48, 4))
            fs = [np.array(Image.open(p).convert('RGBA')) for p in frames(O, L)]
            for a in fs:
                self.assertEqual(a.shape[:2], tuple(M['size_px'][::-1]))
                self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255}, L['file'])
            self.assertFalse(fs[-1][..., 3].any(), 'derniere phase vide ' + L['file'])
        fl = [np.array(Image.open(p).convert('RGBA')) for p in frames(O, FL)]
        cov = [int((a[..., 3] > 0).sum()) for a in fl]
        self.assertLess(cov[0], max(cov) * 0.25, 'la premiere phase ne doit pas etre une flamme pleine')
        self.assertGreater(max(cov), 20000)

    def test_palette(self):
        pal = {tuple(c) for c in M['palette']}
        self.assertLessEqual(len(pal), 16)
        for L in EVT:
            for p in frames(O, L)[::3]:
                a = np.array(Image.open(p).convert('RGBA'))
                cs = {tuple(int(v) for v in c) for c in np.unique(a[a[..., 3] == 255][:, :3], axis=0)}
                self.assertTrue(cs <= pal, p.name)

    def test_project(self):
        gp = S / f'Data/Ground/{ASSET}.rsground'
        doc = json.loads(gp.read_text())['Object']
        for i, L in enumerate(M['layers']):
            self.assertEqual(doc['Layers'][i]['Visible'], not L.get('evenement', False), i)
        with zipfile.ZipFile(B / 'ECC1_projet_pmdo_0812.zip') as z:
            ref = json.loads(z.read('entree_crystal_cave_sud_nord/Data/Ground/ecc1_entree_crystal_cave.rsground'))['Object']
        tags = lambda o: [[c['Tags'] for c in col] for col in o['obstacles']]
        self.assertEqual(tags(doc), tags(ref))
        lua = (S / f'Data/Script/{M["pmdo"]["namespace"]}/ground/{ASSET}/init.lua').read_text()
        self.assertIn('arrivee_legendaire', lua)
        self.assertIn(f'WaitFrames({48 * 4})', lua)
        self.assertFalse(M['pmdo']['runtime_tested']); self.assertFalse(M['art_approved'])


if __name__ == '__main__':
    unittest.main()
