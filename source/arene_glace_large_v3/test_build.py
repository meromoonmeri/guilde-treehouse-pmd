import unittest,json,hashlib,zipfile,io
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from . import build as b
class WideArenaTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.m=json.loads((b.O/'manifest.json').read_text());cls.tile=b.load(b.O/cls.m['aurora']['tile']);cls.terrain=b.load(b.O/'review/terrain_detoure.png')
 def test_new_landscape_and_aspect_preserved(self):
  self.assertEqual(self.m['size'],[768,512]);self.assertGreater(768,512);self.assertLess(512,640)
  for item in self.m['normalization'].values():
   for old,new in zip(item['input_size'],item['resized_size']):self.assertLessEqual(abs(old*item['uniform_scale']-new),.5)
  self.assertGreater(self.m['normalization']['terrain']['input_size'][0],self.m['normalization']['terrain']['input_size'][1])
 def test_hashes(self):
  for s in self.m['sources']+self.m['aurora']['sources']:self.assertEqual(hashlib.sha256((b.R/s['file']).read_bytes()).hexdigest(),s['sha256'])
 def test_partition_and_exact_recomposition(self):
  masks=[np.array(Image.open(p))>0 for p in sorted((b.O/'masques').glob('*.png'))];total=np.sum(masks,axis=0);np.testing.assert_array_equal(total,np.array(self.terrain)[:,:,3]>0)
  merged=b.blank()
  for layer in self.m['layers']:merged.alpha_composite(b.load(b.O/layer['file']))
  np.testing.assert_array_equal(merged,self.terrain)
 def test_sky_independent_opaque(self):
  sky=b.load(b.O/self.m['sky_file']);self.assertEqual(sky.size,(768,512));self.assertTrue(np.all(np.array(sky)[:,:,3]==255));expected,_=b.fit(b.load(b.O/'bruts/ciel.png'),True);stars=b.load(b.O/self.m['stars_file']);self.assertTrue(np.any(np.array(stars)[:,:,3]==0));self.assertTrue(np.any(np.array(stars)[:,:,3]>0));sky.alpha_composite(stars);np.testing.assert_array_equal(sky,expected)
 def test_grid_and_no_magenta_in_terrain(self):
  for p in (b.O/'calques').glob('*.png'):
   im=b.load(p);self.assertEqual(im.size,(768,512));self.assertEqual(im.width%8,0);self.assertEqual(im.height%8,0)
  a=np.array(self.terrain);r,g,blue=a[:,:,:3].astype(float).transpose(2,0,1);self.assertFalse(np.any((a[:,:,3]>0)&(r>70)&(blue>65)&(r>1.5*g)&(blue>1.5*g)))
 def test_spatial_seams_are_transparent(self):
  a=np.array(self.tile);self.assertEqual(self.tile.size,(792,240))
  for x in [0,263,264,527,528,791]:self.assertFalse(np.any(a[:,x]))
  self.assertGreater(a[:,:,3].max(),0);self.assertTrue(np.any((a[:,:,3]>0)&(a[:,:,3]<255)))
 def test_exact_temporal_loop_and_no_hold(self):
  np.testing.assert_array_equal(b.overlay(self.tile,0),b.overlay(self.tile,198));self.assertFalse(np.array_equal(b.overlay(self.tile,197),b.overlay(self.tile,0)))
 def test_every_step_including_wrap_is_same_translation(self):
  for f in range(198):
   now=np.array(b.overlay(self.tile,f));nxt=np.array(b.overlay(self.tile,f+1));np.testing.assert_array_equal(now[:,4:],nxt[:,:-4])
 def test_exported_frames_match_formula(self):
  frames=sorted((b.O/'animation/frames').glob('*.png'));self.assertEqual(len(frames),198)
  for f,p in enumerate(frames):np.testing.assert_array_equal(b.load(p),b.overlay(self.tile,f))
 def test_gif_timing_and_stationary_terrain(self):
  gif=Image.open(b.O/'review/animation.gif');self.assertEqual(gif.n_frames,198);self.assertEqual(gif.info['loop'],0);total=0;first=np.array(gif.convert('RGB'));mask=np.array(self.terrain)[:,:,3]==255
  for f in range(gif.n_frames):
   gif.seek(f);total+=gif.info['duration'];np.testing.assert_array_equal(np.array(gif.convert('RGB'))[mask],first[mask])
  gif.close();self.assertEqual(total,26400);self.assertEqual(198*8/60*1000,26400)
 def test_ora_order_and_merge(self):
  with zipfile.ZipFile(b.O/'arene_large_editable.ora') as z:
   self.assertEqual(z.read('mimetype'),b'image/openraster');root=ET.fromstring(z.read('stack.xml'));layers=root.find('stack').findall('layer');merged=b.blank()
   for layer in reversed(layers):merged.alpha_composite(Image.open(io.BytesIO(z.read(layer.attrib['src']))).convert('RGBA'))
   np.testing.assert_array_equal(merged,b.load(b.O/'review/scene_000.png'));np.testing.assert_array_equal(Image.open(io.BytesIO(z.read('mergedimage.png'))),merged)
 def test_transparent_webp_exact_frames(self):
  with Image.open(b.O/'animation/AreneLargeV3_Aurore_Loop.webp') as im:
   self.assertEqual(im.n_frames,198);self.assertEqual(im.info['loop'],0)
   for f in [0,49,99,148,197]:
    im.seek(f);np.testing.assert_array_equal(im.convert('RGBA'),b.overlay(self.tile,f))
 def test_truthful_status(self):
  self.assertEqual(self.m['runtime_PMDO'],'NOT TESTED');self.assertFalse(self.m['art_approved']);self.assertFalse(self.m['other_zones_complete']);self.assertIn('Not an extracted official',self.m['aurora']['origin'])
if __name__=='__main__':unittest.main()
