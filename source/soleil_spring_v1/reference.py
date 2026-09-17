from pathlib import Path
import json,math,hashlib
from PIL import Image
P=Path(__file__).resolve().parent/'references';o=json.loads((P/'luminous_spring.rsground').read_text(encoding='utf-8-sig'))['Object'];sheets={n:Image.open(P/(n+'.png')).convert('RGBA') for n in ['LuminousSpring','LuminousSpringAnim']}
frames=[]
for f in range(39):
 scene=Image.new('RGBA',(600,600))
 for li,l in enumerate(o['Layers']):
  im=Image.new('RGBA',(600,600))
  for x,col in enumerate(l['Tiles']):
   for y,t in enumerate(col):
    for a in t['Layers']:
     v=a['Frames'][(f*10//a['FrameLength'])%len(a['Frames'])];p=v['TexLoc'];tx,ty=p['X']*24,p['Y']*24;im.alpha_composite(sheets[v['Sheet']].crop((tx,ty,tx+24,ty+24)),(x*24,y*24))
  if f==0:im.save(P/f'halcyon_layer_{li}.png')
  if l['Visible']:scene.alpha_composite(im)
 frames.append(scene)
frames[0].save(P/'halcyon_reference.png');frames[0].save(P/'halcyon_animation.webp',save_all=True,append_images=frames[1:],duration=[167,167,166]*13,lossless=True,loop=0)
print('39 native phases, 600x600, LCM(3,13),10 ticks at60Hz')
