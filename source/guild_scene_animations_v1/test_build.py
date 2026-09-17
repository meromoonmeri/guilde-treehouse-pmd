import unittest,json,xml.etree.ElementTree as ET,sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];REF=ROOT/'source/guild_members_audit/references';OUT=ROOT/'exports/guild_scene_animations_v1'
sys.path.insert(0,str(ROOT/'source/pmd_character_pipeline'))
from validate import run

class SceneTests(unittest.TestCase):
 def test_strict_dungeon(self):
  for name in ['gardevoir_candidate','weavile_canonical']:
   r=run('sprite',OUT/name,'dungeon');self.assertEqual(r['errors'],[])
 def test_all_native_base_pngs_immutable(self):
  for slot,pack in [('0282','gardevoir_candidate'),('0461','weavile_canonical')]:
   for p in (REF/slot/'sprite').glob('*.png'):self.assertEqual(p.read_bytes(),(OUT/pack/p.name).read_bytes())
 def test_base_xml_actions_unchanged(self):
  def fingerprint(n):return [(x.tag,(x.text or '').strip()) for x in n.iter()]
  for slot,pack in [('0282','gardevoir_candidate'),('0461','weavile_canonical')]:
   exported={n.findtext('Name'):n for n in ET.parse(OUT/pack/'AnimData.xml').findall('./Anims/Anim')}
   for n in ET.parse(REF/slot/'sprite/AnimData.xml').findall('./Anims/Anim'):self.assertEqual(fingerprint(n),fingerprint(exported[n.findtext('Name')]))
 def test_special1_uses_cutscene_not_base_appeal(self):
  for k in ['Anim','Offsets','Shadow']:
   got=(OUT/f'gardevoir_candidate/Special1-{k}.png').read_bytes()
   self.assertEqual(got,(REF/f'0282/0002/sprite/Appeal-{k}.png').read_bytes())
   self.assertNotEqual(got,(REF/f'0282/sprite/Appeal-{k}.png').read_bytes())
 def test_nod_static_body_and_markers(self):
  im=np.array(Image.open(OUT/'gardevoir_candidate/Nod-Anim.png').convert('RGBA'));native=np.array(Image.open(REF/'0282/sprite/Idle-Anim.png').convert('RGBA'))[:40,:32]
  self.assertEqual(im.shape,(40,160,4))
  for j in range(5):self.assertTrue(np.array_equal(im[14:,j*32:(j+1)*32],native[14:]))
  self.assertEqual(len({im[:,j*32:(j+1)*32].tobytes() for j in range(5)}),3)
  for kind in ['Offsets','Shadow']:
   a=np.array(Image.open(OUT/f'gardevoir_candidate/Nod-{kind}.png'))
   for j in range(1,5):self.assertTrue(np.array_equal(a[:,:32],a[:,j*32:(j+1)*32]))
 def test_no_false_runtime_or_full_coverage(self):
  r=json.loads((OUT/'verification.json').read_text());self.assertEqual(r['PMDO_runtime'],'NOT TESTED');self.assertFalse(r['art_approved']);self.assertEqual(r['additions']['Nod']['remaining_directions'],7)

if __name__=='__main__':unittest.main()
