"""Tests dédiés — Entrée Underground Lake sud -> nord V1 (EUL1, 4:3 vaste).
.venv/bin/python -m unittest source.entree_underground_lake_sud_nord_v1.test_build -v
Contrôles d'images, de formats, de palettes, de fidélité au rip, de cadence et de grille : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, re, unittest, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_underground_lake_sud_nord_v1'
S = R / '.cache/entree_underground_lake_sud_nord_v1/entree_underground_lake_sud_nord'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
NAMES = [Path(L['file']).name.replace('_fNN', '') for L in M['layers']]
STATIC = ('sable', 'ombres', 'berge', 'roche', 'piliers', 'profondeur')
REF = R / 'Underground_Lake_shore_TDS.png'


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
BY = {re.sub(r'^EUL1_\d\d_', '', Path(n).stem): fr for n, fr in zip(NAMES, STACK)}
ORDER = list(BY)
MASK = {k: np.array(Image.open(O / f'masques/EUL1_masque_{k}.png')) > 0 for k in ('water', 'profondeur', 'sable', 'ombres')}
B = loadmod('eul1_build', HERE / 'build.py')


def alpha(a):
    return a[..., 3] == 255


def colors(frames):
    return {tuple(int(v) for v in c) for a in frames for c in np.unique(a[a[..., 3] == 255][:, :3], axis=0)}


def rip_colors():
    a = np.array(Image.open(REF).convert('RGB'))
    return {tuple(int(v) for v in c) for c in np.unique(a.reshape(-1, 3), axis=0)}


def visible():
    land = np.zeros((H, W), bool)
    for k in STATIC:
        land |= alpha(BY[k][0])
    return MASK['water'] & ~land


def steps(frames, mask=None):
    n = len(frames); m = np.ones((H, W), bool) if mask is None else mask
    return [int((frames[t][m] != frames[(t + 1) % n][m]).any(-1).sum()) for t in range(n)]


class Build(unittest.TestCase):
    def test_raw_hashes_and_reference(self):
        for r in M['raw_inputs']:
            self.assertEqual(hashlib.sha256((R / r['file']).read_bytes()).hexdigest(), r['sha256'])
        ref = M['reference_da']
        self.assertEqual(ref['file'], REF.name)
        self.assertEqual(hashlib.sha256(REF.read_bytes()).hexdigest(), ref['sha256'])
        g = M['generation']
        self.assertEqual([x['file'] for x in g], ['decor_magenta.png', 'sol_complet.png', 'gouttes_ronds_poses.png'])
        self.assertTrue(all(x['images'] and len(x['prompt']) > 100 for x in g))
        self.assertIn(REF.name, g[0]['images']); self.assertIn(REF.name, g[2]['images'])     # rip en référence
        self.assertTrue(g[1]['images'][0].endswith('bruts/decor_magenta.png'))                 # sol : édité du décor
        self.assertIn('choisi par l agent', M['biome'])
        self.assertFalse(M['art_approved']); self.assertFalse(M['pmdo']['runtime_tested'])

    def test_sol_complet_recale_sur_le_decor(self):
        a, f = B.rgb(HERE / 'bruts/decor_magenta.png').astype(float), B.rgb(HERE / 'bruts/sol_complet.png').astype(float)
        zone = np.zeros(a.shape[:2], bool); zone[250:850, :80] = zone[250:850, 1120:] = zone[:60, 200:1000] = True
        err = {(dy, dx): float(np.abs(a - np.roll(np.roll(f, dy, 0), dx, 1))[zone].mean())
               for dy in (-1, 0, 1) for dx in (-1, 0, 1)}
        self.assertEqual(min(err, key=err.get), (0, 0))                     # parois gardées au pixel près
        self.assertAlmostEqual(err[(0, 0)], M['sol_complet']['ecart_moyen_parois'], places=2)

    def test_sizes_names_alpha_no_magenta(self):
        self.assertEqual(len(NAMES), len(set(NAMES))); self.assertTrue(all(n.startswith('EUL1_') for n in NAMES))
        self.assertEqual((W, H, W % 8, H % 8), (768, 576, 0, 0)); self.assertEqual(W * 3, H * 4)   # 4:3
        n = M['normalization']; self.assertAlmostEqual(n['scale'], 576 / 896)
        self.assertEqual(n['scaled'][0] - sum(n['crop_x']), W)
        for frames in STACK:
            for a in frames:
                self.assertEqual(a.shape[:2], (H, W)); self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255})
                v = a[a[..., 3] > 0].astype(int)
                self.assertEqual(int(((v[:, 0] - v[:, 1] > 60) & (v[:, 2] - v[:, 1] > 60)).sum()), 0)   # ni magenta ni frange

    def test_multicalque_full_coverage_and_order(self):
        self.assertEqual(ORDER, ['eau', 'lueur', 'scintillements', 'gouttes', 'sol_complet', *STATIC])
        cover = np.zeros((H, W), bool)
        for frames in STACK:
            cover |= alpha(frames[0])
        self.assertTrue(cover.all())
        fixed = [alpha(BY[k][0]) for k in STATIC]                          # calques fixes exclusifs entre eux
        self.assertEqual(int(np.sum(fixed, 0).max()), 1)
        for k in STATIC:
            self.assertGreater(int(alpha(BY[k][0]).sum()), 500, k)        # aucun calque vide
        self.assertFalse((alpha(BY['sol_complet'][0]) & MASK['water']).any())

    def test_palettes_et_matieres(self):
        pg = M['normalization']['palettes']
        self.assertLessEqual(len(colors([BY[k][0] for k in pg['terrain']['calques']])), 96)
        self.assertLessEqual(len(colors([BY['roche'][0], BY['piliers'][0]])), 64)
        self.assertLessEqual(len(colors(BY['profondeur'])), 12)
        lum = lambda k: BY[k][0][alpha(BY[k][0])][:, :3].astype(float) @ [.299, .587, .114]
        sb = BY['sable'][0][alpha(BY['sable'][0])][:, :3].astype(float).mean(0)
        self.assertGreater(sb[0], sb[2] + 50)                              # sable jaune
        self.assertLess(float(np.median(lum('profondeur'))), 45)           # entrée sombre
        self.assertLess(lum('ombres').mean(), lum('sable').mean() - 8)     # ombres plus sombres que le sable
        ro = nd.distance_transform_edt(~(alpha(BY['roche'][0]) | alpha(BY['berge'][0]) | alpha(BY['piliers'][0])))
        self.assertLessEqual(float(ro[alpha(BY['ombres'][0])].max()), 14)  # ombres au pied des parois ou de la berge

    def test_fidelite_rip(self):
        dec, ref = B.rgb(HERE / 'bruts/decor_magenta.png'), B.rgb(REF)
        fid = B.fidelity(dec, ref)
        for k, v in fid.items():
            self.assertLess(v['distance'], 20, (k, v))                      # brut ≈ rip, matière par matière
            self.assertAlmostEqual(v['distance'], M['fidelite_rip']['brut'][k]['distance'], places=1)
        for nm, v in M['fidelite_rip']['calques_finaux'].items():
            lay = BY[nm][0]; px = lay[alpha(lay)][:, :3].astype(float)
            sel = B.materials(px.reshape(-1, 1, 3))[v['matiere']][:, 0]
            px = px[sel] if sel.sum() > 50 else px
            d = float(np.linalg.norm(px.mean(0) - np.array(fid[v['matiere']]['rip_rgb'])))
            self.assertLess(d, 20, (nm, d)); self.assertAlmostEqual(d, v['distance_rip'], places=1)

    def test_eau_couleurs_du_rip_sans_lisere(self):
        fr = BY['eau']; mask = alpha(fr[0]); rip = rip_colors()
        self.assertEqual((len(fr), M['water']['frame_length_ticks']), (4, 10))
        self.assertGreater(int(mask.sum()), 50000)
        for a in fr:
            self.assertTrue((alpha(a) == mask).all())
        self.assertTrue(colors(fr) <= rip, colors(fr) - rip)                # couleurs EXACTES du rip
        for c in ((119, 127, 175), (167, 167, 223), (103, 103, 159), (79, 87, 143), (148, 230, 238)):
            self.assertNotIn(c, colors(fr))                                  # aucun liseré clair (retour EWC1)
        vis = visible(); rim = vis & nd.binary_dilation(~MASK['water'])
        bande = np.array(M['water']['couleurs']['bande'])
        for a in fr:
            self.assertTrue((a[rim][:, :3] == bande).all())                 # contre la rive : la bande seule
        d = steps(fr, mask)
        self.assertTrue(min(d) > 0 and max(d) < 2 * min(d), d)              # 3 -> 0 compris

    def test_pas_d_eau_devant_l_entree(self):
        dp = MASK['profondeur']; ys, xs = np.nonzero(dp)
        band = np.zeros((H, W), bool); band[ys.max():ys.max() + 40, xs.min():xs.max() + 1] = True
        self.assertFalse((band & MASK['water']).any())                      # chaussée sèche jusqu'à la bouche
        self.assertGreater((band & (MASK['sable'] | MASK['ombres'])).mean() / band.mean(), 0.6)

    def test_lueur_respire_en_boucle_fermee(self):
        L = M['lueur']; fr = BY['lueur']; vis = visible()
        self.assertEqual((len(fr), L['frame_length_ticks']), (12, 10))
        self.assertEqual(colors(fr), {tuple(c) for c in L['couleurs']})     # coeur + 8 anneaux, rien d'autre
        self.assertTrue({tuple(c) for c in L['couleurs']} <= rip_colors())   # couleurs EXACTES du rip
        for a in fr:
            self.assertFalse((alpha(a) & ~vis).any())                       # seulement sur l'eau visible
        centres = [tuple(c) for c in L['centres']]
        for t in (0, 5, 11):
            self.assertTrue((B.glow_frames(vis, centres, ts=[t])[0] == fr[t]).all(), t)   # fichiers = manifeste
        self.assertTrue((B.glow_frames(vis, centres, ts=[12])[0] == fr[0]).all())       # 12 = 0
        d = steps(fr)                                                       # respiration sinusoïdale : pas lents aux
        self.assertTrue(min(d) > 0 and d[11] <= 1.1 * max(d[:11]), d)       # extrêmes ; 11 -> 0 pas plus gros qu'un autre

    def test_sparkles_natifs_sur_la_lueur(self):
        v2 = loadmod('esn2', R / 'source/entree_vapeur_sud_nord_v2/build.py')
        native = {tuple(int(v) for v in px[:3]) for t in v2.decode_tile(R / M['sparkles']['source']).values()
                  for px in t.reshape(-1, 4) if px[3] == 255}
        core = np.ones((H, W), bool)
        for a in BY['lueur']:
            core &= alpha(a) & (a[..., :3] == M['lueur']['couleurs'][0]).all(-1)
        self.assertEqual(len(M['sparkles']['placements']), 6)
        for a in BY['scintillements']:
            cols = colors([a]); self.assertTrue(cols <= native); self.assertGreater(len(cols), 0)
            self.assertFalse((alpha(a) & ~core).any())                      # sur le coeur de la lueur, pas l'eau sombre

    def test_gouttes_boucle_fermee(self):
        G = M['gouttes']; fr = BY['gouttes']; vis = visible()
        poses = {k: load(O / f'poses/EUL1_{k}.png') for k in G['poses']}
        self.assertEqual({k: p.shape[0] for k, p in poses.items()}, {k: v[2] // 8 for k, v in G['poses'].items()})
        self.assertEqual((len(fr), G['frame_length_ticks']), (24, 5))
        self.assertLessEqual(len(colors(fr)), 8)
        em = [tuple(e) for e in G['emetteurs']]; self.assertEqual(len(em), 8)
        calc = B.drop_frames(poses, em, vis)
        for t, a in enumerate(fr):
            self.assertTrue((a == calc[t]).all(), t)                        # fichiers = chronologie du manifeste
            self.assertGreater(int(alpha(a).sum()), 10, t)                   # une goutte ou un rond à chaque phase
        self.assertTrue((B.drop_frames(poses, em, vis, ts=[24])[0] == fr[0]).all())      # 24 = 0
        glow = np.zeros((H, W), bool)
        for a in BY['lueur']:
            glow |= alpha(a)
        for x, y, _ in em:
            self.assertTrue(vis[y - 18:y + 1, x].all() and not glow[y, x], (x, y))       # chute au-dessus de l'eau sombre
        rings = [np.zeros((H, W), bool) for _ in range(24)]
        for x, y, off in em:                                                # hors chute : tout est sur l'eau
            for t in range(24):
                st = B.DROP_SEQ[(t + off) % 24]
                if st and not st[0].startswith('goutte'):
                    rings[t][max(0, y - 20):y + 20, max(0, x - 20):x + 20] = True
        for t, a in enumerate(fr):
            self.assertFalse((alpha(a) & rings[t] & ~vis).any(), t)

    def test_ora_and_scene(self):
        with zipfile.ZipFile(O / 'EUL1_entree_underground_lake_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
            self.assertIn(b'Underground Lake', z.read('stack.xml'))
        sc = Image.new('RGBA', (W, H))
        for frames in STACK:
            sc.alpha_composite(Image.fromarray(frames[0]))
        self.assertTrue((np.array(sc) == merged).all())
        self.assertTrue((np.array(sc) == load(O / 'review/EUL1_scene_t000.png')).all())
        for L in M['layers']:
            self.assertEqual(M['scene_loop_ticks'] % (L['phases'] * L['ticks']) if L['phases'] > 1 else 0, 0)

    def test_access(self):
        a = M['access']; self.assertTrue(a['path_found_16x16'])
        ex, ey = a['entry_px']; tx, ty = a['threshold_px']
        self.assertGreater(ey, H - 64); self.assertLess(ty, H // 3)
        walk = MASK['sable'] | MASK['ombres']
        self.assertTrue(walk[ey:ey + 16, ex:ex + 16].mean() > 0.5)          # arrivée sur le sable
        dp = nd.distance_transform_edt(~MASK['profondeur'])
        self.assertLess(float(dp[ty:ty + 16, tx:tx + 16].min()), 40)          # seuil au pied de l'entrée sombre
        self.assertEqual(a['walkable_cells'] + a['blocked_cells'], (W // 8) * (H // 8))
        self.assertGreater(a['walkable_cells'], 600)

    def test_prefix_and_namespace_unique(self):
        for p in (R / 'source').glob('*/build.py'):
            if p.parent != HERE:
                s = p.read_text(errors='ignore')
                self.assertNotIn("PFX = 'EUL1'", s, p); self.assertNotIn("'entree_underground_lake_sud_nord'", s, p)

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
