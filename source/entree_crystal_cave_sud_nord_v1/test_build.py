"""Tests dédiés — Entrée Grotte de cristal sud -> nord V1 (ECC1, 4:3 vaste).
.venv/bin/python -m unittest source.entree_crystal_cave_sud_nord_v1.test_build -v
Contrôles d'images, de formats, de palettes, de fidélité au rip, de cadence et de grille : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, re, unittest, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_crystal_cave_sud_nord_v1'
S = R / '.cache/entree_crystal_cave_sud_nord_v1/entree_crystal_cave_sud_nord'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
NAMES = [Path(L['file']).name.replace('_fNN', '') for L in M['layers']]
STATIC = ('sol', 'vide', 'fond', 'stalactites', 'rochers', 'racines', 'cristaux', 'grotte')


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
BY = {re.sub(r'^ECC1_\d\d_', '', Path(n).stem): fr for n, fr in zip(NAMES, STACK)}
ORDER = list(BY)
MASK = {k: np.array(Image.open(O / f'masques/ECC1_masque_{k}.png')) > 0 for k in ('water', 'grotte', 'sol', 'cristaux')}


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
        self.assertEqual(ref['file'], 'Waterfall_Cave_gem_TDS.png')
        self.assertEqual(hashlib.sha256((R / ref['file']).read_bytes()).hexdigest(), ref['sha256'])
        g = M['generation']
        self.assertEqual([x['file'] for x in g], ['decor_magenta.png', 'sol_complet.png', 'eclats_poses.png'])
        self.assertTrue(all(x['images'] and len(x['prompt']) > 100 for x in g))
        self.assertIn('Waterfall_Cave_gem_TDS.png', g[0]['images'])      # décor et planche : rip en référence
        self.assertIn('Waterfall_Cave_gem_TDS.png', g[2]['images'])
        self.assertTrue(g[1]['images'][0].endswith('bruts/decor_magenta.png'))    # sol : édité depuis le décor
        self.assertIn('choisie par l agent', M['biome'])
        self.assertFalse(M['art_approved']); self.assertFalse(M['pmdo']['runtime_tested'])

    def test_sizes_names_alpha_no_magenta(self):
        self.assertEqual(len(NAMES), len(set(NAMES))); self.assertTrue(all(n.startswith('ECC1_') for n in NAMES))
        self.assertEqual((W, H, W % 8, H % 8), (768, 576, 0, 0)); self.assertEqual(W * 3, H * 4)   # 4:3
        n = M['normalization']; self.assertAlmostEqual(n['scale'], 576 / 896)
        self.assertEqual(n['scaled'][0] - sum(n['crop_x']), W)
        for frames in STACK:
            for a in frames:
                self.assertEqual(a.shape[:2], (H, W)); self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255})
                v = a[a[..., 3] > 0].astype(int)
                self.assertEqual(int(((v[:, 0] > 200) & (v[:, 2] > 200) & (v[:, 1] < 90)).sum()), 0)

    def test_multicalque_full_coverage_and_order(self):
        self.assertEqual(ORDER, ['eau', 'scintillements', 'sol_complet', *STATIC, 'eclats'])
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
        for g_, v in pg.items():
            self.assertLessEqual(len(colors([BY[k][0] for k in v['calques']])), v['couleurs'], g_)
        so = BY['sol'][0]; px = so[alpha(so)][:, :3].astype(float).mean(0)
        self.assertGreater(px[2], px[0] + 50)                              # galets bleus
        fo = BY['fond'][0]; pf = fo[alpha(fo)][:, :3].astype(float).mean(0)
        self.assertGreater(pf[0], pf[1] + 20)                              # fond marron
        gr = BY['grotte'][0]; lum = gr[alpha(gr)][:, :3] @ [.299, .587, .114]
        self.assertLess(float(np.percentile(lum, 50)), 40)                 # tunnel sombre
        cr = BY['cristaux'][0]; c = cr[alpha(cr)][:, :3].astype(int)
        self.assertGreater(float((c.max(1) - c.min(1)).mean()), 50)        # cristaux saturés

    def test_fidelite_rip(self):
        B = loadmod('ecc1_build', HERE / 'build.py')
        dec, ref = B.rgb(HERE / 'bruts/decor_magenta.png'), B.rgb(R / 'Waterfall_Cave_gem_TDS.png')
        fid = B.fidelity(dec, ref)
        for k, v in fid.items():
            self.assertLess(v['distance'], 25, (k, v))                      # brut ≈ rip, matière par matière
            self.assertAlmostEqual(v['distance'], M['fidelite_rip']['brut'][k]['distance'], places=1)
        for k, v in M['fidelite_rip']['calques_finaux'].items():
            lay = BY[v['calque']][0]; px = lay[alpha(lay)][:, :3].astype(float)
            sel = B.materials(px.reshape(-1, 1, 3))[k][:, 0]
            px = px[sel] if sel.sum() > 50 else px
            d = float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb'])))
            self.assertLess(d, 25, (k, d))                                  # calques finaux ≈ rip

    def test_water_couleurs_rip_sans_lisere(self):
        ref = np.array(Image.open(R / 'Waterfall_Cave_gem_TDS.png').convert('RGB')).reshape(-1, 3)
        rip = {tuple(int(v) for v in c) for c in np.unique(ref, axis=0)}
        fr = BY['eau']; mask = alpha(fr[0])
        self.assertEqual((len(fr), M['water']['frame_length_ticks']), (4, 10))
        self.assertGreater(int(mask.sum()), 20000)
        for a in fr:
            self.assertTrue((alpha(a) == mask).all())
        self.assertTrue(colors(fr) <= rip, colors(fr) - rip)                # couleurs EXACTES du rip
        land = np.zeros((H, W), bool)
        for k in STATIC:
            land |= alpha(BY[k][0])
        rim = mask & ~land & nd.binary_dilation(land)
        bande = np.array(M['water']['couleurs']['bande'])
        for a in fr:
            self.assertTrue((a[rim][:, :3] == bande).all())                 # contre la rive : bande sombre seule
        d = [int((fr[t][mask] != fr[(t + 1) % 4][mask]).any(1).sum()) for t in range(4)]
        self.assertTrue(min(d) > 0 and max(d) < 2 * min(d), d)              # 3 -> 0 compris

    def test_sparkles_native_pixels(self):
        v2 = loadmod('esn2', R / 'source/entree_vapeur_sud_nord_v2/build.py')
        native = {tuple(int(v) for v in px[:3]) for t in v2.decode_tile(R / M['sparkles']['source']).values()
                  for px in t.reshape(-1, 4) if px[3] == 255}
        for a in BY['scintillements']:
            cols = colors([a]); self.assertTrue(cols <= native); self.assertGreater(len(cols), 0)
            self.assertFalse((alpha(a) & ~MASK['water']).any())

    def test_eclats_boucle_fermee(self):
        e = M['eclats']; B = loadmod('ecc1_build', HERE / 'build.py')
        poses = [[load(O / f'poses/ECC1_eclat_{c}_{i}.png') for i in range(4)] for c in ('cyan', 'rose')]
        fr = BY['eclats']; self.assertEqual((len(fr), e['frame_length_ticks']), (48, 5))
        self.assertLessEqual(len(colors(fr)), 10)
        calc = B.glint_frames(poses, e['points'])
        for t, a in enumerate(fr):
            self.assertTrue((a == calc[t]).all(), t)                        # fichiers = chronologie du manifeste
            self.assertGreater(int(alpha(a).sum()), 5)                      # au moins un éclat à chaque phase
        self.assertTrue((B.glint_frames(poses, e['points'], ts=[48])[0] == fr[0]).all())    # 48 = 0
        cr = nd.binary_dilation(MASK['cristaux'], iterations=4)
        for x, y, _, _ in e['points']:
            self.assertTrue(cr[y + 2, x], (x, y))                            # posés sur un cristal
        self.assertEqual(len(e['points']), 18)

    def test_ora_and_scene(self):
        with zipfile.ZipFile(O / 'ECC1_entree_crystal_cave_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
            self.assertIn(b'Grotte de cristal', z.read('stack.xml'))
        sc = Image.new('RGBA', (W, H))
        for frames in STACK:
            sc.alpha_composite(Image.fromarray(frames[0]))
        self.assertTrue((np.array(sc) == merged).all())
        self.assertTrue((np.array(sc) == load(O / 'review/ECC1_scene_t000.png')).all())
        self.assertEqual(M['scene_loop_ticks'] % 40, 0); self.assertEqual(M['scene_loop_ticks'] % 240, 0)

    def test_access(self):
        a = M['access']; self.assertTrue(a['path_found_16x16'])
        ex, ey = a['entry_px']; tx, ty = a['threshold_px']
        self.assertGreater(ey, H - 64); self.assertLess(ty, H // 2)   # haut du sol : le tunnel est sur la paroi du fond
        self.assertTrue(MASK['sol'][ey:ey + 16, ex:ex + 16].mean() > 0.5)   # arrivée sur le sol de galets
        dp = nd.distance_transform_edt(~MASK['grotte'])
        self.assertLess(float(dp[ty:ty + 16, tx:tx + 16].min()), 120)         # seuil au plus près du tunnel (paroi du fond)
        self.assertEqual(a['walkable_cells'] + a['blocked_cells'], (W // 8) * (H // 8))
        self.assertGreater(a['walkable_cells'], 1000)                         # salle vaste

    def test_prefix_and_namespace_unique(self):
        for p in (R / 'source').glob('*/build.py'):
            if p.parent != HERE:
                s = p.read_text(errors='ignore')
                self.assertNotIn("PFX = 'ECC1'", s, p); self.assertNotIn("'entree_crystal_cave_sud_nord'", s, p)

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
