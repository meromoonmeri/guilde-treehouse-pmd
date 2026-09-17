from pathlib import Path
import unittest,json,xml.etree.ElementTree as ET
from PIL import Image
import numpy as np
from source.vegetation_treehouse_v1.verify import verify
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/vegetation_treehouse_v1'
class VegetationTests(unittest.TestCase):
 def test_complete_precheck(self):self.assertEqual(verify()['technical_precheck'],'PASS')
 def test_tiled_subtiles_reconstruct_every_phase(self):
  root=ET.parse(OUT/'tilesheets/VT1_vegetation_8px.tsx').getroot();atlas=Image.open(OUT/'tilesheets'/root.find('image').get('source')).convert('RGBA')
  for f in range(4):
   rebuilt=Image.new('RGBA',(128,64))
   for tile in root.findall('tile'):
    base=int(tile.get('id'));tid=int(tile.findall('./animation/frame')[f].get('tileid'));x=tid%64*8;y=tid//64*8
    rebuilt.paste(atlas.crop((x,y,x+8,y+8)),(base%64*8,base//64*8))
   self.assertEqual(rebuilt.tobytes(),Image.open(OUT/'tilesheets'/f'VT1_vegetation_phase_{f}.png').convert('RGBA').tobytes())
 def test_pmdo_recipe_reconstructs_each_plant(self):
  recipe=json.loads((OUT/'placement_recipe.json').read_text())
  for obj in recipe['objects']:
   for f in range(4):
    rebuilt=Image.new('RGBA',(32,32))
    for cell in obj['cells']:
     frame=cell['frames'][f];sheet=Image.open(OUT/'tilesheets'/(frame['Sheet']+'.png'));x=frame['TexLoc']['X']*8;y=frame['TexLoc']['Y']*8;dx,dy=cell['local_cell'];rebuilt.paste(sheet.crop((x,y,x+8,y+8)),(dx*8,dy*8))
    self.assertEqual(rebuilt.tobytes(),Image.open(OUT/'plants'/f"VT1_{obj['id']}_phase_{f}.png").convert('RGBA').tobytes())
 def test_plain_foliage_has_no_purple_matte_colors(self):
  manifest=json.loads((OUT/'manifest.json').read_text());purple=set(map(tuple,manifest['palette'][10:14]))
  for obj in manifest['assets']:
   if obj['id']=='violet_bells':continue
   for f in range(4):
    a=np.array(Image.open(OUT/'plants'/f"VT1_{obj['id']}_phase_{f}.png").convert('RGBA'));visible=set(map(tuple,a[a[:,:,3]>0,:3]));self.assertFalse(visible&purple)
 def test_reference_and_completion_not_misrepresented(self):
  m=json.loads((OUT/'manifest.json').read_text());self.assertFalse(m['art_approved']);self.assertEqual(m['runtime_PMDO'],'NOT TESTED');self.assertEqual(m['runtime_Tiled'],'NOT TESTED');self.assertEqual(len(m['assets']),8)
  self.assertEqual(m['sequence'],[0,1,0,2]);self.assertEqual(m['duration_game_ticks'],[14]*4)
if __name__=='__main__':unittest.main()
