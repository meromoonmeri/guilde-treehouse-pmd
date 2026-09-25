"""Tests dédiés — Entrée Vapeur sud -> nord V1.
.venv/bin/python -m unittest source.entree_sud_nord_generee_v1.test_build -v
Contrôles d'images, de formats et de grille : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, unittest, zipfile
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_vapeur_sud_nord_v1'
S = R / '.cache/entree_vapeur_sud_nord_v1/entree_vapeur_sud_nord'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']


def load(p):
    return np.array(Image.open(p).convert('RGBA'))


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def statics():
    return [load(O / p) for p in M['layer_order_bottom_to_top'][1:]]


def waters():
    return [load(O / f'animation/eau/ESN1_00_eau_f{t:02d}.png') for t in range(M['water']['frames'])]


class Build(unittest.TestCase):
    def test_raw_inputs_hashes(self):
        for r in M['raw_inputs']:
            self.assertEqual(hashlib.sha256((HERE / 'bruts' / Path(r['file']).name).read_bytes()).hexdigest(), r['sha256'])
            self.assertEqual(r['size'], [1024, 1024] if 'eau' in r['file'] else [848, 1264])

    def test_uniform_normalization_and_grid(self):
        self.assertEqual((W * 2, H * 2), (848, 1264))  # facteur 0,5 identique en X et Y
        self.assertEqual((W % 8, H % 8), (0, 0))
        for a in statics() + waters():
            self.assertEqual(a.shape[:2], (H, W))

    def test_unique_names(self):
        names = [Path(p).name for p in M['layer_order_bottom_to_top'][1:]]
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(n.startswith('ESN1_') for n in names))

    def test_no_magenta_and_binary_alpha(self):
        for p, a in zip(M['layer_order_bottom_to_top'][1:], statics()):
            vis = a[a[..., 3] > 0].astype(int)
            mag = (vis[:, 0] > 200) & (vis[:, 2] > 200) & (vis[:, 1] < 90)
            self.assertEqual(int(mag.sum()), 0, p)
            if 'ombres' not in p:
                self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255}, p)

    def test_full_coverage_no_holes(self):
        cover = waters()[0][..., 3] == 255
        for p, a in zip(M['layer_order_bottom_to_top'][1:], statics()):
            if 'ombres' not in p:
                cover |= a[..., 3] == 255
        self.assertTrue(cover.all())

    def test_water_palette_cycling_fixed_indices(self):
        idx = np.array(Image.open(O / 'animation/eau/ESN1_00_eau_indices.png'))
        pal = json.loads((O / 'animation/eau/palettes_12_phases.json').read_text())['palettes']
        frames = waters(); mask = frames[0][..., 3] == 255
        for t, a in enumerate(frames):
            self.assertTrue(((a[..., 3] == 255) == mask).all())        # même alpha à chaque phase
            rebuilt = np.array(pal[t], 'uint8')[idx]
            self.assertTrue((rebuilt[mask] == a[mask][:, :3]).all())  # seule la palette change
        self.assertEqual(len({json.dumps(p) for p in pal}), len(pal))  # 12 phases distinctes
        # Boucle : la phase suivant la dernière est la phase 0 (décalage de bande cyclique).
        d = [int((frames[t][mask] != frames[(t + 1) % len(frames)][mask]).any(1).sum()) for t in range(len(frames))]
        self.assertTrue(max(d) < 2 * min(d) + 1, d)                    # transitions homogènes, y compris 11 -> 0

    def test_ora_recomposition_exact(self):
        with zipfile.ZipFile(O / 'ESN1_entree_vapeur_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
            self.assertEqual(z.read('mimetype'), b'image/openraster')
        scene = Image.fromarray(waters()[0])
        for a in statics():
            scene.alpha_composite(Image.fromarray(a))
        self.assertTrue((np.array(scene) == merged).all())
        self.assertTrue((np.array(scene) == load(O / 'review/ESN1_scene_phase00.png')).all())

    def test_access_path(self):
        acc = M['access']
        self.assertTrue(acc['path_found_16x16'])
        self.assertGreater(acc['entry_px'][1], H - 64)       # arrivée au sud
        self.assertLess(acc['threshold_px'][1], H // 2)      # seuil au nord

    def test_ground_serialized_roundtrip(self):
        doc = json.loads((S / f"Data/Ground/{M['pmdo']['asset']}.rsground").read_text())
        o = doc['Object']
        self.assertEqual(doc['Version'], '0.8.12.0'); self.assertEqual(o['TexSize'], 1); self.assertFalse(o['Released'])
        self.assertEqual((len(o['Layers'][0]['Tiles']), len(o['Layers'][0]['Tiles'][0])), (W // 8, H // 8))
        self.assertEqual(len(o['Layers']), 10); self.assertEqual(o['Layers'][-1]['Layer'], 4)
        nr = loadmod('native_reader', R / 'source/cote_v5_expeditions/audit_references.py')
        banks = {p.stem: nr.tiles(p)[1] for p in (S / 'Content/Tile').glob('*.tile')}
        self.assertEqual(set(banks), set(M['pmdo']['banks']))
        expected = [waters()] + [[a] for a in statics()]
        for li, frames in enumerate(expected):
            for t in ([0, 5, 11] if li == 0 else [0]):
                out = np.zeros((H, W, 4), 'uint8')
                for x, col in enumerate(o['Layers'][li]['Tiles']):
                    for y, cell in enumerate(col):
                        for track in cell['Layers']:
                            f = track['Frames'][t % len(track['Frames'])]
                            out[y*8:y*8+8, x*8:x*8+8] = np.array(nr.straight(banks[f['Sheet']][f['TexLoc']['X'], f['TexLoc']['Y']]))
                exp = frames[t]
                self.assertTrue((out[..., 3] == exp[..., 3]).all(), (li, t))
                vis = exp[..., 3] == 255
                self.assertLessEqual(int(np.abs(out[vis].astype(int) - exp[vis].astype(int)).max(initial=0)), 0, (li, t))
                semi = (exp[..., 3] > 0) & ~vis
                if semi.any():  # prémultiplication : arrondi toléré sur l'ombre translucide
                    self.assertLessEqual(int(np.abs(out[semi].astype(int) - exp[semi].astype(int)).max()), 8)
        blocked = sum(w['Tags'] for col in o['obstacles'] for w in col)
        self.assertEqual(blocked, M['access']['blocked_cells'])
        names = {m['EntName'] for m in o['Entities'][0]['Markers']}
        self.assertEqual(names, {'entrance', 'donjon_seuil'})

    def test_index_lists_all_banks(self):
        tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
        self.assertEqual(set(tools.read_index(S / 'Content/Tile/index.idx')), set(M['pmdo']['banks']))
        self.assertIn('entree_vapeur_sud_nord', (S / 'Mod.xml').read_text())


if __name__ == '__main__':
    unittest.main()
