"""Tests dédiés — Entrée Vapeur sud -> nord V2 (eau façon Métano + bulles).
.venv/bin/python -m unittest source.entree_vapeur_sud_nord_v2.test_build -v
Contrôles d'images, de formats, de cadence et de grille : PAS un test du moteur PMDO.
"""
from pathlib import Path
import hashlib, importlib.util, io, json, unittest, zipfile
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
R = HERE.parents[1]
O = R / 'renders/entree_vapeur_sud_nord_v2'
V1 = R / 'renders/entree_vapeur_sud_nord_v1'
S = R / '.cache/entree_vapeur_sud_nord_v2/entree_vapeur_sud_nord_v2'
M = json.loads((O / 'manifest.json').read_text())
W, H = M['size_px']
WP, BP = M['water']['phases'], M['bubbles']['phases']


def load(p):
    return np.array(Image.open(p).convert('RGBA'))


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


def statics():
    return [load(O / p) for p in M['layer_order_bottom_to_top'][3:]]


def water():
    return [load(O / f'animation/eau/ESN2_00_eau_metano_f{t}.png') for t in range(WP)]


def sparks():
    return [load(O / f'animation/scintillements/ESN2_01_scintillements_f{t}.png') for t in range(WP)]


def bubbles():
    return [load(O / f'animation/bulles/ESN2_02_bulles_f{t:02d}.png') for t in range(BP)]


class Build(unittest.TestCase):
    def test_cadence_matches_metano(self):
        anim = json.loads((R / 'source/eau_metano/animations_carte.json').read_text())
        txt = json.dumps(anim)
        self.assertIn('"FrameLength": 10', txt.replace('"FrameLength":10', '"FrameLength": 10'))
        self.assertEqual((WP, M['water']['frame_length_ticks']), (4, 10))
        self.assertEqual(M['scene_loop_ticks'] % (WP * 10), 0)
        self.assertEqual(M['scene_loop_ticks'] % (BP * M['bubbles']['frame_length_ticks']), 0)

    def test_v1_terrain_reused_unchanged(self):
        for p in M['layer_order_bottom_to_top'][3:]:
            name = Path(p).name.split('_', 2)[2]
            v1 = next((V1 / 'calques').glob(f'ESN1_??_{name}'))
            self.assertTrue((load(O / p) == load(v1)).all(), name)
        self.assertNotIn('ombres', json.dumps(M['layer_order_bottom_to_top']))

    def test_sizes_names_alpha(self):
        names = [Path(p).name for p in M['layer_order_bottom_to_top']]
        self.assertEqual(len(names), len(set(names))); self.assertTrue(all(n.startswith('ESN2_') for n in names))
        for a in statics() + water() + sparks() + bubbles():
            self.assertEqual(a.shape[:2], (H, W))
            self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255})
            vis = a[a[..., 3] > 0].astype(int)
            self.assertEqual(int(((vis[:, 0] > 200) & (vis[:, 2] > 200) & (vis[:, 1] < 90)).sum()), 0)

    def test_water_metano_structure_and_loop(self):
        fr = water(); mask = fr[0][..., 3] == 255
        pal = {tuple(v) for v in M['water']['couleurs'].values()}
        for a in fr:
            self.assertTrue(((a[..., 3] == 255) == mask).all())
            self.assertTrue({tuple(c) for c in np.unique(a[mask][:, :3], axis=0)} <= pal)
        self.assertEqual(mask.sum(), (np.array(Image.open(V1 / 'masques/ESN1_masque_eau_complete.png')) > 0).sum())
        d = [int((fr[t][mask] != fr[(t + 1) % WP][mask]).any(1).sum()) for t in range(WP)]
        self.assertTrue(min(d) > 0 and max(d) < 2 * min(d), d)          # 3 -> 0 aussi homogène que les autres
        # l'aplat domine comme dans Métano (surface ~ 81 % des pixels opaques Métano)
        surf = (fr[0][mask][:, :3] == M['water']['couleurs']['surface']).all(1).mean()
        self.assertGreater(surf, 0.5)

    def test_overlays_only_on_visible_water(self):
        water_mask = water()[0][..., 3] == 255
        land = np.zeros((H, W), bool)
        for a in statics():
            land |= a[..., 3] == 255
        for a in sparks() + bubbles():
            self.assertFalse(((a[..., 3] > 0) & ~(water_mask & ~land)).any())

    def test_bubble_timeline_and_poses(self):
        b = M['bubbles']; self.assertEqual(len(b['timeline_phases']), 17); self.assertLess(len(b['timeline_phases']), BP)
        self.assertEqual(hashlib.sha256((HERE / 'bruts/bulles_8_poses.png').read_bytes()).hexdigest(), b['sha256'])
        fr = bubbles(); n = [int((a[..., 3] > 0).sum()) for a in fr]
        self.assertGreater(min(n), 0)                          # émetteurs décalés : jamais tous au repos
        self.assertEqual(len({o['decalage'] for o in b['emetteurs']}), len(b['emetteurs']))
        self.assertGreaterEqual(len(b['emetteurs']), 6)
        for k in b['poses']:
            self.assertEqual(load(O / f'poses_bulles/ESN2_bulle_{k}.png').shape, (24, 24, 4))

    def test_ora_and_scene(self):
        with zipfile.ZipFile(O / 'ESN2_entree_vapeur_calques.ora') as z:
            merged = np.array(Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA'))
        sc = Image.fromarray(water()[0]); sc.alpha_composite(Image.fromarray(sparks()[0])); sc.alpha_composite(Image.fromarray(bubbles()[0]))
        for a in statics():
            sc.alpha_composite(Image.fromarray(a))
        self.assertTrue((np.array(sc) == merged).all())
        self.assertTrue((np.array(sc) == load(O / 'review/ESN2_scene_t000.png')).all())
        self.assertTrue((np.array(sc)[..., 3] == 255).all())

    def test_access(self):
        acc = M['access']; self.assertTrue(acc['path_found_16x16'])
        self.assertGreater(acc['entry_px'][1], H - 64); self.assertLess(acc['threshold_px'][1], H // 2)

    def test_ground_roundtrip(self):
        doc = json.loads((S / f"Data/Ground/{M['pmdo']['asset']}.rsground").read_text()); o = doc['Object']
        self.assertEqual(doc['Version'], '0.8.12.0'); self.assertEqual(len(o['Layers']), 11); self.assertEqual(o['Layers'][-1]['Layer'], 4)
        nr = loadmod('native_reader', R / 'source/cote_v5_expeditions/audit_references.py')
        banks = {p.stem: nr.tiles(p)[1] for p in (S / 'Content/Tile').glob('*.tile')}
        self.assertEqual(set(banks), set(M['pmdo']['banks']))
        expected = [(water(), 10), (sparks(), 10), (bubbles(), M['bubbles']['frame_length_ticks'])] + [([a], 60) for a in statics()]
        for li, (frames, ticks) in enumerate(expected):
            for t in sorted({0, len(frames) - 1, len(frames) // 2}):
                out = np.zeros((H, W, 4), 'uint8')
                for x, col in enumerate(o['Layers'][li]['Tiles']):
                    for y, cell in enumerate(col):
                        for track in cell['Layers']:
                            if len(track['Frames']) > 1:
                                self.assertEqual(len(track['Frames']), len(frames)); self.assertEqual(track['FrameLength'], ticks)
                            f = track['Frames'][t % len(track['Frames'])]
                            out[y*8:y*8+8, x*8:x*8+8] = np.array(nr.straight(banks[f['Sheet']][f['TexLoc']['X'], f['TexLoc']['Y']]))
                self.assertTrue((out == frames[t]).all(), (li, t))
        self.assertEqual(sum(w['Tags'] for c in o['obstacles'] for w in c), M['access']['blocked_cells'])
        self.assertEqual({m['EntName'] for m in o['Entities'][0]['Markers']}, {'entrance', 'donjon_seuil'})
        tools = loadmod('index_tools', R / 'source/pmdo_cote/INSTALLER.py')
        self.assertEqual(set(tools.read_index(S / 'Content/Tile/index.idx')), set(M['pmdo']['banks']))


if __name__ == '__main__':
    unittest.main()
