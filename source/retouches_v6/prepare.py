from pathlib import Path
import sys,json
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'source/cote_v5_expeditions'))
from audit_references import tiles,straight
p=ROOT/'.cache/forest-audit'
o=json.loads((p/'apricorn_grove_entrance.rsground').read_text(encoding='utf-8-sig'))['Object']
names={f['Sheet'] for l in o['Layers'] for c in l['Tiles'] for t in c for a in t['Layers'] for f in a['Frames']}
banks={n:tiles(p/(n+'.tile'))[1] for n in names};scene=Image.new('RGBA',(344,304))
for l in o['Layers']:
 im=Image.new('RGBA',scene.size)
 for x,c in enumerate(l['Tiles']):
  for y,t in enumerate(c):
   for a in t['Layers']:
    f=a['Frames'][0];pos=f['TexLoc'];im.alpha_composite(straight(banks[f['Sheet']][pos['X'],pos['Y']]),(x*8,y*8))
 if l['Visible']:scene=Image.alpha_composite(scene,im)
scene.save(p/'halcyon_apricorn_grove.png')
for kind in ['foret','grotte']:
 im=Image.new('RGB',(1024,768),'#ff00ff');d=ImageDraw.Draw(im);d.rectangle((0,0,511,383),fill='#65853c')
 d.polygon([(708,383),(832,383),(802,285),(757,190),(822,0),(742,0),(667,190),(714,290)],fill='#b99a62')
 color='#224e2d' if kind=='foret' else '#6d7760'
 d.polygon([(0,384),(511,384),(511,580),(435,580),(435,512),(343,500),(305,480),(305,460),(207,460),(207,480),(168,500),(85,512),(85,580),(0,580)],fill=color)
 for x in [20,420]:d.ellipse((x,435,x+70,540),fill=color)
 for x in [512,940]:d.ellipse((x,670,x+78,767),fill=color)
 im.save(p/(kind+'_guide.png'))
files=sorted(f for f in (ROOT/'renders/retouches_zones_v6').glob('[0-9]*.png') if not f.stem.endswith('_nuit'));b=Image.new('RGB',(1200,240*5),'#132330');d=ImageDraw.Draw(b)
for i,f in enumerate(files):
 for j,im in enumerate([Image.open(ROOT/'renders/metano_expeditions_actuel'/f.stem/'jour.png'),Image.open(f)]):
  im.thumbnail((288,207));x=(i%2)*600+j*300;y=(i//2)*240;b.paste(im,(x,y+24));d.text((x+4,y+3),f.stem+(' AVANT' if j==0 else ' RETOUCHE'),fill='white')
b.save(ROOT/'renders/retouches_zones_v6/AVANT_APRES.png')
