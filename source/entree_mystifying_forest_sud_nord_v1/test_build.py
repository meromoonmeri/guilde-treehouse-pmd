"""Tests dédiés — Entrée Mystifying Forest sud -> nord V1 (EMF1, 4:3 vaste).
.venv/bin/python -m unittest source.entree_mystifying_forest_sud_nord_v1.test_build -v
Contrôles d'images, de formats, de palettes, de fidélité au rip, de cadence et de grille : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, re, unittest, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_mystifying_forest_sud_nord_v1'
S = R / '.cache/entree_mystifying_forest_sud_nord_v1/entree_mystifying_forest_sud_nord'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
NAMES = [Path(L['file']).name.replace('_fNN', '') for L in M['layers']]
STATIC = ('herbe', 'chemin', 'herbes_hautes', 'rochers', 'arbres', 'profondeur')


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
BY = {re.sub(r'^EMF1_\d\d_', '', Path(n).stem): fr for n, fr in zip(NAMES, STACK)}
ORDER = list(BY)
MASK = {k: np.array(Image.open(O / f'masques/EMF1_masque_{k}.png')) > 0 for k in ('water', 'profondeur', 'chemin', 'herbe')}


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
        self.assertEqual(ref['file'], 'Mystifying_Forest_entrance_TDS.png')
        self.assertEqual(hashlib.sha256((R / ref['file']).read_bytes()).hexdigest(), ref['sha256'])
        g = M['generation']
        self.assertEqual([x['file'] for x in g], ['decor_magenta.png', 'sol_complet.png', 'feuilles_lucioles_poses.png'])
        self.assertTrue(all(x['images'] and len(x['prompt']) > 100 for x in g))
        self.assertIn('Mystifying_Forest_entrance_TDS.png', g[0]['images'])      # décor et planche : rip en référence
        self.assertIn('Mystifying_Forest_entrance_TDS.png', g[2]['images'])
        self.assertTrue(g[1]['images'][0].endswith('bruts/decor_magenta.png'))    # sol : édité depuis le décor
        self.assertIn('a confirmer', M['biome'])
        self.assertFalse(M['art_approved']); self.assertFalse(M['pmdo']['runtime_tested'])

    def test_sizes_names_alpha_no_magenta(self):
        self.assertEqual(len(NAMES), len(set(NAMES))); self.assertTrue(all(n.startswith('EMF1_') for n in NAMES))
        self.assertEqual((W, H, W % 8, H % 8), (768, 576, 0, 0)); self.assertEqual(W * 3, H * 4)   # 4:3
        n = M['normalization']; self.assertAlmostEqual(n['scale'], 576 / 896)
        self.assertEqual(n['scaled'][0] - sum(n['crop_x']), W)
        for frames in STACK:
            for a in frames:
                self.assertEqual(a.shape[:2], (H, W)); self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255})
                v = a[a[..., 3] > 0].astype(int)
                self.assertEqual(int(((v[:, 0] > 200) & (v[:, 2] > 200) & (v[:, 1] < 90)).sum()), 0)

    def test_multicalque_full_coverage_and_order(self):
        self.assertEqual(ORDER, ['eau', 'scintillements', 'sol_complet', *STATIC, 'feuilles', 'lucioles'])
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
        self.assertLessEqual(len(colors(BY['arbres'])), 40)
        self.assertLessEqual(len(colors(BY['rochers'])), 16)
        self.assertLessEqual(len(colors(BY['profondeur'])), 12)
        ch = BY['chemin'][0]; px = ch[alpha(ch)][:, :3].astype(float).mean(0)
        self.assertGreater(px[0], px[2] + 12)                              # chemin rose-brun, pas vert
        dp = BY['profondeur'][0]; lum = dp[alpha(dp)][:, :3] @ [.299, .587, .114]
        self.assertLess(float(np.percentile(lum, 50)), 45)                 # ouverture sombre
        sol = BY['sol_complet'][0]; ls = sol[alpha(sol)][:, :3] @ [.299, .587, .114]
        self.assertGreater(float(np.percentile(ls, 1)), 45)                # bande et rectangle sombres réparés

    def test_fidelite_rip(self):
        B = loadmod('emf1_build', HERE / 'build.py')
        dec, ref = B.rgb(HERE / 'bruts/decor_magenta.png'), B.rgb(R / 'Mystifying_Forest_entrance_TDS.png')
        fid = B.fidelity(dec, ref)
        for k, v in fid.items():
            self.assertLess(v['distance'], 20, (k, v))                      # brut ≈ rip, matière par matière
            self.assertAlmostEqual(v['distance'], M['fidelite_rip']['brut'][k]['distance'], places=1)
        for k, v in M['fidelite_rip']['calques_finaux'].items():
            lay = BY[v['calque']][0]; px = lay[alpha(lay)][:, :3].astype(float)
            sel = B.materials(px.reshape(-1, 1, 3))[k][:, 0]
            px = px[sel] if sel.sum() > 50 else px
            d = float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb'])))
            self.assertLess(d, 20, (k, d))                                  # calques finaux ≈ rip

    def test_water_metano_sans_lisere(self):
        v2 = loadmod('esn2', R / 'source/entree_vapeur_sud_nord_v2/build.py')
        native = set()
        for i in range(1, 5):
            t = v2.decode_tile(R / f'source/eau_metano/natifs/Metano_Town_River_Animation_{i}.tile')
            native |= {tuple(int(v) for v in px[:3]) for a in t.values() for px in a.reshape(-1, 4) if px[3] == 255}
        fr = BY['eau']; mask = alpha(fr[0])
        self.assertEqual((len(fr), M['water']['frame_length_ticks']), (4, 10))
        self.assertGreater(int(mask.sum()), 3000)
        for a in fr:
            self.assertTrue((alpha(a) == mask).all())
        self.assertTrue(colors(fr) <= native, colors(fr) - native)          # couleurs Métano EXACTES
        self.assertNotIn((148, 230, 238), colors(fr))                       # pas de liseré clair (retour EWC1)
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

    def test_feuilles_boucle_fermee(self):
        f = M['feuilles']; B = loadmod('emf1_build', HERE / 'build.py')
        poses = [load(O / f'poses/EMF1_feuille_{i}.png') for i in range(6)]
        self.assertTrue(all(p.shape == (10, 10, 4) for p in poses))
        fr = BY['feuilles']; self.assertEqual((len(fr), f['frame_length_ticks']), (48, 5))
        self.assertTrue(colors(fr) <= colors(BY['arbres']))                 # palette des houppiers
        full = np.ones((H, W), bool)
        calc = B.leaf_frames(poses, f['departs'], full)
        for t, a in enumerate(fr):
            self.assertTrue((a == calc[t]).all(), t)                        # fichiers = trajectoires du manifeste
            self.assertGreater(int(alpha(a).sum()), 60)                     # des feuilles en l'air à chaque phase
        self.assertTrue((B.leaf_frames(poses, f['departs'], full, ts=[48])[0] == fr[0]).all())   # 48 = 0
        starts = np.array([s_[:2] for s_ in f['departs']], float)
        for t in range(48):                                                 # 47 -> 0 compris : pas de saut
            lab0, n0 = nd.label(alpha(fr[t]))
            c0 = np.array(nd.center_of_mass(alpha(fr[t]), lab0, range(1, n0 + 1))).reshape(-1, 2)
            lab1, n1 = nd.label(alpha(fr[(t + 1) % 48]))
            for c in nd.center_of_mass(alpha(fr[(t + 1) % 48]), lab1, range(1, n1 + 1)):
                c = np.array(c)
                near_prev = len(c0) > 0 and float(np.min(np.hypot(*(c0 - c).T))) < 9
                spawn = float(np.min(np.hypot(starts[:, 0] - c[1], starts[:, 1] - c[0]))) < 12
                self.assertTrue(near_prev or spawn, (t, c))

    def test_lucioles_boucle_fermee(self):
        f = M['lucioles']; B = loadmod('emf1_build', HERE / 'build.py')
        poses = [load(O / f'poses/EMF1_luciole_{i}.png') for i in range(6)]
        self.assertTrue(all(p.shape == (6, 6, 4) for p in poses))
        fr = BY['lucioles']; self.assertEqual((len(fr), f['frame_length_ticks']), (48, 5))
        self.assertLessEqual(len(colors(fr)), 8)
        self.assertEqual(48 % len(f['pulsation']), 0)
        calc = B.firefly_frames(poses, f['points'])
        for t, a in enumerate(fr):
            self.assertTrue((a == calc[t]).all(), t)                        # fichiers = boucles du manifeste
            self.assertGreater(int(alpha(a).sum()), 20)                     # des lucioles allumées à chaque phase
        self.assertTrue((B.firefly_frames(poses, f['points'], ts=[48])[0] == fr[0]).all())      # 48 = 0

    def test_ora_and_scene(self):
        with zipfile.ZipFile(O / 'EMF1_entree_mystifying_forest_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
            self.assertIn(b'Mystifying Forest', z.read('stack.xml'))
        sc = Image.new('RGBA', (W, H))
        for frames in STACK:
            sc.alpha_composite(Image.fromarray(frames[0]))
        self.assertTrue((np.array(sc) == merged).all())
        self.assertTrue((np.array(sc) == load(O / 'review/EMF1_scene_t000.png')).all())
        self.assertEqual(M['scene_loop_ticks'] % 40, 0); self.assertEqual(M['scene_loop_ticks'] % 240, 0)

    def test_access(self):
        a = M['access']; self.assertTrue(a['path_found_16x16'])
        ex, ey = a['entry_px']; tx, ty = a['threshold_px']
        self.assertGreater(ey, H - 64); self.assertLess(ty, H // 3)
        self.assertTrue(MASK['chemin'][ey:ey + 16, ex:ex + 16].mean() > 0.5)   # arrivée sur le chemin
        dp = nd.distance_transform_edt(~MASK['profondeur'])
        self.assertLess(float(dp[ty:ty + 16, tx:tx + 16].min()), 40)          # seuil au pied de l'ouverture sombre
        self.assertEqual(a['walkable_cells'] + a['blocked_cells'], (W // 8) * (H // 8))
        self.assertGreater(a['walkable_cells'], 1000)                         # clairière vaste

    def test_prefix_and_namespace_unique(self):
        for p in (R / 'source').glob('*/build.py'):
            if p.parent != HERE:
                s = p.read_text(errors='ignore')
                self.assertNotIn("PFX = 'EMF1'", s, p); self.assertNotIn("'entree_mystifying_forest_sud_nord'", s, p)

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
