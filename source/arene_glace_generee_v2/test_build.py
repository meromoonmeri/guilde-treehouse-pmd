import unittest,json,hashlib,io,zipfile,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'renders/arene_glace_generee_v2';OLD=R/'exports/ice_arena_aurora_v1'
class GeneratedArenaTests(unittest.TestCase):
 def setUp(self):self.m=json.loads((O/'manifest.json').read_text())
 def test_workflow_and_sources(self):
  self.assertIn('NEW GENERATED DRAWING',self.m['terrain_origin']);self.assertEqual(len(self.m['terrain_inputs']),2);self.assertNotIn('terrain_operations',self.m)
  for s in self.m['terrain_inputs']:self.assertEqual(hashlib.sha256((R/s['file']).read_bytes()).hexdigest(),s['sha256'])
 def test_terrain_exactly_reassembles_the_generated_render(self):
  comp=Image.new('RGBA',(512,640))
  for l in self.m['layers']:comp.alpha_composite(Image.open(O/l['file']).convert('RGBA'))
  self.assertEqual(comp.tobytes(),Image.open(O/'review/terrain_detoure.png').convert('RGBA').tobytes())
 def test_partitions_are_disjoint_and_complete(self):
  masks=[np.array(Image.open(p))>0 for p in sorted((O/'masques').glob('*.png'))];count=np.sum(masks,axis=0);valid=np.array(Image.open(O/'review/terrain_detoure.png'))[:,:,3]>0;self.assertTrue(np.array_equal(count,valid.astype(int)))
 def test_grid_alpha_and_no_magenta(self):
  for l in self.m['layers']:
   a=np.array(Image.open(O/l['file']));self.assertEqual(a.shape,(640,512,4));self.assertTrue(set(np.unique(a[:,:,3])).issubset({0,255}));self.assertFalse(((a[:,:,0]>200)&(a[:,:,2]>200)&(a[:,:,1]<80)&(a[:,:,3]>0)).any())
 def test_generated_clean_floor_under_reliefs(self):
  a=np.array(Image.open(O/'calques/AreneGenV2_01_sol_complet_genere.png'));self.assertTrue((a[300:,20:100,3]>0).all());self.assertEqual(len(list((O/'bruts').glob('*.png'))),2)
 def test_animation_retained_byte_identical(self):
  for f in range(64):
   for typ,folder,label in [('aurores','aurora_frames','Ribbons'),('etoiles','star_frames','Stars')]:self.assertEqual((O/'animation'/typ/f'AreneGenV2_{typ}_{f:02}.png').read_bytes(),(OLD/folder/f'IceAuroraV1_{label}_{f:02}.png').read_bytes())
 def test_full_animated_preview(self):
  with Image.open(O/'review/animation.gif') as im:
   self.assertGreaterEqual(im.n_frames,48);self.assertEqual(im.info['loop'],0);duration=0
   for f in range(im.n_frames):im.seek(f);duration+=im.info['duration']
   self.assertEqual(duration,6400)
 def test_gif_delta_frames_preserve_the_full_scene(self):
  palette=Image.open(O/'review/scene_00.png').convert('RGB').quantize(colors=256)
  with Image.open(O/'review/animation.gif') as im:
   self.assertEqual(im.n_frames,64)
   for f in [0,16,32,48]:
    im.seek(f);expected=Image.open(O/'review'/f'scene_{f:02}.png').convert('RGB').quantize(palette=palette,dither=Image.Dither.NONE).convert('RGB');self.assertEqual(im.convert('RGB').tobytes(),expected.tobytes())
 def test_terrain_does_not_move(self):
  base=np.array(Image.open(O/'review/scene_00.png'))
  for f in [16,32,48]:self.assertTrue(np.array_equal(base[216:],np.array(Image.open(O/'review'/f'scene_{f:02}.png'))[216:]))
 def test_ora_recomposition(self):
  with zipfile.ZipFile(O/'arene_generee_editable.ora') as z:
   root=ET.fromstring(z.read('stack.xml'));c=Image.new('RGBA',(512,640))
   for node in reversed(root.findall('./stack/layer')):c.alpha_composite(Image.open(io.BytesIO(z.read(node.get('src')))).convert('RGBA'))
   self.assertEqual(c.tobytes(),Image.open(io.BytesIO(z.read('mergedimage.png'))).convert('RGBA').tobytes());self.assertEqual(c.tobytes(),Image.open(O/'review/scene_00.png').convert('RGBA').tobytes())
 def test_no_false_native_or_runtime_claim(self):
  self.assertIn('not a recovered',self.m['animation']['origin']);self.assertEqual(self.m['runtime_PMDO'],'NOT TESTED');self.assertFalse(self.m['art_approved']);self.assertFalse(self.m['other_zones_complete'])
if __name__=='__main__':unittest.main()
