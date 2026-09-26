"""Tests dédiés — Entrée Waterfall Cave sud -> nord V1 (EWC1, 4:3 vaste).
.venv/bin/python -m unittest source.entree_waterfall_cave_sud_nord_v1.test_build -v
Contrôles d'images, de formats, de palettes, de fidélité au rip, de cadence et de grille : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, re, unittest, zipfile
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_waterfall_cave_sud_nord_v1'
S = R / '.cache/entree_waterfall_cave_sud_nord_v1/entree_waterfall_cave_sud_nord'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
NAMES = [Path(L['file']).name.replace('_fNN', '') for L in M['layers']]


def load(p):
    return np.array(Image.open(p).convert('RGBA'))


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def expand(L):
    if L['phases'] == 1:
        return [load(O / L['file'])]
    return [load(O / L['file'].replace('fNN', f'f{t:02d}')) for t in range(L['phases'])]


STACK = [expand(L) for L in M['layers']]
BY = {re.sub(r'^EWC1_\d\d_', '', Path(n).stem): fr for n, fr in zip(NAMES, STACK)}
MASK = {k: np.array(Image.open(O / f'masques/EWC1_masque_{k}.png')) > 0
        for k in ('water', 'cascade', 'ecume_pied', 'entree_sombre')}


def colors(frames):
    return {tuple(int(v) for v in c) for a in frames for c in np.unique(a[a[..., 3] == 255][:, :3], axis=0)}


class Build(unittest.TestCase):
    def test_raw_hashes_and_reference(self):
        for r in M['raw_inputs']:
            self.assertEqual(hashlib.sha256((R / r['file']).read_bytes()).hexdigest(), r['sha256'])
        ref = M['reference_da']
        self.assertEqual(hashlib.sha256((R / ref['file']).read_bytes()).hexdigest(), ref['sha256'])
        # chaque brut généré à partir du rip ou du décor référencé, prompts conservés
        self.assertEqual([g['file'] for g in M['generation']], ['decor_magenta.png', 'sol_complet.png', 'ecume_poses.png'])
        self.assertTrue(all(g['images'] and len(g['prompt']) > 100 for g in M['generation']))
        self.assertIn('entrancecascade.png', M['generation'][0]['images'])

    def test_sizes_names_alpha_no_magenta(self):
        self.assertEqual(len(NAMES), len(set(NAMES))); self.assertTrue(all(n.startswith('EWC1_') for n in NAMES))
        self.assertEqual((W, H, W % 8, H % 8), (768, 576, 0, 0)); self.assertEqual(W * 3, H * 4)   # 4:3
        n = M['normalization']; self.assertAlmostEqual(n['scale'], 576 / 896)
        self.assertEqual(n['scaled'][0] - sum(n['crop_x']), W)
        for frames in STACK:
            for a in frames:
                self.assertEqual(a.shape[:2], (H, W)); self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255})
                v = a[a[..., 3] > 0].astype(int)
                self.assertEqual(int(((v[:, 0] > 200) & (v[:, 2] > 200) & (v[:, 1] < 90)).sum()), 0)

    def test_multicalque_full_coverage(self):
        self.assertGreaterEqual(len(STACK), 15)
        cover = np.zeros((H, W), bool)
        for frames in STACK:
            cover |= frames[0][..., 3] == 255
        self.assertTrue(cover.all())
        # calques fixes exclusifs entre eux (aucun pixel doublé hors sol complet)
        fixed = [BY[k][0][..., 3] == 255 for k in ('sable', 'cailloux', 'touffes', 'plateaux', 'berge', 'falaises',
                                                   'arbres', 'entree_sombre', 'ecume_pied')]
        self.assertEqual(int(np.sum(fixed, 0).max()), 1)

    def test_palettes_separees(self):
        pg = M['normalization']['palettes']
        terrain = colors([BY[k][0] for k in pg['terrain']['calques']])
        self.assertLessEqual(len(terrain), 96)
        self.assertLessEqual(len(colors(BY['arbres'])), 24)
        self.assertLessEqual(len(colors(BY['cascade']) | colors(BY['ecume_pied'])), 24)
        self.assertLessEqual(len(colors(BY['entree_sombre'])), 12)
        # régressions du virage de palette : rideau bleu, bouche sombre
        cas = BY['cascade'][0]; px = cas[cas[..., 3] == 255][:, :3].astype(float)
        self.assertGreater(px[:, 2].mean(), px[:, 0].mean() + 60)
        cave = BY['entree_sombre'][0]; lum = cave[cave[..., 3] == 255][:, :3] @ [.299, .587, .114]
        self.assertLess(float(np.percentile(lum, 25)), 60)

    def test_fidelite_rip(self):
        B = loadmod('ewc1_build', HERE / 'build.py')
        dec, ref = B.rgb(HERE / 'bruts/decor_magenta.png'), B.rgb(R / 'entrancecascade.png')
        fid = B.fidelity(dec, ref, B.classify(dec)['cascade'])
        for k, v in fid.items():
            self.assertLess(v['distance'], 20, (k, v))                      # brut ≈ rip, matière par matière
            self.assertAlmostEqual(v['distance'], M['fidelite_rip']['brut'][k]['distance'], places=1)
        for k, v in M['fidelite_rip']['calques_finaux'].items():
            lay = BY[v['calque']][0]; px = lay[lay[..., 3] == 255][:, :3].astype(float)
            if v['calque'] == 'arbres':
                px = px[(px[:, 1] > px[:, 0] + 8) & (px[:, 1] > px[:, 2] + 20)]
            d = float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb'])))
            self.assertLess(d, 20, (k, d))                                  # calques finaux ≈ rip

    def test_water_metano_exact_and_loop(self):
        v2 = loadmod('esn2', R / 'source/entree_vapeur_sud_nord_v2/build.py')
        native = set()
        for i in range(1, 5):
            t = v2.decode_tile(R / f'source/eau_metano/natifs/Metano_Town_River_Animation_{i}.tile')
            native |= {tuple(int(v) for v in px[:3]) for a in t.values() for px in a.reshape(-1, 4) if px[3] == 255}
        fr = BY['eau']; mask = fr[0][..., 3] == 255
        self.assertEqual((len(fr), M['water']['frame_length_ticks']), (4, 10))
        for a in fr:
            self.assertTrue(((a[..., 3] == 255) == mask).all())
        self.assertTrue(colors(fr) <= native, colors(fr) - native)          # couleurs Métano EXACTES
        d = [int((fr[t][mask] != fr[(t + 1) % 4][mask]).any(1).sum()) for t in range(4)]
        self.assertTrue(min(d) > 0 and max(d) < 2 * min(d), d)              # 3 -> 0 compris

    def test_sparkles_native_pixels(self):
        v2 = loadmod('esn2', R / 'source/entree_vapeur_sud_nord_v2/build.py')
        native = {tuple(int(v) for v in px[:3]) for t in v2.decode_tile(R / M['sparkles']['source']).values()
                  for px in t.reshape(-1, 4) if px[3] == 255}
        for a in BY['scintillements']:
            cols = colors([a]); self.assertTrue(cols <= native); self.assertGreater(len(cols), 0)

    def test_cascade_pure_translation_closed_loop(self):
        fr = BY['cascade']; c = M['cascade']; step, n = c['step_px'], c['phases']
        self.assertEqual((n, c['frame_length_ticks'], c['period_px'] % n, step * n), (12, 4, 0, c['period_px']))
        mask = fr[0][..., 3] == 255; both = mask.copy(); both[:step] = False; both[step:] &= mask[:-step]
        for t in range(n):                                                  # 11 -> 0 compris : boucle fermée
            a, b = fr[t], fr[(t + 1) % n]
            self.assertTrue(((b[..., 3] == 255) == mask).all())
            shifted = np.zeros_like(a); shifted[step:] = a[:-step]
            self.assertTrue((b[both] == shifted[both]).all(), t)            # translation pure de 6 px vers le sud
            self.assertGreater(int((a[mask] != b[mask]).any(1).sum()), 1000)
        self.assertFalse((fr[0][..., 3] & MASK['entree_sombre']).any())      # la bouche n'est jamais recouverte

    def test_foam_spray_generated_loops(self):
        f = M['foam']
        for k, n in (('bouillon', 8), ('embrun', 4)):
            for i in range(n):
                self.assertEqual(load(O / f'poses/EWC1_{k}_{i}.png').shape, (32, 32, 4))
        clip = (MASK['water'] | MASK['ecume_pied'] | MASK['cascade']) & ~MASK['entree_sombre']
        for key, part in (('ecume', 'bouillon'), ('embruns', 'embruns')):
            fr = BY[key]; self.assertEqual((len(fr), f['frame_length_ticks']), (12, 4))
            seq, em = f[part]['sequence'], f[part]['emetteurs']
            for t, a in enumerate(fr):
                on = a[..., 3] > 0
                self.assertGreater(int(on.sum()), 20, (key, t))             # écume visible à chaque phase
                self.assertFalse((on & ~clip).any())                        # jamais sur le sable, les falaises ou la bouche
                self.assertTrue(any(seq[(t + e[2]) % len(seq)] >= 0 for e in em))
        self.assertEqual(M['foam']['bouillon']['sequence'][:8], list(range(8)))

    def test_ora_and_scene(self):
        with zipfile.ZipFile(O / 'EWC1_entree_waterfall_cave_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
            self.assertIn(b'Waterfall Cave', z.read('stack.xml'))
        sc = Image.new('RGBA', (W, H))
        for frames in STACK:
            sc.alpha_composite(Image.fromarray(frames[0]))
        self.assertTrue((np.array(sc) == merged).all())
        self.assertTrue((np.array(sc) == load(O / 'review/EWC1_scene_t000.png')).all())
        self.assertEqual(M['scene_loop_ticks'] % 40, 0); self.assertEqual(M['scene_loop_ticks'] % 48, 0)

    def test_access(self):
        a = M['access']; self.assertTrue(a['path_found_16x16'])
        self.assertGreater(a['entry_px'][1], H - 64); self.assertLess(a['threshold_px'][1], H // 2)
        cave = np.nonzero(MASK['entree_sombre'].any(0))[0]
        self.assertTrue(cave.min() - 16 <= a['threshold_px'][0] <= cave.max())   # seuil face à la bouche

    def test_prefix_and_namespace_unique(self):
        for p in (R / 'source').glob('*/build.py'):
            if p.parent != HERE:
                s = p.read_text(errors='ignore')
                self.assertNotIn("PFX = 'EWC1'", s, p); self.assertNotIn("'entree_waterfall_cave_sud_nord'", s, p)

    def test_ground_roundtrip(self):
        doc = json.loads((S / f"Data/Ground/{M['pmdo']['asset']}.rsground").read_text()); o = doc['Object']
        self.assertEqual(doc['Version'], '0.8.12.0'); self.assertEqual(len(o['Layers']), len(STACK) + 1)
        self.assertEqual(o['Layers'][-1]['Layer'], 4)
        nr = loadmod('native_reader', R / 'source/cote_v5_expeditions/audit_references.py')
        banks = {p.stem: nr.tiles(p)[1] for p in (S / 'Content/Tile').glob('*.tile')}
        self.assertEqual(set(banks), set(M['pmdo']['banks']))
        for li, (frames, L) in enumerate(zip(STACK, M['layers'])):
            for t in sorted({0, len(frames) // 2, len(frames) - 1}):
                out = np.zeros((H, W, 4), 'uint8')
                for x, col in enumerate(o['Layers'][li]['Tiles']):
                    for y, cell in enumerate(col):
                        for track in cell['Layers']:
                            if len(track['Frames']) > 1:
                                self.assertEqual((len(track['Frames']), track['FrameLength']), (len(frames), L['ticks']))
                            f = track['Frames'][t % len(track['Frames'])]
                            out[y*8:y*8+8, x*8:x*8+8] = np.array(nr.straight(banks[f['Sheet']][f['TexLoc']['X'], f['TexLoc']['Y']]))
                self.assertTrue((out == frames[t]).all(), (li, t))
        self.assertEqual(sum(w['Tags'] for c in o['obstacles'] for w in c), M['access']['blocked_cells'])
        self.assertEqual({m['EntName'] for m in o['Entities'][0]['Markers']}, {'entrance', 'donjon_seuil'})
        tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
        self.assertEqual(set(tools.read_index(S / 'Content/Tile/index.idx')), set(M['pmdo']['banks']))


if __name__ == '__main__':
    unittest.main()
