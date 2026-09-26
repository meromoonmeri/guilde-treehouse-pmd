"""Tests du lot Entrée Cascade V1 (pixels natifs exacts).
.venv/bin/python -m unittest source.entree_cascade_sud_nord_v1.test_build -v   (après build.py)
"""
from pathlib import Path
import importlib.util, json, struct, unittest, zipfile

import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'renders/entree_cascade_sud_nord_v1'
S = R / '.cache/entree_cascade_sud_nord_v1/entree_cascade_sud_nord'


def loadmod(name, path):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m


B = loadmod('ecn1_build', R / 'source/entree_cascade_sud_nord_v1/build.py')
M = json.loads((O / 'manifest.json').read_text())
PROV = np.load(O / 'provenance' / 'ECN1_provenance.npz')
SRC = B.load_sources()
LAYERS = {p.split('/')[-1]: p for p in M['layer_order_bottom_to_top']}


def rgba(p):
    return np.array(Image.open(O / p).convert('RGBA'))


def frames(pattern):
    return [rgba(pattern.replace('fX', f'f{t}')) for t in range(B.PHASES)]


class Provenance(unittest.TestCase):
    """Chaque pixel opaque provient tel quel d'une source canonique (aucun pixel généré, recoloré, tourné ou redimensionné)."""

    def check(self, arr, pid, sx, sy):
        op = arr[..., 3] == 255
        self.assertTrue(np.array_equal(op, pid > 0), 'provenance manquante ou excédentaire')
        self.assertTrue(((arr[..., 3] == 0) | op).all(), 'alpha non binaire')
        for i in np.unique(pid[op]):
            m = pid == i
            src = SRC[int(i)]
            self.assertTrue((src[sy[m], sx[m], 3] == 255).all(), f'source {i} : pixel transparent copié')
            self.assertTrue(np.array_equal(arr[m][:, :3], src[sy[m], sx[m], :3]), f'source {i} : pixel modifié')

    def test_static_layers(self):
        for key, base in [('fond', '00'), ('sol', '01'), ('eau', '02'), ('plafond', '03'), ('parois', '04'), ('rochers', '06')]:
            fn = [p for p in LAYERS.values() if p.startswith('calques/ECN1_' + base)][0]
            self.check(rgba(fn), PROV[f'{key}_pid'], PROV[f'{key}_sx'], PROV[f'{key}_sy'])

    def test_cascade_frames_native_translation(self):
        fr = frames('animation/cascade/ECN1_05_cascade_fX.png')
        x0, y0, x1, y1 = B.FALLS
        for t in range(B.PHASES):
            self.check(fr[t], PROV[f'cascade_f{t}_pid'], PROV[f'cascade_f{t}_sx'], PROV[f'cascade_f{t}_sy'])
            self.assertEqual(set(np.unique(PROV[f'cascade_f{t}_pid'][fr[t][..., 3] == 255]).tolist()), {3 + t})
            body = SRC[3 + t][24:120, 8:56]
            self.assertTrue(np.array_equal(fr[t][y0:y1, x0:x0 + 48], body))
            self.assertTrue(np.array_equal(fr[t][y0:y1, x0 + 48:x1], body))
            outside = fr[t].copy(); outside[y0:y1, x0:x1] = 0
            self.assertEqual(int(outside[..., 3].sum()), 0)
        self.assertEqual(len({f.tobytes() for f in fr}), B.PHASES, 'phases identiques')

    def test_sparkles_native(self):
        fams = B.BM.sparkle_families()
        fr = frames('animation/scintillements/ECN1_07_scintillements_fX.png')
        names = list(fams)
        for t in range(B.PHASES):
            pv = PROV[f'scintillements_f{t}']; op = fr[t][..., 3] == 255
            self.assertTrue(np.array_equal(op, pv[..., 0] > 0))
            for fi, name in enumerate(names, start=1):
                m = pv[..., 0] == fi
                if m.any():
                    ref = fams[name][t]
                    self.assertTrue(np.array_equal(fr[t][m], ref[pv[m][:, 2], pv[m][:, 1]]))
        for p in M['sparkles']['placements']:
            self.assertIn(p['famille'], names)

    def test_no_generated_pixels(self):
        guide = R / M['guide_composition']['file']
        self.assertTrue(guide.exists())
        for op in M['operations']:
            self.assertIn(op['source'], ('L', 'G', 'cascade_frame_1..4'))
        for i, meta in M['sources'].items():
            self.assertEqual(B.sha(R / meta['file']), meta['sha256'], 'source canonique modifiée')


class Geometry(unittest.TestCase):
    def test_sizes_and_stack(self):
        self.assertEqual(M['size_px'], [768, 576])
        for p in M['layer_order_bottom_to_top']:
            a = rgba(p.replace('fX', 'f0'))
            self.assertEqual(a.shape[:2], (576, 768))
        self.assertEqual(len(M['layer_order_bottom_to_top']), 8)
        self.assertEqual(M['layer_order_bottom_to_top'][-3].split('/')[1], 'cascade')

    def test_access_and_markers(self):
        a = M['access']
        self.assertTrue(a['path_found_16x16'])
        self.assertEqual(a['entry_px'][1], 576 - 16)
        x, y = a['threshold_px']
        lx0, ly0, lx1, ly1 = B.LEDGE
        self.assertTrue(lx0 <= x and x + 16 <= lx1 and ly0 <= y and y + 16 <= ly1, 'seuil hors plateforme')
        self.assertGreaterEqual(y, B.FALLS[3], 'seuil sous la chute')
        self.assertLess(a['blocked_cells'], a['total_cells'])

    def test_loop_and_cadence(self):
        self.assertEqual(M['cascade']['frame_length_ticks'], 10)
        self.assertEqual(M['sparkles']['frame_length_ticks'], 10)
        self.assertEqual(M['scene_loop_ticks'], 40)
        with Image.open(O / 'review/ECN1_scene_animee.webp') as im:
            self.assertEqual(im.n_frames, 4)
        # dernière -> première : la scène au tick 40 est la scène au tick 0
        fr = frames('animation/cascade/ECN1_05_cascade_fX.png')
        self.assertTrue(np.array_equal(fr[(40 // 10) % 4], fr[0]))

    def test_water_static_under_sparkles(self):
        self.assertEqual(M['water']['phases'], 1)
        eau = rgba(LAYERS['ECN1_02_eau_profonde.png'])
        for t in range(B.PHASES):
            sp = rgba(f'animation/scintillements/ECN1_07_scintillements_f{t}.png')
            self.assertTrue((eau[..., 3][sp[..., 3] == 255] == 255).all(), 'scintillement hors eau')


class Package(unittest.TestCase):
    def test_ground_project(self):
        g = json.loads((S / f'Data/Ground/{B.ASSET}.rsground').read_text())
        o = g['Object']
        self.assertEqual(len(o['Layers']), 9)
        self.assertEqual(o['Layers'][-1]['Name'], '08 Vos elements avant-plan (Top)')
        self.assertEqual(len(o['obstacles']), 96); self.assertEqual(len(o['obstacles'][0]), 72)
        names = [m['EntName'] for m in o['Entities'][0]['Markers']]
        self.assertEqual(names, ['entrance', 'donjon_seuil'])
        for p in sorted((S / 'Content/Tile').glob('*.tile')):
            with p.open('rb') as f:
                h, n = struct.unpack('<ii', f.read(8))
            self.assertEqual(h, 8); self.assertGreater(n, 0)
        self.assertTrue((S / 'Content/Tile/index.idx').exists())
        self.assertTrue((S / 'INSTALLER.py').exists())
        self.assertIn("if relative.as_posix() == 'Content/Tile/index.idx'", (S / 'INSTALLER.py').read_text())

    def test_ora(self):
        with zipfile.ZipFile(O / 'ECN1_entree_cascade_calques.ora') as z:
            self.assertEqual(z.read('mimetype'), b'image/openraster')
            stack = z.read('stack.xml').decode()
            for i in range(8):
                self.assertIn(f'{i:02d}_', stack)


if __name__ == '__main__':
    unittest.main()
