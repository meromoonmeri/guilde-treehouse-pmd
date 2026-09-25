"""Tests dédiés — Entrée Jungle sud -> nord V1 (4:3 vaste).
.venv/bin/python -m unittest source.entree_jungle_sud_nord_v1.test_build -v
Contrôles d'images, de formats, de cadence et de grille : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, unittest, zipfile
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_jungle_sud_nord_v1'
S = R / '.cache/entree_jungle_sud_nord_v1/entree_jungle_sud_nord'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
WP, TP = M['water']['phases'], M['butterflies']['phases']


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
TICKS = [10, 10] + [60] * 9 + [M['butterflies']['frame_length_ticks']]


class Build(unittest.TestCase):
    def test_raw_hashes(self):
        for r in M['raw_inputs']:
            self.assertEqual(hashlib.sha256((R / r['file']).read_bytes()).hexdigest(), r['sha256'])

    def test_sizes_names_alpha_no_magenta(self):
        names = [Path(p).name for p in M['layer_order_bottom_to_top']]
        self.assertEqual(len(names), len(set(names))); self.assertTrue(all(n.startswith('EJN1_') for n in names))
        self.assertEqual((W, H, W % 8, H % 8), (768, 576, 0, 0)); self.assertEqual(W * 3, H * 4)   # 4:3
        n = M['normalization']; self.assertAlmostEqual(n['scale'], 576 / 896)
        self.assertEqual(n['scaled'][0] - sum(n['crop_x']), W)
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

    def test_water_metano_structure_and_loop(self):
        fr = STACK[0]; mask = fr[0][..., 3] == 255; pal = {tuple(v) for v in M['water']['couleurs'].values()}
        for a in fr:
            self.assertTrue(((a[..., 3] == 255) == mask).all())
            self.assertTrue({tuple(int(v) for v in c) for c in np.unique(a[mask][:, :3], axis=0)} <= pal)
        d = [int((fr[t][mask] != fr[(t + 1) % WP][mask]).any(1).sum()) for t in range(WP)]
        self.assertTrue(min(d) > 0 and max(d) < 2 * min(d), d)

    def test_sparkles_native_pixels(self):
        v2 = loadmod('esn2', R / 'source/entree_vapeur_sud_nord_v2/build.py')
        native = {tuple(int(v) for v in px[:3]) for t in v2.decode_tile(R / M['sparkles']['source']).values() for px in t.reshape(-1, 4) if px[3] == 255}
        for a in STACK[1]:
            cols = {tuple(int(v) for v in c) for c in np.unique(a[a[..., 3] > 0][:, :3], axis=0)}
            self.assertTrue(cols <= native)
            self.assertGreater(len(cols), 0)

    def test_butterflies_closed_loop(self):
        bfly = M['butterflies']; self.assertEqual(FLY := bfly['phases'], 48); self.assertEqual(FLY % 6, 0)
        for tr in bfly['trajectoires']:
            p = np.array(tr['positions']); steps = np.abs(np.diff(np.vstack([p, p[:1]]), axis=0)).max(1)
            self.assertLessEqual(int(steps.max()), 14)   # pic théorique ay*2*2π/48 ≈ 13 px, y compris 47 -> 0 : pas de téléportation
        n = [int((a[..., 3] > 0).sum()) for a in STACK[-1]]
        self.assertGreater(min(n), 6 * 20)                          # les 6 papillons visibles à chaque phase
        for nm in ('jaune', 'bleu'):
            for i in range(6):
                self.assertEqual(load(O / f'poses_papillons/EJN1_papillon_{nm}_{i}.png').shape, (24, 24, 4))

    def test_ora_and_scene(self):
        with zipfile.ZipFile(O / 'EJN1_entree_jungle_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
        sc = Image.new('RGBA', (W, H))
        for frames in STACK:
            sc.alpha_composite(Image.fromarray(frames[0]))
        self.assertTrue((np.array(sc) == merged).all())
        self.assertTrue((np.array(sc) == load(O / 'review/EJN1_scene_t000.png')).all())

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
