"""Read-only asset validation; report written only with --report."""
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from scipy import ndimage as nd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from source.beach_layers_v1 import build as b

class BeachTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=json.loads((b.OUT/'manifest.json').read_text())
        cls.ref=np.array(Image.open(b.SRC).convert('RGBA'))
        cls.sea=np.array(Image.open(b.OUT/'masques/mer.png'))>0
        cls.layers=[np.array(Image.open(b.OUT/l['file']).convert('RGBA')) for l in cls.m['layers']]
        cls.frames=[];cls.water=[];cls.foam=[]
        fixed=Image.new('RGBA',tuple(cls.m['source']['size']))
        for l,a in zip(cls.m['layers'],cls.layers):
            if l['id'] not in ['03_mer','04_ecume']:fixed.alpha_composite(Image.fromarray(a))
        for k in range(b.N):
            a=Image.open(b.OUT/'animation/mer'/f'BeachV1_mer_{k:02d}.png').convert('RGBA')
            f=Image.open(b.OUT/'animation/ecume'/f'BeachV1_ecume_{k:02d}.png').convert('RGBA')
            cls.water.append(np.array(a));cls.foam.append(np.array(f));a.alpha_composite(f);a.alpha_composite(fixed);cls.frames.append(np.array(a))
    def test_01_sources(self):
        for key in ['source','wave_reference']:
            s=self.m[key];self.assertEqual(b.sha(ROOT/s['file']),s['sha256'])
    def test_02_nine_disjoint_exact_layers(self):
        self.assertEqual(len(self.layers),9)
        self.assertTrue(np.all(np.sum([a[:,:,3]>0 for a in self.layers],axis=0)==1))
        total=np.sum([a.astype(np.uint16) for a in self.layers],axis=0).astype(np.uint8)
        np.testing.assert_array_equal(total,self.ref)
    def test_03_phase_zero_exact_and_all_dry_pixels_fixed(self):
        np.testing.assert_array_equal(self.frames[0],self.ref)
        for frame in self.frames:np.testing.assert_array_equal(frame[~self.sea],self.ref[~self.sea])
    def test_04_64_frames_dimensions_alpha_footprint(self):
        for a,f in zip(self.water,self.foam):
            self.assertEqual(a.shape,self.ref.shape);self.assertEqual(f.shape,self.ref.shape)
            np.testing.assert_array_equal(a[:,:,3]>0,self.sea)
            self.assertFalse(np.any((f[:,:,3]>0)&~self.sea))
            for arr in [a,f]:self.assertTrue(set(np.unique(arr[:,:,3])) <= {0,255})
    def test_05_source_palette_no_new_colours(self):
        palette=set(map(tuple,self.ref[:,:,:3].reshape(-1,3)))
        for a,f in zip(self.water,self.foam):
            for arr in [a,f]:
                visible=arr[arr[:,:,3]>0,:3]
                self.assertTrue(set(map(tuple,np.unique(visible,axis=0))) <= palette)
    def test_06_motion_and_loop(self):
        masks=np.array(Image.open(b.OUT/'masques/ecume.png'))>0
        fun,_=b.animator(self.ref[:,:,:3],self.sea,masks,b.wave_guide())
        for a,c in zip(fun(0),fun(b.N)):np.testing.assert_array_equal(a,c)
        self.assertGreater(len({a.tobytes() for a in self.water}),20)
        self.assertGreater(len({a.tobytes() for a in self.foam}),8)
        changes=[np.abs(self.frames[k].astype(float)-self.frames[(k+1)%b.N].astype(float)).mean() for k in range(b.N)]
        self.assertLessEqual(changes[-1],max(changes[:-1]))
        anchored=self.sea & (nd.distance_transform_edt(self.sea)<=5)
        for frame in self.frames:np.testing.assert_array_equal(frame[anchored],self.ref[anchored])
    def test_07_lossless_webp_and_gif_clock(self):
        for ext in ['webp','gif']:
            im=Image.open(b.OUT/f'BeachV1_plage_animee.{ext}');elapsed=0
            self.assertGreater(im.n_frames,20)
            for k in range(im.n_frames):
                im.seek(k);im.load();duration=im.info['duration']
                self.assertEqual(duration%b.MS,0)
                if ext=='webp':
                    for tick in range(elapsed//b.MS,(elapsed+duration)//b.MS):
                        np.testing.assert_array_equal(np.array(im.convert('RGBA')),self.frames[tick])
                elapsed+=duration
            self.assertEqual(elapsed,b.N*b.MS)
    def test_08_ora_recomposition(self):
        with zipfile.ZipFile(b.OUT/'BeachV1_calques.ora') as z:
            self.assertEqual(z.read('mimetype'),b'image/openraster')
            root=ET.fromstring(z.read('stack.xml'));layers=root.find('stack').findall('layer')
            self.assertEqual(len(layers),9)
            comp=Image.new('RGBA',tuple(self.m['source']['size']))
            for l in reversed(layers):comp.alpha_composite(Image.open(io.BytesIO(z.read(l.get('src')))).convert('RGBA'))
            np.testing.assert_array_equal(np.array(comp),self.ref)
    def test_09_padding_without_resampling(self):
        files=list((b.OUT/'calques').glob('*.png'))+list((b.OUT/'animation').rglob('*.png'))
        self.assertEqual(len(files),9+2*b.N)
        h,w=self.ref.shape[:2]
        for p in files:
            q=b.OUT/'import_8px'/p.relative_to(b.OUT);q=q.with_name(p.stem+'_PAD8.png')
            a=np.array(Image.open(p).convert('RGBA'));c=np.array(Image.open(q).convert('RGBA'))
            self.assertEqual(c.shape,(472,704,4));np.testing.assert_array_equal(a,c[:h,:w])
            self.assertFalse(c[h:,:,3].any());self.assertFalse(c[:,w:,3].any())
    def test_10_honest_manifest(self):
        self.assertFalse(self.m['animation']['official_cycle'])
        self.assertEqual(self.m['import']['runtime'],'NOT TESTED')

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(BeachTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if '--report' in sys.argv:
        (b.OUT/'verification.json').write_text(json.dumps({'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'pass':result.wasSuccessful(),'runtime_PMDO':'NOT TESTED','source_sha256':b.sha(b.SRC)},indent=2)+'\n')
    raise SystemExit(not result.wasSuccessful())
