"""Tests dédiés — Entrée Cascade V2 (rendu généré référencé Waterfall Cave, 4:3 vaste).
.venv/bin/python -m unittest source.entree_cascade_sud_nord_v2.test_build -v
Contrôles d'images, de formats, de cadence et de grille : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, unittest, zipfile
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_cascade_sud_nord_v2'
S = R / '.cache/entree_cascade_sud_nord_v2/entree_cascade_sud_nord_v2'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
WP = M['water']['phases']


def load(p):
    return np.array(Image.open(p).convert('RGBA'))


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def expand(p):
    return [load(O / p.replace('fX', f'f{t}')) for t in range(WP)] if 'fX' in p else [load(O / p)]


STACK = [expand(p) for p in M['layer_order_bottom_to_top']]
TICKS = [10, 10, 10] + [60] * 6


class Build(unittest.TestCase):
    def test_raw_hashes_and_reference(self):
        for r in M['raw_inputs']:
            self.assertEqual(hashlib.sha256((R / r['file']).read_bytes()).hexdigest(), r['sha256'])
            self.assertEqual(r['size'], [1200, 896])
        for ref in M['reference_da']:
            self.assertTrue((R / ref).exists())

    def test_sizes_names_alpha_no_magenta(self):
        names = [Path(p).name for p in M['layer_order_bottom_to_top']]
        self.assertEqual(len(names), len(set(names))); self.assertTrue(all(n.startswith('ECN2_') for n in names))
        self.assertEqual((W, H, W % 8, H % 8), (768, 576, 0, 0)); self.assertEqual(W * 3, H * 4)
        n = M['normalization']; self.assertAlmostEqual(n['scale'], 576 / 896)
        self.assertEqual(n['scaled'][0] - sum(n['crop_x']), W)
        for frames in STACK:
            for a in frames:
                self.assertEqual(a.shape[:2], (H, W)); self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255})
                v = a[a[..., 3] > 0].astype(int)
                self.assertEqual(int(((v[:, 0] > 200) & (v[:, 2] > 200) & (v[:, 1] < 90)).sum()), 0)

    def test_full_coverage(self):
        cover = np.zeros((H, W), bool)
        for frames in STACK[:2] + STACK[3:]:
            cover |= frames[0][..., 3] == 255
        self.assertTrue(cover.all())

    def test_water_metano_structure_and_loop(self):
        fr = STACK[0]; mask = fr[0][..., 3] == 255; pal = {tuple(v) for v in M['water']['couleurs'].values()}
        for a in fr:
            self.assertTrue(((a[..., 3] == 255) == mask).all())
            self.assertTrue({tuple(int(v) for v in c) for c in np.unique(a[mask][:, :3], axis=0)} <= pal)
        d = [int((fr[t][mask] != fr[(t + 1) % WP][mask]).any(1).sum()) for t in range(WP)]
        self.assertTrue(min(d) > 0 and max(d) < 2 * min(d), d)
        # palette = couleurs exactes présentes dans les sources turquoise du rip Waterfall Cave (ledge)
        rip = np.array(Image.open(R / 'Waterfall_Cave_ledge_TDS.png').convert('RGB'))[273:373, 89:165].reshape(-1, 3)
        ripcols = {tuple(int(v) for v in c) for c in np.unique(rip, axis=0)}
        self.assertTrue(pal <= ripcols, pal - ripcols)

    def test_cascade_native_translation(self):
        cm = M['cascade']['mapping']; r0, r1, r2 = cm['rows']; body = r1 - r0
        mask = STACK[1][0][..., 3] == 255
        yy, xx = np.mgrid[:H, :W]; k = cm['y_bottom'] - yy
        src_row = np.where(k <= (r2 - r1), r2 - k, r1 - 1 - ((k - (r2 - r1) - 1) % body)); src_col = 8 + ((xx - cm['x_left']) % 48)
        for t, a in enumerate(STACK[1]):
            nat = np.array(Image.open(R / f'sprites/eau_metano/cascade_frame_{t + 1}.png').convert('RGBA'))
            self.assertTrue(((a[..., 3] == 255) == mask).all())
            self.assertTrue(np.array_equal(a[mask][:, :3], nat[src_row[mask], src_col[mask]][:, :3]))
            self.assertTrue((nat[src_row[mask], src_col[mask]][:, 3] == 255).all())
        self.assertEqual(len({a.tobytes() for a in STACK[1]}), WP)
        self.assertEqual(M['cascade']['frame_length_ticks'], 10)

    def test_sparkles_native_pixels(self):
        v2 = loadmod('esn2', R / 'source/entree_vapeur_sud_nord_v2/build.py')
        native = {tuple(int(v) for v in px[:3]) for t in v2.decode_tile(R / M['sparkles']['source']).values() for px in t.reshape(-1, 4) if px[3] == 255}
        water = STACK[0][0][..., 3] == 255
        for a in STACK[2]:
            cols = {tuple(int(v) for v in c) for c in np.unique(a[a[..., 3] > 0][:, :3], axis=0)}
            self.assertTrue(cols <= native); self.assertGreater(len(cols), 0)
            self.assertTrue(water[a[..., 3] == 255].all())

    def test_ora_and_scene(self):
        with zipfile.ZipFile(O / 'ECN2_entree_cascade_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
        sc = Image.new('RGBA', (W, H))
        for frames in STACK:
            sc.alpha_composite(Image.fromarray(frames[0]))
        self.assertTrue((np.array(sc) == merged).all())
        self.assertTrue((np.array(sc) == load(O / 'review/ECN2_scene_t000.png')).all())
        with Image.open(O / 'review/ECN2_scene_animee.webp') as im:
            self.assertEqual(im.n_frames, WP)
        self.assertEqual(M['scene_loop_ticks'], 40)

    def test_access(self):
        a = M['access']; self.assertTrue(a['path_found_16x16'])
        self.assertGreater(a['entry_px'][1], H - 64); self.assertLess(a['threshold_px'][1], H // 2)
        falls = STACK[1][0][..., 3] == 255; fx = np.nonzero(falls.any(0))[0]
        self.assertTrue(fx[0] <= a['threshold_px'][0] + 8 <= fx[-1])        # seuil sous la cascade
        self.assertGreaterEqual(a['threshold_px'][1], M['cascade']['mapping']['y_bottom'])

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
