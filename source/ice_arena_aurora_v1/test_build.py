import unittest,json,hashlib,sys
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'exports/ice_arena_aurora_v1';sys.path.insert(0,str(R))
from source.ice_arena_aurora_v1.build import motion,star_frame,N,load,REF
class AnimatedArenaTests(unittest.TestCase):
 def setUp(self):self.m=json.loads((O/'manifest.json').read_text())
 def test_counts_duration_and_labels(self):
  self.assertEqual(self.m['frames'],64);self.assertEqual(self.m['duration_seconds'],6.4);self.assertEqual(len(self.m['static_layers']),8);self.assertIn('NEW AUTHORED',self.m['animation_origin']);self.assertIn('NOT a recovered',self.m['animation_origin']);self.assertEqual(self.m['runtime_PMDO'],'NOT TESTED')
 def test_native_originals_unchanged(self):
  for s in self.m['sources']:self.assertEqual(hashlib.sha256((R/s['file']).read_bytes()).hexdigest(),s['sha256'])
 def test_aurora_pixels_match_recorded_native_source(self):
  native=np.array(load(R/'aurorepmdsky.png'));coords=np.load(O/'provenance/aurora_source_xy.npz')['source_xy'];self.assertEqual(coords.shape,(64,216,264,2))
  for f in range(64):
   a=np.array(load(O/'aurora_frames'/f'IceAuroraV1_Ribbons_{f:02}.png'));mask=a[:,:,3]>0;p=coords[f][mask];self.assertTrue(np.array_equal(a[mask],native[p[:,1],p[:,0]]));self.assertTrue((coords[f][~mask]==-1).all())
 def test_continuous_loop_and_native_start(self):
  raw=load(REF/'ZonesV2_aurora_03_aurora_ribbons.png');self.assertEqual(motion(raw,0)[0].tobytes(),raw.tobytes());self.assertEqual(motion(raw,64)[0].tobytes(),raw.tobytes());self.assertEqual(star_frame(load(REF/'ZonesV2_aurora_02_stars.png'),0).tobytes(),star_frame(load(REF/'ZonesV2_aurora_02_stars.png'),64).tobytes())
  for f in range(64):self.assertLessEqual(np.max(np.abs(motion(raw,f)[2]-motion(raw,f+1)[2])),1)
 def test_real_animation_not_static_duplicates(self):
  frames=[load(O/'aurora_frames'/f'IceAuroraV1_Ribbons_{f:02}.png').tobytes() for f in range(64)];self.assertGreaterEqual(len(set(frames)),48)
  for name in ['scene','background']:
   with Image.open(O/'review'/f'{name}.gif') as im:
    self.assertGreaterEqual(im.n_frames,48);self.assertEqual(im.info['loop'],0);duration=0
    for f in range(im.n_frames):im.seek(f);duration+=im.info['duration']
    self.assertEqual(duration,6400)
 def test_stars_keep_shapes_and_rgb(self):
  raw=np.array(load(REF/'ZonesV2_aurora_02_stars.png'));mask=raw[:,:,3]>0
  for f in range(64):
   a=np.array(load(O/'star_frames'/f'IceAuroraV1_Stars_{f:02}.png'));self.assertTrue(np.array_equal(mask,a[:,:,3]>0));self.assertTrue(np.array_equal(raw[mask,:3],a[mask,:3]));self.assertGreaterEqual(a[mask,3].min(),178)
 def test_static_terrain_does_not_move(self):
  base=np.array(load(O/'review/scene_00.png'))
  for f in [16,32,48]:self.assertTrue(np.array_equal(base[216:],np.array(load(O/'review'/f'scene_{f:02}.png'))[216:]))
 def test_atlases_match_every_png(self):
  for label,folder in [('Ribbons','aurora_frames'),('Stars','star_frames')]:
   atlas=load(O/f'IceAuroraV1_{label}_64frames.png');self.assertEqual(atlas.size,(2112,1728))
   for f in range(64):self.assertEqual(atlas.crop((f%8*264,f//8*216,(f%8+1)*264,(f//8+1)*216)).tobytes(),load(O/folder/f'IceAuroraV1_{label}_{f:02}.png').tobytes())
 def test_static_native_rgb_and_grid(self):
  palette=set()
  for f in ['pmdskyicearena.png','aurorepmdsky.png']:
   a=np.array(load(R/f));palette.update(map(tuple,a[a[:,:,3]>0,:3]))
  for l in self.m['static_layers']:
   a=np.array(load(O/l['file']));self.assertEqual(a.shape,(720,512,4));self.assertTrue(set(map(tuple,a[a[:,:,3]>0,:3])).issubset(palette))
 def test_south_approach_clear_of_ice(self):
  floor=np.array(Image.open(O/'snow_surface_mask_NOT_COLLISION.png'))>0;self.assertTrue(floor[456:,248:264].all())
  for name in ['06_north_ice_rim','07_side_ice_and_ramp','08_native_fissures']:
   a=np.array(load(O/'static'/f'IceAuroraV1_{name}.png'));self.assertFalse((a[456:,248:264,3]>0).any())
if __name__=='__main__':unittest.main()
