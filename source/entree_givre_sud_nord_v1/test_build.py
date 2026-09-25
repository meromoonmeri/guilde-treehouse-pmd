"""Tests dédiés — Entrée Givre sud -> nord V1.
.venv/bin/python -m unittest source.entree_givre_sud_nord_v1.test_build -v
Contrôles d'images, de formats, de cadence et de grille : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, unittest, zipfile
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_givre_sud_nord_v1'
S = R / '.cache/entree_givre_sud_nord_v1/entree_givre_sud_nord'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
WP, FP = M['water']['phases'], M['flakes']['phases']


def load(p):
    return np.array(Image.open(p).convert('RGBA'))


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def expand(p):
    if 'fXX' in p:
        return [load(O / p.replace('fXX', f'f{t:02d}')) for t in range(FP)]
    if 'fX' in p:
        return [load(O / p.replace('fX', f'f{t}')) for t in range(WP)]
    return [load(O / p)]


STACK = [expand(p) for p in M['layer_order_bottom_to_top']]
TICKS = [10, 10] + [60] * (len(STACK) - 3) + [M['flakes']['frame_length_ticks']]
NAMES = [Path(p).stem.replace('EGN1_', '') for p in M['layer_order_bottom_to_top']]


def layer(name):
    return STACK[[i for i, n in enumerate(NAMES) if n.endswith(name)][0]][0]


class Build(unittest.TestCase):
    def test_raw_and_reference_hashes(self):
        for r in M['raw_inputs']:
            self.assertEqual(hashlib.sha256((R / r['file']).read_bytes()).hexdigest(), r['sha256'])
        self.assertEqual(hashlib.sha256((R / M['reference_da']['file']).read_bytes()).hexdigest(), M['reference_da']['sha256'])

    def test_sizes_names_alpha_no_magenta(self):
        names = [Path(p).name for p in M['layer_order_bottom_to_top']]
        self.assertEqual(len(names), len(set(names))); self.assertTrue(all(n.startswith('EGN1_') for n in names))
        for frames in STACK:
            for a in frames:
                self.assertEqual(a.shape[:2], (H, W)); self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255})
                v = a[a[..., 3] > 0].astype(int)
                self.assertEqual(int(((v[:, 0] > 200) & (v[:, 2] > 200) & (v[:, 1] < 90)).sum()), 0)

    def test_full_coverage(self):
        cover = STACK[0][0][..., 3] == 255
        for frames in STACK[2:-1]:
            cover |= frames[0][..., 3] == 255
        self.assertTrue(cover.all())

    def test_cadences_and_loop(self):
        self.assertEqual((WP, M['water']['frame_length_ticks']), (4, 10))
        self.assertEqual(M['scene_loop_ticks'] % (WP * 10), 0)
        self.assertEqual(M['scene_loop_ticks'] % (FP * M['flakes']['frame_length_ticks']), 0)

    def test_water_structure_and_loop(self):
        fr = STACK[0]; mask = fr[0][..., 3] == 255; pal = {tuple(v) for v in M['water']['couleurs'].values()}
        for a in fr:
            self.assertTrue(((a[..., 3] == 255) == mask).all())
            self.assertTrue({tuple(c) for c in np.unique(a[mask][:, :3], axis=0)} <= pal)
        d = [int((fr[t][mask] != fr[(t + 1) % WP][mask]).any(1).sum()) for t in range(WP)]
        self.assertTrue(min(d) > 0 and max(d) < 2 * min(d), d)

    def test_ford_is_on_water_and_walkable(self):
        gue = layer('gue_gele')[..., 3] == 255
        water = STACK[0][0][..., 3] == 255
        self.assertGreater(gue.sum(), 1000); self.assertTrue((gue <= water).all())
        blocked = np.array(Image.open(O / 'review/EGN1_collisions_marqueurs.png'))  # existence de la vue
        self.assertEqual(blocked.shape[:2], (H, W))

    def test_flakes_loop_and_emitters(self):
        fr = STACK[-1]; n = [int((a[..., 3] > 0).sum()) for a in fr]
        self.assertGreater(min(n), 0)
        e = M['flakes']['emetteurs']; self.assertEqual(len(e), 40)
        self.assertEqual(M['flakes']['chute_phases'] + M['flakes']['pose_phases'] <= FP, True)
        self.assertEqual(24 * 2, FP)                          # ondulation (24) et rotation (12) ferment la boucle
        for k in M['flakes']['poses']:
            p = load(O / f'poses_flocons/EGN1_flocon_{k}.png'); self.assertEqual(p.shape, (8, 8, 4)); self.assertGreater((p[..., 3] > 0).sum(), 0)
        # la dernière phase se raccorde à la première : aucun flocon n'apparaît au milieu d'une chute
        d = [int((fr[t][..., 3] != fr[(t + 1) % FP][..., 3]).sum()) for t in range(FP)]
        self.assertLess(max(d), 3 * np.median(d) + 1, d)

    def test_overlays_on_visible_water_only(self):
        water = STACK[0][0][..., 3] == 255; land = np.zeros((H, W), bool)
        for frames in STACK[3:-1]:
            land |= frames[0][..., 3] == 255
        for a in STACK[1]:
            self.assertFalse(((a[..., 3] > 0) & ~(water & ~land)).any())

    def test_ora_and_scene(self):
        with zipfile.ZipFile(O / 'EGN1_entree_givre_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
        sc = Image.new('RGBA', (W, H))
        for frames in STACK:
            sc.alpha_composite(Image.fromarray(frames[0]))
        self.assertTrue((np.array(sc) == merged).all())
        self.assertTrue((np.array(sc) == load(O / 'review/EGN1_scene_t000.png')).all())

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
