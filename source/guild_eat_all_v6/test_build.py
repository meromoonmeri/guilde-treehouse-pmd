import unittest,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/guild_eat_all_v6';REF=ROOT/'source/guild_members_audit/references'
sys.path.insert(0,str(ROOT))
from source.guild_eat_all_v6.build import MEMBERS,NEW,FOOT_START,read_action
sys.path.insert(0,str(ROOT/'source/pmd_character_pipeline'))
from validate import run
class GuildEatTests(unittest.TestCase):
 def test_all_nine_have_valid_full_base_packs(self):
  self.assertEqual(len(MEMBERS),9)
  for slot,_ in MEMBERS:self.assertEqual(run('sprite',OUT/'characters'/slot,'dungeon')['errors'],[])
 def test_every_native_png_preserved(self):
  for slot,_ in MEMBERS:
   for p in (REF/slot/'sprite').glob('*.png'):self.assertEqual(p.read_bytes(),(OUT/'characters'/slot/p.name).read_bytes())
 def test_native_three_xml_and_eat_bytes_unchanged(self):
  for slot in ['0371','0440','0417']:
   for name in ['AnimData.xml','Eat-Anim.png','Eat-Offsets.png','Eat-Shadow.png']:
    self.assertEqual((REF/slot/'sprite'/name).read_bytes(),(OUT/'characters'/slot/name).read_bytes())
   rows,ticks=read_action(OUT/'characters'/slot);self.assertEqual(len(rows),1);self.assertEqual(ticks,[6,8,6,8])
 def test_retained_v5_eat_unchanged(self):
  for slot,name in [('0282','gardevoir_candidate'),('0285','shroomish_candidate')]:
   for kind in ['Anim','Offsets','Shadow']:self.assertEqual((ROOT/'exports/guild_scene_recovery_v5'/name/f'Eat-{kind}.png').read_bytes(),(OUT/'characters'/slot/f'Eat-{kind}.png').read_bytes())
 def test_native_xml_actions_still_identical(self):
  def fp(n):return [(x.tag,(x.text or '').strip()) for x in n.iter()]
  for slot,_ in MEMBERS:
   exported={n.findtext('Name'):n for n in ET.parse(OUT/'characters'/slot/'AnimData.xml').findall('./Anims/Anim')}
   for n in ET.parse(REF/slot/'sprite/AnimData.xml').findall('./Anims/Anim'):self.assertEqual(fp(n),fp(exported[n.findtext('Name')]))
 def test_new_cycles_eight_views_closed_and_nonstatic(self):
  for slot in NEW:
   rows,ticks=read_action(OUT/'characters'/slot);self.assertEqual(len(rows),8);self.assertEqual(len(ticks),16)
   for row in rows:
    self.assertEqual(row[0][0].tobytes(),row[-1][0].tobytes());self.assertGreaterEqual(len({t[0].tobytes() for t in row}),3)
 def test_identical_art_has_identical_offsets(self):
  for slot in NEW:
   rows,_=read_action(OUT/'characters'/slot);seen={}
   for row in rows:
    for art,off,shadow in row:
     key=(art.tobytes(),shadow.tobytes())
     if key in seen:self.assertEqual(off.tobytes(),seen[key])
     seen[key]=off.tobytes()
 def test_accessories_and_antenna_preserved(self):
  for slot in ['0083','0674','0186']:
   rows,_=read_action(OUT/'characters'/slot)
   for d,row in enumerate(rows):
    direction=['D','DR','R','UR','U','UL','L','DL'][d];mask=np.array(Image.open(OUT/'masks'/f'{slot}_{direction}_protected.png'))>0;a=np.array(row[0][0])
    self.assertEqual(bool(mask.any()),not (slot=='0674' and direction in ['U','UL'])) # leaf occluded in these native views
    for art,_,_ in row:self.assertTrue(np.array_equal(np.array(art)[mask],a[mask]))
 def test_planted_feet_and_shadows(self):
  for slot in NEW:
   rows,_=read_action(OUT/'characters'/slot)
   for row in rows:
    start=FOOT_START.get(slot,23);native=np.array(row[0][0])
    for art,_,shadow in row:
     self.assertTrue(np.array_equal(np.array(art)[start:],native[start:]));self.assertEqual(shadow.tobytes(),row[0][2].tobytes())
 def test_new_palettes_stay_native(self):
  for slot in NEW:
   original=np.array(Image.open(REF/slot/'sprite/Idle-Anim.png').convert('RGBA'));palette=set(map(tuple,original[original[:,:,3]>0,:3]))
   new=np.array(Image.open(OUT/'characters'/slot/'Eat-Anim.png').convert('RGBA'));self.assertTrue(set(map(tuple,new[new[:,:,3]>0,:3])).issubset(palette))
 def test_57_real_gifs_and_honest_status(self):
  gifs=list((OUT/'review').glob('*.gif'));self.assertEqual(len(gifs),57)
  for path in gifs:
   with Image.open(path) as im:self.assertGreaterEqual(im.n_frames,3);self.assertEqual(im.info.get('loop'),0)
  r=json.loads((OUT/'verification.json').read_text());self.assertEqual(r['coverage']['members_with_Eat'],9);self.assertEqual(r['coverage']['native_single_view_cycles'],3);self.assertFalse(r['food_in_sprite']);self.assertEqual(r['runtime_PMDO'],'NOT TESTED');self.assertFalse(r['new_art_approved'])
if __name__=='__main__':unittest.main()
