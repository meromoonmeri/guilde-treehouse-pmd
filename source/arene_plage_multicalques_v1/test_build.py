import unittest, json, xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RENDERS_DIR = ROOT / 'renders/arene_plage_multicalques_v1'
EXPORTS_DIR = ROOT / 'exports/arene_plage_multicalques_v1'

class BeachArenaMulticalquesTests(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((RENDERS_DIR / 'manifest.json').read_text())

    def test_three_layouts_exist(self):
        self.assertEqual(len(self.manifest['layouts']), 3)
        ids = [l['id'] for l in self.manifest['layouts']]
        self.assertIn('01_grande_arene_plage_ouverte', ids)
        self.assertIn('02_defile_cotier_terrasse', ids)
        self.assertIn('03_atoll_sable_double_recif', ids)

    def test_dimensions_512x512_and_grid_8px(self):
        for lay in self.manifest['layouts']:
            self.assertEqual(lay['size'], [512, 512])
            self.assertEqual(lay['size'][0] % 8, 0)
            self.assertEqual(lay['size'][1] % 8, 0)

    def test_multicalque_layers_separation(self):
        for lay in self.manifest['layouts']:
            layer_ids = [l['id'] for l in lay['layers']]
            self.assertIn('01_arene_sable_sol', layer_ids)
            self.assertIn('03_ecume_rivage', layer_ids)
            self.assertIn('04_falaises_rouges_fond', layer_ids)
            self.assertIn('05_massifs_rocheux_lateraux', layer_ids)
            self.assertIn('06_rochers_et_recifs_premier_plan', layer_ids)
            self.assertEqual(len(lay['water_frames']), 8)

    def test_water_palette_cycling_integrity(self):
        for lay in self.manifest['layouts']:
            r_dir = RENDERS_DIR / lay['id'] / '02_eau_mer_palette_cycling'
            frames = [np.array(Image.open(r_dir / fn)) for fn in lay['water_frames']]
            self.assertEqual(len(frames), 8)

            # 1. All frames have identical dimensions
            for f in frames:
                self.assertEqual(f.shape, (512, 512, 4))

            # 2. Alpha mask is strictly identical across all 8 frames
            alpha0 = frames[0][:, :, 3]
            for f in frames[1:]:
                self.assertTrue(np.array_equal(f[:, :, 3], alpha0))

            # 3. Water colors shift across frames
            diff_count = 0
            for i in range(1, 8):
                if np.any(frames[i][:, :, :3] != frames[0][:, :, :3]):
                    diff_count += 1
            self.assertEqual(diff_count, 7, "All 7 non-zero phases must differ from phase 0")

    def test_pixel_provenance_to_source_reference(self):
        ref_arr = np.array(Image.open(ROOT / 'arenapmdskybeach.png').convert('RGBA'))
        for lay in self.manifest['layouts']:
            e_dir = EXPORTS_DIR / lay['id']
            for l in lay['layers']:
                prov_path = e_dir / l['provenance']
                self.assertTrue(prov_path.exists())
                prov = np.load(prov_path)['source_xy']
                img_path = e_dir / l['file_day']
                arr = np.array(Image.open(img_path))
                mask = arr[:, :, 3] > 0
                self.assertTrue((prov[~mask] == -1).all())

                # Check mapped coordinates match reference image pixels
                ys, xs = np.where(mask)
                for y, x in zip(ys[::50], xs[::50]): # Sample checks
                    sx, sy = prov[y, x]
                    self.assertGreaterEqual(sx, 0)
                    self.assertGreaterEqual(sy, 0)
                    self.assertLess(sx, ref_arr.shape[1])
                    self.assertLess(sy, ref_arr.shape[0])
                    self.assertTrue(np.array_equal(arr[y, x], ref_arr[sy, sx]))

    def test_tiled_tsx_metadata(self):
        for lay in self.manifest['layouts']:
            e_dir = EXPORTS_DIR / lay['id']
            for l in lay['layers']:
                tsx_path = e_dir / Path(l['file_day']).with_suffix('.tsx')
                self.assertTrue(tsx_path.exists())
                tree = ET.parse(tsx_path)
                root = tree.getroot()
                self.assertEqual(root.get('tilewidth'), '8')
                self.assertEqual(root.get('tileheight'), '8')
                self.assertEqual(root.get('columns'), '64')
                self.assertEqual(root.get('tilecount'), '4096')

    def test_night_mode_validity(self):
        for lay in self.manifest['layouts']:
            r_dir = RENDERS_DIR / lay['id']
            for l in lay['layers']:
                day_im = np.array(Image.open(r_dir / l['file_day']))
                night_im = np.array(Image.open(r_dir / l['file_night']))
                # Alpha channels must be 100% identical
                self.assertTrue(np.array_equal(day_im[:, :, 3], night_im[:, :, 3]))
                # Night pixels should be generally darker (lower average luminance)
                mask = day_im[:, :, 3] > 0
                if mask.any():
                    self.assertLessEqual(night_im[mask, :3].mean(), day_im[mask, :3].mean() + 2)

if __name__ == '__main__':
    unittest.main()
