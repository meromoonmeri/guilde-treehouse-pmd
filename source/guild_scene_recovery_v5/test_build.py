import unittest,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/guild_scene_recovery_v5';REF=ROOT/'source/guild_members_audit/references'
sys.path.insert(0,str(ROOT/'source/pmd_character_pipeline'))
from validate import run
ACTIONS=[('gardevoir','Eat',32,40),('gardevoir','Nod',32,40),('shroomish','Eat',32,32)]
class RecoveryTests(unittest.TestCase):
 def test_geometry(self):
  for who,action,w,h in ACTIONS:
   for k in ['Anim','Offsets','Shadow']:
    with Image.open(OUT/(who+'_candidate')/f'{action}-{k}.png') as im:self.assertEqual(im.size,(w*16,h*8))
 def test_closed_cycles_and_real_drawings(self):
  for who,action,w,h in ACTIONS:
   a=Image.open(OUT/(who+'_candidate')/f'{action}-Anim.png').convert('RGBA')
   for d in range(8):
    frames=[a.crop((f*w,d*h,(f+1)*w,(d+1)*h)).tobytes() for f in range(16)];self.assertEqual(frames[0],frames[-1]);self.assertGreaterEqual(len(set(frames)),3)
 def test_all_eight_rest_views_native(self):
  for who,action,w,h in ACTIONS:
   slot='0282' if who=='gardevoir' else '0285';nw,nh=(32,40) if who=='gardevoir' else (24,24);base=Image.open(REF/slot/'sprite/Idle-Anim.png').convert('RGBA');sheet=Image.open(OUT/(who+'_candidate')/f'{action}-Anim.png').convert('RGBA')
   for d in range(8):
    expected=Image.new('RGBA',(w,h));expected.alpha_composite(base.crop((0,d*nh,nw,(d+1)*nh)),(0,0) if who=='gardevoir' else (4,4));self.assertEqual(expected.tobytes(),sheet.crop((0,d*h,w,(d+1)*h)).tobytes())
 def test_native_pngs_preserved(self):
  for who,slot in [('gardevoir','0282'),('shroomish','0285')]:
   for p in (REF/slot/'sprite').glob('*.png'):self.assertEqual(p.read_bytes(),(OUT/(who+'_candidate')/p.name).read_bytes())
 def test_native_xml_semantics_preserved(self):
  def fp(n):return [(e.tag,(e.text or '').strip()) for e in n.iter()]
  for who,slot in [('gardevoir','0282'),('shroomish','0285')]:
   exported={n.findtext('Name'):n for n in ET.parse(OUT/(who+'_candidate')/'AnimData.xml').findall('./Anims/Anim')}
   for n in ET.parse(REF/slot/'sprite/AnimData.xml').findall('./Anims/Anim'):self.assertEqual(fp(n),fp(exported[n.findtext('Name')]))
 def test_strict_dungeon_prechecks(self):
  for who in ['gardevoir','shroomish']:self.assertEqual(run('sprite',OUT/(who+'_candidate'),'dungeon')['errors'],[])
 def test_identical_frames_equivalent_markers(self):
  for who,action,w,h in ACTIONS:
   pack=OUT/(who+'_candidate');sheets=[Image.open(pack/f'{action}-{k}.png').convert('RGBA') for k in ['Anim','Offsets','Shadow']];seen={}
   for d in range(8):
    for f in range(16):
     box=(f*w,d*h,(f+1)*w,(d+1)*h);art,off,shadow=[s.crop(box).tobytes() for s in sheets]
     if art in seen:self.assertEqual(seen[art],(off,shadow))
     seen[art]=(off,shadow)
 def test_feet_and_shadows_fixed(self):
  for who,action,w,h in ACTIONS:
   pack=OUT/(who+'_candidate');a=np.array(Image.open(pack/f'{action}-Anim.png').convert('RGBA'));s=np.array(Image.open(pack/f'{action}-Shadow.png').convert('RGBA'));lower=24 if who=='gardevoir' else 19
   for d in range(8):
    for f in range(16):
     self.assertTrue(np.array_equal(a[d*h+lower:(d+1)*h,:w],a[d*h+lower:(d+1)*h,f*w:(f+1)*w]));self.assertTrue(np.array_equal(s[d*h:(d+1)*h,:w],s[d*h:(d+1)*h,f*w:(f+1)*w]))
 def test_rear_head_occludes_hand(self):
  native=Image.open(REF/'0282/sprite/Idle-Anim.png').convert('RGBA');a=np.array(Image.open(OUT/'gardevoir_candidate/Eat-Anim.png').convert('RGBA'))
  for d in [3,4,5]:
   b=np.array(native.crop((0,d*40,32,d*40+14)));visible=b[:,:,3]>0
   for f in range(16):self.assertTrue(np.array_equal(a[d*40:d*40+14,f*32:(f+1)*32][visible],b[visible]))
 def test_no_food_colors(self):
  for who in ['gardevoir','shroomish']:
   a=np.array(Image.open(OUT/(who+'_candidate')/'Eat-Anim.png').convert('RGBA'))
   for c in [(232,135,40,255),(255,192,79,255)]:self.assertFalse(np.any(np.all(a==c,axis=2)))
 def test_27_animated_cycle_previews(self):
  gifs=list((OUT/'review').glob('*.gif'));self.assertEqual(len(gifs),27)
  for p in gifs:
   with Image.open(p) as im:self.assertGreaterEqual(im.n_frames,3);self.assertEqual(im.info.get('loop'),0)
 def test_three_real_halcyon_examples(self):
  r=json.loads((OUT/'halcyon_review/inspection.json').read_text());self.assertEqual(len(r['examples']),3)
  for ex in r['examples']:
   self.assertEqual(ex['engine_action'],48);self.assertEqual(len(ex['first_sequence']),4)
   with Image.open(OUT/'halcyon_review'/ex['gif']) as im:self.assertGreaterEqual(im.n_frames,2)
 def test_no_false_completion_or_runtime_claim(self):
  r=json.loads((OUT/'verification.json').read_text());self.assertFalse(r['food_in_sprite']);self.assertFalse(r['art_approved']);self.assertEqual(r['runtime_PMDO'],'NOT TESTED');self.assertEqual(len(r['actions']),3)
if __name__=='__main__':unittest.main()
