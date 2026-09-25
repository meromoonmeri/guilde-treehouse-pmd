"""Tests dédiés — Entrée Cratère sud -> nord V1.
.venv/bin/python -m unittest source.entree_cratere_sud_nord_v1.test_build -v
Contrôles d'images, de formats, de cadence et de grille : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, unittest, zipfile
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_cratere_sud_nord_v1'
S = R / '.cache/entree_cratere_sud_nord_v1/entree_cratere_sud_nord'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
LP, BP, EP = M['lava']['phases'], M['bubbles']['phases'], M['embers']['phases']


def load(p):
    return np.array(Image.open(p).convert('RGBA'))


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def expand(p):
    """Chemin du manifeste -> liste de frames."""
    if 'fXX' in p:
        return [load(O / p.replace('fXX', f'f{t:02d}')) for t in range(BP)]
    if 'fX' in p:
        n = EP if 'braises' in p else LP
        return [load(O / p.replace('fX', f'f{t}')) for t in range(n)]
    return [load(O / p)]


STACK = [expand(p) for p in M['layer_order_bottom_to_top']]
TICKS = [M['lava']['frame_length_ticks']] * 2 + [60, M['bubbles']['frame_length_ticks']] + [60] * 4 + [M['embers']['frame_length_ticks']]


class Build(unittest.TestCase):
    def test_raw_hashes(self):
        for r in M['raw_inputs']:
            self.assertEqual(hashlib.sha256((R / r['file']).read_bytes()).hexdigest(), r['sha256'])
        sizes = {Path(r['file']).name: r['size'] for r in M['raw_inputs']}
        self.assertEqual(sizes['decor_magenta.png'], [848, 1264]); self.assertEqual(sizes['sol_complet.png'], [848, 1264])

    def test_sizes_names_alpha_no_magenta(self):
        names = [Path(p).name for p in M['layer_order_bottom_to_top']]
        self.assertEqual(len(names), len(set(names))); self.assertTrue(all(n.startswith('ECN1_') for n in names))
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

    def test_cadences_and_loop(self):
        self.assertEqual((LP, M['lava']['frame_length_ticks']), (4, 10))
        for n, t in ((LP, 10), (BP, M['bubbles']['frame_length_ticks']), (EP, M['embers']['frame_length_ticks'])):
            self.assertEqual(M['scene_loop_ticks'] % (n * t), 0)

    def test_lava_structure_and_loop(self):
        fr = STACK[0]; mask = fr[0][..., 3] == 255; pal = {tuple(v) for v in M['lava']['couleurs'].values()}
        for a in fr:
            self.assertTrue(((a[..., 3] == 255) == mask).all())
            self.assertTrue({tuple(c) for c in np.unique(a[mask][:, :3], axis=0)} <= pal)
        d = [int((fr[t][mask] != fr[(t + 1) % LP][mask]).any(1).sum()) for t in range(LP)]
        self.assertTrue(min(d) > 0 and max(d) < 2 * min(d), d)

    def test_embers_pulse_loop(self):
        fr = STACK[-1]; mask = fr[0][..., 3] == 255
        self.assertGreater(mask.sum(), 50)
        for a in fr:
            self.assertTrue(((a[..., 3] == 255) == mask).all())
        self.assertTrue((fr[0] == fr[-1]).all())            # pulsation 0,1,2,2,1,0 : 5 -> 0 sans saut
        self.assertFalse((fr[0] == fr[2]).all())

    def test_overlays_on_visible_lava_only(self):
        lava = STACK[0][0][..., 3] == 255; land = np.zeros((H, W), bool)
        for frames in STACK[4:8]:
            land |= frames[0][..., 3] == 255
        for a in STACK[1] + STACK[3]:
            self.assertFalse(((a[..., 3] > 0) & ~(lava & ~land)).any())

    def test_bubbles(self):
        b = M['bubbles']; self.assertLess(len(b['timeline_phases']), BP)
        for k in b['poses']:
            p = load(O / f'poses_bulles/ECN1_bulle_{k}.png'); self.assertEqual(p.shape, (24, 24, 4))
            self.assertGreater(int((p[..., 3] > 0).sum()), 0, k)
        n = [int((a[..., 3] > 0).sum()) for a in STACK[3]]
        self.assertGreater(min(n), 0); self.assertGreaterEqual(len(b['emetteurs']), 4)
        self.assertEqual(len({e['decalage'] for e in b['emetteurs']}), len(b['emetteurs']))

    def test_ora_and_scene(self):
        with zipfile.ZipFile(O / 'ECN1_entree_cratere_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
        sc = Image.new('RGBA', (W, H))
        for frames in STACK:
            sc.alpha_composite(Image.fromarray(frames[0]))
        self.assertTrue((np.array(sc) == merged).all())
        self.assertTrue((np.array(sc) == load(O / 'review/ECN1_scene_t000.png')).all())

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
