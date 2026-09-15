from pathlib import Path
import sys,json,re,math,hashlib,io
import numpy as np
from PIL import Image
from sources import SOURCES
R=Path(__file__).resolve().parents[2];P=Path(__file__).parent/'references';O=R/'renders/donjons_dtef_v2';O.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'source/cote_v5_expeditions'));from audit_references import tiles,straight
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
text=(R/'source/dungeon_autotiles_v1/references/engine/DtefImportHelper.cs').read_text();mapping=[int(x,16) if x.startswith('0x') else -1 for x in re.search(r'FieldDtefMapping\s*=\s*\{(.*?)\}',text,re.S).group(1).replace('\n','').replace(' ','').split(',') if x];assert len(mapping)==48;slots={m:i for i,m in enumerate(mapping) if m>=0}
banks={}
for path in (P/'DumpAsset/Content/Tile').glob('*.tile'):
 size,b,_=tiles(path);assert size==24;banks[path.stem]={xy:straight(im) for xy,im in b.items()}
manifest=dict(mapping=mapping,layout='Wall / Secondary / Floor; 6x8 cells per type; 432x192 pixels',tile_px=24,runtime_validated=False,themes=[]);report=[]
for theme,source in SOURCES.items():
 sheets={};groups={};spec={};records=[];checks=0
 for typ,kind in enumerate(['wall','secondary','floor']):
  obj=json.loads((P/'DumpAsset/Data/AutoTile'/f'{source}_{kind}.json').read_text(encoding='utf-8-sig'))['Object']['Tiles']
  for slot,mask in enumerate(mapping):
   if mask<0:continue
   for vi,layers in enumerate(obj[f'Tilex{mask:02X}']):
    assert vi<3
    for li,l in enumerate(layers):
     assert li>0 or len(l['Frames'])==1
     group=(typ,li,len(l['Frames']),l['FrameLength'])
     if li and group not in groups:groups[group]=len(groups)
     gl=groups.get(group,-1)
     for fi,f in enumerate(l['Frames']):
      name=f'tileset_{vi}.png' if li==0 else f'tileset_{vi}_frame{gl}_{fi}.{l["FrameLength"]}.png'
      if name not in sheets:sheets[name]=Image.new('RGBA',(432,192))
      xy=((typ*6+slot%6)*24,slot//6*24);cell=banks[f['Sheet']][f['TexLoc']['X'],f['TexLoc']['Y']];sheets[name].alpha_composite(cell,xy);records.append(dict(file=name,xy=xy,source=f,layer=li,mask=mask,variant=vi,type=kind))
      if li:spec[f'{vi}:{gl}']=dict(count=len(l['Frames']),duration=l['FrameLength'])
 for v in range(3):sheets.setdefault(f'tileset_{v}.png',Image.new('RGBA',(432,192)))
 ref=O/'references_dtef'/source;ref.mkdir(parents=True,exist_ok=True)
 for name,im in sheets.items():im.save(ref/name)
 # Verify exact native extraction before any texturing.
 for rec in records:
  x,y=rec['xy'];f=rec['source'];assert np.array_equal(np.array(sheets[rec['file']].crop((x,y,x+24,y+24))),np.array(banks[f['Sheet']][f['TexLoc']['X'],f['TexLoc']['Y']]));checks+=1
 changed={name:im.copy() for name,im in sheets.items()};bomb_records=[]
 # All original variation occupancy remains intact. Only static, fully connected floor variants1/2 receive stamps.
 slot=slots[255];sx=(12+slot%6)*24;sy=slot//6*24;box=(sx,sy,sx+24,sy+24);donors=[np.array(sheets[f'tileset_{v}.png'].crop(box)) for v in range(3)]
 if theme not in ['volcan','illuminant_reference']:
  rng=np.random.default_rng(int(hashlib.sha256(theme.encode()).hexdigest()[:8],16))
  for v in [1,2]:
   name=f'tileset_{v}.png';a=np.array(changed[name]);cell=a[sy:sy+24,sx:sx+24];base=cell.copy()
   if not np.all(cell[:,:,3]==255):continue
   for k in range(5):
    donor=int(rng.integers(0,3));dx,dy=map(int,rng.integers(5,15,size=2));tx,ty=map(int,rng.integers(5,15,size=2));w=5;stamp=donors[donor][dy:dy+w,dx:dx+w];yy,xx=np.mgrid[:w,:w];mask=((xx-2)**2+(yy-2)**2<=5)&(stamp[:,:,3]==255)
    cell[ty:ty+w,tx:tx+w][mask]=stamp[mask];bomb_records.append(dict(variant=v,donor_variant=donor,donor_xy=[dx,dy],target_xy=[tx,ty],size=5))
   border=np.ones((24,24),bool);border[4:20,4:20]=False;assert np.array_equal(cell[border],base[border]);changed[name]=Image.fromarray(a)
 yy,xx=np.mgrid[:192,:432];gasket=(xx%24<4)|(xx%24>=20)|(yy%24<4)|(yy%24>=20)
 for name,im in changed.items():
  a=np.array(im);b=np.array(sheets[name]);assert np.array_equal(a[:,:,3],b[:,:,3]);assert np.array_equal(a[gasket],b[gasket]);
  if '_frame' in name:assert np.array_equal(a,b)
  for t in range(3):assert not a[48:72,(t*6+5)*24:(t*6+6)*24,3].any()
 periods=[v['count']*v['duration'] for v in spec.values()];entry=dict(id=theme,source=source,files=list(changed),animation_layers=spec,cycle_game_frames=math.lcm(*periods) if periods else 1,native_records=checks,bomb_stamps=bomb_records)
 # Dungeon stress test: use actual PMDO neighbor bit order. No remapped generic 8-column sheet.
 grid=np.zeros((18,24),dtype='uint8');grid[2:8,2:10]=2;grid[2:8,13:22]=2;grid[11:16,4:20]=2;grid[4:6,8:15]=2;grid[6:14,6:8]=2;grid[6:14,17:19]=2;grid[3:6,3:6]=1;grid[12:15,11:17]=1
 def code(x,y,t):
  def q(dx,dy):return not(0<=x+dx<24 and 0<=y+dy<18) or grid[y+dy,x+dx]==t
  bits=[q(0,1),q(-1,0),q(0,-1),q(1,0)];m=sum(1<<i for i,b in enumerate(bits) if b)
  for i,(dx,dy) in enumerate([(-1,1),(-1,-1),(1,-1),(1,1)]):
   if bits[i] and bits[(i+1)%4] and q(dx,dy):m|=1<<(i+4)
  return m
 demo=[];rng=np.random.default_rng(875)
 for y in range(18):
  for x in range(24):
   typ=int(grid[y,x]);mask=code(x,y,typ) if typ!=2 else 255;slot=slots[mask];sx=(typ*6+slot%6)*24;sy=slot//6*24;box=(sx,sy,sx+24,sy+24);choices=[v for v in range(3) if changed[f'tileset_{v}.png'].crop(box).getbbox()];v=int(rng.choice(choices)) if choices else 0;demo.append([x*24,y*24,sx,sy,v])
 entry['demo_tiles']=demo
 def render(bank,tick,force0=False):
  out=Image.new('RGBA',(576,432))
  for x,y,sx,sy,v in demo:
   if force0:v=0
   box=(sx,sy,sx+24,sy+24);out.alpha_composite(bank[f'tileset_{v}.png'].crop(box),(x,y))
   for key,s in spec.items():
    av,layer=map(int,key.split(':'))
    if av==v:out.alpha_composite(bank[f'tileset_{v}_frame{layer}_{tick//s["duration"]%s["count"]}.{s["duration"]}.png'].crop(box),(x,y))
  return out
 for mode in ['jour','nuit']:
  name=f'd2_{theme}_{mode}';D=O/'RAW/TileDtef'/name;D.mkdir(parents=True,exist_ok=True);bank={n:night(im) if mode=='nuit' else im for n,im in changed.items()}
  for n,im in bank.items():im.save(D/n)
  A=O/'apercus'/name;A.mkdir(parents=True,exist_ok=True);preview=bank['tileset_0.png'].copy()
  for n,im in bank.items():
   if re.match(r'tileset_0_frame\d+_0\.',n):preview.alpha_composite(im)
  preview.save(A/'DTEF_COMPOSE.png');render(bank,0).save(A/'COMPOSITION.png');render(bank,0,True).save(A/'SANS_VARIATION.png')
  frames=[render(bank,t) for t in range(0,120,6)];frames[0].save(A/'EXTRAIT_2S.webp',save_all=True,append_images=frames[1:],duration=100,lossless=True,loop=0)
  # Native material study enlarged only in the viewer, not in exports.
  floors=[bank[f'tileset_{v}.png'].crop(((12+slots[255]%6)*24,slots[255]//6*24,(13+slots[255]%6)*24,slots[255]//6*24+24)) for v in range(3)]
  study=Image.new('RGBA',(72,24))
  for v,im in enumerate(floors):study.alpha_composite(im,(v*24,0))
  study.save(A/'SOL_VARIANTES.png')
  (D/'provenance.json').write_text(json.dumps(dict(source=source,mode=mode,adaptation='native originals; localized native-patch texture bombing on full floor variants1/2 only',bomb_stamps=bomb_records),indent=2))
 (O/'references_dtef'/source/'records.json').write_text(json.dumps(records,indent=2));manifest['themes'].append(entry);report.append(dict(biome=theme,native_copies=checks,animation_files=sum('_frame' in f for f in sheets),bomb_stamps=len(bomb_records),alpha_and_gasket_preserved=True,animation_native_exact=True))
 print(theme,len(changed),'sheets',checks,'native references',len(bomb_records),'stamps')
(O/'manifest.json').write_text(json.dumps(manifest,indent=2));(O/'verification_build.json').write_text(json.dumps(report,indent=2))
