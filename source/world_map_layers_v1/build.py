from pathlib import Path
import hashlib,json,math,shutil
import numpy as np
from PIL import Image,ImageDraw,ImageChops

ROOT=Path(__file__).resolve().parents[2]; RAW=ROOT/'source/world_map_layers_v1/raws'; REF=ROOT/'source/world_map_layers_v1_reference.png'
OUT=ROOT/'renders/world_map_layers_v1';LAY=OUT/'layers';ANIM=OUT/'animations';SPR=OUT/'assetsprite'
if OUT.exists():shutil.rmtree(OUT)
for p in (LAY,ANIM,SPR):p.mkdir(parents=True,exist_ok=True)

def key(im,tol=32):
 a=np.array(im.convert('RGBA'));sample=a[3,3,:3].astype(int);d=np.sqrt(((a[:,:,:3].astype(int)-sample)**2).sum(axis=2));a[:,:,3]=np.where(d<tol,0,a[:,:,3]);return Image.fromarray(a)
def paste(dst,im,box,center,scale=1.0):
 im=key(im).resize((int(im.width*scale),int(im.height*scale)),Image.Resampling.NEAREST);dst.alpha_composite(im,(int(center[0]-im.width/2),int(center[1]-im.height/2)))
# Generated parchment background layer, kept without motifs.
fond=Image.open(RAW/'fond_parchemin.png').convert('RGBA');W,H=fond.size;fond.save(LAY/'00_fond_sans_motifs.png')
# Continents are generated separately, then keyed and placed as one independent layer.
continents=key(Image.open(RAW/'continents_separes.png'),tol=34); continent_layer=Image.new('RGBA',(W,H),(0,0,0,0));continent_layer.alpha_composite(continents);continent_layer.save(LAY/'01_continents.png')
# Islands/continents extra detail uses the same generated continent source, separated as its own overlay.
islands=Image.new('RGBA',(W,H),(0,0,0,0));src=continents
for crop,center in [((0,0,420,250),(180,170)),((700,0,1260,260),(1000,150)),((0,430,530,840),(250,680)),((540,490,1260,840),(980,700))]:paste(islands,src.crop(crop),crop,center,0.55)
islands.save(LAY/'02_iles_et_archipels.png')
# Lieux/donjons: crop each generated motif separately, removing the printed labels by limiting crops above them.
places=Image.open(RAW/'lieux_donjons_emblemes.png').convert('RGBA');place_layer=Image.new('RGBA',(W,H),(0,0,0,0))
place_defs=[('reverie_town','Reverie Town',(30,15,420,285),(170,690),0.36),('harbor','Harbor',(420,15,850,245),(590,300),0.34),('forest_shrine','Forest Shrine',(840,15,1260,245),(1040,180),0.34),('desert_outpost','Desert Outpost',(960,15,1260,245),(1110,450),0.32),('observatory','Snowy Observatory',(420,280,850,525),(1120,100),0.32),('volcanic_fortress','Volcanic Fortress',(700,280,1000,525),(240,300),0.34),('ancient_ruins','Ancient Ruins',(970,280,1260,540),(830,520),0.32),('marsh_village','Marsh Village',(20,280,420,550),(460,760),0.34),('cave_entrance','Cave Entrance',(0,550,330,770),(760,760),0.34),('dungeon_gate','Dungeon Gate',(520,550,850,770),(920,780),0.30),('lighthouse','Lighthouse Island',(310,550,530,770),(1320,730),0.33)]
for keyname,label,crop,center,scale in place_defs:paste(place_layer,places.crop(crop),crop,center,scale)
place_layer.save(LAY/'03_lieux_villes_donjons.png')
# Routes and game state are independent of all generated art.
routes=Image.new('RGBA',(W,H),(0,0,0,0));rd=ImageDraw.Draw(routes);r=[(170,690),(460,760),(590,300),(830,520),(1110,450),(1320,730),(1120,100),(240,300)];rd.line(r,fill=(95,58,34,220),width=7);rd.line(r,fill=(250,220,157,220),width=2);routes.save(LAY/'04_routes.png')
state=Image.new('RGBA',(W,H),(0,0,0,0));sd=ImageDraw.Draw(state)
for i,(keyname,label,crop,(x,y),scale) in enumerate(place_defs):
 c=(57,160,78,255) if i<3 else (145,79,50,255);sd.ellipse((x-10,y-10,x+10,y+10),fill=(67,40,24,255),outline=(255,226,154,255),width=2);sd.ellipse((x-6,y-6,x+6,y+6),fill=c)
state.save(LAY/'05_etat_deblocage.png')
# Cloud overlay from separately generated cloud motifs, placed independently and animated.
cloudsrc=key(Image.open(RAW/'nuages_separes.png'),tol=30);clouds=Image.new('RGBA',(W,H),(0,0,0,0))
for crop,center,scale in [((0,0,420,260),(220,110),0.5),((420,0,850,260),(820,105),0.45),((850,0,1264,260),(1250,130),0.45),((0,260,420,520),(260,500),0.4),((850,260,1264,520),(1250,520),0.42)]:paste(clouds,cloudsrc.crop(crop),crop,center,scale)
clouds.save(LAY/'06_nuages_overlay.png')
full=fond.copy()
for l in (continent_layer,islands,place_layer,routes,state,clouds):full.alpha_composite(l)
full.save(OUT/'WorldMap_Layers_DA.png')
# True cloud animation frames: independent cloud overlays, opacity/position varied.
frames=[]
for i in range(8):
 overlay=Image.new('RGBA',(W,H),(0,0,0,0));overlay.alpha_composite(clouds,(int((i-3)*2),0));a=np.array(overlay);a[:,:,3]=(a[:,:,3].astype(float)*(0.72+0.2*(1+math.sin(i*math.pi/4))/2)).astype('uint8');overlay=Image.fromarray(a)
 frame=fond.copy()
 for l in (continent_layer,islands,place_layer,routes,state):frame.alpha_composite(l)
 frame.alpha_composite(overlay);frame.save(ANIM/f'WorldMap_clouds_{i:02d}.png');frames.append(frame)
frames[0].save(ANIM/'WorldMap_clouds.webp',save_all=True,append_images=frames[1:],duration=150,loop=0,lossless=True)
# AssetSprite metadata for places/dungeon entries.
sheet=Image.new('RGBA',(len(place_defs)*96,96),(0,0,0,0));entries=[]
for i,(keyname,label,crop,center,scale) in enumerate(place_defs):
 icon=key(places.crop(crop)).resize((96,96),Image.Resampling.NEAREST);sheet.alpha_composite(icon,(i*96,0));entries.append({'id':keyname,'label':label,'rect':[i*96,0,96,96],'map_position_px':list(center),'unlocked_by_default':i<3})
sheet.save(SPR/'WorldMap_Places_Donjons_AssetSprite.png');(SPR/'WorldMap_Places_Donjons_AssetSprite.json').write_text(json.dumps({'format':'AssetSprite','frame_size':[96,96],'entries':entries},ensure_ascii=False,indent=2))
state_contract={'format':'WorldMapLayeredDA','canvas_px':[W,H],'departure_place':'reverie_town','layers':['00_fond_sans_motifs','01_continents','02_iles_et_archipels','03_lieux_villes_donjons','04_routes','05_etat_deblocage','06_nuages_overlay'],'places':[{'id':k,'label':l,'position_px':list(c),'unlocked_by_default':i<3} for i,(k,l,crop,c,s) in enumerate(place_defs)]}
(OUT/'world_map_state.json').write_text(json.dumps(state_contract,ensure_ascii=False,indent=2))
files={}
for p in OUT.rglob('*'):
 if p.is_file():files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps({'canvas_px':[W,H],'layers':7,'places':len(place_defs),'cloud_frames':8,'generated_raws':[str(p.relative_to(ROOT)) for p in RAW.glob('*.png')],'files':files},ensure_ascii=False,indent=2));print('built layered DA map',W,H)
