import unittest,json,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/guild_scene_animations_v2';PACK=OUT/'gardevoir_eat_candidate'
sys.path.insert(0,str(ROOT/'source/pmd_character_pipeline'))
from validate import run
class EatTests(unittest.TestCase):
 def test_strict_precheck(self):self.assertEqual(run('sprite',PACK,'dungeon')['errors'],[])
 def test_inherited_pngs_unchanged(self):
  for p in (ROOT/'exports/guild_scene_animations_v1/gardevoir_candidate').glob('*.png'):self.assertEqual(p.read_bytes(),(PACK/p.name).read_bytes())
 def test_real_moving_hand_markers(self):
  r=json.loads((OUT/'verification.json').read_text());im=np.array(Image.open(PACK/'Eat-Anim.png').convert('RGBA'));offset=np.array(Image.open(PACK/'Eat-Offsets.png').convert('RGBA'))
  self.assertGreater(len(set(map(tuple,r['active_hand_offsets']))),4)
  for i,(x,y) in enumerate(r['active_hand_offsets']):
   self.assertEqual(im[y,i*32+x,3],255);self.assertEqual(offset[y,i*32+x].tolist(),[255,0,0,255])
 def test_final_rest_and_static_ground(self):
  native=np.array(Image.open(ROOT/'source/guild_members_audit/references/0282/sprite/Idle-Anim.png').convert('RGBA'))[:40,:32]
  im=np.array(Image.open(PACK/'Eat-Anim.png').convert('RGBA'));self.assertTrue(np.array_equal(im[:,224:256],native))
  for j in range(8):self.assertTrue(np.array_equal(im[24:,j*32:(j+1)*32],native[24:]))
  s=np.array(Image.open(PACK/'Eat-Shadow.png').convert('RGBA'))
  for j in range(1,8):self.assertTrue(np.array_equal(s[:,:32],s[:,j*32:(j+1)*32]))
 def test_truthful_scope(self):
  r=json.loads((OUT/'verification.json').read_text());self.assertEqual(r['remaining_directions'],7);self.assertFalse(r['art_approved']);self.assertEqual(r['runtime_PMDO'],'NOT TESTED')
if __name__=='__main__':unittest.main()
