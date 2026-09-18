import unittest,json,hashlib,sys
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'exports/zones_relayout_v1'
sys.path.insert(0,str(R/'source'));import git_provenance
class RelayoutTests(unittest.TestCase):
 def setUp(self):self.man=json.loads((O/'manifest.json').read_text())
 def test_two_candidates_eleven_layers(self):
  self.assertEqual(len(self.man['maps']),2);self.assertEqual(sum(len(m['layers']) for m in self.man['maps']),11)
 def test_every_visible_pixel_exactly_matches_recorded_source(self):
  for m in self.man['maps']:
   native=np.array(Image.open(R/m['source']).convert('RGBA'))
   for l in m['layers']:
    a=np.array(Image.open(O/m['id']/l['png']));xy=np.load(O/m['id']/l['provenance'])['source_xy'];opaque=a[:,:,3]>0
    self.assertEqual(xy.shape,a.shape[:2]+(2,));p=xy[opaque];self.assertTrue((p>=0).all());self.assertTrue((p[:,0]<native.shape[1]).all());self.assertTrue((p[:,1]<native.shape[0]).all());self.assertTrue(np.array_equal(a[opaque],native[p[:,1],p[:,0]]));self.assertTrue((xy[~opaque]==-1).all())
 def test_sources_untouched_against_user_commit(self):
  """Manifest hash is always checked; the blob comparison needs full history."""
  missing=[]
  for m in self.man['maps']:
   p=R/m['source'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),m['source_sha256'])
   blob=git_provenance.pinned_blob('9ec9a081',m['source'],R)
   if blob is None: missing.append(m['source']);continue
   self.assertEqual(p.read_bytes(),blob)
  if missing: self.skipTest(f"pinned commit 9ec9a081 not in this checkout (shallow); hash-vs-manifest checked, blob comparison skipped for {len(missing)}/{len(self.man['maps'])} sources")
 def test_composite_and_alpha(self):
  for m in self.man['maps']:
   comp=Image.new('RGBA',tuple(m['dimensions']))
   for l in m['layers']:
    im=Image.open(O/m['id']/l['png']).convert('RGBA');self.assertEqual(im.size,comp.size);self.assertTrue(set(np.unique(np.array(im)[:,:,3])).issubset({0,255}));comp.alpha_composite(im)
   expected=Image.open(O/m['id']/'composite.png').convert('RGBA');self.assertEqual(comp.tobytes(),expected.tobytes());self.assertTrue((np.array(comp)[:,:,3]==255).all())
 def test_grid_and_unmodified_whole_cliff(self):
  for m in self.man['maps']:
   self.assertTrue(all(v%8==0 for v in m['dimensions']))
   for op in m['operations']:
    if 'destination' in op:self.assertTrue(all(v%8==0 for v in op['destination']))
  forest=self.man['maps'][0];cliff=[op for op in forest['operations'] if op['layer']=='03_cliff_entrance'];self.assertEqual(len(cliff),1);self.assertEqual(cliff[0]['source_rect'],[288,0,600,216]);self.assertEqual(cliff[0]['destination'],[456,0])
 def test_no_runtime_or_collision_claim(self):
  for m in self.man['maps']:self.assertFalse(m['art_approved']);self.assertEqual(m['runtime_PMDO'],'NOT TESTED');self.assertIn('NOT PROVIDED',m['collision'])
 def test_architecture_not_quilted(self):
  for m in self.man['maps']:
   for op in m['operations']:
    if 'operation' in op:self.assertIn('ground',op['layer'])
if __name__=='__main__':unittest.main()
