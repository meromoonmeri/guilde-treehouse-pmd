import unittest,json,hashlib
from pathlib import Path
from PIL import Image
import numpy as np
R=Path(__file__).resolve().parents[2];O=R/'exports/guild_structures_v1'
class StructureTests(unittest.TestCase):
 def setUp(self):self.m=json.loads((O/'manifest.json').read_text())
 def test_five_distinct_structures(self):
  self.assertEqual(len(self.m['structures']),5);self.assertEqual(len({(O/s['object']).read_bytes() for s in self.m['structures']}),5)
 def test_grid_and_layers(self):
  for s in self.m['structures']:
   self.assertTrue(all(v%8==0 for v in s['canvas_px']+s['anchor_px']));self.assertEqual(len(s['layers']),4)
   for l in s['layers']:
    with Image.open(O/l['file']) as im:self.assertEqual(list(im.size),s['canvas_px'])
 def test_exact_recomposition(self):
  for s in self.m['structures']:
   c=Image.new('RGBA',tuple(s['canvas_px']));obj=c.copy()
   for i,l in enumerate(s['layers']):
    im=Image.open(O/l['file']).convert('RGBA');c.alpha_composite(im)
    if i:obj.alpha_composite(im)
   self.assertEqual(c.tobytes(),Image.open(O/s['composite']).convert('RGBA').tobytes());self.assertEqual(obj.tobytes(),Image.open(O/s['object']).convert('RGBA').tobytes())
 def test_native_palette_binary_alpha_no_magenta(self):
  palette=set(map(tuple,json.loads((R/'source/guild_structures_v1/references/palette.json').read_text())))
  for s in self.m['structures']:
   a=np.array(Image.open(O/s['object']));self.assertTrue(set(np.unique(a[:,:,3])).issubset({0,255}));self.assertTrue(set(map(tuple,a[a[:,:,3]>0,:3])).issubset(palette));self.assertFalse(np.any((a[:,:,0]>170)&(a[:,:,2]>170)&(a[:,:,1]<70)&(a[:,:,3]>0)))
 def test_no_false_runtime_claim(self):self.assertFalse(self.m['art_approved']);self.assertEqual(self.m['runtime_PMDO'],'NOT TESTED');self.assertIn('not reconstructed interiors',self.m['layer_limit'])
 def test_canonical_reference_unchanged(self):
  ref=self.m['source_reference'];self.assertEqual(hashlib.sha256((R/ref['path']).read_bytes()).hexdigest(),ref['sha256'])
 def test_zone_audit(self):
  r=json.loads((R/'exports/zones_bg_audit_v1/audit.json').read_text());self.assertEqual(len(r['entries']),23);self.assertEqual(len(r['maps']),2);self.assertEqual(r['relayouts_produced'],0)
  for e in r['entries']+r['maps']:self.assertEqual(hashlib.sha256((R/e['file']).read_bytes()).hexdigest(),e['sha256'])
  for m in r['maps']:self.assertEqual(m['background']['BGAnim']['AnimIndex'],'')
if __name__=='__main__':unittest.main()
