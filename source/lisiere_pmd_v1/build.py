"""One forest-edge entrance: five generated semantic layers + native light tracks.
No old map is overwritten. Only generated art is resized/palette-aligned.
"""
from pathlib import Path
import sys,io,json,zipfile,hashlib,subprocess,shutil
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent;O=R/'renders/lisiere_pmd_v1';C=R/'.cache/lisiere_pmd_v1';P=C/'pack';SIZE=(480,336)
sys.path.insert(0,str(R/'source/dungeon_biomes_v1'))
from red import decode,palettes
from release import output_path
N=C/'native/data/map_bg'
OLDPACK=R/'renders/dungeon_biomes_v1/DB1_cinq_duos_multicalques.zip'

def sha(b):return hashlib.sha256(b).hexdigest()
def raw(key):
 records=json.loads((S/'raws/archive.json').read_text());rec=next(r for r in records if r['id']==key);p=R/rec['path']
 b=p.read_bytes() if p.exists() else subprocess.check_output(['git','show',rec['commit']+':'+rec['path']],cwd=R)
 assert sha(b)==rec['sha256'];return Image.open(io.BytesIO(b)).convert('RGBA')

def png(im,path):
 path.parent.mkdir(parents=True,exist_ok=True);a=np.array(im.convert('RGBA'));col,inv=np.unique(a.view(np.uint32).reshape(-1),return_inverse=True)
 if len(col)<=256:
  rgba=col.astype(np.uint32).view(np.uint8).reshape(-1,4);q=Image.fromarray(inv.reshape(a.shape[:2]).astype(np.uint8),'P');q.putpalette(rgba[:,:3].tobytes());q.info['transparency']=rgba[:,3].tobytes();q.save(path,optimize=True)
 elif (a[:,:,3]==255).all():Image.fromarray(a[:,:,:3]).save(path,optimize=True)
 else:im.save(path,optimize=True)
 assert Image.open(path).convert('RGBA').tobytes()==a.tobytes()

def save(im,name):png(im,P/name);return name

def palette_reference():
 with zipfile.ZipFile(OLDPACK) as z:ref=Image.open(io.BytesIO(z.read('references/DB1_native_H07P03.png'))).convert('RGBA')
 a=np.array(ref);col=np.unique(a[:,:,:3][a[:,:,3]>0],axis=0);pal=Image.new('P',(1,1));pal.putpalette(np.vstack([col,np.tile(col[0],(256-len(col),1))]).astype(np.uint8).tobytes());return pal,col,ref

def keyed(key):
 im=raw(key).resize(SIZE,Image.Resampling.NEAREST);a=np.array(im);r,g,b=np.moveaxis(a[:,:,:3].astype(np.int16),2,0)
 matte=(r>120)&(b>100)&(g<130)&(r>g*1.6)&(b>g*1.5);a[matte]=0
 pal,_,_=palette_reference();q=np.array(Image.fromarray(a[:,:,:3]).quantize(palette=pal,dither=Image.Dither.NONE).convert('RGBA'));q[:,:,3]=a[:,:,3];q[q[:,:,3]==0]=0
 return Image.fromarray(q)

def static_layers():
 fond=keyed('fond');sol=keyed('sol')
 # Crop only the generated northern grass extension; the far forest owns this
 # depth interval. The walkable near plane remains filled underneath objects.
 sol.paste((0,0,0,0),(0,0,480,96))
 trees=keyed('arbres_detoures');plants=keyed('vegetation');source=keyed('rochers');rocks=Image.new('RGBA',SIZE)
 placements=[]
 for box,size,xy in [((0,0,240,168),(40,32),(128,192)),((240,0,480,168),(40,32),(312,192)),((0,168,240,336),(32,64),(64,224)),((240,168,480,336),(32,64),(384,224))]:
  part=source.crop(box);bb=part.getbbox();assert bb;part=part.crop(bb).resize(size,Image.Resampling.NEAREST);rocks.alpha_composite(part,xy)
  placements.append({'source_region':box,'tight_bbox':bb,'size':size,'position':xy,'scope':'complete generated rock group, not native pixels'})
 return [('01_fond_forestier',fond),('02_sol_continu',sol),('03_rochers',rocks),('04_arbres_racines',trees),('05_vegetation_basse',plants)],placements

@lru_cache(maxsize=32)
def native(name,tick=0):return decode(name,tick,N)
def color(name,idx,tick):
 p,_=palettes((N/(name+'.bpl')).read_bytes(),tick);bank=np.zeros((256,4),np.uint8);bank[:len(p)*16]=p.reshape(-1,4)
 assert not ((idx//16>=len(p))&(idx%16!=0)).any();return Image.fromarray(bank[idx])

def forest_parts(b,p):
 idx=native('H07P04W',b*7)[2][0];a=np.array(color('H07P04W',idx,p*8));particle=np.isin(idx%16,[1,14,15]);rays=a.copy();rays[particle]=0;mot=a.copy();mot[~particle]=0
 return Image.fromarray(rays),Image.fromarray(mot)

def additive(base,over):
 b=np.array(base).astype(np.uint16);o=np.array(over).astype(np.uint16);b[:,:,:3]=np.minimum((b[:,:,:3]>>3)+((o[:,:,:3]>>3)*(o[:,:,3:4]>0)),31)*255//31
 return Image.fromarray(b.astype(np.uint8))

def scene(layers,tick=64,light=True):
 out=Image.new('RGBA',SIZE,(4,44,12,255))
 for _,im in layers:out.alpha_composite(im)
 if light:
  a,b=forest_parts((tick//7)%14,(tick//8)%32);effect=Image.alpha_composite(a,b);out=additive(out,effect)
 return out


def effects():
 rays=[];particles=[]
 for p in range(32):rays.append(save(forest_parts(0,p)[0],f'06_lumiere/rayons/LE1_rayons_{p:02d}.png'))
 for b in range(14):particles.append(save(forest_parts(b,0)[1],f'06_lumiere/particules/LE1_particules_{b:02d}.png'))
 falls=[];idx=native('H26P01')[2][0];mask=idx//16==4;labels,n=ndimage.label(mask);assert n==6
 for i,sl in enumerate(ndimage.find_objects(labels)):
  y,x=sl;box=(x.start,y.start,x.stop,y.stop);frames=[]
  for f in range(8):
   a=np.array(color('H26P01',idx,f*3));a[labels!=i+1]=0;im=Image.fromarray(a).crop(box)
   assert im.width%8==im.height%8==0
   frames.append(save(im,f'bonus_lave/cascade_{i+1}/LE1_cascade_{i+1}_{f:02d}.png'))
  falls.append({'id':i+1,'source_box':box,'frames':frames,'frame_ticks':3,'period_ticks':24,'scale':1,'blend':'normal-over','note':'ceiling-connected native column, including native foot/halo pixels; no invented offscreen top'})
 return {'rayons':{'frames':rays,'frame_ticks':8,'period_ticks':256,'blend':'add RGB555 16/16','source':'H07P04W BPL, indices2..13'},'particules':{'frames':particles,'frame_ticks':7,'period_ticks':98,'blend':'add RGB555 16/16','source':'H07P04W BPA, indices1/14/15; palette verified invariant'},'cascades':falls,'combined_forest_period_ticks':12544,'phase':'steady-state tick0 convention, no emulator startup capture','preview_hz':60}

def duration_ticks(ticks,dt):return [round((t+dt)*1000/60)-round(t*1000/60) for t in ticks]
def webp(frames,path,ticks,dt,loop):
 frames[0].convert('RGB').save(path,save_all=True,append_images=[i.convert('RGB')for i in frames[1:]],duration=duration_ticks(ticks,dt),loop=loop,lossless=False,quality=65,minimize_size=True,method=6)

def build():
 O.mkdir(parents=True,exist_ok=True);C.mkdir(parents=True,exist_ok=True)
 if P.exists():shutil.rmtree(P)
 P.mkdir()
 with zipfile.ZipFile(OLDPACK) as z:
  native_bytes=z.read('native_sources.zip');audit=json.loads(z.read('audit.json'))
 with zipfile.ZipFile(io.BytesIO(native_bytes)) as z:z.extractall(C/'native')
 layers,placements=static_layers();paths=[save(im,'calques/LE1_'+name+'.png')for name,im in layers]
 anim=effects();ticks=list(range(0,256,8));frames=[scene(layers,t)for t in ticks]
 png(scene(layers),O/'LE1_lisiere.png');png(scene(layers,light=False),P/'apercus/LE1_sans_lumiere.png')
 webp(frames,output_path('LE1_lisiere_animee.webp'),ticks,8,1)
 # A separate true 24tick loop for the lava columns, never put into this forest.
 lava_frames=[]
 for f in range(8):
  im=Image.new('RGBA',(320,208),'#311e16');d=ImageDraw.Draw(im);d.text((8,8),'Cascades PMD : 8 phases / 400 ms',fill='#ffda73')
  x=8
  for rec in anim['cascades']:
   cut=Image.open(P/rec['frames'][f]).convert('RGBA');im.alpha_composite(cut,(x,32));x+=cut.width+8
  lava_frames.append(im)
 png(lava_frames[0],P/'apercus/LE1_cascades.png');webp(lava_frames,O/'LE1_cascades_animees.webp',list(range(0,24,3)),3,0)
 # Layer board is in the ZIP, not another duplicate heavyweight public asset.
 board=Image.new('RGB',(960,1128),'#132519');draw=ImageDraw.Draw(board)
 panel=layers+[('06_lumiere_PMD',Image.alpha_composite(*forest_parts(0,8)))]
 for i,(name,im) in enumerate(panel):
  x=(i%2)*480;y=(i//2)*376;draw.text((x+12,y+10),name,fill='#d2e9b2');bg=Image.new('RGBA',SIZE,'#173c23');bg.alpha_composite(im);board.paste(bg.convert('RGB'),(x,y+32))
 png(board,P/'apercus/LE1_six_calques.png')
 # Presentation thumbnail only; import layers and the full board stay at1x.
 small=Image.new('RGB',(720,848),'#132519');small.paste(board.resize((720,846),Image.Resampling.NEAREST),(0,0));png(small,O/'LE1_calques_apercu.png')
 manifest={'version':1,'map':'lisiere_foret_envahie_entree','size':SIZE,'groups':paths+[{'id':'06_lumiere','tracks':['rayons','particules']}],'static_layers':paths,'animations':anim,'generated_palette_reference':'H07P03, 76 visible native colours; only generated art palette-aligned','rock_placements':placements,'walkability_guides':{'arrival_south':[240,312],'forest_entrance_north':[240,144],'status':'pixel-space suggestions only, no engine warp/collision entities'},'light_reuse':'Native H07P04W light re-used as an explicit design choice; H07P03 is not claimed to possess this animation originally.','native_changes':'None after source decoding except selecting transparent masks and cropping each complete visible cascade window; intrinsic BPC flips belong to the original map.','preview':{'ticks':ticks,'duration_ms':sum(duration_ticks(ticks,8)),'loop':1,'scope':'sampled excerpt, not the complete209s combined forest cycle','compression':'presentation WebP lossy; all import PNG pixels lossless'},'limitations':['Not a PMDO/PC-port runtime validation or artistic approval.','Generated border trees are canvas-anchored scenery, not complete offscreen tree sprites.','Native lava columns have a source foot/halo; no invented upper connection.'],'source_audit':{'port_repo':audit['port_repo'],'port_commit':audit['port_commit'],'native_archive_sha256':sha(native_bytes),'files':[r for r in audit['files'] if any(n in r['path']for n in ['H07P03','H07P04W','H26P01'])]},'prior_work_preserved':True}
 (P/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n');(O/'manifest.json').write_text(json.dumps({k:v for k,v in manifest.items()if k not in ['animations','source_audit']},indent=2,ensure_ascii=False)+'\n')
 shutil.copy2(S/'assemble.py',P/'assemble.py');shutil.copy2(S/'PACK_README.md',P/'README.md');shutil.copy2(S/'PACK_README.md',O/'README.md')
 with zipfile.ZipFile(output_path('LE1_lisiere_calques_et_effets.zip'),'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(P.rglob('*')):
   if p.is_file():
    zi=zipfile.ZipInfo(p.relative_to(P).as_posix(),(2026,9,21,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,p.read_bytes())
 if (S/'release.json').exists():
  records=json.loads((S/'release.json').read_text());links='\n## Téléchargements directs\n\n'+''.join('- ['+r['name']+']('+r['url']+')\n' for r in records)
  links+='\n[Planche des six groupes](LE1_calques_apercu.png) : aperçu réduit à75% ; les calques PNG du ZIP et sa planche complète restent à1×.\n\nCes deux fichiers lourds sont conservés à l’identique dans Git au commit indiqué par les liens. Le serveur et `release.py` les rematérialisent avec contrôle SHA-256 ; ce ne sont pas des fichiers perdus. Tous les calques PNG sont dans le ZIP.\n'
  (O/'README.md').write_text((O/'README.md').read_text()+links)
 print('Built one map; five generated layers, two native light tracks, six lava modules')
 for p in O.iterdir():print(p.name,p.stat().st_size)
if __name__=='__main__':build()
