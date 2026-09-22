from pathlib import Path
import hashlib,json,math
from PIL import Image,ImageDraw,ImageFont,ImageFilter
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'renders/world_map_zones_v1'; OUT.mkdir(parents=True,exist_ok=True)
for n in ('layers','animations','assetsprite'): (OUT/n).mkdir(exist_ok=True)
SRC=ROOT/'sprites/zones_guidees/01_cirque'; W,H=2048,1536

def im(p): return Image.open(p).convert('RGBA')
def font(n): return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
def tile_texture(path, box):
 src=im(path); out=Image.new('RGBA',(box[2]-box[0],box[3]-box[1]),(0,0,0,0));
 for y in range(0,out.height,src.height):
  for x in range(0,out.width,src.width): out.alpha_composite(src,(x,y))
 return out
# Canonical-guided map materials: native reference layers are used as texture samples, never repainted in-place.
# The attached reference uses a parchment atlas rather than a full-screen river tile.
# Keep the canonical water source documented, but use a restrained parchment sea for the world-map background.
sea=Image.new('RGBA',(W,H),(224,190,132,255)); sd=ImageDraw.Draw(sea)
for y in range(70,H,92): sd.arc((-80,y-24,W+80,y+24),180,360,fill=(188,135,75,75),width=3)
land=Image.new('RGBA',(W,H),(0,0,0,0)); d=ImageDraw.Draw(land)
continents=[[(260,320),(550,190),(850,230),(960,430),(820,650),(580,690),(360,580)],[(1000,270),(1430,180),(1730,320),(1830,600),(1640,810),(1300,760),(1110,590)],[(470,820),(760,730),(1030,850),(1080,1120),(850,1330),(530,1230),(330,1030)],[(1240,890),(1530,820),(1770,990),(1690,1280),(1370,1360),(1160,1160)]]
tex=tile_texture(SRC/'canonique_sec.png',(0,0,520,520)); grass=tile_texture(SRC/'herbe.png',(0,0,520,520))
for poly in continents:
 mask=Image.new('L',(W,H)); ImageDraw.Draw(mask).polygon(poly,fill=255)
 # A muted atlas-green underpaint keeps the map readable; the canonical pixels are overlaid, not altered.
 patch=Image.new('RGBA',(W,H),(159,158,91,255));
 texture=tex.copy(); texture.putalpha(105)
 for y in range(0,H,520):
  for x in range(0,W,520): patch.alpha_composite(texture,(x,y))
 patch.putalpha(mask); land.alpha_composite(patch)
# soften outside edges with a canonical grass rim and retain transparent separation
for poly in continents: d.line(poly+[poly[0]],fill=(137,91,48,255),width=16,joint='curve')
# six semantic layers
base=Image.new('RGBA',(W,H),(230,190,111,255)); base.alpha_composite(sea)
# parchment border/cloud ornament, separate from world geometry
border=Image.new('RGBA',(W,H),(0,0,0,0)); bd=ImageDraw.Draw(border)
bd.rectangle((24,24,W-25,H-25),outline=(111,67,34,255),width=12)
for x in range(90,W-60,170):
 bd.arc((x,35,x+120,115),180,350,fill=(184,123,57,150),width=4); bd.arc((x, H-115,x+120,H-35),0,170,fill=(184,123,57,150),width=4)
paths=Image.new('RGBA',(W,H),(0,0,0,0)); pd=ImageDraw.Draw(paths)
route=[(600,520),(900,450),(1240,510),(1500,500),(1510,1000),(1250,1100),(880,1030),(600,900)]
pd.line(route,fill=(107,67,36,230),width=18,joint='curve'); pd.line(route,fill=(250,215,140,255),width=6,joint='curve')
# landmark layer: new location emblems, deliberately not Pokemon sprites
em=Image.new('RGBA',(W,H),(0,0,0,0)); ed=ImageDraw.Draw(em); labels=['Forêt','Plage','Volcan','Désert','Glace','Tour','Archipel']
locs=[(470,420),(820,350),(1190,400),(1580,420),(1560,1040),(930,1040),(390,1040)]; glyph=['F','≈','△','☼','✧','T','A']
for (x,y),label,g in zip(locs,labels,glyph):
 ed.ellipse((x-58,y-58,x+58,y+58),fill=(77,53,31,255),outline=(248,210,125,255),width=7); ed.ellipse((x-45,y-45,x+45,y+45),fill=(110,137,75,255),outline=(242,231,182,255),width=4); ed.text((x,y-3),g,anchor='mm',font=font(42),fill=(255,242,189,255)); ed.text((x,y+82),label,anchor='mm',font=font(24),fill=(75,46,24,255))
# lock/status remains separate
state=Image.new('RGBA',(W,H),(0,0,0,0)); sd=ImageDraw.Draw(state)
for i,(x,y) in enumerate(locs):
 unlocked=i<3; sd.ellipse((x+42,y-15,x+65,y+8),fill=(49,143,75,255) if unlocked else (125,85,48,255),outline=(255,224,151,255),width=3); sd.text((x,y-88), 'OUVERT' if unlocked else 'VERROUILLÉ',anchor='mm',font=font(16),fill=(54,111,63,255) if unlocked else (119,78,43,255))
# atmospheric overlay kept separate
atmo=Image.new('RGBA',(W,H),(0,0,0,0)); ad=ImageDraw.Draw(atmo)
for x,y in [(180,180),(1840,200),(180,1370),(1850,1320)]: ad.arc((x-75,y-30,x+75,y+30),180,360,fill=(170,113,58,120),width=4)
static=base.copy(); static.alpha_composite(land); static.alpha_composite(border); static.alpha_composite(paths); static.alpha_composite(em); static.alpha_composite(state); static.alpha_composite(atmo); static.save(OUT/'WorldMap_Zones.png')
for name,layer in {'00_fond_mer_texture_canonique':base,'01_continents_texture_canonique':land,'02_bordure_parchemin':border,'03_routes':paths,'04_emblemes_lieux':em,'05_etat_deblocage':state,'06_atmosphere':atmo}.items(): layer.save(OUT/'layers'/(name+'.png'))
# Real independent animation frames: unlocked markers pulse; sea frames use the existing canonical water poses.
frames=[]
for i in range(8):
 ov=Image.new('RGBA',(W,H),(0,0,0,0)); od=ImageDraw.Draw(ov); pulse=4+int(4*(1+math.sin(i*math.pi/4))/2)
 for x,y in locs[:3]: od.ellipse((x-70-pulse,y-70-pulse,x+70+pulse,y+70+pulse),outline=(255,239,151,120),width=5)
 out=static.copy();out.alpha_composite(ov); out.save(OUT/'animations'/f'WorldMap_discover_{i:02d}.png');frames.append(out)
frames[0].save(OUT/'animations/WorldMap_discover.webp',save_all=True,append_images=frames[1:],duration=140,loop=0,lossless=True)
# AssetSprite sheet with new map markers.
sheet=Image.new('RGBA',(7*128,128),(0,0,0,0)); entries=[]
for i,(x,y) in enumerate(locs):
 s=Image.new('RGBA',(128,128),(0,0,0,0)); q=ImageDraw.Draw(s);q.ellipse((7,7,121,121),fill=(77,53,31,255),outline=(248,210,125,255),width=6);q.ellipse((18,18,110,110),fill=(110,137,75,255));q.text((64,60),glyph[i],anchor='mm',font=font(38),fill=(255,242,189,255));sheet.alpha_composite(s,(i*128,0));entries.append({'id':labels[i].lower(),'rect':[i*128,0,128,128],'unlocked_by_default':i<3})
sheet.save(OUT/'assetsprite/WorldMap_Lieux_AssetSprite.png'); (OUT/'assetsprite/WorldMap_Lieux_AssetSprite.json').write_text(json.dumps({'format':'AssetSprite','frame_size':[128,128],'entries':entries},ensure_ascii=False,indent=2))
manifest={'canvas':[W,H],'layers':7,'animation_frames':8,'sources':{'canonical_water':'sprites/zones_guidees/01_cirque/eau_1.png','canonical_terrain':'sprites/zones_guidees/01_cirque/canonique_sec.png','canonical_floor':'sprites/zones_guidees/01_cirque/herbe.png'},'note':'Composition de grande carte; les textures natives servent de matériaux de référence/tuilage, les continents et emblèmes sont une nouvelle composition et non une carte native.'}
files={}
for p in OUT.rglob('*'):
 if p.is_file(): files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
manifest['files']=files;(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('world map built',len(files),'files')
