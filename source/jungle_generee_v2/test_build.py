"""Controles Jungle G2 (generee magenta) : pas de magenta, recomposition, boucle, echelle."""
import json
import unittest
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'renders/jungle_generee_v2'
W, H = 512, 640
MAN = json.loads((O / 'manifest.json').read_text(encoding='utf-8'))
LAYERS = ['01_sol', '02_paroi', '03_cascades', '04_bassins', '05_vegetation']
PHASES = MAN['animation']['phases']
STEP = MAN['animation']['step_px']
BANDS = [tuple(b) for b in MAN['partition']['bandes_chutes']]
FEET = MAN['partition']['pieds_y']


def magenta_stain(rgba):
    rgb = rgba[:, :, :3].astype(int)
    return (np.minimum(rgb[:, :, 0], rgb[:, :, 2]) - rgb[:, :, 1] > 25) & (rgba[:, :, 3] > 0)


class T(unittest.TestCase):
    def test_layers_size_mode(self):
        for n in LAYERS:
            im = Image.open(O / f'JungleG2_{n}.png')
            self.assertEqual(im.size, (W, H))
            self.assertEqual(im.mode, 'RGBA')

    def test_pmdo_scale_8px(self):
        self.assertEqual(W % 8, 0)
        self.assertEqual(H % 8, 0)
        self.assertEqual(MAN['pmdo_scale']['cases_8px'], [W // 8, H // 8])
        self.assertEqual(MAN['pmdo_scale']['texsize'], 1)

    def test_zero_magenta_residuel(self):
        for n in LAYERS:
            rgba = np.array(Image.open(O / f'JungleG2_{n}.png'))
            self.assertFalse(magenta_stain(rgba).any(), n)
        for p in (0, PHASES // 2, PHASES - 1):
            rgba = np.array(Image.open(O / f'cascades_phases/JungleG2_03_cascades_phase_{p:02d}.png'))
            self.assertFalse(magenta_stain(rgba).any(), p)

    def test_sol_full_bleed(self):
        a = np.array(Image.open(O / 'JungleG2_01_sol.png'))[:, :, 3]
        self.assertTrue((a == 255).all())

    def test_falls_touch_top(self):
        rgba = np.array(Image.open(O / 'JungleG2_03_cascades.png'))
        top = rgba[0, :, 3] > 0
        for x0, x1 in BANDS:
            self.assertTrue(top[x0:x1].any(), (x0, x1))

    def test_animation_loop_exact(self):
        self.assertEqual(PHASES * STEP, FEET)
        offs = MAN['animation']['offsets']
        p0 = np.array(Image.open(O / 'cascades_phases/JungleG2_03_cascades_phase_00.png'))
        for p in range(PHASES):
            cur = np.array(Image.open(O / f'cascades_phases/JungleG2_03_cascades_phase_{p:02d}.png'))
            for (x0, x1), off in zip(BANDS, offs):
                expect = np.roll(p0[0:FEET, x0:x1], (off + p * STEP - offs[BANDS.index((x0, x1))]) if False else p * STEP, axis=0)
                base = np.roll(p0[0:FEET, x0:x1], -off, axis=0)
                self.assertTrue((cur[0:FEET, x0:x1] == np.roll(base, off + p * STEP, axis=0)).all(), (p, x0, x1))
        # phase PHASES == phase 0
        for (x0, x1), off in zip(BANDS, offs):
            base = np.roll(p0[0:FEET, x0:x1], -off, axis=0)
            self.assertTrue((np.roll(base, off + PHASES * STEP, axis=0) == p0[0:FEET, x0:x1]).all())

    def test_recomposition_exact(self):
        comp = Image.new('RGBA', (W, H))
        for n in LAYERS:
            comp.alpha_composite(Image.open(O / f'JungleG2_{n}.png'))
        ref = Image.open(O / 'JungleG2_composite_phase_00.png')
        self.assertTrue((np.array(comp) == np.array(ref)).all())

    def test_gif_loop(self):
        g = Image.open(O / 'JungleG2_animation.gif')
        self.assertEqual(getattr(g, 'n_frames', 1), PHASES)
        self.assertEqual(g.info.get('duration'), MAN['animation']['frame_ms'])

    def test_ora_valid(self):
        import xml.etree.ElementTree as ET
        z = zipfile.ZipFile(O / 'JungleG2_5_calques.ora')
        self.assertEqual(z.read('mimetype').decode(), 'image/openraster')
        root = ET.fromstring(z.read('stack.xml'))
        self.assertEqual(len(root.findall('.//layer')), 5)

    def test_manifest_honest(self):
        self.assertEqual(MAN['methode'], 'generee_magenta')
        self.assertFalse(MAN['natif'])
        self.assertFalse(MAN['art_approved'])
        self.assertEqual(MAN['runtime'], 'NOT TESTED')


if __name__ == '__main__':
    unittest.main()
