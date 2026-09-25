"""Tests V17 : provenance native exacte, boucles d'animation, chemins, formats."""
import json
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image

R = Path(__file__).resolve().parents[2]
O = R / 'renders/glace_aurore_canonique_v1'
MAN = json.loads((O / 'manifest.json').read_text())
A = {i: np.array(Image.open(R / s['file']).convert('RGBA'))
     for i, s in [(x['id'], x) for x in MAN['sources']]}

LAYERS = {
    'bg_aurore': ('GLACE_V17_bg_aurore_01_ciel_nuages.png', 'GLACE_V17_bg_aurore_02_etoiles.png',
                  'GLACE_V17_bg_aurore_04_frise_glace.png'),
    'arene_glace': ('GLACE_V17_arene_glace_01_sol_neige.png', 'GLACE_V17_arene_glace_02_mur_nord.png',
                    'GLACE_V17_arene_glace_03_blocs_cotes.png', 'GLACE_V17_arene_glace_04_crete_sud.png',
                    'GLACE_V17_arene_glace_05_fissures.png'),
    'route_glacee': ('GLACE_V17_route_glacee_01_fond_montagnes.png', 'GLACE_V17_route_glacee_02_lac_gele.png',
                     'GLACE_V17_route_glacee_03_parois_nord.png', 'GLACE_V17_route_glacee_04_blocs_sud.png',
                     'GLACE_V17_route_glacee_05_fissures.png'),
}
NPZ = {'bg_aurore': ('01_ciel_nuages', '02_etoiles', '04_frise_glace'),
       'arene_glace': ('01_sol_neige', '02_mur_nord', '03_blocs_cotes', '04_crete_sud', '05_fissures'),
       'route_glacee': ('01_fond_montagnes', '02_lac_gele', '03_parois_nord', '04_blocs_sud', '05_fissures')}


class T(unittest.TestCase):
    def test_dims_mult8(self):
        for p in O.rglob('*.png'):
            w, h = Image.open(p).size
            self.assertEqual(w % 8, 0, p)
            self.assertEqual(h % 8, 0, p)

    def test_sources_unchanged(self):
        import hashlib
        for s in MAN['sources']:
            self.assertEqual(hashlib.sha256((R / s['file']).read_bytes()).hexdigest(), s['sha256'])

    def test_provenance_exact(self):
        for mid, names in LAYERS.items():
            for fn, nz in zip(names, NPZ[mid]):
                a = np.array(Image.open(O / mid / fn))
                q = np.load(O / mid / (nz + '_source.npz'))['source_sxy']
                op = a[:, :, 3] > 0
                self.assertTrue(op.any(), (mid, fn))
                self.assertTrue((q[op][:, 0] >= 0).all(), (mid, fn))
                for s in (0, 1, 2):
                    sel = op & (q[:, :, 0] == s)
                    if sel.any():
                        ys, xs = np.nonzero(sel)
                        self.assertTrue((a[sel] == A[s][q[sel][:, 2], q[sel][:, 1]]).all(),
                                        (mid, fn, 'source', s))
                sans = op & (q[:, :, 0] < 0)
                self.assertFalse(sans.any(), (mid, fn))

    def test_tsx(self):
        for mid, names in LAYERS.items():
            for fn in names:
                t = O / mid / (Path(fn).stem + '.tsx')
                root = ET.parse(t).getroot()
                im = root.find('image')
                w, h = Image.open(O / mid / fn).size
                self.assertEqual(int(im.get('width')), w)
                self.assertEqual(int(im.get('height')), h)
                self.assertEqual(root.get('tilewidth'), '8')

    def test_aurore_loop_exact(self):
        import sys
        sys.path.insert(0, str(R / 'source' / 'glace_aurore_canonique_v1'))
        sys.path.insert(0, str(R))
        from source.glace_aurore_canonique_v1.build import onde_frame, extraire_rubans
        effet, _ = extraire_rubans()
        f0 = np.array(onde_frame(effet, 0))
        f10 = np.array(onde_frame(effet, 10))
        self.assertTrue((f0 == f10).all())
        saved = np.array(Image.open(O / 'bg_aurore' / 'GLACE_V17_bg_aurore_03_aurore_f00.png'))
        self.assertTrue((saved == f0).all())

    def test_aurore_frames_distinct(self):
        fr = [np.array(Image.open(O / 'bg_aurore' / f'GLACE_V17_bg_aurore_03_aurore_f{t:02d}.png'))
              for t in range(10)]
        n = sum(not np.array_equal(fr[i], fr[j]) for i in range(10) for j in range(i + 1, 10))
        self.assertEqual(n, 45)

    def test_onde_vertical_only(self):
        import sys
        sys.path.insert(0, str(R / 'source' / 'glace_aurore_canonique_v1'))
        sys.path.insert(0, str(R))
        from source.glace_aurore_canonique_v1.build import onde_frame, extraire_rubans, decalage, enveloppe
        effet, _ = extraire_rubans()
        base = np.array(effet)
        H, W = base.shape[:2]
        for t in (1, 4, 7):
            fr = np.array(onde_frame(effet, t))
            for x in range(0, W, 7):
                d = int(round(float(decalage(x, t, W)) * float(enveloppe(x, W))))
                col, ref = fr[:, x, :], base[:, x, :]
                if d > 0:
                    self.assertTrue((col[d:] == ref[:H - d]).all(), (t, x))
                    self.assertTrue((col[:d] == 0).all(), (t, x))
                elif d < 0:
                    self.assertTrue((col[:H + d] == ref[-d:]).all(), (t, x))
                    self.assertTrue((col[H + d:] == 0).all(), (t, x))
                else:
                    self.assertTrue((col == ref).all(), (t, x))

    def test_stars_twinkle_alpha_only(self):
        d = O / 'bg_aurore'
        base = np.array(Image.open(d / 'GLACE_V17_bg_aurore_02_etoiles.png'))
        for f in range(4):
            g = np.array(Image.open(d / f'GLACE_V17_bg_aurore_02_etoiles_tw{f}.png'))
            self.assertTrue((g[:, :, :3] == base[:, :, :3]).all(), f)
            self.assertTrue(set(np.unique(g[:, :, 3])) <= {0, 176, 216, 255}, f)
        # au moins un pixel module entre tw0 et tw2
        g0 = np.array(Image.open(d / 'GLACE_V17_bg_aurore_02_etoiles_tw0.png'))
        g2 = np.array(Image.open(d / 'GLACE_V17_bg_aurore_02_etoiles_tw2.png'))
        self.assertTrue(((g0[:, :, 3] > 0) & (g0[:, :, 3] != g2[:, :, 3])).any())

    def test_reflets_loop_and_scale(self):
        for mid, W, H in (('arene_glace', 504, 408), ('route_glacee', 504, 360)):
            d = O / mid
            fr = [np.array(Image.open(d / f'GLACE_V17_{mid}_06_reflets_f{f}.png')) for f in range(4)]
            m0 = fr[0][:, :, 3] > 0
            self.assertTrue(m0.any(), mid)
            for f in range(1, 4):
                self.assertTrue(((fr[f][:, :, 3] > 0) == m0).all(), (mid, f))
            # pulse documente A-B-A-C : f0==f2 (neutre), f1/f3 groupes inverses
            self.assertTrue(np.array_equal(fr[0], fr[2]), mid)
            self.assertFalse(np.array_equal(fr[1], fr[3]), mid)
            self.assertFalse(np.array_equal(fr[0], fr[1]), mid)

    def test_paths_clear(self):
        crete = np.array(Image.open(O / 'arene_glace' / 'GLACE_V17_arene_glace_04_crete_sud.png'))
        yy, xx = np.mgrid[:408, :504]
        path = (xx >= 232) & (xx < 304) & (yy >= 200)
        self.assertEqual(int(((crete[:, :, 3] > 0) & path).sum()), 0)
        blocs = np.array(Image.open(O / 'route_glacee' / 'GLACE_V17_route_glacee_04_blocs_sud.png'))
        parois = np.array(Image.open(O / 'route_glacee' / 'GLACE_V17_route_glacee_03_parois_nord.png'))
        yy, xx = np.mgrid[:360, :504]
        path = (xx >= 224) & (xx < 280) & (yy >= 140)
        bloq = ((blocs[:, :, 3] > 0) | (parois[:, :, 3] > 0)) & path
        self.assertEqual(int(bloq.sum()), 0)

    def test_ciel_identity_outside_holes(self):
        ciel = np.array(Image.open(O / 'bg_aurore' / 'GLACE_V17_bg_aurore_01_ciel_nuages.png'))
        q = np.load(O / 'bg_aurore' / '01_ciel_nuages_source.npz')['source_sxy']
        yy, xx = np.mgrid[:216, :264]
        ident = (q[:, :, 0] == 0) & (q[:, :, 1] == xx) & (q[:, :, 2] == yy)
        self.assertTrue(ident.any())
        self.assertTrue((ciel[ident] == A[0][ident]).all())

    def test_viewer_complete(self):
        h = (R / 'apercu_glace_aurore_canonique_v1.html').read_text()
        self.assertNotIn('__DATA__', h)
        for key in ('01_sol_neige', '03_parois_nord', '03_aurore', '06_reflets', 'Grille 8px'):
            self.assertIn(key, h)

    def test_manifest_files_present(self):
        for mid, names in LAYERS.items():
            for fn in names:
                self.assertTrue((O / mid / fn).exists(), fn)
        for t in range(10):
            self.assertTrue((O / 'bg_aurore' / f'GLACE_V17_bg_aurore_03_aurore_f{t:02d}.png').exists())


if __name__ == '__main__':
    unittest.main()
