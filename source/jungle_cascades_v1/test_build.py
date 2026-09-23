"""Controles Jungle V1 : provenance native exacte, boucle animation, recomposition."""
import json
import unittest
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'exports' / 'jungle_cascades_v1'
W, H = 512, 640
MAN = json.loads((O / 'manifest.json').read_text(encoding='utf-8'))
SRC = [np.array(Image.open(R / s['file']).convert('RGBA')) for s in MAN['sources']]
LAYERS = ['01_sol', '02_paroi', '03_cascades', '04_bassins', '05_vegetation']
PHASES = MAN['animation']['phases']
STEP = MAN['animation']['step_px']
DST_FALLS = [(42, 86), (121, 135), (171, 227), (285, 341), (377, 391), (426, 470)]
SRC_FALLS = [(74, 118), (153, 167), (203, 259), (485, 541), (577, 591), (626, 670)]
FALL_H = 416


class T(unittest.TestCase):
    def test_layers_size_mode(self):
        for n in LAYERS:
            im = Image.open(O / f'JungleV1_{n}.png')
            self.assertEqual(im.size, (W, H))
            self.assertEqual(im.mode, 'RGBA')
            self.assertGreater(np.array(im)[:, :, 3].sum(), 0, n)

    def test_provenance_exact_rgb(self):
        for n in LAYERS:
            rgba = np.array(Image.open(O / f'JungleV1_{n}.png'))
            q = np.load(O / f'{n}_source.npz')['source_sxy']
            m = rgba[:, :, 3] > 0
            self.assertTrue((q[m] >= 0).all(), n)
            s, sx, sy = q[m][:, 0], q[m][:, 1], q[m][:, 2]
            for si in (0, 1):
                k = s == si
                if k.any():
                    self.assertTrue((rgba[m][k] == SRC[si][sy[k], sx[k]]).all(), (n, si))

    def test_no_mirror_rotation_scale(self):
        # mape localement rigide : pas de longues series de pas -1 (miroir), coutures bornees
        q = np.load(O / '01_sol_source.npz')['source_sxy']
        m = q[:, :, 0] == 0
        dx = np.diff(q[:, :, 1].astype(int), axis=1)
        ok = m[:, :-1] & m[:, 1:]
        neg = (dx == -1) & ok
        worst = 0
        for row in neg:
            run = 0
            for v in row:
                run = run + 1 if v else 0
                worst = max(worst, run)
        self.assertLessEqual(worst, 4)
        self.assertLess((np.abs(dx[ok]) > 1).mean(), 0.12)

    def test_falls_cut_at_top_source_hidden(self):
        rgba = np.array(Image.open(O / 'JungleV1_03_cascades.png'))
        top = rgba[0, :, 3] > 0
        self.assertGreater(top.sum(), 100)
        for x0, x1 in DST_FALLS:
            self.assertTrue(top[x0:x1].all(), (x0, x1))

    def test_falls_texture_96_periodic(self):
        for x0, x1 in SRC_FALLS:
            c = SRC[0][0:FALL_H, x0:x1].astype(int)
            self.assertTrue((c[:FALL_H - 96] == c[96:]).all(), (x0, x1))

    def test_falls_animation_loop_exact(self):
        self.assertEqual(PHASES * STEP, FALL_H)  # boucle = hauteur complete
        offs = MAN['animation']['offsets']
        prev = None
        for p in range(PHASES):
            cur = np.array(Image.open(O / f'cascades_phases/JungleV1_03_cascades_phase_{p:02d}.png'))
            for (x0, x1), (sx0, sx1), off in zip(DST_FALLS, SRC_FALLS, offs):
                expect = np.roll(SRC[0][0:FALL_H, sx0:sx1], off + p * STEP, axis=0)
                self.assertTrue((cur[0:FALL_H, x0:x1] == expect).all(), (p, x0, x1))
            if prev is not None:
                self.assertFalse((prev == cur).all(), p)
            prev = cur
        # phase PHASES == phase 0 : roulement de 416px = identite
        p0 = np.array(Image.open(O / 'cascades_phases/JungleV1_03_cascades_phase_00.png'))
        for (x0, x1), (sx0, sx1), off in zip(DST_FALLS, SRC_FALLS, offs):
            expect = np.roll(SRC[0][0:FALL_H, sx0:sx1], off + PHASES * STEP, axis=0)
            self.assertTrue((expect == p0[0:FALL_H, x0:x1]).all(), (x0, x1))

    def test_falls_phases_provenance(self):
        for p in (0, PHASES // 2, PHASES - 1):
            rgba = np.array(Image.open(O / f'cascades_phases/JungleV1_03_cascades_phase_{p:02d}.png'))
            q = np.load(O / f'cascades_phases/phase_{p:02d}_source.npz')['source_sxy']
            m = rgba[:, :, 3] > 0
            self.assertTrue((rgba[m] == SRC[0][q[m][:, 2], q[m][:, 1]]).all(), p)

    def test_feet_surrounded_by_foam(self):
        bas = np.array(Image.open(O / 'JungleV1_04_bassins.png'))
        opaque = bas[:, :, 3] > 0
        bright = opaque & (bas[:, :, :3].astype(int).sum(2) > 450)
        for x0, x1 in DST_FALLS:
            near = np.zeros((H, W), bool)
            near[392:416, max(0, x0 - 10):x0] = True
            near[392:416, x1:min(W, x1 + 10)] = True
            self.assertGreater(bright[near].mean(), 0.25, (x0, x1))  # ecume claire autour des pieds

    def test_path_continuous_south_to_basins(self):
        sol = np.array(Image.open(O / 'JungleV1_01_sol.png'))[:, :, :3].astype(int)
        light = (sol[:, :, 1] > 140) & (sol[:, :, 1] > sol[:, :, 0] + 5)
        for y in range(505, 640, 5):
            self.assertGreater(light[y, 200:320].sum(), 20, y)  # chemin clair continu, pixels uniquement

    def test_recomposition_exact(self):
        comp = Image.new('RGBA', (W, H))
        for n in LAYERS:
            comp.alpha_composite(Image.open(O / f'JungleV1_{n}.png'))
        ref = Image.open(O / 'JungleV1_composite_phase_00.png')
        self.assertTrue((np.array(comp) == np.array(ref)).all())

    def test_gif_loop(self):
        g = Image.open(O / 'JungleV1_animation.gif')
        self.assertEqual(getattr(g, 'n_frames', 1), PHASES)
        self.assertEqual(g.info.get('duration'), MAN['animation']['frame_ms'])

    def test_ora_valid(self):
        import xml.etree.ElementTree as ET
        z = zipfile.ZipFile(O / 'JungleV1_5_calques.ora')
        self.assertEqual(z.read('mimetype').decode(), 'image/openraster')
        root = ET.fromstring(z.read('stack.xml'))
        layers = root.findall('.//layer')
        self.assertEqual(len(layers), 5)
        for i, n in enumerate(LAYERS):
            self.assertEqual(layers[i].attrib['src'], f'data/{i}.png')
            self.assertIn(f'data/{i}.png', z.namelist())

    def test_manifest_coherent(self):
        self.assertEqual([l['id'] for l in MAN['layers']], LAYERS)
        self.assertEqual(MAN['animation']['loop_ms'], PHASES * MAN['animation']['frame_ms'])
        self.assertFalse(MAN['art_approved'])
        self.assertEqual(MAN['runtime'], 'NOT TESTED')


if __name__ == '__main__':
    unittest.main()
