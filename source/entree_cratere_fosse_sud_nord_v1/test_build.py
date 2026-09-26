"""Tests dédiés — Entrée fosse du Dark Crater sud -> nord V1 (ECF1, 4:3 vaste).
.venv/bin/python -m unittest source.entree_cratere_fosse_sud_nord_v1.test_build -v
Contrôles d'images, de formats, de palettes, de fidélité au rip, de cadence et de grille : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, re, unittest, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_cratere_fosse_sud_nord_v1'
S = R / '.cache/entree_cratere_fosse_sud_nord_v1/entree_cratere_fosse_sud_nord'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
NAMES = [Path(L['file']).name.replace('_fNN', '') for L in M['layers']]
STATIC = ('sol', 'bordures', 'pics', 'paroi', 'grotte')


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
BY = {re.sub(r'^ECF1_\d\d_', '', Path(n).stem): fr for n, fr in zip(NAMES, STACK)}
ORDER = list(BY)
MASK = {k: np.array(Image.open(O / f'masques/ECF1_masque_{k}.png')) > 0 for k in ('lava', 'grotte', 'sol', 'bordures')}


def alpha(a):
    return a[..., 3] == 255


def colors(frames):
    return {tuple(int(v) for v in c) for a in frames for c in np.unique(a[a[..., 3] == 255][:, :3], axis=0)}


def step_changes(frames):
    n = len(frames)
    return [int((frames[t] != frames[(t + 1) % n]).any(-1).sum()) for t in range(n)]


class Build(unittest.TestCase):
    def test_raw_hashes_and_reference(self):
        for r in M['raw_inputs']:
            self.assertEqual(hashlib.sha256((R / r['file']).read_bytes()).hexdigest(), r['sha256'])
        ref = M['reference_da']
        self.assertEqual(ref['file'], 'Dark_Crater_Pit_TDS.png')
        self.assertEqual(hashlib.sha256((R / ref['file']).read_bytes()).hexdigest(), ref['sha256'])
        g = M['generation']
        self.assertEqual([x['file'] for x in g], ['decor_magenta.png', 'sol_complet.png', 'bulles_lave_poses.png'])
        self.assertTrue(all(x['images'] and len(x['prompt']) > 100 for x in g))
        self.assertIn('Dark_Crater_Pit_TDS.png', g[0]['images'])      # décor et planche : rip en référence
        self.assertIn('Dark_Crater_Pit_TDS.png', g[2]['images'])
        self.assertTrue(g[1]['images'][0].endswith('bruts/decor_magenta.png'))    # sol : édité depuis le décor
        self.assertIn('choisi par l agent', M['biome'])
        self.assertFalse(M['art_approved']); self.assertFalse(M['pmdo']['runtime_tested'])

    def test_sizes_names_alpha_no_magenta(self):
        self.assertEqual(len(NAMES), len(set(NAMES))); self.assertTrue(all(n.startswith('ECF1_') for n in NAMES))
        self.assertEqual((W, H, W % 8, H % 8), (768, 576, 0, 0)); self.assertEqual(W * 3, H * 4)   # 4:3
        n = M['normalization']; self.assertAlmostEqual(n['scale'], 576 / 896)
        self.assertEqual(n['scaled'][0] - sum(n['crop_x']), W)
        for frames in STACK:
            for a in frames:
                self.assertEqual(a.shape[:2], (H, W)); self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255})
                v = a[a[..., 3] > 0].astype(int)
                self.assertEqual(int(((v[:, 0] > 200) & (v[:, 2] > 200) & (v[:, 1] < 90)).sum()), 0)

    def test_multicalque_full_coverage_and_order(self):
        self.assertEqual(ORDER, ['lave', 'bulles', 'sol_complet', *STATIC])
        cover = np.zeros((H, W), bool)
        for frames in STACK:
            cover |= alpha(frames[0])
        self.assertTrue(cover.all())
        fixed = [alpha(BY[k][0]) for k in STATIC]                          # calques fixes exclusifs entre eux
        self.assertEqual(int(np.sum(fixed, 0).max()), 1)
        for k in STATIC:
            self.assertGreater(int(alpha(BY[k][0]).sum()), 200, k)        # aucun calque vide

    def test_palettes_separees(self):
        pg = M['normalization']['palettes']
        self.assertLessEqual(len(colors([BY[k][0] for k in pg['terrain']['calques']])), 96)
        self.assertLessEqual(len(colors(BY['pics'])), 16); self.assertLessEqual(len(colors(BY['paroi'])), 32)
        self.assertLessEqual(len(colors(BY['grotte'])), 8)
        dp = BY['grotte'][0]; lum = dp[alpha(dp)][:, :3] @ [.299, .587, .114]
        self.assertLess(float(np.median(lum)), 40)                        # bouche sombre
        so = BY['sol'][0]; px = so[alpha(so)][:, :3].astype(float); sat = px.max(1) - px.min(1)
        self.assertLess(float(sat.mean()), 30)                             # sol gris-brun

    def test_fidelite_rip(self):
        B = loadmod('ecf1_build', HERE / 'build.py')
        dec, ref = B.rgb(HERE / 'bruts/decor_magenta.png'), B.rgb(R / 'Dark_Crater_Pit_TDS.png')
        fid = B.fidelity(dec, ref)
        for k, v in fid.items():
            self.assertLess(v['distance'], 30, (k, v))                      # roche noire du brut plus sombre (28,8)
            self.assertAlmostEqual(v['distance'], M['fidelite_rip']['brut'][k]['distance'], places=1)
        for k, v in M['fidelite_rip']['calques_finaux'].items():
            lay = BY[v['calque']][0]; px = lay[alpha(lay)][:, :3].astype(float)
            sel = B.materials(px.reshape(-1, 1, 3))[k][:, 0]
            px = px[sel] if sel.sum() > 50 else px
            d = float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb'])))
            self.assertLess(d, 35, (k, d))                                  # calques finaux (bordures 32,5)

    def test_lave_couleurs_exactes_et_boucle(self):
        ref = np.array(Image.open(R / 'Dark_Crater_Pit_TDS.png').convert('RGB')).reshape(-1, 3)
        rip = {tuple(int(v) for v in c) for c in np.unique(ref, axis=0)}
        fr = BY['lave']; self.assertEqual((len(fr), M['lave']['frame_length_ticks']), (12, 8))
        self.assertTrue(colors(fr) <= rip, colors(fr) - rip)                 # couleurs EXACTES du rip
        self.assertGreaterEqual(len(colors(fr)), 9)
        mask = alpha(fr[0]); self.assertGreater(int(mask.sum()), 100000)
        for a in fr:
            self.assertTrue((alpha(a) == mask).all())
        land = np.zeros((H, W), bool)
        for k in STATIC:
            land |= alpha(BY[k][0])
        self.assertFalse((mask & land).any())
        rim = mask & nd.binary_dilation(land)
        for a in fr:
            self.assertTrue((a[rim][:, :3] == (247, 39, 31)).all())          # bande rouge contre la roche
        B = loadmod('ecf1_build', HERE / 'build.py')
        dist = nd.distance_transform_edt(mask)
        self.assertTrue((B.lava_frames(mask, dist, ts=[12])[0] == fr[0]).all())   # 12 = 0
        d = step_changes(fr); self.assertTrue(min(d) > 0 and max(d) < 2 * min(d), d)   # 11 -> 0 compris

    def test_bulles_boucle_fermee(self):
        f = M['bulles']; B = loadmod('ecf1_build', HERE / 'build.py')
        poses = [load(O / f'poses/ECF1_bulle_{i}.png') for i in range(6)]
        fr = BY['bulles']; self.assertEqual((len(fr), f['frame_length_ticks']), (24, 4))
        self.assertLessEqual(len(colors(fr)), 8)
        calc = B.bubble_frames(poses, f['points'])
        lave = alpha(BY['lave'][0])
        for t, a in enumerate(fr):
            calc[t][~lave] = 0
            self.assertTrue((a == calc[t]).all(), t)
            self.assertFalse((alpha(a) & ~lave).any())                       # bulles seulement sur la lave
        self.assertTrue(any(alpha(a).any() for a in fr))
        self.assertTrue((B.bubble_frames(poses, f['points'], ts=[24])[0] == B.bubble_frames(poses, f['points'], ts=[0])[0]).all())

    def test_ora_and_scene(self):
        with zipfile.ZipFile(O / 'ECF1_entree_cratere_fosse_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
            self.assertIn(b'Dark Crater', z.read('stack.xml'))
        sc = Image.new('RGBA', (W, H))
        for frames in STACK:
            sc.alpha_composite(Image.fromarray(frames[0]))
        self.assertTrue((np.array(sc) == merged).all())
        self.assertTrue((np.array(sc) == load(O / 'review/ECF1_scene_t000.png')).all())
        self.assertEqual(M['scene_loop_ticks'], 96)

    def test_access(self):
        a = M['access']; self.assertTrue(a['path_found_16x16'])
        ex, ey = a['entry_px']; tx, ty = a['threshold_px']
        self.assertGreater(ey, H - 64); self.assertLess(ty, H // 3)
        self.assertTrue(MASK['sol'][ey:ey + 16, ex:ex + 16].mean() > 0.5)   # arrivée sur le chemin
        dp = nd.distance_transform_edt(~MASK['grotte'])
        self.assertLess(float(dp[ty:ty + 16, tx:tx + 16].min()), 40)          # seuil devant la grotte
        self.assertEqual(a['walkable_cells'] + a['blocked_cells'], (W // 8) * (H // 8))
        self.assertGreater(a['walkable_cells'], 800)                         # camp vaste

    def test_prefix_and_namespace_unique(self):
        for p in (R / 'source').glob('*/build.py'):
            if p.parent != HERE:
                s = p.read_text(errors='ignore')
                self.assertNotIn("PFX = 'ECF1'", s, p); self.assertNotIn("'entree_cratere_fosse_sud_nord'", s, p)

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
