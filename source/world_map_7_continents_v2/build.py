from pathlib import Path
import hashlib,json,math,shutil
from PIL import Image,ImageDraw,ImageFilter,ImageChops

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/world_map_7_continents_v2'; RAW=ROOT/'source/world_map_7_continents_v2/raws/world_map_7_continents_generated.png'
LAY=OUT/'layers';ANIM=OUT/'animations';SPR=OUT/'assetsprite'
if OUT.exists(): shutil.rmtree(OUT)
for p in (LAY,ANIM,SPR): p.mkdir(parents=True,exist_ok=True)
raw=Image.open(RAW).convert('RGBA'); W,H=raw.size
# Seven semantic landmasses traced from the generated composition. These are masks, not claimed native segmentation.
continents=[
 ('Cendre',(180,80,515,490),[(180,85),(310,60),(470,115),(520,330),(430,465),(225,480),(120,320)]),
 ('Sylve',(670,80,855,315),[(700,75),(805,80),(880,180),(820,315),(700,280),(655,170)]),
 ('Aurore',(1110,80,1510,465),[(1160,105),(1380,70),(1515,180),(1450,380),(1230,460),(1090,305)]),
 ('Verdance',(540,345,1110,820),[(610,380),(850,340),(1080,465),(1070,720),(910,850),(620,775),(520,585)]),
 ('SylveSud',(150,650,570,1000),[(185,700),(360,650),(570,765),(500,960),(280,1015),(130,870)]),
 ('Lacs',(545,835,1110,1050),[(575,890),(790,825),(1030,870),(1110,1000),(900,1060),(620,1025)]),
 ('Cime',(1120,630,1510,990),[(1190,680),(1390,625),(1515,780),(1460,950),(1240,1000),(1090,825)]),
]
# The generator returned a larger canvas than the prompt reference; scale the traced masks to it.
SX, SY = W / 1536.0, H / 1056.0
continents=[(name,box,[(round(x*SX),round(y*SY)) for x,y in points]) for name,box,points in continents]
def mask_for(points):
 m=Image.new('L',(W,H),0);ImageDraw.Draw(m).polygon(points,fill=255);return m
masks=[mask_for(p) for _,_,p in continents]
allmask=Image.new('L',(W,H),0)
for m in masks: allmask=ImageChops.lighter(allmask,m)
# Fond layer: use an empty-looking parchment sample from the generated artwork and tile it, preserving its texture/DA.
patch=raw.crop((790,0,1080,260)).filter(ImageFilter.GaussianBlur(0.3)); fond=Image.new('RGBA',(W,H),(0,0,0,0))
for y in range(0,H,patch.height):
 for x in range(0,W,patch.width): fond.alpha_composite(patch,(x,y))
# Preserve ornamental border from raw while keeping continents out of the fond.
edge=raw.copy(); edge.putalpha(ImageChops.subtract(Image.new('L',(W,H),255),allmask)); fond.alpha_composite(edge)
fond.save(LAY/'00_fond_parchemin.png')
# Continents layer: generated map pixels isolated by semantic masks.
continents_layer=Image.new('RGBA',(W,H),(0,0,0,0)); continents_layer.paste(raw,(0,0),allmask); continents_layer.save(LAY/'01_continents_texture.png')
# Coasts, elevation and motif details stay independent.
coasts=Image.new('RGBA',(W,H),(0,0,0,0));d=ImageDraw.Draw(coasts)
for name,box,points in continents:
 d.line(points+[points[0]],fill=(112,76,49,235),width=6,joint='curve')
 d.line(points+[points[0]],fill=(246,214,158,145),width=2,joint='curve')
coasts.save(LAY/'02_cotes_et_motifs.png')
# Routes are new gameplay paths, separated from generated terrain.
centers=[(sum(x for x,y in points)//len(points),sum(y for x,y in points)//len(points)) for _,box,points in continents]
routes=Image.new('RGBA',(W,H),(0,0,0,0));rd=ImageDraw.Draw(routes)
for a,b in zip(centers,centers[1:]):
 rd.line((a,b),fill=(82,53,35,220),width=12);rd.line((a,b),fill=(250,218,155,230),width=4)
routes.save(LAY/'03_routes.png')
# Emblems and unlock state are separate, newly designed location markers.
emblems=Image.new('RGBA',(W,H),(0,0,0,0));state=Image.new('RGBA',(W,H),(0,0,0,0));ed=ImageDraw.Draw(emblems);sd=ImageDraw.Draw(state)
for i,(name,box,points) in enumerate(continents):
 x,y=centers[i]; unlocked=i<3
 ed.ellipse((x-34,y-34,x+34,y+34),fill=(71,47,31,255),outline=(246,211,143,255),width=5)
 ed.ellipse((x-24,y-24,x+24,y+24),fill=((76,141,82,255) if unlocked else (106,76,60,255)),outline=(255,235,178,255),width=3)
 ed.text((x,y),str(i+1),anchor='mm',fill=(255,242,193,255))
 sd.ellipse((x+25,y-5,x+39,y+9),fill=((55,160,77,255) if unlocked else (143,77,52,255)),outline=(255,225,155,255),width=2)
emblems.save(LAY/'04_emblemes_continents.png');state.save(LAY/'05_etat_deblocage.png')
# Full composition.
full=fond.copy()
for layer in (continents_layer,coasts,routes,emblems,state): full.alpha_composite(layer)
full.save(OUT/'WorldMap_7_Continents_Generated.png')
# Discovery animation: one more continent per frame, true independent PNGs.
frames=[]
for n in range(8):
 frame=fond.copy()
 if n:
  visible=Image.new('RGBA',(W,H),(0,0,0,0))
  for i in range(min(n,7)): visible.alpha_composite(Image.composite(continents_layer,Image.new('RGBA',(W,H),(0,0,0,0)),masks[i]))
  frame.alpha_composite(visible);frame.alpha_composite(coasts);frame.alpha_composite(routes)
  glow=Image.new('RGBA',(W,H),(0,0,0,0));gd=ImageDraw.Draw(glow)
  for i in range(min(n,7)):
   x,y=centers[i];pulse=4+int(3*(1+math.sin(n*math.pi/4))/2);gd.ellipse((x-42-pulse,y-42-pulse,x+42+pulse,y+42+pulse),outline=(255,239,143,170),width=5)
  frame.alpha_composite(glow)
 frame.save(ANIM/f'WorldMap_7Continents_v2_{n:02d}.png');frames.append(frame)
frames[0].save(ANIM/'WorldMap_7Continents_v2.webp',save_all=True,append_images=frames[1:],duration=150,loop=0,lossless=True)
# AssetSprite contact sheet: seven generated emblems, documented as generated UI assets.
sheet=Image.new('RGBA',(7*64,64),(0,0,0,0));entries=[]
for i,(name,box,points) in enumerate(continents):
 x,y=centers[i];icon=emblems.crop((x-34,y-34,x+34,y+34));sheet.alpha_composite(icon,(i*64,0));entries.append({'id':name.lower(),'rect':[i*64,0,64,64],'unlocked_by_default':i<3})
sheet.save(SPR/'WorldMap_7Continents_v2_AssetSprite.png');(SPR/'WorldMap_7Continents_v2_AssetSprite.json').write_text(json.dumps({'format':'AssetSprite','frame_size':[64,64],'entries':entries},ensure_ascii=False,indent=2))
state_contract={'format':'WorldMap7ContinentsGenerated','canvas_px':[W,H],'continents':[{'id':name.lower(),'label':name,'center_px':list(centers[i]),'unlocked_by_default':i<3} for i,(name,box,points) in enumerate(continents)],'layers':['00_fond_parchemin','01_continents_texture','02_cotes_et_motifs','03_routes','04_emblemes_continents','05_etat_deblocage'],'raw_generated_source':str(RAW.relative_to(ROOT))}
(OUT/'world_map_state.json').write_text(json.dumps(state_contract,ensure_ascii=False,indent=2))
files={}
for p in OUT.rglob('*'):
 if p.is_file(): files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps({'canvas_px':[W,H],'continents':7,'frames':8,'generated_source':str(RAW.relative_to(ROOT)),'notes':'Composition générée référencée par les images fournies; séparation par masques sémantiques, pas prétention de calques natifs.','files':files},ensure_ascii=False,indent=2))
print('built generated 7-continent layered map',W,H)
