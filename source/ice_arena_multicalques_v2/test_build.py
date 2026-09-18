"""Checks for the 5-layer ice arena decomposition + animated boréal.

- The 5 layer PNGs must partition the reference exactly (recomposite == guide).
- Boréal frames: frame 0 equals the boréal layer; loop closes; the undulation
  never exceeds the declared amplitude; colors actually change across the loop.
- Alpha is binary on every static layer.
"""
import unittest, json
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R/'exports/ice_arena_multicalques_v2'
GUIDE = R/'source/ice_arena_aurora_v1/generation/layout_guide.png'
LAYERS = ['ciel', 'boreal', 'terrain', 'bordure', 'cliff']


class IceArenaLayersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rep = json.loads((O/'verification.json').read_text())
        cls.src = np.array(Image.open(GUIDE).convert('RGB'))
        cls.layers = {k: np.array(Image.open(O/'layers'/f'{k}.png').convert('RGBA')) for k in LAYERS}

    def test_reconstruction_exact(self):
        self.assertTrue(self.rep['reconstruction_exact'])
        comp = np.zeros((*self.src.shape[:2], 4), np.uint8)
        for k in ['ciel', 'boreal', 'terrain', 'bordure', 'cliff']:
            lay = self.layers[k]
            comp = np.where(lay[:, :, 3:4] > 0, lay, comp)
        self.assertTrue(np.array_equal(comp[:, :, :3], self.src))

    def test_layers_partition_reference(self):
        masks = {k: self.layers[k][:, :, 3] > 0 for k in LAYERS}
        total = np.zeros(self.src.shape[:2], int)
        for k in LAYERS:
            total += masks[k]
        self.assertTrue((total == 1).all(), 'layers must be disjoint and cover every pixel')
        for k in LAYERS:
            self.assertEqual(int(masks[k].sum()), self.rep['layer_pixel_counts'][k])

    def test_layer_pixels_come_from_reference(self):
        for k in LAYERS:
            lay = self.layers[k]; m = lay[:, :, 3] > 0
            self.assertTrue(np.array_equal(lay[m][:, :3], self.src[m]))

    def test_alpha_binary(self):
        for k in LAYERS:
            self.assertTrue(set(np.unique(self.layers[k][:, :, 3])).issubset({0, 255}))

    def test_boreal_frame0_and_loop(self):
        f0 = np.array(Image.open(O/'aurora_frames/frame_00.png').convert('RGBA'))
        self.assertTrue(np.array_equal(f0, self.layers['boreal']))
        n = self.rep['frames']
        mid = np.array(Image.open(O/'aurora_frames'/f'frame_{n//2:02d}.png').convert('RGBA'))
        m = f0[:, :, 3] > 0
        self.assertGreater(np.mean(np.any(mid[:, :, :3] != f0[:, :, :3], axis=2)[m]), 0.05, 'no color change')

    def test_undulation_amplitude(self):
        self.assertLessEqual(self.rep['wave_amplitude_px'], 2)


if __name__ == '__main__':
    unittest.main()
