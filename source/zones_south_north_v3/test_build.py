import unittest,json,hashlib,sys,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy import ndimage as nd
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'exports/zones_south_north_v3'
sys.path.insert(0,str(R/'source'));import git_provenance
class SouthNorthTests(unittest.TestCase):
 def setUp(self):self.m=json.loads((O/'manifest.json').read_text())
 def test_two_south_north_maps(self):
  self.assertEqual(len(self.m['maps']),2)
  for m in self.m['maps']:
   self.assertEqual(m['orientation'],'SOUTH_TO_NORTH');self.assertLess(m['entrance'][1],m['size'][1]/2);self.assertEqual(m['south_access'][1]+m['south_access'][3],m['size'][1])
 def test_continuous_south_to_entrance_path(self):
  for m in self.m['maps']:
   a=np.array(Image.open(O/m['id']/'path_connectivity_mask.png'))>0;labels,n=nd.label(a);x,y=m['entrance'];self.assertGreater(labels[y,x],0);self.assertTrue(np.any(labels[-1]==labels[y,x]));self.assertEqual(n,1)
 def test_eight_pixel_radius_clearance_along_center_route(self):
  for m in self.m['maps']:
   a=np.array(Image.open(O/m['id']/'path_connectivity_mask.png'))>0;inner=nd.distance_transform_edt(a)>=8;labels,n=nd.label(inner);x,y=m['entrance'];self.assertGreater(labels[y+8,x],0);self.assertTrue(np.any(labels[-8]==labels[y+8,x]))
 def test_pixels_have_exact_multisource_provenance(self):
  sources=[np.array(Image.open(R/s['file']).convert('RGBA')) for s in self.m['sources']]
  for m in self.m['maps']:
   for l in m['layers']:
    a=np.array(Image.open(O/m['id']/l['file']));q=np.load(O/m['id']/l['provenance'])['source_sxy'];mask=a[:,:,3]>0;self.assertTrue((q[~mask]==-1).all())
    for i in np.unique(q[mask,0]):
     self.assertGreaterEqual(i,0);self.assertLess(i,len(sources));where=mask&(q[:,:,0]==i);p=q[where];self.assertTrue(np.array_equal(a[where],sources[i][p[:,2],p[:,1]]))
 def test_original_sources_unchanged(self):
  # The manifest sha256 values were recorded from the pinned historical commit,
  # so hash equality alone proves identity. The extra byte-for-byte comparison
  # against `git show 438b9288:<file>` only runs when that object is reachable;
  # shallow or squashed checkouts (where it is absent) keep the hash check and
  # report the gap as a skip instead of passing silently.
  missing=[]
  for s in self.m['sources']:
   raw=(R/s['file']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),s['sha256'])
   blob=git_provenance.pinned_blob('438b9288',s['file'],R)
   if blob is None: missing.append(s['file']);continue
   self.assertEqual(raw,blob)
  if missing: self.skipTest(f"pinned commit 438b9288 not in this checkout (shallow); hash-vs-manifest checked, blob comparison skipped for {len(missing)}/{len(self.m['sources'])} sources")
 def test_composite_rebuild_and_alpha(self):
  for m in self.m['maps']:
   c=Image.new('RGBA',tuple(m['size']))
   for l in m['layers']:
    a=Image.open(O/m['id']/l['file']).convert('RGBA');self.assertEqual(a.size,c.size);self.assertTrue(set(np.unique(np.array(a)[:,:,3])).issubset({0,255}));c.alpha_composite(a)
   self.assertEqual(c.tobytes(),Image.open(O/m['id']/'composite.png').convert('RGBA').tobytes());self.assertTrue((np.array(c)[:,:,3]==255).all())
 def test_ground_path_and_entrance_separate(self):
  for m in self.m['maps']:
   names=[l['id'] for l in m['layers']];self.assertTrue(any('soil' in n for n in names));self.assertTrue(any('path' in n for n in names));self.assertTrue(any('cave' in n for n in names))
 def test_portal_open_pixels_not_duplicated_in_frame(self):
  d=O/'blue_rock_cave';a=np.array(Image.open(d/'SouthNorthV3_blue_rock_cave_05_gateway_frame.png'));b=np.array(Image.open(d/'SouthNorthV3_blue_rock_cave_06_open_cave.png'));self.assertFalse(np.any((a[:,:,3]>0)&(b[:,:,3]>0)))
 def test_no_rotated_or_mirrored_modules(self):
  for m in self.m['maps']:
   for layer in m['layers']:
    ops=[op for op in m['operations'] if op['layer']==layer['id'] and 'rect' in op]
    if not ops:continue
    q=np.load(O/m['id']/layer['provenance'])['source_sxy'];covered=np.zeros(q.shape[:2],bool)
    for op in ops:
     x,y=op['position'];x0,y0,x1,y1=op['rect'];h=min(y1-y0,m['size'][1]-y);w=min(x1-x0,m['size'][0]-x)
     if h<=0 or w<=0:continue
     p=q[y:y+h,x:x+w];sy,sx=np.mgrid[y0:y0+h,x0:x0+w];covered[y:y+h,x:x+w]|=(p[:,:,0]==op['source'])&(p[:,:,1]==sx)&(p[:,:,2]==sy)
    self.assertTrue(np.all(covered[q[:,:,0]>=0]))
 def test_tsx_grid(self):
  for m in self.m['maps']:
   for l in m['layers']:
    p=O/m['id']/l['file'];r=ET.parse(p.with_suffix('.tsx')).getroot();self.assertEqual(int(r.get('tilecount')),m['size'][0]//8*(m['size'][1]//8));self.assertEqual(r.find('image').get('source'),p.name)
 def test_no_obsolete_layer_exports(self):
  for m in self.m['maps']:
   d=O/m['id'];self.assertEqual({p.name for p in d.glob('SouthNorthV3_*.png')},{l['file'] for l in m['layers']});self.assertEqual({p.name for p in d.glob('*_source.npz')},{l['provenance'] for l in m['layers']})
 def test_no_false_runtime_approval(self):
  for m in self.m['maps']:self.assertEqual(m['runtime'],'NOT TESTED');self.assertFalse(m['art_approved']);self.assertIn('not engine',m['connectivity'])
if __name__=='__main__':unittest.main()
