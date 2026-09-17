import unittest,hashlib,json
import numpy as np
from PIL import Image
from . import build as b
class AnimationTests(unittest.TestCase):
 def test_88_distinct_intrinsic_poses(self):
  files=sorted((b.O/'animation/frames').glob('*.png'));self.assertEqual(len(files),88);self.assertEqual(len({hashlib.sha256(p.read_bytes()).hexdigest() for p in files}),88)
 def test_not_a_translation(self):
  # Rigid rolling preserves foreground pixel count and alpha histogram; deformation does neither.
  a=np.array(b.motion(0));c=np.array(b.motion(22));self.assertGreater(abs(int((a[:,:,3]>40).sum())-int((c[:,:,3]>40).sum())),500)
  self.assertFalse(np.array_equal(np.bincount(a[:,:,3].ravel(),minlength=256),np.bincount(c[:,:,3].ravel(),minlength=256)))
 def test_animates_when_wrap_disabled(self):
  a=np.array(b.viewport(b.motion(0),0,False));c=np.array(b.viewport(b.motion(22),22,False));self.assertGreater(np.count_nonzero(np.any(a!=c,axis=2)),15000)
 def test_both_loops_exact(self):
  np.testing.assert_array_equal(b.motion(0),b.motion(88));np.testing.assert_array_equal(b.viewport(b.motion(0),0),b.viewport(b.motion(264),264))
 def test_loop_step_not_a_jump(self):
  frames=[np.array(b.motion(f))[:,:,3].astype(float) for f in range(88)];diffs=[np.abs(frames[(f+1)%88]-frames[f]).mean() for f in range(88)];self.assertLess(diffs[-1],np.median(diffs)*1.5)
 def test_static_layers_byte_identical(self):
  for p in (b.O/'calques').glob('*.png'):self.assertEqual(p.read_bytes(),(b.OLD/'calques'/p.name).read_bytes())
 def test_webp_exact_and_transparent(self):
  with Image.open(b.O/'animation/aurore_sans_defilement.webp') as im:
   self.assertEqual(im.n_frames,88);self.assertEqual(im.info['loop'],0)
   for f in [0,22,44,66,87]:
    im.seek(f);a=np.array(im.convert('RGBA'));a[a[:,:,3]==0]=0;np.testing.assert_array_equal(a,b.motion(f));self.assertTrue(np.any(a[:,:,3]==0));self.assertTrue(np.any((a[:,:,3]>0)&(a[:,:,3]<255)))
 def test_scene_gif_duration_and_static_terrain(self):
  mask=np.array(Image.open(b.OLD/'review/terrain_detoure.png').convert('RGBA').resize((384,256),Image.Resampling.NEAREST))[:,:,3]==255
  with Image.open(b.O/'review/scene_animee_wrap.gif') as im:
   self.assertEqual(im.n_frames,264);first=np.array(im.convert('RGB'));duration=0
   for f in range(im.n_frames):
    im.seek(f);duration+=im.info['duration'];np.testing.assert_array_equal(np.array(im.convert('RGB'))[mask],first[mask])
   self.assertEqual(duration,26400)
 def test_no_scroll_gif_is_animated(self):
  with Image.open(b.O/'review/aurore_ANIMEE_sans_scroll.gif') as im:
   self.assertEqual(im.n_frames,88);im.seek(0);a=np.array(im.convert('RGB'));im.seek(22);self.assertFalse(np.array_equal(a,im.convert('RGB')))
if __name__=='__main__':unittest.main()
