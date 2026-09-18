import unittest,json,hashlib,sys,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'exports/zones_relayout_v2'
sys.path.insert(0,str(R/'source'));import git_provenance
class IceAndBGTests(unittest.TestCase):
 def setUp(self):self.m=json.loads((O/'manifest.json').read_text())
 def test_scope_and_counts(self):
  self.assertEqual(len(self.m['assets']),3);self.assertEqual(sum(len(s['layers']) for s in self.m['assets']),19);self.assertEqual([s['kind'] for s in self.m['assets']],['terrain_relayout','BG_relayout','BG_layer_preparation'])
 def test_all_visible_pixels_match_source_coordinates(self):
  for s in self.m['assets']:
   a=np.array(Image.open(R/s['source']).convert('RGBA'))
   for l in s['layers']:
    p=np.array(Image.open(O/s['id']/l['file']).convert('RGBA'));xy=np.load(O/s['id']/l['provenance'])['source_xy'];mask=p[:,:,3]>0;q=xy[mask];self.assertTrue((q>=0).all());self.assertTrue((q[:,0]<a.shape[1]).all());self.assertTrue((q[:,1]<a.shape[0]).all());self.assertTrue(np.array_equal(p[mask],a[q[:,1],q[:,0]]));self.assertTrue((xy[~mask]==-1).all())
 def test_originals_unchanged(self):
  """Manifest hash is always checked; the blob comparison needs full history."""
  missing=[]
  for s in self.m['assets']:
   raw=(R/s['source']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),s['sha256'])
   blob=git_provenance.pinned_blob('9ec9a081',s['source'],R)
   if blob is None: missing.append(s['source']);continue
   self.assertEqual(raw,blob)
  if missing: self.skipTest(f"pinned commit 9ec9a081 not in this checkout (shallow); hash-vs-manifest checked, blob comparison skipped for {len(missing)}/{len(self.m['assets'])} sources")
 def test_exact_layer_composition_and_alpha(self):
  for s in self.m['assets']:
   im=Image.new('RGBA',tuple(s['size']))
   for l in s['layers']:
    p=Image.open(O/s['id']/l['file']).convert('RGBA');self.assertEqual(p.size,im.size);self.assertTrue(set(np.unique(np.array(p)[:,:,3])).issubset({0,255}));im.alpha_composite(p)
   final=Image.open(O/s['id']/'composite.png').convert('RGBA');self.assertEqual(im.tobytes(),final.tobytes());self.assertTrue((np.array(final)[:,:,3]==255).all())
 def test_aurora_keeps_original_composition(self):self.assertEqual(Image.open(R/'aurorepmdsky.png').convert('RGBA').tobytes(),Image.open(O/'aurora/composite.png').convert('RGBA').tobytes())
 def test_moon_reflection_and_reef_not_moved_or_scaled(self):
  s=self.m['assets'][1];a=np.array(Image.open(R/s['source']).convert('RGBA'))
  for l in s['layers']:
   if l['id'] in ['03_moon','07_moon_reflection','08_reef']:
    p=np.array(Image.open(O/s['id']/l['file']));mask=p[:,:,3]>0;self.assertTrue(mask.any());self.assertTrue(np.array_equal(p[mask],a[mask]));xy=np.load(O/s['id']/l['provenance'])['source_xy'];ys,xs=np.where(mask);self.assertTrue(np.array_equal(xy[mask],np.stack([xs,ys],1)))
 def test_grid_and_tsx(self):
  for s in self.m['assets']:
   self.assertTrue(all(n%8==0 for n in s['size']))
   for l in s['layers']:
    path=O/s['id']/l['file'];root=ET.parse(path.with_suffix('.tsx')).getroot();self.assertEqual(root.get('tilewidth'),'8');self.assertEqual(int(root.get('tilecount')),s['size'][0]//8*(s['size'][1]//8));self.assertEqual(root.find('image').get('source'),path.name)
 def test_truthful_static_candidates(self):
  for s in self.m['assets']:self.assertFalse(s['art_approved']);self.assertEqual(s['runtime'],'NOT TESTED');self.assertTrue(s['animation'].startswith('NONE'))
if __name__=='__main__':unittest.main()
