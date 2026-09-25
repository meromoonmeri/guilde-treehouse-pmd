"""Tests dédiés — Entrée Ruine sud -> nord V1.
.venv/bin/python -m unittest source.entree_ruine_sud_nord_v1.test_build -v
Contrôles d'images, de formats, de cadence et de grille : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, unittest, zipfile
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_ruine_sud_nord_v1'
S = R / '.cache/entree_ruine_sud_nord_v1/entree_ruine_sud_nord'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
N = {'sables': M['quicksand']['phases'], 'bulles': M['bubbles']['phases'], 'tourbillons': M['dust_devils']['phases']}


def load(p):
    return np.array(Image.open(p).convert('RGBA'))


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def expand(p):
    if p.startswith('animation/'):
        n = N[p.split('/')[1]]
        return [load(O / (p.replace('fXX', f'f{t:02d}') if 'fXX' in p else p.replace('fX', f'f{t}'))) for t in range(n)]
    return [load(O / p)]


STACK = [expand(p) for p in M['layer_order_bottom_to_top']]
TICKS = M['layer_ticks']


class Build(unittest.TestCase):
    def test_raw_hashes(self):
        for r in M['raw_inputs']:
            self.assertEqual(hashlib.sha256((R / r['file']).read_bytes()).hexdigest(), r['sha256'])

    def test_sizes_names_alpha_no_magenta(self):
        names = [Path(p).name for p in M['layer_order_bottom_to_top']]
        self.assertEqual(len(names), len(set(names))); self.assertTrue(all(n.startswith('ERN1_') for n in names))
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

    def test_cadences_loop(self):
        self.assertEqual((N['sables'], M['quicksand']['frame_length_ticks']), (4, 10))
        for p, t in zip(M['layer_order_bottom_to_top'], TICKS):
            if p.startswith('animation/'):
                self.assertEqual(M['scene_loop_ticks'] % (N[p.split('/')[1]] * t), 0)

    def test_quicksand_structure_loop(self):
        fr = STACK[0]; mask = fr[0][..., 3] == 255; pal = {tuple(v) for v in M['quicksand']['couleurs'].values()}
        for a in fr:
            self.assertTrue(((a[..., 3] == 255) == mask).all())
            self.assertTrue({tuple(c) for c in np.unique(a[mask][:, :3], axis=0)} <= pal)
        d = [int((fr[t][mask] != fr[(t + 1) % len(fr)][mask]).any(1).sum()) for t in range(len(fr))]
        self.assertTrue(min(d) > 0 and max(d) < 2 * min(d), d)

    def test_bubbles_only_on_visible_pits(self):
        pits = STACK[0][0][..., 3] == 255; land = np.zeros((H, W), bool)
        for frames in STACK[3:8]:
            land |= frames[0][..., 3] == 255
        for a in STACK[1]:
            self.assertFalse(((a[..., 3] > 0) & ~(pits & ~land)).any())
        self.assertGreater(min(int((a[..., 3] > 0).sum()) for a in STACK[1]), 0)
        b = M['bubbles']; self.assertLess(len(b['timeline_phases']), b['phases'])
        self.assertEqual(len({e['decalage'] for e in b['emetteurs']}), len(b['emetteurs']))

    def test_poses_nonempty(self):
        for k in M['bubbles']['poses'] + M['dust_devils']['poses']:
            self.assertGreater(int((load(O / f'poses/ERN1_{k}.png')[..., 3] > 0).sum()), 0, k)

    def test_dust_devils_loop_and_distinct(self):
        fr = STACK[M['layer_order_bottom_to_top'].index(next(p for p in M['layer_order_bottom_to_top'] if 'tourbillons' in p))]
        self.assertEqual(len(M['dust_devils']['positions']), 2)
        self.assertEqual(len({f.tobytes() for f in fr}), len(fr))             # 8 poses distinctes, boucle 7 -> 0 = pose suivante
        sand = STACK[3][0][..., 3] == 255                                      # posés sur le sable dégagé
        for x, y in M['dust_devils']['positions']:
            self.assertTrue(sand[y:y + 40, x:x + 40].all())

    def test_trees_stay_grey(self):
        a = STACK[-1][0]; v = a[a[..., 3] == 255][:, :3].astype(int)
        self.assertLess(float((v.max(1) - v.min(1)).mean()), 45)

    def test_ora_and_scene(self):
        with zipfile.ZipFile(O / 'ERN1_entree_ruine_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
        sc = Image.new('RGBA', (W, H))
        for frames in STACK:
            sc.alpha_composite(Image.fromarray(frames[0]))
        self.assertTrue((np.array(sc) == merged).all())
        self.assertTrue((np.array(sc) == load(O / 'review/ERN1_scene_t000.png')).all())

    def test_access(self):
        a = M['access']; self.assertTrue(a['path_found_16x16'])
        self.assertGreater(a['entry_px'][1], H - 64); self.assertLess(a['threshold_px'][1], H // 2)

    def test_ground_roundtrip(self):
        doc = json.loads((S / f"Data/Ground/{M['pmdo']['asset']}.rsground").read_text()); o = doc['Object']
        self.assertEqual(doc['Version'], '0.8.12.0'); self.assertEqual(len(o['Layers']), len(STACK) + 1)
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
        tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
        self.assertEqual(set(tools.read_index(S / 'Content/Tile/index.idx')), set(M['pmdo']['banks']))


if __name__ == '__main__':
    unittest.main()
