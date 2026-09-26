"""Tests dédiés — Entrée Amp sud -> nord V1 (4:3 vaste).
.venv/bin/python -m unittest source.entree_amp_sud_nord_v1.test_build -v
Contrôles d'images, de formats, de cadence et de grille : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, unittest, zipfile
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_amp_sud_nord_v1'
S = R / '.cache/entree_amp_sud_nord_v1/entree_amp_sud_nord'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
TP, SP = M['touffes']['phases'], M['etincelles']['phases']


def load(p):
    return np.array(Image.open(p).convert('RGBA'))


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def expand(p):
    if 'fXX' in p:
        n = TP if 'touffes' in p else SP
        return [load(O / p.replace('fXX', f'f{t:02d}')) for t in range(n)]
    return [load(O / p)]


STACK = [expand(p) for p in M['layer_order_bottom_to_top']]
TICKS = [60] * 7 + [M['touffes']['frame_length_ticks'], M['etincelles']['frame_length_ticks']]


class Build(unittest.TestCase):
    def test_raw_hashes(self):
        for r in M['raw_inputs']:
            self.assertEqual(hashlib.sha256((R / r['file']).read_bytes()).hexdigest(), r['sha256'])

    def test_sizes_names_alpha_no_magenta(self):
        names = [Path(p).name for p in M['layer_order_bottom_to_top']]
        self.assertEqual(len(names), len(set(names))); self.assertTrue(all(n.startswith('EAN1_') for n in names))
        self.assertEqual((W, H, W % 8, H % 8), (768, 576, 0, 0)); self.assertEqual(W * 3, H * 4)   # 4:3
        n = M['normalization']; self.assertAlmostEqual(n['scale'], 576 / 896)
        self.assertEqual(n['scaled'][0] - sum(n['crop_x']), W)
        for frames in STACK:
            for a in frames:
                self.assertEqual(a.shape[:2], (H, W)); self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255})
                v = a[a[..., 3] > 0].astype(int)
                self.assertEqual(int(((v[:, 0] > 200) & (v[:, 2] > 200) & (v[:, 1] < 90)).sum()), 0)

    def test_full_coverage(self):
        cover = np.zeros((H, W), bool)
        for frames in STACK[:7]:
            cover |= frames[0][..., 3] == 255
        self.assertTrue(cover.all())

    def test_tufts_measured_cycle(self):
        tu = M['touffes']; self.assertEqual(tu['poses'], 8); self.assertEqual(TP, 12)
        leans = np.array(tu['inclinaisons_mesurees']); cyc = tu['cycle']
        self.assertEqual(len(cyc), 12); self.assertTrue(all(0 <= c < 8 for c in cyc))
        # borne de tan : pas sinusoïdal max + granularité des poses (un cycle mélangé la violerait)
        mid = (leans.max() + leans.min()) / 2; amp = (leans.max() - leans.min()) / 2
        bound = amp * 2 * np.pi / 12 + np.diff(np.sort(leans)).max() + 1e-9
        steps = [abs(float(leans[cyc[(t + 1) % 12]] - leans[cyc[t]])) for t in range(12)]
        self.assertLessEqual(max(steps), bound, (steps, bound))
        self.assertGreater(len(set(cyc)), 2)   # le cycle utilise vraiment plusieurs poses
        poses = [load(O / f'poses_touffes/EAN1_touffe_{i}.png') for i in range(8)]
        pal = {tuple(v) for v in tu['palette_7']}
        for p in poses:
            self.assertEqual(p.shape, (16, 16, 4)); self.assertGreater((p[..., 3] > 0).sum(), 20)
            self.assertTrue({tuple(int(v) for v in c) for c in np.unique(p[p[..., 3] > 0][:, :3], axis=0)} <= pal)
        n = [int((a[..., 3] > 0).sum()) for a in STACK[7]]
        self.assertGreater(min(n), 10 * 20)    # les 10 touffes visibles à chaque phase
        self.assertEqual(len(tu['emetteurs']), 10)

    def test_sparks_lifecycle(self):
        sp = M['etincelles']; self.assertEqual(sp['poses'], 8); self.assertEqual(SP, 24)
        poses = [load(O / f'poses_etincelles/EAN1_etincelle_{i}.png') for i in range(8)]
        spal = {tuple(v) for v in sp['palette_12']}
        for p in poses:
            self.assertEqual(p.shape, (24, 24, 4)); self.assertGreater((p[..., 3] > 0).sum(), 15)
            self.assertTrue({tuple(int(v) for v in c) for c in np.unique(p[p[..., 3] > 0][:, :3], axis=0)} <= spal)
        for i in range(8):
            for j in range(i + 1, 8):
                self.assertTrue((poses[i] != poses[j]).any(), (i, j))
        offs = [e['decalage'] for e in sp['emetteurs']]
        for t in range(24):   # toujours au moins une étincelle active : pas de phase morte
            self.assertTrue(any((t - o) % 24 < M['etincelles']['phases_actives'] for o in offs), t)
        n = [int((a[..., 3] > 0).sum()) for a in STACK[8]]
        self.assertTrue(all(v > 0 for v in n), n)
        # ordre exact du lifecycle sur l'émetteur 0 (pas de chevauchement entre émetteurs)
        x, y = sp['emetteurs'][0]['xy']; o0 = sp['emetteurs'][0]['decalage']
        for t in range(24):
            cell = STACK[8][t][y:y + 24, x:x + 24]
            u = (t - o0) % 24
            if u < M['etincelles']['phases_actives']:
                self.assertTrue((cell == poses[u // 2]).all(), t)
            else:
                self.assertEqual(int((cell[..., 3] > 0).sum()), 0, t)

    def test_canonical_grass(self):
        # « même endroit » : l'herbe du décor reste proche de celle de la ref canonique (moyennes).
        ref = np.array(Image.open(R / 'Amp_Plains_entrance_TD.png').convert('RGB')).astype(int)
        rr, rg, rb_ = ref.transpose(2, 0, 1); rlum = ref @ [.299, .587, .114]
        rm = ref[((rr - rb_) > 15) & (rlum > 100) & (rlum < 175)][:, :3].mean(0)
        dec = STACK[1][0]; v = dec[dec[..., 3] > 0][:, :3].astype(int)
        lum = v @ [.299, .587, .114]
        dm = v[((v[:, 0] - v[:, 2]) > 15) & (lum > 100) & (lum < 175)].mean(0)
        self.assertLess(float(np.linalg.norm(dm - rm)), 35, (dm, rm))
        self.assertLess(M['canonique']['distance'], 35)

    def test_ora_and_scene(self):
        with zipfile.ZipFile(O / 'EAN1_entree_amp_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
        sc = Image.new('RGBA', (W, H))
        for frames in STACK:
            sc.alpha_composite(Image.fromarray(frames[0]))
        self.assertTrue((np.array(sc) == merged).all())
        self.assertTrue((np.array(sc) == load(O / 'review/EAN1_scene_t000.png')).all())

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
