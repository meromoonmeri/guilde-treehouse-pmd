"""Contrôles d’assets, couches, animation et Ground (pas un test de jeu PMDO).
Lancer après build.py : .venv/bin/python -m unittest source.entree_grotte_cascade_sud_nord_v1.test_build -v
"""
from pathlib import Path
import hashlib
import importlib.util
import io
import json
import struct
import unittest
import zipfile

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / 'renders/entree_grotte_cascade_sud_nord_v1'
STAGE = ROOT / '.cache/entree_grotte_cascade_sud_nord_v1/entree_grotte_cascade_sud_nord'
PREFIX = 'EGC1'
MANIFEST = json.loads((OUT / 'manifest.json').read_text())
W, H = MANIFEST['size_px']
WATER_N = MANIFEST['water']['cycle_frames']


def rgba(path):
    with Image.open(path) as image:
        return np.array(image.convert('RGBA'))


def load_build():
    path = HERE / 'build.py'
    spec = importlib.util.spec_from_file_location('egc_build_test_helpers', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def decode_tile(path):
    raw = Path(path).read_bytes()
    tile_size, count = struct.unpack_from('<II', raw, 0)
    if tile_size != 8:
        raise AssertionError((path, tile_size))
    result, payload_cache = {}, {}
    for i in range(count):
        x, y, offset = struct.unpack_from('<IIQ', raw, 8 + 16 * i)
        if offset not in payload_cache:
            length = struct.unpack_from('<q', raw, offset)[0]
            payload_cache[offset] = np.asarray(Image.open(io.BytesIO(raw[offset + 8:offset + 8 + length])).convert('RGBA'))
        result[(x, y)] = payload_cache[offset]
    return result


def reconstruct_ground_layer(layer, banks, index, frame, width, height):
    out = np.zeros((height * 8, width * 8, 4), dtype=np.uint8)
    tiles = layer['Tiles']
    for x in range(width):
        for y in range(height):
            tracks = tiles[x][y].get('Layers', [])
            if not tracks:
                continue
            refs = tracks[0]['Frames']
            ref = refs[frame % len(refs)]
            bank = ref['Sheet']
            loc = ref['TexLoc']
            tile = banks[bank][(loc['X'], loc['Y'])]
            out[y * 8:y * 8 + 8, x * 8:x * 8 + 8] = tile
    return out


class Build(unittest.TestCase):
    def test_reference_and_raw_hashes(self):
        self.assertEqual(hashlib.sha256((ROOT / MANIFEST['reference']['file']).read_bytes()).hexdigest(),
                         MANIFEST['reference']['sha256'])
        for item in MANIFEST['raw_inputs']:
            self.assertEqual(hashlib.sha256((ROOT / item['file']).read_bytes()).hexdigest(), item['sha256'])
            with Image.open(ROOT / item['file']) as image:
                self.assertEqual(image.size, tuple(item['size_px']))

    def test_dimensions_alpha_and_no_magenta_leak(self):
        self.assertEqual((W, H), (768, 576))
        self.assertEqual((W // 8, H // 8), (96, 72))
        self.assertEqual(W * 3, H * 4)
        static_files = sorted((OUT / 'calques').glob('*.png'))
        self.assertEqual(len(static_files), 4)
        for path in static_files:
            a = rgba(path)
            self.assertEqual(a.shape, (H, W, 4))
            self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255}, path.name)
            opaque = a[a[..., 3] == 255].astype(np.int16)
            key = (opaque[:, 0] > 35) & (opaque[:, 2] > 45) & (opaque[:, 1] < np.minimum(opaque[:, 0], opaque[:, 2]) * 1.20) & (np.abs(opaque[:, 0] - opaque[:, 2]) < 130)
            self.assertEqual(int(key.sum()), 0, path.name)
        for i in range(WATER_N):
            a = rgba(OUT / 'animation/eau' / f'{PREFIX}_01_eau_caverne_f{i:02d}.png')
            self.assertEqual(a.shape, (H, W, 4))
            self.assertTrue(set(np.unique(a[..., 3])) <= {0, 255})
            opaque = a[a[..., 3] == 255].astype(np.int16)
            key = (opaque[:, 0] > 35) & (opaque[:, 2] > 45) & (opaque[:, 1] < np.minimum(opaque[:, 0], opaque[:, 2]) * 1.20) & (np.abs(opaque[:, 0] - opaque[:, 2]) < 130)
            self.assertEqual(int(key.sum()), 0, f'water frame {i}')

    def test_uniform_normalization_is_documented(self):
        n = MANIFEST['normalization']
        self.assertAlmostEqual(n['scale'], 576 / 896)
        self.assertEqual(n['scaled_px'], [771, 576])
        self.assertEqual(n['crop_x_px'], [1, 2])
        self.assertNotIn('anisotropic', n['method'])

    def test_water_mask_and_closed_palette_cycle(self):
        frames = [rgba(OUT / 'animation/eau' / f'{PREFIX}_01_eau_caverne_f{i:02d}.png') for i in range(WATER_N)]
        masks = [a[..., 3] == 255 for a in frames]
        self.assertTrue(all(np.array_equal(masks[0], m) for m in masks[1:]))
        self.assertGreater(int(masks[0].sum()), 1000)
        differences = [int(np.count_nonzero(np.any(frames[i][masks[0]] != frames[(i + 1) % WATER_N][masks[0]], axis=1)))
                       for i in range(WATER_N)]
        self.assertTrue(all(v > 0 for v in differences), differences)
        self.assertLess(max(differences), int(masks[0].sum() * 0.8), differences)
        self.assertEqual(MANIFEST['water']['cycle_frames'], 12)
        self.assertEqual(MANIFEST['water']['frame_length_ticks'], 10)
        self.assertIn('non native', MANIFEST['water']['source_role'].lower())

    def test_full_map_alpha_and_ora_recomposition(self):
        expected_names = ['00_sol_complet', '02_parois_rocheuses', '03_chemin', '04_voute_et_seuil_nord']
        layers = [rgba(OUT / 'calques' / f'{PREFIX}_{name}.png') for name in expected_names]
        water = rgba(OUT / 'animation/eau' / f'{PREFIX}_01_eau_caverne_f00.png')
        scene = np.zeros((H, W, 4), dtype=np.uint8)
        for array in [layers[0], water, *layers[1:]]:
            scene = np.asarray(Image.alpha_composite(Image.fromarray(scene), Image.fromarray(array)))
        self.assertTrue(np.all((scene[..., 3] == 255) | (scene[..., 3] == 0)))
        with zipfile.ZipFile(OUT / f'{PREFIX}_entree_grotte_cascade_calques.ora') as archive:
            merged = rgba(io.BytesIO(archive.read('mergedimage.png')))
        self.assertTrue(np.array_equal(scene, merged))
        self.assertTrue(np.array_equal(scene, rgba(OUT / 'review' / f'{PREFIX}_scene_phase00.png')))

    def test_south_to_north_access_and_markers(self):
        mod = load_build()
        doc = json.loads((STAGE / f'Data/Ground/{MANIFEST["pmdo"]["asset"]}.rsground').read_text())
        obj = doc['Object']
        blocked = np.asarray([[bool(obj['obstacles'][x][y]['Tags']) for x in range(W // 8)]
                              for y in range(H // 8)], dtype=bool)
        access = MANIFEST['access']
        entry = access['entry_px']; goal = access['threshold_px']
        self.assertGreater(entry[1], H - 64)
        self.assertLess(goal[1], H // 2)
        self.assertTrue(access['path_found'])
        for px, py in (entry, goal):
            self.assertFalse(blocked[py // 8:py // 8 + 2, px // 8:px // 8 + 2].any())
        ok, _, _, _ = mod.reachable(blocked,
                                   (entry[1] // 8, entry[0] // 8),
                                   [(goal[1] // 8, goal[0] // 8)])
        self.assertTrue(ok)

    def test_blocked_start_is_not_traversable(self):
        mod = load_build()
        blocked = np.zeros((8, 8), dtype=bool)
        blocked[3, 3] = True
        ok, goal, explored, free = mod.reachable(blocked, (3, 3), [(3, 3)])
        self.assertFalse(ok)
        self.assertIsNone(goal)
        self.assertEqual(explored, 0)
        self.assertFalse(free[3, 3])

    def test_ground_schema_tiles_roundtrip_and_index(self):
        manifest = MANIFEST
        asset = manifest['pmdo']['asset']
        doc = json.loads((STAGE / f'Data/Ground/{asset}.rsground').read_text())
        obj = doc['Object']
        self.assertEqual(doc['Version'], '0.8.12.0')
        self.assertEqual(obj['TexSize'], 1)
        self.assertEqual((len(obj['Layers']), len(obj['Layers'][0]['Tiles']), len(obj['Layers'][0]['Tiles'][0])),
                         (6, W // 8, H // 8))
        self.assertEqual(obj['Layers'][-1]['Layer'], 4)
        tile_paths = sorted((STAGE / 'Content/Tile').glob('*.tile'))
        self.assertEqual({p.stem for p in tile_paths}, set(manifest['pmdo']['tile_banks']))
        banks = {path.stem: decode_tile(path) for path in tile_paths}
        checks = [(0, 0, 'calques/EGC1_00_sol_complet.png')]
        checks += [(1, t, f'animation/eau/EGC1_01_eau_caverne_f{t:02d}.png') for t in range(WATER_N)]
        checks += [(2, 0, 'calques/EGC1_02_parois_rocheuses.png'),
                   (3, 0, 'calques/EGC1_03_chemin.png'),
                   (4, 0, 'calques/EGC1_04_voute_et_seuil_nord.png')]
        for li, frame, expected in checks:
            actual = reconstruct_ground_layer(obj['Layers'][li], banks, {}, frame, W // 8, H // 8)
            self.assertTrue(np.array_equal(actual, rgba(OUT / expected)), (li, frame, expected))
        markers = {m['EntName']: m['Collider'] for m in obj['Entities'][0]['Markers']}
        self.assertEqual(set(markers), {'entrance', 'donjon_seuil'})
        self.assertEqual(markers['entrance']['X'], manifest['access']['entry_px'][0])
        self.assertEqual(markers['donjon_seuil']['Y'], manifest['access']['threshold_px'][1])
        tools_spec = importlib.util.spec_from_file_location('egc_test_index_tools', ROOT / 'source/pmdo_cote/INSTALLER.py')
        tools = importlib.util.module_from_spec(tools_spec); tools_spec.loader.exec_module(tools)
        self.assertEqual(set(tools.read_index(STAGE / 'Content/Tile/index.idx')), set(manifest['pmdo']['tile_banks']))

    def test_limits_are_not_overstated(self):
        self.assertFalse(MANIFEST['pmdo']['runtime_tested'])
        self.assertFalse(MANIFEST['gameplay_validated'])
        self.assertFalse(MANIFEST['art_approved'])
        self.assertIn('pas une texture native', MANIFEST['terrain_origin'])


if __name__ == '__main__':
    unittest.main()
