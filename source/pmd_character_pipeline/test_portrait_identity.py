import unittest
from pathlib import Path
import numpy as np
from PIL import Image
from source.pmd_character_pipeline.make_prompt import make
from source.pokemon_custom.next_species.portrait_identity import constrained_expression, PROFILES, SRC


class PromptIdentityTests(unittest.TestCase):
    def setUp(self):
        self.brief = {'species':'Mega Raichu X', 'references':['normal.png'],
                      'normal_portrait_reference':'normal.png', 'spritecollab_slot':'0026/0002'}

    def test_anatomy_rule_in_prompt(self):
        text = make(self.brief, 'portrait', 'Happy')
        self.assertIn('FIXED anatomical master', text)
        self.assertIn('do not invent a new face angle or head tilt', text)

    def test_missing_normal_rejected(self):
        self.brief.pop('normal_portrait_reference')
        with self.assertRaises(ValueError):
            make(self.brief, 'portrait', 'Happy')

    def test_normal_must_be_among_supplied_references(self):
        self.brief['normal_portrait_reference'] = 'other.png'
        with self.assertRaises(ValueError):
            make(self.brief, 'portrait', 'Happy')

    def test_stellar_portraits_blocked(self):
        self.brief['spritecollab_slot'] = '1024/0002'
        with self.assertRaises(ValueError):
            make(self.brief, 'portrait', 'Happy')

    def test_immutable_pixels_and_native_palette(self):
        for name, profile in PROFILES.items():
            with self.subTest(name=name):
                normal = Image.open(SRC/'references'/name/'Normal.png').convert('RGBA')
                result, mask = constrained_expression(normal, Image.new('RGB',(40,40),'red'), profile)
                a,b = np.array(normal),np.array(result)
                self.assertTrue(np.array_equal(a[~mask],b[~mask]))
                self.assertTrue(np.array_equal(a[:,:,3],b[:,:,3]))
                self.assertTrue(set(result.getdata()).issubset(set(normal.getdata())))
                for x1,y1,x2,y2 in profile['protected']:
                    self.assertTrue(np.array_equal(a[y1:y2,x1:x2],b[y1:y2,x1:x2]))


if __name__=='__main__':
    unittest.main()
