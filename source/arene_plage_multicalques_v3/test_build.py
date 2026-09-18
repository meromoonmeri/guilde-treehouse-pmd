import unittest, json, hashlib, zipfile, io
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RENDER_DIR = ROOT / 'renders/arene_plage_multicalques_v3'
CALQUES_DIR = RENDER_DIR / 'calques'
MASQUES_DIR = RENDER_DIR / 'masques'
ANIM_DIR = RENDER_DIR / 'animation'
REVIEW_DIR = RENDER_DIR / 'review'

class BeachArenaMulticalquesV3Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads((RENDER_DIR / 'manifest.json').read_text())
        cls.w, cls.h = cls.manifest['dimensions']
        cls.terrain_ta = Image.open(REVIEW_DIR / 'terrain_detoure.png').convert('RGBA')

    def test_dimensions_and_grid_8px(self):
        self.assertEqual(self.w, 648)
        self.assertEqual(self.h, 504)
        self.assertEqual(self.w % 8, 0, "Largeur doit être divisible par 8")
        self.assertEqual(self.h % 8, 0, "Hauteur doit être divisible par 8")

    def test_every_element_has_its_own_layer(self):
        layers = self.manifest['layers']
        self.assertEqual(len(layers), 14, "Doit comporter exactement 14 calques indépendants")
        layer_ids = [l['id'] for l in layers]
        expected_ids = [
            '00_ciel_pmd', '00b_etoiles', '01_nuages_wrap', '02_eau_mer_port',
            '03_ecume_rivage', '04_sol_sable_complet', '05_sol_sable_visible',
            '06_acces_sud', '07_falaises_rouges_arriere', '08_falaises_rouges_gauche',
            '09_falaises_rouges_droite', '10_rochers_arriere_plan', '11_rochers_avant_plan',
            '12_ombres_contact'
        ]
        self.assertEqual(layer_ids, expected_ids)

    def test_layer_files_exist_in_calques(self):
        for l in self.manifest['layers']:
            p_day = RENDER_DIR / l['file_day']
            p_night = RENDER_DIR / l['file_night']
            self.assertTrue(p_day.exists(), f"Fichier jour manquant: {p_day}")
            self.assertTrue(p_night.exists(), f"Fichier nuit manquant: {p_night}")
            with Image.open(p_day) as im_d:
                self.assertEqual(im_d.size, (self.w, self.h))
            with Image.open(p_night) as im_n:
                self.assertEqual(im_n.size, (self.w, self.h))

    def test_disjoint_partition_and_recomposition(self):
        partition_names = [
            '05_sol_sable_visible', '06_acces_sud', '07_falaises_rouges_arriere',
            '08_falaises_rouges_gauche', '09_falaises_rouges_droite',
            '10_rochers_arriere_plan', '11_rochers_avant_plan'
        ]
        masks = [np.array(Image.open(MASQUES_DIR / f'{name}.png')) > 0 for name in partition_names]
        total_sum = np.sum(masks, axis=0)
        valid = np.array(self.terrain_ta)[:, :, 3] > 0
        np.testing.assert_array_equal(total_sum, valid.astype(int),
            err_msg="La partition du terrain doit être strictement disjointe et couvrir 100% du terrain")

    def test_underlay_sand_floor_continuous(self):
        floor_im = Image.open(CALQUES_DIR / 'ArenePlageV3_04_sol_sable_complet_jour.png')
        self.assertEqual(floor_im.size, (self.w, self.h))
        floor_alpha = np.array(floor_im)[:, :, 3]
        valid = np.array(self.terrain_ta)[:, :, 3] > 0
        self.assertTrue(np.all(floor_alpha[valid] == 255),
            "Le sous-sol de sable doit couvrir 100% du terrain sans interstice")

    def test_shore_foam_layer_exists(self):
        foam_im = Image.open(CALQUES_DIR / 'ArenePlageV3_03_ecume_rivage_jour.png')
        self.assertEqual(foam_im.size, (self.w, self.h))
        foam_alpha = np.array(foam_im)[:, :, 3]
        self.assertGreater(np.sum(foam_alpha > 0), 1000, "Le calque d'écume doit contenir les pixels de ressac")

    def test_water_animation_frames_and_timing(self):
        self.assertEqual(self.manifest['timing']['frames'], 30)
        self.assertEqual(self.manifest['timing']['frame_ms'], 130)
        self.assertEqual(self.manifest['timing']['loop_ms'], 3900)
        water_frames = list((ANIM_DIR / 'frames').glob('ArenePlageV3_Eau_*_jour.png'))
        self.assertEqual(len(water_frames), 30)

    def test_composite_opacity_100_percent(self):
        comp_d = Image.open(REVIEW_DIR / 'COMPOSITION_JOUR.png')
        comp_n = Image.open(REVIEW_DIR / 'COMPOSITION_NUIT.png')
        self.assertEqual(comp_d.size, (self.w, self.h))
        self.assertEqual(comp_n.size, (self.w, self.h))
        self.assertTrue(np.all(np.array(comp_d)[:, :, 3] == 255), "Composition de jour doit être 100% opaque")
        self.assertTrue(np.all(np.array(comp_n)[:, :, 3] == 255), "Composition de nuit doit être 100% opaque")

    def test_webp_animation_exists(self):
        webp_p = ANIM_DIR / 'ANIMATION_WRAP.webp'
        self.assertTrue(webp_p.exists())
        with Image.open(webp_p) as im:
            self.assertEqual(im.size, (self.w, self.h))
            self.assertEqual(im.n_frames, 30)

    def test_ora_order_and_archive(self):
        ora_p = RENDER_DIR / 'arene_plage_editable.ora'
        self.assertTrue(ora_p.exists())
        with zipfile.ZipFile(ora_p) as z:
            self.assertEqual(z.read('mimetype'), b'image/openraster')
            root = ET.fromstring(z.read('stack.xml'))
            layers = root.find('stack').findall('layer')
            self.assertEqual(len(layers), 14, "L'ORA doit contenir les 14 calques")

    def test_readme_and_manifest(self):
        self.assertTrue((RENDER_DIR / 'README.md').exists())
        self.assertTrue((RENDER_DIR / 'manifest.json').exists())
        self.assertTrue((RENDER_DIR / 'placement_recipe.json').exists())
        self.assertTrue((RENDER_DIR / 'verification.json').exists())

if __name__ == '__main__':
    unittest.main()
