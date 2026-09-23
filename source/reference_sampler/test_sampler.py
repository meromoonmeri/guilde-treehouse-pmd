"""Controles echantillonneur : packs complets, prompts verrouilles, patchs reels."""
import json
import unittest
from pathlib import Path

from PIL import Image

R = Path(__file__).resolve().parents[2]
PACKS = ['aride', 'plage', 'jardin']


class T(unittest.TestCase):
    def test_packs_complets(self):
        for p in PACKS:
            d = R / 'source/reference_sampler/packs' / p
            for f in ('palette.png', 'patch_board.png', 'samples.json', 'prompt.txt'):
                self.assertTrue((d / f).exists(), (p, f))
            s = json.loads((d / 'samples.json').read_text(encoding='utf-8'))
            self.assertGreaterEqual(len(s['colors']), 8, p)
            for c in s['colors']:
                self.assertTrue((d / c['file']).exists(), (p, c['file']))
                im = Image.open(d / c['file'])
                self.assertGreaterEqual(im.width, 16)
                r = c['rect']
                self.assertEqual([im.width, im.height], [r[2] - r[0], r[3] - r[1]])

    def test_prompt_verrouille(self):
        for p in PACKS:
            d = R / 'source/reference_sampler/packs' / p
            s = json.loads((d / 'samples.json').read_text(encoding='utf-8'))
            t = (d / 'prompt.txt').read_text(encoding='utf-8')
            for c in s['colors'][:8]:
                self.assertIn(c['color'], t, (p, c['color']))
            for kw in ('#FF00FF', '8px', 'No sky'):
                self.assertIn(kw, t, (p, kw))

    def test_patchs_propres(self):
        # Les patchs sont des extraits originaux : pas de magenta dedans
        import numpy as np
        for p in PACKS:
            d = R / 'source/reference_sampler/packs' / p
            s = json.loads((d / 'samples.json').read_text(encoding='utf-8'))
            for c in s['colors']:
                a = np.array(Image.open(d / c['file']).convert('RGB')).astype(int)
                mg = (a[:, :, 0] > 200) & (a[:, :, 2] > 150) & (a[:, :, 1] < 120)
                self.assertFalse(mg.any(), (p, c['file']))


if __name__ == '__main__':
    unittest.main()
