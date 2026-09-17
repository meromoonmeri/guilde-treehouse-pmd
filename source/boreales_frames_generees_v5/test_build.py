import unittest,hashlib,json
import numpy as np
from PIL import Image
from . import build as b
class GeneratedPaletteTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.keys=[(np.array(Image.open(b.O/'keyframes'/f'pose_{i:02}_indexed.png')),np.array(Image.open(b.O/'keyframes'/f'pose_{i:02}_alpha.png'))) for i in range(9)]
 def test_nine_generated_drawings(self):
  files=sorted((b.O/'keyframes').glob('pose_??.png'));self.assertEqual(len(files),9);self.assertEqual(len({hashlib.sha256(p.read_bytes()).digest() for p in files}),9)
 def test_generated_source_hash(self):
  m=json.loads((b.O/'manifest.json').read_text());self.assertEqual(hashlib.sha256((b.O/'bruts/aurores_8_poses.png').read_bytes()).hexdigest(),m['raw_source_sha256']);self.assertEqual(m['actual_sheet_grid'],[3,3])
 def test_indexed_palette_files(self):
  for i in range(9):
   with Image.open(b.O/'keyframes'/f'pose_{i:02}_indexed.png') as im:self.assertEqual(im.mode,'P');self.assertEqual(im.size,(312,208))
  self.assertEqual(len(json.loads((b.O/'animation/palettes_72.json').read_text())),72)
 def test_palette_only_changes_rgb_not_alpha_or_shape(self):
  a=np.array(b.tile(self.keys,0,animate=False));c=np.array(b.tile(self.keys,24,animate=False));np.testing.assert_array_equal(a[:,:,3],c[:,:,3]);self.assertGreater(np.count_nonzero(a[:,:,:3]!=c[:,:,:3]),10000)
 def test_drawing_changes_without_palette(self):
  a=np.array(b.tile(self.keys,0,cycling=False));c=np.array(b.tile(self.keys,24,cycling=False));self.assertGreater(np.count_nonzero(a[:,:,3]!=c[:,:,3]),5000)
 def test_palette_preserves_brightness_levels(self):
  for f in range(72):np.testing.assert_array_equal(b.palette(f).max(axis=1),b.palette(0).max(axis=1))
 def test_closed_loops(self):
  np.testing.assert_array_equal(b.palette(0),b.palette(72));np.testing.assert_array_equal(b.tile(self.keys,0),b.tile(self.keys,72));self.assertEqual((288*13//4)%936,0);self.assertEqual(288%72,0)
 def test_all_exported_frames(self):
  paths=sorted((b.O/'animation/frames').glob('*.png'));self.assertEqual(len(paths),72)
  for f,p in enumerate(paths):np.testing.assert_array_equal(Image.open(p),b.tile(self.keys,f))
 def test_static_layers_preserved(self):
  for p in (b.O/'calques').glob('*.png'):self.assertEqual(p.read_bytes(),(b.OLD/'calques'/p.name).read_bytes())
 def test_webp_visible_pixels_and_alpha(self):
  with Image.open(b.O/'animation/dessins_et_palette_cycling.webp') as im:
   self.assertEqual(im.n_frames,72)
   for f in [0,18,36,54,71]:
    im.seek(f);a=np.array(im.convert('RGBA'));a[a[:,:,3]==0]=0;np.testing.assert_array_equal(a,b.tile(self.keys,f))
 def test_gif_full_cycle(self):
  with Image.open(b.O/'review/scene_dessins_generes_palette.gif') as im:
   self.assertEqual(im.n_frames,72);total=0
   for f in range(72):im.seek(f);total+=im.info['duration']
   self.assertEqual(total,7200)
if __name__=='__main__':unittest.main()
