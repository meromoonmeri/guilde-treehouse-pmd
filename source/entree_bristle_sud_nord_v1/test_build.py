"""Tests dédiés — Entrée Bristle sud -> nord V1.
.venv/bin/python -m unittest source.entree_bristle_sud_nord_v1.test_build -v
Contrôles d'images, de formats, de cadence et de grille : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, unittest, zipfile
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_bristle_sud_nord_v1'
S = R / '.cache/entree_bristle_sud_nord_v1/entree_bristle_sud_nord'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
WP, TP = M['water']['phases'], M['tufts']['phases']


def load(p):
    return np.array(Image.open(p).convert('RGBA'))


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def expand(p):
    if 'fXX' in p:
        return [load(O / p.replace('fXX', f'f{t:02d}')) for t in range(TP)]
    if 'fX' in p:
        return [load(O / p.replace('fX', f'f{t}')) for t in range(WP)]
    return [load(O / p)]


STACK = [expand(p) for p in M['layer_order_bottom_to_top']]
TICKS = [10, 10, 60, 60, 60, 60, M['tufts']['frame_length_ticks'], 60, 60]


class Build(unittest.TestCase):
    def test_raw_hashes(self):
        for r in M['raw_inputs']:
            self.assertEqual(hashlib.sha256((R / r['file']).read_bytes()).hexdigest(), r['sha256'])

    def test_sizes_names_alpha_no_magenta(self):
        names = [Path(p).name for p in M['layer_order_bottom_to_top']]
        self.assertEqual(len(names), len(set(names))); self.assertTrue(all(n.startswith('EBN1_') for n in names))
        self.assertEqual((W * 2, H * 2, W % 8, H % 8), (848, 1264, 0, 0))
        for frames in STACK:
            for a in frames:
                self.assertEqual(a.shape[:2], (H, W)); self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255})
                v = a[a[..., 3] > 0].astype(int)
                self.assertEqual(int(((v[:, 0] > 200) & (v[:, 2] > 200) & (v[:, 1] < 90)).sum()), 0)

    def test_full_coverage(self):
        cover = STACK[0][0][..., 3] == 255
        for frames in STACK[2:]:
            cover |= frames[0][..., 3] == 255
        self.assertTrue(cover.all())

    def test_water_metano_colors_and_loop(self):
        fr = STACK[0]; mask = fr[0][..., 3] == 255
        metano = {(131, 218, 230), (87, 135, 191), (95, 183, 207), (111, 207, 231), (148, 230, 238)}
        for a in fr:
            self.assertTrue(((a[..., 3] == 255) == mask).all())
            self.assertTrue({tuple(int(v) for v in c) for c in np.unique(a[mask][:, :3], axis=0)} <= metano)
        d = [int((fr[t][mask] != fr[(t + 1) % WP][mask]).any(1).sum()) for t in range(WP)]
        self.assertTrue(min(d) > 0 and max(d) < 2 * min(d), d)

    def test_sparkles_native_pixels(self):
        v2 = loadmod('esn2', R / 'source/entree_vapeur_sud_nord_v2/build.py')
        native = {tuple(int(v) for v in px[:3]) for t in v2.decode_tile(R / M['sparkles']['source']).values() for px in t.reshape(-1, 4) if px[3] == 255}
        for a in STACK[1]:
            cols = {tuple(int(v) for v in c) for c in np.unique(a[a[..., 3] > 0][:, :3], axis=0)}
            self.assertTrue(cols <= native)
            self.assertGreater(len(cols), 0)

    def test_tufts_cycle_loop(self):
        t = M['tufts']; self.assertEqual(len(t['cycle_indices_par_phase']), TP)
        leans = t['inclinaisons_mesurees']; c = t['cycle_indices_par_phase']
        steps = [abs(leans[c[(i + 1) % TP]] - leans[c[i]]) for i in range(TP)]
        self.assertLessEqual(max(steps), 0.25)                  # y compris 11 -> 0 : pas de saut gauche-droite complet
        self.assertLess(min(leans[i] for i in c), -0.1); self.assertGreater(max(leans[i] for i in c), 0.1)
        self.assertEqual(len(t['placements']), 8)
        for a in STACK[6]:
            self.assertGreater(int((a[..., 3] > 0).sum()), 8 * 40)

    def test_ora_and_scene(self):
        with zipfile.ZipFile(O / 'EBN1_entree_bristle_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
        sc = Image.new('RGBA', (W, H))
        for frames in STACK:
            sc.alpha_composite(Image.fromarray(frames[0]))
        self.assertTrue((np.array(sc) == merged).all())
        self.assertTrue((np.array(sc) == load(O / 'review/EBN1_scene_t000.png')).all())

    def test_access(self):
        a = M['access']; self.assertTrue(a['path_found_16x16'])
        self.assertGreater(a['entry_px'][1], H - 64); self.assertLess(a['threshold_px'][1], H // 2)

    def test_ground_roundtrip(self):
        doc = json.loads((S / f"Data/Ground/{M['pmdo']['asset']}.rsground").read_text()); o = doc['Object']
        self.assertEqual(doc['Version'], '0.8.12.0'); self.assertEqual(len(o['Layers']), len(STACK) + 1)
        self.assertEqual(o['Layers'][-1]['Layer'], 4)
        nr = loadmod('native_reader', R / 'source/cote_v5_expeditions/audit_references.py')
        banks = {p.stem: nr.tiles(p)[1] for p in (S / 'Content/Tile').glob('*.tile')}
        self.assertEqual(set(banks), set(M['pmdo']['banks']))
        for li, (frames, ticks) in enumerate(zip(STACK, TICKS)):
            for t in sorted({0, len(frames) // 2, len(frames) - 1}):
                out = np.zeros((H, W, 4), 'uint8')
                for x, col in enumerate(o['Layers'][li]['Tiles']):
                    for y, cell in enumerate(col):
                        for track in cell['Layers']:
                            if len(track['Frames']) > 1:
                                self.assertEqual((len(track['Frames']), track['FrameLength']), (len(frames), ticks))
                            f = track['Frames'][t % len(track['Frames'])]
                            out[y*8:y*8+8, x*8:x*8+8] = np.array(nr.straight(banks[f['Sheet']][f['TexLoc']['X'], f['TexLoc']['Y']]))
                self.assertTrue((out == frames[t]).all(), (li, t))
        self.assertEqual(sum(w['Tags'] for c in o['obstacles'] for w in c), M['access']['blocked_cells'])
        self.assertEqual({m['EntName'] for m in o['Entities'][0]['Markers']}, {'entrance', 'donjon_seuil'})
        tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
        self.assertEqual(set(tools.read_index(S / 'Content/Tile/index.idx')), set(M['pmdo']['banks']))


if __name__ == '__main__':
    unittest.main()
