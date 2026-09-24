import unittest,json,hashlib,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
import numpy as np
from scipy import ndimage as nd
from PIL import Image
R=Path(__file__).resolve().parents[2];O=R/'exports/zones_south_north_v4'
BASELINE='3d4ea6f0'
class Lot4Tests(unittest.TestCase):
 def setUp(self):self.m=json.loads((O/'manifest.json').read_text())
 def test_two_south_north_maps(self):
  self.assertEqual(len(self.m['maps']),2)
  for m in self.m['maps']:
   self.assertEqual(m['orientation'],'SOUTH_TO_NORTH');self.assertLess(m['entrance'][1],m['size'][1]/2);self.assertEqual(m['south_access'][1]+m['south_access'][3],m['size'][1])
 def test_continuous_south_to_entrance_path(self):
  for m in self.m['maps']:
   a=np.array(Image.open(O/m['id']/'path_connectivity_mask.png'))>0;labels,n=nd.label(a);x,y=m['entrance']
   self.assertGreater(labels[y,x],0);self.assertTrue(np.any(labels[-1]==labels[y,x]));self.assertEqual(n,1)
 def test_eight_pixel_radius_clearance_along_center_route(self):
  for m in self.m['maps']:
   a=np.array(Image.open(O/m['id']/'path_connectivity_mask.png'))>0;inner=nd.distance_transform_edt(a)>=8;labels,n=nd.label(inner);x,y=m['entrance']
   self.assertGreater(labels[y+8,x],0);self.assertTrue(np.any(labels[-8]==labels[y+8,x]))
 def test_pixels_have_exact_multisource_provenance(self):
  sources=[np.array(Image.open(R/s['file']).convert('RGBA')) for s in self.m['sources']]
  for m in self.m['maps']:
   for l in m['layers']:
    a=np.array(Image.open(O/m['id']/l['file']));q=np.load(O/m['id']/l['provenance'])['source_sxy'];mask=a[:,:,3]>0
    self.assertTrue((q[~mask]==-1).all())
    for i in np.unique(q[mask,0]):
     self.assertGreaterEqual(i,0);self.assertLess(i,len(sources));where=mask&(q[:,:,0]==i);p=q[where]
     self.assertTrue(np.array_equal(a[where],sources[i][p[:,2],p[:,1]]))
 def test_original_sources_unchanged(self):
  for s in self.m['sources']:
   raw=(R/s['file']).read_bytes();self.assertEqual(hashlib.sha256(raw).hexdigest(),s['sha256'])
   self.assertEqual(raw,subprocess.check_output(['git','show',BASELINE+':'+s['file']],cwd=R))
 def test_composite_rebuild_and_alpha(self):
  for m in self.m['maps']:
   c=Image.new('RGBA',tuple(m['size']))
   for l in m['layers']:
    a=Image.open(O/m['id']/l['file']).convert('RGBA');self.assertEqual(a.size,c.size)
    self.assertTrue(set(np.unique(np.array(a)[:,:,3])).issubset({0,255}));c.alpha_composite(a)
   self.assertEqual(c.tobytes(),Image.open(O/m['id']/'composite.png').convert('RGBA').tobytes())
   self.assertTrue((np.array(c)[:,:,3]==255).all())
 def test_layers_cover_ground_walls_entrance(self):
  for m in self.m['maps']:
   names=[l['id'] for l in m['layers']]
   self.assertTrue(any(('sand' in n) or ('floor' in n) or ('soil' in n) for n in names))
   self.assertTrue(any(('wall' in n) or ('boulders' in n) for n in names))
   self.assertTrue(any(('cave' in n) or ('exit' in n) for n in names))
 def test_exits_dark_and_separate(self):
  arid=[m for m in self.m['maps'] if m['id']=='arid_cave_entrance'][0]
  cave=arid['layers'][[l['id'] for l in arid['layers']].index('05_cave_entrance')]
  a=np.array(Image.open(O/arid['id']/cave['file']));d=(a[:,:,3]>0)&(a[:,:,:3].astype(float).sum(2)<120);self.assertGreater(d.sum(),400)
  pur=[m for m in self.m['maps'] if m['id']=='purple_two_exit_cave'][0]
  names={l['id']:l for l in pur['layers']};boxes=[]
  for n in ['05_exit_west','06_exit_east']:
   a=np.array(Image.open(O/pur['id']/names[n]['file']));d=(a[:,:,3]>0)&(a[:,:,:3].astype(float).sum(2)<120)
   self.assertGreater(d.sum(),400);ys,xs=np.where(d);boxes.append((xs.min(),xs.max()))
  self.assertGreaterEqual(boxes[1][0]-boxes[0][1],40)
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
    p=O/m['id']/l['file'];r=ET.parse(p.with_suffix('.tsx')).getroot()
    self.assertEqual(int(r.get('tilecount')),m['size'][0]//8*(m['size'][1]//8));self.assertEqual(r.find('image').get('source'),p.name)
 def test_no_obsolete_layer_exports(self):
  for m in self.m['maps']:
   d=O/m['id'];self.assertEqual({p.name for p in d.glob('SouthNorthV4_*.png')},{l['file'] for l in m['layers']})
   self.assertEqual({p.name for p in d.glob('*_source.npz')},{l['provenance'] for l in m['layers']})
 def test_no_false_runtime_approval(self):
  for m in self.m['maps']:
   self.assertEqual(m['runtime'],'NOT TESTED');self.assertFalse(m['art_approved']);self.assertIn('not engine',m['connectivity'])
if __name__=='__main__':unittest.main()
