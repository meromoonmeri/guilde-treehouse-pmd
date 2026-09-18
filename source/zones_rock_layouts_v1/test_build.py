import unittest, json, hashlib, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'exports/zones_rock_layouts_v1'

class ZonesRockLayoutsTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((O / 'manifest.json').read_text())

    def test_three_rock_maps_produced(self):
        self.assertEqual(len(self.manifest['maps']), 3)
        ids = [m['id'] for m in self.manifest['maps']]
        self.assertIn('01_defile_rocheux_bleu', ids)
        self.assertIn('02_plateau_volcanique_croisement', ids)
        self.assertIn('03_caverne_violette_deux_galeries', ids)

    def test_dimensions_512x512_and_grid_8px(self):
        for m in self.manifest['maps']:
            self.assertEqual(m['size'], [512, 512])
            self.assertEqual(m['size'][0] % 8, 0)
            self.assertEqual(m['size'][1] % 8, 0)

    def test_pixels_have_exact_canonical_provenance(self):
        sources = [np.array(Image.open(R / s['file']).convert('RGBA')) for s in self.manifest['sources']]
        for m in self.manifest['maps']:
            for l in m['layers']:
                img_path = O / m['id'] / l['file']
                prov_path = O / m['id'] / l['provenance']
                a = np.array(Image.open(img_path))
                q = np.load(prov_path)['source_sxy']
                mask = a[:, :, 3] > 0
                # Opaque pixels must have valid source coords
                self.assertTrue((q[~mask] == -1).all(), f"Transparent pixels must have -1 provenance in {l['file']}")
                for s_id in np.unique(q[mask, 0]):
                    self.assertGreaterEqual(s_id, 0)
                    self.assertLess(s_id, len(sources))
                    where = mask & (q[:, :, 0] == s_id)
                    p = q[where]
                    # Verify exact 1:1 pixel equivalence
                    src_pixels = sources[s_id][p[:, 2], p[:, 1]]
                    dst_pixels = a[where]
                    self.assertTrue(np.array_equal(dst_pixels, src_pixels), f"Pixel mismatch in layer {l['file']} against source {s_id}")

    def test_composite_matches_layer_stack(self):
        for m in self.manifest['maps']:
            comp = Image.new('RGBA', tuple(m['size']))
            for l in m['layers']:
                layer_im = Image.open(O / m['id'] / l['file']).convert('RGBA')
                self.assertEqual(layer_im.size, (512, 512))
                comp.alpha_composite(layer_im)
            saved_comp = Image.open(O / m['id'] / 'composite.png').convert('RGBA')
            self.assertEqual(comp.tobytes(), saved_comp.tobytes(), f"Composite mismatch for map {m['id']}")

    def test_tiled_tsx_validity(self):
        for m in self.manifest['maps']:
            for l in m['layers']:
                tsx_path = O / m['id'] / Path(l['file']).with_suffix('.tsx')
                self.assertTrue(tsx_path.exists())
                tree = ET.parse(tsx_path)
                root = tree.getroot()
                self.assertEqual(root.get('tilewidth'), '8')
                self.assertEqual(root.get('tileheight'), '8')
                self.assertEqual(root.get('columns'), '64')
                self.assertEqual(root.get('tilecount'), '4096')
                img_el = root.find('image')
                self.assertIsNotNone(img_el)
                self.assertEqual(img_el.get('width'), '512')
                self.assertEqual(img_el.get('height'), '512')

    def test_path_continuity(self):
        for m in self.manifest['maps']:
            path_im = Image.open(O / m['id'] / 'path_connectivity_mask.png')
            arr = np.array(path_im) > 0
            self.assertTrue(arr.any(), f"Path mask is empty for map {m['id']}")
            # Path touches bottom arrival
            self.assertTrue(arr[-8:, :].any(), f"Path does not reach bottom in {m['id']}")

    def test_clean_status_no_false_engine_claim(self):
        for m in self.manifest['maps']:
            self.assertEqual(m['runtime'], 'NOT TESTED')
            self.assertFalse(m['art_approved'])
            self.assertIn('not tested', m['connectivity'].lower())

if __name__ == '__main__':
    unittest.main()
