import unittest,tempfile,json
from pathlib import Path
from PIL import Image
import numpy as np
from validate import run,C
class ContractTests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def portrait(self,size=(40,40),colors=1):
  a=np.zeros((size[1],size[0],4),dtype='uint8');a[:,:,3]=255
  for x in range(size[0]):a[:,x,:3]=[x%colors,80,120]
  Image.fromarray(a).save(self.p/'portrait.png');return self.p/'portrait.png'
 def sprite(self):
  p=self.p/'sprite';p.mkdir();(p/'AnimData.xml').write_text('<AnimData><ShadowSize>0</ShadowSize><Anims><Anim><Name>Idle</Name><Index>7</Index><FrameWidth>8</FrameWidth><FrameHeight>8</FrameHeight><Durations><Duration>10</Duration></Durations></Anim></Anims></AnimData>')
  for kind,xy,color in [('Anim',(3,3),(40,90,60,255)),('Offsets',(3,4),(0,255,0,255)),('Shadow',(4,6),(255,255,255,255))]:
   im=Image.new('RGBA',(8,64))
   for row in range(8):im.putpixel((xy[0],row*8+xy[1]),color)
   im.save(p/f'Idle-{kind}.png')
  return p
 def test_portrait_good(self):self.assertEqual(run('portrait',self.portrait(colors=15))['technical_precheck'],'PASS')
 def test_portrait_16(self):self.assertEqual(run('portrait',self.portrait(colors=16))['technical_precheck'],'FAIL')
 def test_portrait_size(self):self.assertEqual(run('portrait',self.portrait((41,40)))['technical_precheck'],'FAIL')
 def test_portrait_alpha_hole(self):
  p=self.portrait();a=Image.open(p);a.putpixel((4,4),(0,0,0,0));a.save(p);self.assertEqual(run('portrait',p)['technical_precheck'],'FAIL')
 def test_portrait_semi_alpha(self):
  p=self.portrait();a=Image.open(p);a.putpixel((4,4),(0,0,0,128));a.save(p);self.assertEqual(run('portrait',p)['technical_precheck'],'FAIL')
 def test_portrait_empty(self):
  p=self.portrait();Image.new('RGBA',(40,40)).save(p);self.assertEqual(run('portrait',p)['technical_precheck'],'FAIL')
 def test_portrait_full(self):
  p=self.portrait((200,160));self.assertEqual(run('portrait',p,'full')['technical_precheck'],'PASS')
 def test_asymmetric_pair(self):
  p=self.portrait();self.assertEqual(run('portrait',p,asymmetric=True)['technical_precheck'],'FAIL')
 def test_good_sprite(self):self.assertEqual(run('sprite',self.sprite())['technical_precheck'],'PASS')
 def test_sprite_global_palette(self):
  p=self.sprite();a=Image.open(p/'Idle-Anim.png');
  for i in range(16):a.putpixel((i%8,i//8),(i,12,20,255))
  a.save(p/'Idle-Anim.png');self.assertEqual(run('sprite',p)['technical_precheck'],'FAIL')
 def test_sprite_rows(self):
  p=self.sprite()
  for file in p.glob('*.png'):Image.open(file).crop((0,0,8,16)).save(file)
  self.assertEqual(run('sprite',p)['technical_precheck'],'FAIL')
 def test_marker(self):
  p=self.sprite();a=Image.open(p/'Idle-Offsets.png');a.putpixel((3,4),(0,0,0,0));a.save(p/'Idle-Offsets.png');self.assertEqual(run('sprite',p)['technical_precheck'],'FAIL')
 def test_invalid_marker_color(self):
  p=self.sprite();a=Image.open(p/'Idle-Offsets.png');a.putpixel((1,1),(128,0,0,255));a.save(p/'Idle-Offsets.png');self.assertEqual(run('sprite',p)['technical_precheck'],'FAIL')
 def test_missing_shadow(self):
  p=self.sprite();(p/'Idle-Shadow.png').unlink();self.assertEqual(run('sprite',p)['technical_precheck'],'FAIL')
 def test_extra_file(self):
  p=self.sprite();(p/'readme.txt').write_text('no');self.assertEqual(run('sprite',p)['technical_precheck'],'FAIL')
 def test_copy_cycle(self):
  p=self.sprite();f=p/'AnimData.xml';s=f.read_text().replace('</Anims>','<Anim><Name>Sleep</Name><Index>5</Index><CopyOf>Sleep</CopyOf></Anim></Anims>');f.write_text(s);self.assertEqual(run('sprite',p)['technical_precheck'],'FAIL')
 def test_missing_completion(self):self.assertEqual(run('sprite',self.sprite(),'dungeon')['technical_precheck'],'FAIL')
 def test_wrong_index(self):
  p=self.sprite();f=p/'AnimData.xml';f.write_text(f.read_text().replace('<Index>7','<Index>0'));self.assertEqual(run('sprite',p)['technical_precheck'],'FAIL')
 def test_not_runtime_or_approval(self):
  result=run('sprite',self.sprite());self.assertEqual(result['runtime_PMDO'],'NOT_TESTED');self.assertEqual(result['SpriteCollab_acceptance'],'NOT_EVALUATED')
if __name__=='__main__':unittest.main()
