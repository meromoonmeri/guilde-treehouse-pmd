from pathlib import Path
import hashlib, json, math, shutil
from PIL import Image, ImageDraw, ImageFont, ImageChops

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/world_map_7_continents_v1'; LAY=OUT/'layers'; ANIM=OUT/'animations'; SPR=OUT/'assetsprite'
if OUT.exists(): shutil.rmtree(OUT)
for p in (LAY,ANIM,SPR): p.mkdir(parents=True,exist_ok=True)
WORLD=ROOT/'Explorers_of_Sky_-_World_Map.png'; ATLAS=ROOT/'MapAssetsPMD2.webp'
SCALE=2
native=Image.open(WORLD).convert('RGBA'); W,H=native.width*SCALE,native.height*SCALE
base=native.resize((W,H),Image.Resampling.NEAREST)
atlas=Image.open(ATLAS).convert('RGBA')
# The supplied atlas has black transparency; this is only alpha cleanup, not recoloring.
pix=atlas.load()
for y in range(atlas.height):
 for x in range(atlas.width):
  r,g,b,a=pix[x,y]
  if r<18 and g<18 and b<18: pix[x,y]=(0,0,0,0)

def F(n): return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
def poly(points): return [(x*SCALE,y*SCALE) for x,y in points]
# Seven distinct landmasses, laid out on the canonical parchment canvas.
continents=[
 ('Cendre', 'volcan', [(18,35),(52,22),(85,32),(91,62),(70,84),(35,78),(16,59)], (30,0,116,157), True),
 ('Sylve', 'foret', [(123,18),(173,12),(204,27),(211,60),(190,78),(149,73),(126,52)], (620,0,780,145), True),
 ('Aurore', 'glace', [(270,10),(315,16),(334,43),(320,70),(280,67),(259,44)], (1135,315,1320,510), True),
 ('Dunes', 'desert', [(382,47),(429,39),(466,57),(470,89),(445,111),(399,102),(375,78)], (495,190,640,315), False),
 ('Archipel', 'plage', [(40,144),(72,127),(103,141),(110,168),(91,184),(57,177),(38,161)], (365,0,480,92), True),
 ('Marais', 'ruines', [(147,166),(185,150),(218,169),(220,198),(194,217),(157,208),(140,187)], (680,116,860,275), False),
 ('Cime', 'tour', [(270,208),(308,190),(346,207),(355,238),(335,263),(294,264),(266,239)], (970,12,1100,170), False),
]
# 00: exact canonical parchment/landscape reference at 2x; source remains in manifest.
base.save(LAY/'00_fond_canonique_2x.png')
continent_layer=Image.new('RGBA',(W,H),(0,0,0,0)); cd=ImageDraw.Draw(continent_layer)
for name,key,points,box,unlocked in continents:
 p=poly(points); cd.polygon(p,fill=(190,156,85,245),outline=(105,66,35,255),width=5*SCALE)
 # canonical-guided texture sample: crop from supplied asset atlas, nearest-neighbor tiled inside each continent mask.
 mask=Image.new('L',(W,H),0); ImageDraw.Draw(mask).polygon(p,fill=205)
 crop=atlas.crop(box)
 if crop.width and crop.height:
  crop=crop.resize((max(1,crop.width//3),max(1,crop.height//3)),Image.Resampling.NEAREST)
  tex=Image.new('RGBA',(W,H),(0,0,0,0))
  for yy in range(0,H,crop.height):
   for xx in range(0,W,crop.width): tex.alpha_composite(crop,(xx,yy))
  tex.putalpha(ImageChops.multiply(tex.getchannel('A'), mask)); continent_layer.alpha_composite(tex)
continent_layer.save(LAY/'01_continents_7_silhouettes.png')
# 02: explicit coast/relief boundary.
coasts=Image.new('RGBA',(W,H),(0,0,0,0)); q=ImageDraw.Draw(coasts)
for name,key,points,box,unlocked in continents:
 p=poly(points); q.line(p+[p[0]],fill=(91,54,31,255),width=3*SCALE,joint='curve')
 # inner contour provides visual separation without cooking a map character.
 q.line(poly(points[1:-1]),fill=(247,216,142,110),width=1*SCALE,joint='curve')
coasts.save(LAY/'02_cotes_et_reliefs.png')
# 03: small canonical-derived terrain stamps inside each continent.
relief=Image.new('RGBA',(W,H),(0,0,0,0)); rd=ImageDraw.Draw(relief)
for i,(name,key,points,box,unlocked) in enumerate(continents):
 x=sum(a for a,b in points)//len(points)*SCALE; y=sum(b for a,b in points)//len(points)*SCALE
 rd.ellipse((x-12*SCALE,y-8*SCALE,x+12*SCALE,y+8*SCALE),fill=((117,87,44,150) if i%2 else (70,118,74,170)),outline=(255,225,151,210),width=1*SCALE)
 rd.text((x,y),str(i+1),anchor='mm',font=F(9*SCALE),fill=(255,245,196,255))
relief.save(LAY/'03_repères_continents.png')
# 04: routes between the seven continents, separate gameplay layer.
routes=Image.new('RGBA',(W,H),(0,0,0,0)); r=ImageDraw.Draw(routes)
centers=[(sum(a for a,b in pts)//len(pts)*SCALE,sum(b for a,b in pts)//len(pts)*SCALE) for _,_,pts,_,_ in continents]
for a,b in zip(centers,centers[1:]):
 r.line((a,b),fill=(70,43,26,210),width=5*SCALE); r.line((a,b),fill=(249,216,137,240),width=2*SCALE)
routes.save(LAY/'04_routes.png')
# 05: unlock state, independent from geometry.
state=Image.new('RGBA',(W,H),(0,0,0,0)); s=ImageDraw.Draw(state)
for i,((name,key,pts,box,unlocked),(x,y)) in enumerate(zip(continents,centers)):
 col=(55,151,73,255) if unlocked else (137,82,46,255)
 s.ellipse((x-8*SCALE,y-8*SCALE,x+8*SCALE,y+8*SCALE),fill=(52,33,20,255),outline=(255,223,139,255),width=2*SCALE)
 s.ellipse((x-5*SCALE,y-5*SCALE,x+5*SCALE,y+5*SCALE),fill=col)
 s.text((x,y+13*SCALE),name,anchor='ma',font=F(7*SCALE),fill=(71,43,24,255))
state.save(LAY/'05_etat_deblocage.png')
# 06: labels are a separate UI layer.
labels=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(labels)
for i,((name,key,pts,box,unlocked),(x,y)) in enumerate(zip(continents,centers)):
 ld.text((x,y-15*SCALE),f'CONTINENT {i+1}',anchor='ms',font=F(6*SCALE),fill=(83,49,25,210))
labels.save(LAY/'06_labels.png')
# Composition preview.
full=base.copy()
for layer in (continent_layer,coasts,relief,routes,state,labels): full.alpha_composite(layer)
full.save(OUT/'WorldMap_7_Continents.png')
# Discovery animation: each frame reveals one more continent, true independent PNGs.
frames=[]
for n in range(8):
 frame=base.copy()
 if n:
  for layer in (continent_layer,coasts,relief,routes): frame.alpha_composite(layer)
  visible=Image.new('RGBA',(W,H),(0,0,0,0)); vd=ImageDraw.Draw(visible)
  for i,((name,key,pts,box,unlocked),center) in enumerate(zip(continents,centers)):
   if i<n: vd.ellipse((center[0]-14*SCALE,center[1]-14*SCALE,center[0]+14*SCALE,center[1]+14*SCALE),outline=(255,239,142,220),width=2*SCALE)
  frame.alpha_composite(visible)
 frame.save(ANIM/f'WorldMap_7continents_discover_{n:02d}.png'); frames.append(frame)
frames[0].save(ANIM/'WorldMap_7continents_discover.webp',save_all=True,append_images=frames[1:],duration=150,loop=0,lossless=True)
# AssetSprite: seven numbered continent markers plus source boxes.
sheet=Image.new('RGBA',(7*48,48),(0,0,0,0)); entries=[]
for i,((name,key,pts,box,unlocked)) in enumerate(continents):
 icon=Image.new('RGBA',(48,48),(0,0,0,0)); idr=ImageDraw.Draw(icon); idr.ellipse((4,4,44,44),fill=(75,48,27,255),outline=(247,210,127,255),width=2); idr.text((24,24),str(i+1),anchor='mm',font=F(18),fill=(255,238,175,255)); sheet.alpha_composite(icon,(i*48,0)); entries.append({'id':key,'continent':name,'rect':[i*48,0,48,48],'unlocked_by_default':unlocked})
sheet.save(SPR/'WorldMap_7Continents_AssetSprite.png'); (SPR/'WorldMap_7Continents_AssetSprite.json').write_text(json.dumps({'format':'AssetSprite','frame_size':[48,48],'entries':entries},ensure_ascii=False,indent=2))
state_contract={'format':'WorldMap7Continents','canvas_px':[W,H],'native_reference_px':[504,336],'continents':[{'id':key,'name':name,'index':i+1,'center_px':list(centers[i]),'unlocked_by_default':unlocked} for i,(name,key,pts,box,unlocked) in enumerate(continents)],'layers':['00_fond_canonique_2x','01_continents_7_silhouettes','02_cotes_et_reliefs','03_repères_continents','04_routes','05_etat_deblocage','06_labels']}
(OUT/'world_map_7_continents_state.json').write_text(json.dumps(state_contract,ensure_ascii=False,indent=2))
files={}
for p in OUT.rglob('*'):
 if p.is_file(): files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
manifest={'canvas_px':[W,H],'native_reference':'Explorers_of_Sky_-_World_Map.png','scale':'nearest 2x preview; native source preserved','continents':7,'animation_frames':8,'asset_source':'MapAssetsPMD2.webp','files':files,'provenance':'Fond canonique fourni; continents, routes, reliefs et etat sont des calques de composition separes. Les textures atlas sont prelevees et normalisees nearest-neighbor, pas declarees pixels natifs de la carte.'}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)); print('built 7-continent map',W,H)
