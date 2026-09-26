"""Tests dédiés — Entrée Foggy Forest sans tentes sud -> nord V2 (EFF2, 4:3 vaste).
.venv/bin/python -m unittest source.entree_foggy_forest_sud_nord_v2.test_build -v
Contrôles d'images, de formats, de palettes, de fidélité au rip, de cadence et de grille : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, re, unittest, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_foggy_forest_sud_nord_v2'
S = R / '.cache/entree_foggy_forest_sud_nord_v2/entree_foggy_forest_sans_tentes'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
NAMES = [Path(L['file']).name.replace('_fNN', '') for L in M['layers']]
STATIC = ('herbe', 'chemin', 'sous_bois', 'buissons', 'rochers', 'ombres_arbres', 'troncs', 'houppiers', 'grotte')


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
BY = {re.sub(r'^EFF2_\d\d_', '', Path(n).stem): fr for n, fr in zip(NAMES, STACK)}
ORDER = list(BY)
MASK = {k: np.array(Image.open(O / f'masques/EFF2_masque_{k}.png')) > 0 for k in ('water', 'grotte', 'chemin', 'herbe')}


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
        self.assertEqual(ref['file'], 'Foggy_Forest_Base_Camp_TDS.png')
        self.assertEqual(hashlib.sha256((R / ref['file']).read_bytes()).hexdigest(), ref['sha256'])
        g = M['generation']
        self.assertEqual([x['file'] for x in g], ['decor_magenta.png', 'sol_complet.png', 'brume_poses.png'])
        self.assertTrue(all(x['images'] and len(x['prompt']) > 100 for x in g))
        self.assertIn('Foggy_Forest_Base_Camp_TDS.png', g[0]['images'])      # décor et planche : rip en référence
        self.assertIn('Foggy_Forest_Base_Camp_TDS.png', g[2]['images'])
        self.assertTrue(g[1]['images'][0].endswith('bruts/decor_magenta.png'))    # sol : édité depuis le décor
        self.assertIn('sans tentes', M['biome']); self.assertTrue(all('entree_foggy_forest_sud_nord_v1/bruts' in r['file'] for r in M['raw_inputs']))   # bruts EFF1 réutilisés
        self.assertFalse(M['art_approved']); self.assertFalse(M['pmdo']['runtime_tested'])

    def test_sizes_names_alpha_no_magenta(self):
        self.assertEqual(len(NAMES), len(set(NAMES))); self.assertTrue(all(n.startswith('EFF2_') for n in NAMES))
        self.assertEqual((W, H, W % 8, H % 8), (768, 576, 0, 0)); self.assertEqual(W * 3, H * 4)   # 4:3
        n = M['normalization']; self.assertAlmostEqual(n['scale'], 576 / 896)
        self.assertEqual(n['scaled'][0] - sum(n['crop_x']), W)
        for frames in STACK:
            for a in frames:
                self.assertEqual(a.shape[:2], (H, W)); self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255})
                v = a[a[..., 3] > 0].astype(int)
                self.assertEqual(int(((v[:, 0] > 200) & (v[:, 2] > 200) & (v[:, 1] < 90)).sum()), 0)

    def test_multicalque_full_coverage_and_order(self):
        self.assertEqual(ORDER, ['eau', 'scintillements', 'sol_complet', *STATIC, 'brume'])
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
        self.assertLessEqual(len(colors(BY['houppiers'])), 40); self.assertLessEqual(len(colors(BY['troncs'])), 16)
        self.assertLessEqual(len(colors(BY['ombres_arbres'])), 12)
        self.assertLessEqual(len(colors(BY['rochers'])), 16)
        self.assertLessEqual(len(colors(BY['grotte'])), 16)

        ch = BY['chemin'][0]; px = ch[alpha(ch)][:, :3].astype(float).mean(0)
        self.assertGreater(px[0], px[2] + 12)                              # chemin rose-brun, pas vert
        dp = BY['grotte'][0]; lum = dp[alpha(dp)][:, :3] @ [.299, .587, .114]
        self.assertLess(float(np.percentile(lum, 30)), 110)                # bouche sombre dans la grotte
        sol = BY['sol_complet'][0]; ls = sol[alpha(sol)][:, :3] @ [.299, .587, .114]
        self.assertGreater(float(np.percentile(ls, 1)), 45)                # herbe complète sans zone sombre

    def test_fidelite_rip(self):
        B = loadmod('eff2_build', HERE / 'build.py')
        dec, ref = B.rgb(B.RAW / 'decor_magenta.png'), B.rgb(R / 'Foggy_Forest_Base_Camp_TDS.png')
        fid = B.fidelity(dec, ref)
        for k, v in fid.items():
            self.assertLess(v['distance'], 40, (k, v))                      # brut plus laiteux que le rip : seuil 40 (EMF1 : 20)
            self.assertAlmostEqual(v['distance'], M['fidelite_rip']['brut'][k]['distance'], places=1)
        for k, v in M['fidelite_rip']['calques_finaux'].items():
            lay = BY[v['calque']][0]; px = lay[alpha(lay)][:, :3].astype(float)
            sel = B.materials(px.reshape(-1, 1, 3))[k][:, 0]
            px = px[sel] if sel.sum() > 50 else px
            d = float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb'])))
            self.assertLess(d, 40, (k, d))                                  # calques finaux, même seuil documenté

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

    def test_brume_boucle_fermee_et_trame(self):
        f = M['brume']; B = loadmod('eff2_build', HERE / 'build.py')
        poses = [load(O / f'poses/EFF2_brume_{i}.png') for i in range(8)]
        fr = BY['brume']; self.assertEqual((len(fr), f['frame_length_ticks']), (48, 5))
        self.assertLessEqual(len(colors(fr)), 6)                            # palette des nappes générées
        calc = B.fog_frames(poses, f['nappes'])
        yy, xx = np.mgrid[:H, :W]; odd = (xx + yy) % 2 == 1
        for t, a in enumerate(fr):
            self.assertTrue((a == calc[t]).all(), t)                        # fichiers = dérive du manifeste
            self.assertFalse(alpha(a)[odd].any())                           # trame en damier fixe
            self.assertGreater(int(alpha(a).sum()), 3000)                   # de la brume à chaque phase
        self.assertTrue((B.fog_frames(poses, f['nappes'], ts=[48])[0] == fr[0]).all())      # 48 = 0
        ch = step_changes(fr)                                               # 47 -> 0 compris : pas de saut
        self.assertLess(max(ch), 3 * (sum(ch) / len(ch)), ch)

    def test_sans_tentes(self):
        self.assertNotIn('tentes', ORDER)
        sc = Image.new('RGBA', (W, H))
        for frames in STACK[:-1]:                                            # scène sans la brume
            sc.alpha_composite(Image.fromarray(frames[0]))
        v = np.array(sc)[..., :3].astype(int)
        pink = (v[..., 0] > v[..., 1] + 40) & (v[..., 0] > v[..., 2] + 30) & (v[..., 0] > 170)
        lab, n = nd.label(pink); sizes = nd.sum(pink, lab, range(1, n + 1)) if n else [0]
        self.assertLess(max(sizes), 400)                                     # plus aucune tente rose (rochers < 400 px)
        t = M['retrait_tentes']; self.assertGreaterEqual(len(t['pieces']), 4)   # 4 tentes (+ fragments d'oreilles)
        self.assertEqual(t['residu_rose_px'], 0)
        self.assertGreater(M['access']['walkable_cells'], 1475)              # l'emprise des tentes est praticable

    def test_arbres_trois_calques(self):
        sh, tr, cp = (BY[k][0] for k in ('ombres_arbres', 'troncs', 'houppiers'))
        self.assertLess(ORDER.index('ombres_arbres'), ORDER.index('troncs')); self.assertLess(ORDER.index('troncs'), ORDER.index('houppiers'))
        ps, pt, pc = (x[alpha(x)][:, :3].astype(float) for x in (sh, tr, cp))
        self.assertGreater((ps[:, 2] / ps[:, 1]).mean(), (pc[:, 2] / pc[:, 1]).mean() + 0.04)   # ombre plus bleutée
        self.assertLess((ps @ [.299, .587, .114]).mean(), (pc @ [.299, .587, .114]).mean())     # et plus sombre
        self.assertGreater(pt[:, 0].mean(), pt[:, 1].mean())                                    # troncs bruns
        lab, n = nd.label(alpha(sh)); self.assertGreater(n, 20)              # une ombre par arbre, à peu près
        below = np.roll(alpha(cp), 12, axis=0)                               # ombres sous les houppiers
        self.assertGreater((alpha(sh) & nd.binary_dilation(below, iterations=12)).mean() / alpha(sh).mean(), 0.8)
        for k in ('ombres_arbres', 'troncs', 'houppiers'):
            self.assertFalse((alpha(BY[k][0]) & (alpha(BY['herbe'][0]) | alpha(BY['chemin'][0]))).any())

    def test_ora_and_scene(self):
        with zipfile.ZipFile(O / 'EFF2_entree_foggy_forest_sans_tentes_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
            self.assertIn(b'Foggy Forest', z.read('stack.xml'))
        sc = Image.new('RGBA', (W, H))
        for frames in STACK:
            sc.alpha_composite(Image.fromarray(frames[0]))
        self.assertTrue((np.array(sc) == merged).all())
        self.assertTrue((np.array(sc) == load(O / 'review/EFF2_scene_t000.png')).all())
        self.assertEqual(M['scene_loop_ticks'] % 40, 0); self.assertEqual(M['scene_loop_ticks'] % 240, 0)

    def test_access(self):
        a = M['access']; self.assertTrue(a['path_found_16x16'])
        ex, ey = a['entry_px']; tx, ty = a['threshold_px']
        self.assertGreater(ey, H - 64); self.assertLess(ty, H // 3)
        self.assertTrue(MASK['chemin'][ey:ey + 16, ex:ex + 16].mean() > 0.5)   # arrivée sur le chemin
        dp = nd.distance_transform_edt(~MASK['grotte'])
        self.assertLess(float(dp[ty:ty + 16, tx:tx + 16].min()), 40)          # seuil devant la grotte
        self.assertEqual(a['walkable_cells'] + a['blocked_cells'], (W // 8) * (H // 8))
        self.assertGreater(a['walkable_cells'], 1000)                         # camp vaste

    def test_prefix_and_namespace_unique(self):
        for p in (R / 'source').glob('*/build.py'):
            if p.parent != HERE:
                s = p.read_text(errors='ignore')
                self.assertNotIn("PFX = 'EFF2'", s, p); self.assertNotIn("'entree_foggy_forest_sans_tentes'", s, p)

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
