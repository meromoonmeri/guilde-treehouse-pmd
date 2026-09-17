import unittest,json
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'exports/pokemon_custom/politoed_portraits_v3';OLD=ROOT/'exports/pokemon_custom/politoed_portraits_v1'
class PortraitTests(unittest.TestCase):
 def test_preferred_thirteen_byte_identical(self):
  for p in (OLD/'portraits_individual').glob('*.png'):
   if p.stem!='Dizzy':self.assertEqual(p.read_bytes(),(OUT/'portraits_individual'/p.name).read_bytes())
 def test_additions_opaque_palette_and_composite(self):
  for name in ['Dizzy','Special0']:
   im=Image.open(OUT/f'portraits_individual/{name}.png').convert('RGBA');self.assertEqual(im.size,(40,40));self.assertLessEqual(len(im.getcolors(999)),15)
   self.assertTrue(np.all(np.array(im)[:,:,3]==255));bg=Image.open(OUT/f'editable/{name}_canonical_background.png').convert('RGBA');fg=Image.open(OUT/f'editable/{name}_subject.png');bg.alpha_composite(fg);self.assertEqual(bg.tobytes(),im.tobytes())
 def test_explicit_special_background(self):
  expected=Image.open(ROOT/'Extra_Backgrounds.png').convert('RGBA').crop((40,0,80,40));got=Image.open(OUT/'editable/Special0_canonical_background.png');self.assertEqual(expected.tobytes(),got.tobytes())
 def test_not_silently_filled_with_disliked_v2(self):
  r=json.loads((OUT/'verification.json').read_text());self.assertEqual(r['missing_required'],['Sigh','Stunned']);self.assertFalse(r['art_approval_of_additions'])
if __name__=='__main__':unittest.main()
