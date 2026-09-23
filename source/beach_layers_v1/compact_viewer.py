"""Reuse existing PNGs in the repo viewer; compare against every embedded pixel first."""
from pathlib import Path
import base64,io,json
from PIL import Image
R=Path(__file__).resolve().parents[2];P=R/'apercu_beach_calques_v1.html';prefix='renders/beach_layers_v1/'
def compact():
 page=P.read_text();start=page.index('const DATA=')+len('const DATA=');data,length=json.JSONDecoder().raw_decode(page[start:]);count=0
 def image(uri,relative):
  nonlocal count
  if uri.startswith('data:'):
   with Image.open(io.BytesIO(base64.b64decode(uri.split(',',1)[1]))) as src,Image.open(R/relative) as dst:
    assert src.size==dst.size and src.convert('RGBA').tobytes()==dst.convert('RGBA').tobytes(),relative
  else:assert uri==relative
  count+=1;return relative
 for layer in data['layers']:layer['uri']=image(layer['uri'],prefix+'calques/BeachV1_'+layer['id']+'.png')
 data['surface']=[image(u,prefix+f'animation/mer/BeachV1_mer_{i:02d}.png') for i,u in enumerate(data['surface'])]
 data['foam']=[image(u,prefix+f'animation/ecume/BeachV1_ecume_{i:02d}.png') for i,u in enumerate(data['foam'])]
 data['reference']=image(data['reference'],prefix+'BeachV1_reference_recomposee.png')
 P.write_text(page[:start]+json.dumps(data,ensure_ascii=False)+page[start+length:]);print('PASS',count,'pixel-identical PNG references;',P.stat().st_size,'bytes')
if __name__=='__main__':compact()
