"""Tests dédiés — Entrée Waterfall Cave sud -> nord V2 (EWC2, 4:3 vaste, cascade en deux temps).
.venv/bin/python -m unittest source.entree_waterfall_cave_sud_nord_v2.test_build -v
Contrôles d'images, de formats, de palettes, de fidélité au rip, de cadence, d'états et de grille : PAS un test du
moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, re, unittest, zipfile
import numpy as np
from PIL import Image
from scipy import ndimage as nd

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_waterfall_cave_sud_nord_v2'
S = R / '.cache/entree_waterfall_cave_sud_nord_v2/entree_waterfall_cave_v2'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
NAMES = [Path(L['file']).name.replace('_fNN', '') for L in M['layers']]
CLAIR = tuple(M['changements_v2']['liseré_de_rive']['rgb'])


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
KEYS = [re.sub(r'^EWC2_\d\d_', '', Path(n).stem) for n in NAMES]
BY = dict(zip(KEYS, STACK))
ETAT = {k: L['etat'] for k, L in zip(KEYS, M['layers'])}
MASK = {k: np.array(Image.open(O / f'masques/EWC2_masque_{k}.png')) > 0
        for k in ('water', 'cascade', 'ecume_pied', 'entree_sombre', 'porte', 'couloir', 'sable')}


def colors(frames):
    return {tuple(int(v) for v in c) for a in frames for c in np.unique(a[a[..., 3] == 255][:, :3], axis=0)}


def alpha(a):
    return a[..., 3] == 255


def shifted(a, step):
    s = np.zeros_like(a); s[step:] = a[:-step]; return s


class Build(unittest.TestCase):
    def test_raw_hashes_same_as_ewc1(self):
        v1 = json.loads((R / 'renders/entree_waterfall_cave_sud_nord_v1/manifest.json').read_text())
        self.assertEqual([r['sha256'] for r in M['raw_inputs']], [r['sha256'] for r in v1['raw_inputs']])   # mêmes bruts
        for r in M['raw_inputs']:
            self.assertEqual(hashlib.sha256((R / r['file']).read_bytes()).hexdigest(), r['sha256'])
        ref = M['reference_da']
        self.assertEqual(hashlib.sha256((R / ref['file']).read_bytes()).hexdigest(), ref['sha256'])
        self.assertEqual(M['generation'], v1['generation'])
        self.assertIn('entrancecascade.png', M['generation'][0]['images'])

    def test_sizes_names_alpha_no_magenta(self):
        self.assertEqual(len(NAMES), len(set(NAMES))); self.assertTrue(all(n.startswith('EWC2_') for n in NAMES))
        self.assertEqual((W, H, W % 8, H % 8), (768, 576, 0, 0)); self.assertEqual(W * 3, H * 4)
        for frames in STACK:
            for a in frames:
                self.assertEqual(a.shape[:2], (H, W)); self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255})
                v = a[a[..., 3] > 0].astype(int)
                self.assertEqual(int(((v[:, 0] > 200) & (v[:, 2] > 200) & (v[:, 1] < 90)).sum()), 0)

    def test_multicalque_full_coverage_each_state(self):
        self.assertGreaterEqual(len(STACK), 19)
        for state in ('fermee', 'ouverte'):
            cover = np.zeros((H, W), bool)
            for k, frames in BY.items():
                if ETAT[k] in (None, state):
                    cover |= alpha(frames[0])
            self.assertTrue(cover.all(), state)
        fixed = [alpha(BY[k][0]) for k in ('sable', 'cailloux', 'touffes', 'plateaux', 'berge', 'falaises', 'arbres',
                                           'entree_sombre', 'ecume_pied')]
        self.assertEqual(int(np.sum(fixed, 0).max()), 1)

    def test_palettes_separees(self):
        pg = M['normalization']['palettes']
        self.assertLessEqual(len(colors([BY[k][0] for k in pg['terrain']['calques']])), 96)
        self.assertLessEqual(len(colors(BY['arbres'])), 24)
        eau_dessinee = colors(BY['cascade_fermee']) | colors(BY['cascade_ouverture']) | colors(BY['cascade_ouverte']) | colors(BY['ecume_pied'])
        self.assertLessEqual(len(eau_dessinee), 24)                          # lèvres de la fente = couleurs du rideau
        self.assertLessEqual(len(colors(BY['entree_sombre'])), 12)
        cas = BY['cascade_fermee'][0]; px = cas[alpha(cas)][:, :3].astype(float)
        self.assertGreater(px[:, 2].mean(), px[:, 0].mean() + 60)
        cave = BY['entree_sombre'][0]; lum = cave[alpha(cave)][:, :3] @ [.299, .587, .114]
        self.assertLess(float(np.percentile(lum, 25)), 60)

    def test_fidelite_rip(self):
        V1 = loadmod('ewc1_build', R / 'source/entree_waterfall_cave_sud_nord_v1/build.py')
        dec, ref = V1.rgb(V1.RAW / 'decor_magenta.png'), V1.rgb(R / 'entrancecascade.png')
        fid = V1.fidelity(dec, ref, V1.classify(dec)['cascade'])
        for k, v in fid.items():
            self.assertLess(v['distance'], 20, (k, v))
            self.assertAlmostEqual(v['distance'], M['fidelite_rip']['brut'][k]['distance'], places=1)
        for k, v in M['fidelite_rip']['calques_finaux'].items():
            lay = BY[v['calque']][0]; px = lay[alpha(lay)][:, :3].astype(float)
            if v['calque'] == 'arbres':
                px = px[(px[:, 1] > px[:, 0] + 8) & (px[:, 1] > px[:, 2] + 20)]
            self.assertLess(float(np.linalg.norm(px.mean(0) - np.array(fid[k]['rip_rgb']))), 20, k)

    def test_water_metano_sans_lisere(self):
        v2 = loadmod('esn2', R / 'source/entree_vapeur_sud_nord_v2/build.py')
        native = set()
        for i in range(1, 5):
            t = v2.decode_tile(R / f'source/eau_metano/natifs/Metano_Town_River_Animation_{i}.tile')
            native |= {tuple(int(v) for v in px[:3]) for a in t.values() for px in a.reshape(-1, 4) if px[3] == 255}
        fr = BY['eau']; mask = alpha(fr[0])
        self.assertEqual((len(fr), M['water']['frame_length_ticks']), (4, 10))
        for a in fr:
            self.assertTrue((alpha(a) == mask).all())
        self.assertTrue(colors(fr) <= native, colors(fr) - native)          # couleurs Métano EXACTES
        self.assertNotIn(CLAIR, colors(fr))                                  # plus de petits traits blancs
        # contre les rives visibles : uniquement la bande sombre
        land = np.zeros((H, W), bool)
        for k in ('sable', 'cailloux', 'touffes', 'plateaux', 'berge', 'falaises', 'arbres', 'entree_sombre', 'ecume_pied'):
            land |= alpha(BY[k][0])
        rim = mask & ~land & nd.binary_dilation(land)
        bande = np.array(M['water']['couleurs']['bande'])
        for a in fr:
            self.assertTrue((a[rim][:, :3] == bande).all())
        d = [int((fr[t][mask] != fr[(t + 1) % 4][mask]).any(1).sum()) for t in range(4)]
        self.assertTrue(min(d) > 0 and max(d) < 2 * min(d), d)

    def test_sparkles_native_pixels(self):
        v2 = loadmod('esn2', R / 'source/entree_vapeur_sud_nord_v2/build.py')
        native = {tuple(int(v) for v in px[:3]) for t in v2.decode_tile(R / M['sparkles']['source']).values()
                  for px in t.reshape(-1, 4) if px[3] == 255}
        for a in BY['scintillements']:
            cols = colors([a]); self.assertTrue(cols <= native); self.assertGreater(len(cols), 0)

    def test_pas_d_eau_devant_la_bouche(self):
        cave = MASK['entree_sombre']; ys, xs = np.nonzero(cave)
        box = np.zeros((H, W), bool); box[ys.max() + 1:252, xs.min() + 10:xs.max() - 9] = True   # cœur du couloir (lisière d'écume exclue)
        self.assertFalse((alpha(BY['eau'][0]) & ~alpha(BY['sable'][0]) & box & ~land_mask()).any())
        self.assertFalse(MASK['water'][box].any())
        self.assertFalse(alpha(BY['ecume_pied'][0])[box].any())
        self.assertGreater(float(alpha(BY['sable'][0])[box].mean()), 0.97)  # sable praticable jusqu'à la bouche
        c = M['changements_v2']['couloir']; self.assertGreater(c['eau_retiree_px'], 5000)

    def test_cascade_deux_temps(self):
        c = M['cascade']; step, n = c['step_px'], c['phases']
        fe, ou, ov = BY['cascade_fermee'], BY['cascade_ouverture'], BY['cascade_ouverte']
        self.assertEqual((len(fe), len(ou), len(ov), c['ouverture_phases']), (12, 24, 12, 24))
        self.assertEqual([ETAT[k] for k in ('cascade_fermee', 'cascade_ouverture', 'cascade_ouverte')], ['fermee', 'ouverture', 'ouverte'])
        porte, cave = MASK['porte'], MASK['entree_sombre']
        for frames, state in ((fe, 'fermee'), (ov, 'ouverte')):              # boucles : translation pure, 11 -> 0 compris
            mask = alpha(frames[0]); both = mask.copy(); both[:step] = False; both[step:] &= mask[:-step]
            for t in range(n):
                a, b = frames[t], frames[(t + 1) % n]
                self.assertTrue((alpha(b) == mask).all(), state)
                self.assertTrue((b[both] == shifted(a, step)[both]).all(), (state, t))
        self.assertTrue((alpha(fe[0]) >= porte).all())                     # fermée : toute la bouche est recouverte
        self.assertTrue((alpha(fe[0]) >= cave).all())
        self.assertFalse((alpha(ov[0]) & cave).any())                        # ouverte : la bouche n'est jamais recouverte
        self.assertTrue((ou[0] == fe[0]).all())                              # départ = fermée phase 0
        self.assertTrue((ou[-1] == ov[11]).all())                            # arrivée = ouverte phase 11 -> ouverte 0
        opened = []
        for k in range(24):
            self.assertTrue((alpha(ou[k]) <= alpha(fe[0])).all())
            if k:
                self.assertTrue((alpha(ou[k]) <= alpha(ou[k - 1])).all(), k)  # la fente ne fait que s'ouvrir
            out = ~porte                                                     # hors porte : le rideau défile à l'identique
            self.assertTrue((ou[k][out] == fe[k % 12][out]).all(), k)
            opened.append(int((porte & ~alpha(ou[k])).sum()))
        self.assertEqual(opened[0], 0); self.assertEqual(opened[-1], int(porte.sum()))
        self.assertGreater(sum(b > a for a, b in zip(opened, opened[1:])), 18)
        first = next(k for k in range(24) if opened[k])
        fy = np.nonzero(porte & ~alpha(ou[first]))[0]; py = np.nonzero(porte)[0]
        self.assertLess(fy.max(), py.min() + 0.5 * (py.max() - py.min()))    # la fente naît en haut de la bouche

    def test_foam_spray_and_door_foam(self):
        f = M['foam']
        for k, n in (('bouillon', 8), ('embrun', 4)):
            for i in range(n):
                self.assertEqual(load(O / f'poses/EWC2_{k}_{i}.png').shape, (32, 32, 4))
        clip = (MASK['water'] | MASK['ecume_pied'] | MASK['cascade']) & ~MASK['entree_sombre']
        for key in ('ecume', 'embruns'):
            fr = BY[key]; self.assertEqual((len(fr), f['frame_length_ticks']), (12, 4))
            for a in fr:
                on = a[..., 3] > 0; self.assertGreater(int(on.sum()), 20)
                self.assertFalse((on & ~clip).any())
                self.assertFalse((on & MASK['couloir']).any())               # jamais sur le couloir
        pf, po = BY['ecume_porte_fermee'], BY['ecume_porte_ouverture']
        self.assertEqual((len(pf), len(po)), (12, 24))
        self.assertTrue(all(int(alpha(a).sum()) > 40 for a in pf))
        self.assertTrue((po[0] == pf[0]).all())
        self.assertEqual(int(alpha(po[-1]).sum()), 0)                        # ouverte : plus d'écume devant la bouche

    def test_ora_and_scene(self):
        with zipfile.ZipFile(O / 'EWC2_entree_waterfall_cave_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
            stack = z.read('stack.xml').decode()
        self.assertIn('Waterfall Cave', stack)
        self.assertEqual(stack.count('visibility="hidden"'), sum(ETAT[k] in ('ouverture', 'ouverte') for k in KEYS))
        for state, ref in (('fermee', merged), ('fermee', load(O / 'review/EWC2_scene_fermee_t000.png')),
                           ('ouverte', load(O / 'review/EWC2_scene_ouverte_t000.png'))):
            sc = Image.new('RGBA', (W, H))
            for k, frames in BY.items():
                if ETAT[k] in (None, state):
                    sc.alpha_composite(Image.fromarray(frames[0]))
            self.assertTrue((np.array(sc) == ref).all(), state)
        self.assertEqual(M['scene_loop_ticks'] % 40, 0); self.assertEqual(M['scene_loop_ticks'] % 48, 0)
        self.assertEqual(M['etats']['ouverture_ticks'] % 48, 0)

    def test_access(self):
        a = M['access']; self.assertTrue(a['path_found_16x16'])
        self.assertGreater(a['entry_px'][1], H - 64); self.assertLess(a['threshold_px'][1], H // 2)
        ys, xs = np.nonzero(MASK['entree_sombre'])
        tx, ty = a['threshold_px']
        self.assertTrue(xs.min() <= tx and tx + 16 <= xs.max() + 1)          # seuil sous la bouche
        self.assertTrue(ys.max() - 8 <= ty <= ys.max() + 16, (ty, ys.max()))
        self.assertGreater(float(MASK['sable'][ty:ty + 16, tx:tx + 16].mean()), 0.9)

    def test_prefix_and_namespace_unique(self):
        for p in (R / 'source').glob('*/build.py'):
            if p.parent != HERE:
                s = p.read_text(errors='ignore')
                self.assertNotIn("PFX = 'EWC2'", s, p); self.assertNotIn("'entree_waterfall_cave_v2'", s, p)

    def test_ewc1_intact(self):
        v1 = json.loads((R / 'renders/entree_waterfall_cave_sud_nord_v1/manifest.json').read_text())
        self.assertEqual(v1['prefix'], 'EWC1')
        for p in ('EWC1_projet_pmdo_0812.zip', 'EWC1_calques_png_8px.zip', 'EWC1_entree_waterfall_cave_calques.ora'):
            self.assertTrue((R / 'renders/entree_waterfall_cave_sud_nord_v1' / p).exists())
        self.assertTrue((R / 'apercu_entree_waterfall_cave_sud_nord_v1.html').exists())

    def test_ground_roundtrip_and_states(self):
        doc = json.loads((S / f"Data/Ground/{M['pmdo']['asset']}.rsground").read_text()); o = doc['Object']
        self.assertEqual(doc['Version'], '0.8.12.0'); self.assertEqual(len(o['Layers']), len(STACK) + 1)
        self.assertEqual(o['Layers'][-1]['Layer'], 4)
        for k, lay in zip(KEYS, o['Layers']):
            self.assertEqual(lay['Visible'], ETAT[k] in (None, 'fermee'), k)
        etats = M['etats']['pmdo_calques']
        self.assertEqual(etats, {e: [i for i, k in enumerate(KEYS) if ETAT[k] == e] for e in ('fermee', 'ouverture', 'ouverte')})
        lua = (S / f"Data/Script/{M['pmdo']['namespace']}/ground/{M['pmdo']['asset']}/init.lua").read_text()
        self.assertIn('NON TESTE', lua); self.assertIn(f"WaitFrames({M['etats']['ouverture_ticks']})", lua)
        for e, ids in etats.items():
            self.assertIn(f"{e} = {{{', '.join(map(str, ids))}}}", lua)
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


def land_mask():
    land = np.zeros((H, W), bool)
    for k in ('sable', 'cailloux', 'touffes', 'plateaux', 'berge', 'falaises', 'arbres', 'entree_sombre', 'ecume_pied'):
        land |= alpha(BY[k][0])
    return land


if __name__ == '__main__':
    unittest.main()
