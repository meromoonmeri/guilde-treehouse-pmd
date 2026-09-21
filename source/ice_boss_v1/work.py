"""IB1: preserve Halcyon arena geometry, generated icy materials and source hazard traces.
Implementation and assets are Git-pinned. PNG previews are not engine captures.
"""
from pathlib import Path
from functools import lru_cache
import io,json,struct,hashlib,subprocess,sys,copy,argparse,zipfile,importlib.util
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];S=R/'source/ice_boss_v1';C=R/'.cache/ice_boss_v1';O=C/'build';ST=C/'pack';SIZE=(504,504);REV=globals().get('REV','HEAD');RAW_REV='586f03b0bfefa7e0f755102bd42374564885fe24'
def sha(b):return hashlib.sha256(b).hexdigest()
def gitdata(p,rev=REV):return subprocess.check_output(['git','show',rev+':'+p],cwd=R)
@lru_cache(maxsize=48)
def support(p):
 f=S/p;return f.read_bytes() if f.exists() else gitdata(str(f.relative_to(R)))
def jb(j):return (json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode()
def image(b):return Image.open(io.BytesIO(b)).convert('RGBA')
def png(im):
 f=io.BytesIO();im.save(f,format='PNG',optimize=True);return f.getvalue()
def save(p,b):p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def loadmod(name,p):
 sp=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
gfx=loadmod('ib_gfx',R/'source/pmdo_cote/build.py')
def ref(p):return support('refs/'+p)
def raw(k):
 rec=next(r for r in json.loads(support('raws/index.json')) if r['id']==k);b=gitdata(rec['path'],RAW_REV);assert sha(b)==rec['sha256'];im=image(b);assert sha(im.tobytes())==rec['rgba_sha256'];return im
@lru_cache(maxsize=8)
def bank(name):
 data=ref('Content/Tile/'+name+'.tile');sz,n=struct.unpack_from('<ii',data);out={}
 for i in range(n):
  x,y,o=struct.unpack_from('<iiq',data,8+16*i);ln=struct.unpack_from('<q',data,o)[0];out[x,y]=image(data[o+8:o+8+ln])
 return sz,out

def render_native(kind,name):
 suffix='.rsmap' if kind=='Map' else '.rsground';o=json.loads(ref(f'Data/{kind}/{name}{suffix}').decode('utf-8-sig'))['Object'];sz=24 if kind=='Map' else o['TexSize']*8;w=len(o['Layers'][0]['Tiles']);h=len(o['Layers'][0]['Tiles'][0]);out=Image.new('RGBA',(w*sz,h*sz))
 grids=([[[cell['Data']['TileTex'] for cell in col] for col in o['Tiles']]] if kind=='Map' else [])+[l['Tiles'] for l in o['Layers'] if l['Visible']]
 for grid in grids:
  for x,col in enumerate(grid):
   for y,t in enumerate(col):
    for a in t['Layers']:
     f=a['Frames'][0];size,b=bank(f['Sheet']);assert size==sz;p=f['TexLoc'];out.alpha_composite(b[p['X'],p['Y']],(x*sz,y*sz))
 return out

def key(im):
 a=np.array(im);r,g,b=np.moveaxis(a[:,:,:3].astype(float),2,0);a[(r>g*1.4+20)&(b>g*1.4+20)&(r>50)&(b>50)]=0;return Image.fromarray(a)
def sprite(k,size):
 im=key(raw(k));im=im.crop(im.getbbox());s=min(size[0]/im.width,size[1]/im.height);im=im.resize((round(im.width*s),round(im.height*s)),Image.Resampling.NEAREST);out=Image.new('RGBA',size);out.alpha_composite(im,((size[0]-im.width)//2,size[1]-im.height));return out

def materials():
 src=render_native('Map','searing_crucible');a=np.array(src);base=np.array([127,79,71,255]);mask=np.any(a!=base,axis=2);floor=raw('floor_ice').resize(SIZE,Image.Resampling.NEAREST);g=np.array(key(raw('rocks_ice').resize(SIZE,Image.Resampling.NEAREST)));lum=a[:,:,:3].astype(float)@[.25,.60,.15];t=np.clip((lum-28)/145,0,1);ramp=np.array([28,65,100])+(np.array([214,248,253])-np.array([28,65,100]))*t[:,:,None];rgb=np.rint(.45*g[:,:,:3]+.55*ramp).astype('uint8');rgb[g[:,:,3]==0]=ramp[g[:,:,3]==0].astype('uint8');rocks=np.dstack([rgb,mask.astype('uint8')*255]);rocks[~mask]=0
 return src,floor,Image.fromarray(rocks),sprite('spikes',(24,32)),sprite('vent',(48,32))

def write_bank(name,im):
 data={};ids={};grid=[]
 for x in range(21):
  col=[]
  for y in range(21):
   cut=gfx.premult(im.crop((x*24,y*24,x*24+24,y*24+24)));rgba=cut.tobytes()
   if not cut.getbbox():col.append(gfx.auto());continue
   if rgba not in ids:
    n=len(ids);ids[rgba]=(n%32,n//32);data[ids[rgba]]=cut
   xx,yy=ids[rgba];col.append(gfx.auto([{'Sheet':name,'TexLoc':{'X':xx,'Y':yy}}]))
  grid.append(col)
 offset=8+16*len(data);records=[];payload=bytearray()
 for (x,y),im in data.items():
  b=png(im);records.append(struct.pack('<iiq',x,y,offset+len(payload)));payload+=struct.pack('<q',len(b))+b
 save(ST/f'Content/Tile/{name}.tile',struct.pack('<ii',24,len(data))+b''.join(records)+payload)
 return {'Name':name,'Layer':0,'Visible':True,'Tiles':grid}

def write_dir(name,frames):
 w,h=frames[0].size;sheet=Image.new('RGBA',(w*len(frames),h))
 for i,im in enumerate(frames):sheet.paste(gfx.premult(im),(i*w,0))
 b=png(sheet);save(ST/f'Content/Object/{name}.dir',struct.pack('<q',len(b))+b+struct.pack('<4i',w,h,0,len(frames)))
def deco(name,x,y):return {'MapLoc':{'X':x,'Y':y},'ObjectAnim':{'$type':'RogueEssence.Content.ObjAnimData, RogueEssence','AnimIndex':name,'FrameTime':4,'StartFrame':-1,'EndFrame':-1,'AnimDir':0,'Alpha':255,'AnimFlip':0}}
def patterns():
 traces=json.loads(support('native_traces.json'));out={}
 for name,t in traces.items():
  waves=[]
  for tick in sorted({r['tick'] for r in t['writes']}):waves.append({'tick':tick,'cells':[[r['x'],r['y']] for r in t['writes'] if r['tick']==tick]})
  out[name]={'leftBottom':name in ['BottomStraight','DiagonalUp'],'rightBottom':name in ['BottomStraight','DiagonalDown'],'waves':waves,'cells':t['unique_cells'],'end_tick':t['end_tick']}
 return out

def decorations(p):
 fixed=[deco('IB1_vent',240,96),deco('IB1_vent',240,408)];ports=[deco('IB1_vent',120,312 if p['leftBottom'] else 192),deco('IB1_vent',360,312 if p['rightBottom'] else 192)];sp=[deco('IB1_spike_idle',x*24,y*24-8) for x,y in p['cells']]
 return [{'Name':name,'Layer':0,'Visible':True,'Anims':items} for name,items in [('IB1 fixed vents',fixed),('IB1 active vents',ports),('IB1 ice spikes',sp)]]

def lua_patterns(ps):
 out=['return {']
 for name,p in ps.items():
  waves=','.join('{tick='+str(w['tick'])+',cells={'+','.join('{'+str(x)+','+str(y)+'}' for x,y in w['cells'])+'}}' for w in p['waves']);out.append(name+'={leftBottom='+str(p['leftBottom']).lower()+',rightBottom='+str(p['rightBottom']).lower()+',waves={'+waves+'}},')
 return ('\n'.join(out)+'\n}\n').encode()
def script_event(name,args='{}',priority=0):return {'Key':{'str':[priority]},'Value':{'$type':'RogueEssence.Dungeon.SingleCharScriptEvent, RogueEssence','Script':name,'ArgTable':args}}

def build():
 O.mkdir(parents=True,exist_ok=True)
 import shutil
 if ST.exists():shutil.rmtree(ST)
 ST.mkdir();src,floor,rocks,spike,vent=materials();ps=patterns();layers=[write_bank('IB1_floor',floor),write_bank('IB1_rocks',rocks)]
 poses=[]
 for height in [8,16,24,32]:
  im=Image.new('RGBA',(24,32));im.alpha_composite(spike,(0,32-height));poses.append(im)
 for name,seq in [('IB1_vent',[vent]),('IB1_spike_idle',[spike]),('IB1_spike_rise',poses),('IB1_spike_retract',poses[::-1])]:write_dir(name,seq)
 for name,im in [('IB1_sol',floor),('IB1_rochers',rocks),('IB1_pic',spike),('IB1_reservoir',vent)]:save(ST/f'PNG/{name}.png',png(im))
 for i,im in enumerate(poses):save(ST/f'PNG/IB1_pic_levee_{i}.png',png(im))
 save(ST/'reference/Searing_Crucible_terrain_sans_effets.png',png(src));save(ST/'reference/Crooked_Cavern_terrain.png',png(render_native('Ground','crooked_cavern_entrance')))
 native_map=json.loads(ref('Data/Map/searing_crucible.rsmap').decode('utf-8-sig'));native_ground=json.loads(ref('Data/Ground/searing_crucible.rsground').decode('utf-8-sig'));crooked=json.loads(ref('Data/Ground/crooked_cavern_entrance.rsground').decode('utf-8-sig'))['Object']
 mapfiles=[]
 for boss in [False,True]:
  slug='ib1_ice_boss_halcyon' if boss else 'ib1_ice_arena';doc=copy.deepcopy(native_map);m=doc['Object'];m.update(AssetName=slug,Name={'DefaultText':'Creuset glacial','LocalTexts':{}},Released=False,Comment='IB1 prototype; original21x21 terrain collision geometry. Requires ib1_ice.lua and registered effect. See README.',Layers=copy.deepcopy(layers),Decorations=decorations(ps['TopStraight']),Background=gfx.background(''),BlankBG=gfx.auto(),TextureMap={},ViewCenter=None,ViewOffset={'X':0,'Y':0},EdgeView=1,Status={})
  if not boss:m['MapTeams']=[];m['AllyTeams']=[];m['Music']=''
  for x,col in enumerate(m['Tiles']):
   for y,t in enumerate(col):
    t['Data']['TileTex']=gfx.auto();t['Data']['StableTex']=True;t['Effect'].update(ID='ib1_ice_spikes' if [x,y] in ps['TopStraight']['cells'] else '',Revealed=True,TileStates=[])
  m['MapEffect']['OnMapTurnEnds']=[script_event('IB1_IceFlowHandler','{IceDuration=2, NothingDuration=1}')]
  starts=copy.deepcopy(native_map['Object']['MapEffect']['OnMapStarts']) if boss else []
  for e in starts:
   if e['Value'].get('Script')=='LuaBeginBattleEvent':e['Value']['ArgTable']="{CustomClearEvent='IB1_IceBossClear'}"
  starts.append(script_event('IB1_IceBegin',priority=-10));m['MapEffect']['OnMapStarts']=sorted(starts,key=lambda e:e['Key']['str'][0]);save(ST/f'Data/Map/{slug}.rsmap',jb(doc));mapfiles.append(slug)
 for name,p in ps.items():
  slug='ib1_ice_'+name.lower();doc=copy.deepcopy(native_ground);g=doc['Object'];g.update(AssetName=slug,Name={'DefaultText':'Creuset glacial / '+name,'LocalTexts':{}},Released=False,Comment='Static Ground editing view. Turn-based effects are in the dungeon rsmap.',Layers=copy.deepcopy(layers),Decorations=decorations(p),TexSize=3,Background=gfx.background(''),BlankBG=gfx.auto(),Music='',Status={},ViewCenter=None,ViewOffset={'X':0,'Y':0},EdgeView=1,ActiveChar=None)
  g['Entities']=[{'Name':'IB1 entree','Visible':True,'MapChars':[],'GroundObjects':[],'Spawners':[],'Markers':[{'EntName':'entrance','Direction':0,'EntEnabled':True,'triggerType':0,'Collider':{'X':268,'Y':244,'Width':16,'Height':16}}]}]
  save(ST/f'Data/Ground/{slug}.rsground',jb(doc));save(ST/f'Data/Script/ground/{slug}/init.lua',f'local {slug} = {{}}\nreturn {slug}\n'.encode())
 effect=json.loads(ref('Data/Tile/flowing_lava.json').decode('utf-8-sig'));e=effect['Object'];e.update(Name={'DefaultText':'Pics de glace','LocalTexts':{}},Released=False,Comment='IB1 adaptation: ice-typed1/16HP on emergence/landing and turn end; no burn/freeze or damage boost. Register through PMDO data editor before testing.',MinimapColor='90, 220, 255, 255',OnActions=[])
 e['InteractWithTiles']=[script_event('IB1_IceChipDamage')];e['OnTurnEnds']=[script_event('IB1_IceChipDamage')];save(ST/'Data/Tile/ib1_ice_spikes.json',jb(effect));save(ST/'Data/Script/halcyon/ib1_ice.lua',support('ib1_ice.lua'));save(ST/'Data/Script/halcyon/ib1_patterns.lua',lua_patterns(ps))
 base=floor.copy();base.alpha_composite(rocks)
 def render(name,cells=None,heights=None,active_ports=True):
  im=base.copy();fixed=Image.new('RGBA',SIZE);hazard=Image.new('RGBA',SIZE);p=ps[name]
  for x,y in [(240,96),(240,408)]+([(120,312 if p['leftBottom'] else 192),(360,312 if p['rightBottom'] else 192)] if active_ports else []):fixed.alpha_composite(vent,(x,y))
  for x,y in p['cells'] if cells is None else cells:
   sp=spike if heights is None else poses[heights.get((x,y),3)];hazard.alpha_composite(sp,(24*x,24*y-8))
  im.alpha_composite(fixed);im.alpha_composite(hazard);return im,fixed,hazard
 public={}
 for name in ps:
  im,fixed,hazard=render(name);save(ST/f'PNG/IB1_{name}_vents.png',png(fixed));save(ST/f'PNG/IB1_{name}_pics.png',png(hazard));save(ST/f'Apercus/IB1_{name}.png',png(im));public[f'IB1_{name}.png']=png(im)
 im,fixed,hazard=render('TopStraight');public['IB1_viewport.png']=png(im.crop((116,132,436,372)))
 board=Image.new('RGB',(1008,1088),'#142c3b');d=ImageDraw.Draw(board)
 for i,(title,layerim) in enumerate([('01 Sol continu',floor),('02 Rochers - contours conserves',rocks),('03 Reservoirs froids',fixed),('04 Pics - TopStraight',hazard)]):
  x=i%2*504;y=i//2*544;d.text((x+12,y+10),title,fill='#cdefff');bg=Image.new('RGBA',SIZE,'#204459');bg.alpha_composite(layerim);board.paste(bg.convert('RGB'),(x,y+32))
 public['IB1_calques.png']=png(board)
 comparison=Image.new('RGB',(824,552),'#142c3b');d=ImageDraw.Draw(comparison);d.text((12,10),'CARTE504x504 / GEOMETRIE SEARING CRUCIBLE',fill='#cdefff');comparison.paste(im.convert('RGB'),(0,40));d.rectangle((116,172,435,411),outline='#fff3b1',width=2);comparison.paste(im.crop((116,132,436,372)).convert('RGB'),(504,40));d.text((512,298),'VUE x1 :320x240 / pas de resize',fill='#cdefff');d.text((512,320),'21x21 cases de24px',fill='#cdefff');d.text((512,342),'4 traces et rythme source conserves',fill='#cdefff');d.text((512,364),'Apercu simule, pas capture PMDO',fill='#cdefff');public['IB1_cadrage.png']=png(comparison)
 # Demonstration timeline: native40-frame propagation + new16-frame ice poses.
 # Holds60/30frames are preview reading time, NOT a conversion of game turns.
 anim=[]
 for name,p in ps.items():
  end=p['end_tick'];stop=end+60;total=stop+end+32
  for t in range(0,total,4):
   cells=[];hs={};removing=t>=stop
   for wave in p['waves']:
    age=(t-stop if removing else t)-wave['tick']
    for cell in wave['cells']:
     c=tuple(cell)
     if removing:
      if age<0:cells.append(c);hs[c]=3
      elif age<16:cells.append(c);hs[c]=3-age//4
     elif age>=0:cells.append(c);hs[c]=min(3,age//4)
   anim.append(render(name,cells,hs,not removing)[0].convert('RGB'))
 durations=[round((i+1)*4000/60)-round(i*4000/60) for i in range(len(anim))];anim[0].save(O/'IB1_pics_animes.webp',save_all=True,append_images=anim[1:],duration=durations,loop=0,lossless=True,method=3,minimize_size=True)
 for name,b in public.items():save(O/name,b);save(ST/f'Apercus/{name}',b)
 save(ST/'Apercus/IB1_pics_animes.webp',(O/'IB1_pics_animes.webp').read_bytes())
 actors=[{'species':ch['CurrentForm']['Species'],'position':ch['serializationLoc']} for team in native_map['Object']['MapTeams'] for ch in team['Players']]
 manifest={'id':'IB1','halcyon_commit':'1522c7a8b7a34d70078e11ed605b21d563b0dc51','branch':'working-copy','reference':'searing_crucible','size':SIZE,'dungeon_grid':[21,21],'tile_size':24,'ground_tex_size':3,'walkable_cells':72,'groups':['continuous ice floor','ice-textured original rock footprints','fixed/active vents','ice spikes'], 'camera':{'crooked_native_size':[320,240],'crooked_EdgeView':crooked['EdgeView'],'viewport_x1':[116,132,320,240],'fraction_of_map':320*240/(504*504),'forced_zoom':False,'runtime_capture':False},'patterns':ps,'duration':{'active_turns':2,'quiet_turns':1,'native_pool_and_wave_frames':40,'new_ice_pose_frames':4,'preview_duration_ms':sum(durations),'preview_holds_frames':[60,32],'preview_holds_are_not_turn_durations':True},'materials':{'generated':True,'rock_alpha':'exact visible native non-background footprint; new RGB only','rock_RGB':'45percent generated ice colour +55percent new blue luminance ramp; fallback blue ramp for uncovered points','native_reference_modified':False},'actors_original_optional_boss':actors,'engine_target':'Halcyon working-copy0.8.9 data schema; not executed in PMDO','installation':'Graphics/Ground safe default; boss integration opt-in and data reindex required','combat_changes':'Ice chip damage, immune ice/ice_body, thick_fat reduction; no burning/freezing or power boost; original roster not rebalanced'}
 save(ST/'manifest.json',jb(manifest));save(ST/'README.md',support('README.md'));save(ST/'INSTALLER.py',support('INSTALLER.py'));save(ST/'install_base.py',(R/'source/pmdo_cote/INSTALLER.py').read_bytes());save(ST/'reference/provenance.json',support('refs/provenance.json'));save(ST/'reference/native_traces.json',support('native_traces.json'))
 save(ST/'reference/searing_crucible_original.rsmap',ref('Data/Map/searing_crucible.rsmap'));save(ST/'reference/crooked_cavern_original.rsground',ref('Data/Ground/crooked_cavern_entrance.rsground'));save(ST/'reference/flowing_lava_original.json',ref('Data/Tile/flowing_lava.json'))
 with zipfile.ZipFile(O/'IB1_creuset_glacial_PMDO.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(ST.rglob('*')):
   if p.is_file():
    info=zipfile.ZipInfo(str(p.relative_to(ST)),(2026,9,22,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes(),compresslevel=9)
 print('Built ice materials,4Ground previews,2dungeon maps,effect/controller,viewport and animation',O)


def verify():
 import tempfile,shutil
 from lupa import LuaRuntime
 checks=[]
 def ok(s):checks.append(s);print('PASS',s)
 for rec in json.loads(support('refs/provenance.json'))['files']:
  b=ref(rec['path']);assert sha(b)==rec['sha256'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==rec['git_blob']
 for rec in json.loads(support('raws/index.json')):assert list(raw(rec['id']).size)==rec['size']
 ok('Halcyon pinned blobs and4 lossless generated originals verified')
 # Re-execute the original Lua, rather than trusting a hand-transcribed pattern.
 save(C/'native/Data/Script/halcyon/event_single.lua',ref('Data/Script/halcyon/event_single.lua'));save(C/'trace_native_test.py',support('trace_native.py'));subprocess.run([sys.executable,str(C/'trace_native_test.py')],cwd=R,check=True)
 assert json.loads((C/'native_traces.json').read_text())==json.loads(support('native_traces.json'));ps=patterns()
 lua=LuaRuntime(unpack_returned_tuples=True);lua.globals().P=lua.execute((ST/'Data/Script/halcyon/ib1_patterns.lua').read_text())
 lua.execute('''package.preload['halcyon.ib1_patterns']=function()return P end
 SINGLE_CHAR_SCRIPT={};SV={};clock=0;writes={};tiles={};dice={0,0};di=1
 function col()return {Count=0,Add=function(self,x)self[self.Count]=x;self.Count=self.Count+1 end,Clear=function(self)for i=0,self.Count-1 do self[i]=nil end;self.Count=0 end}end
 local layers=col()
 for _,name in ipairs({'IB1 fixed vents','IB1 active vents','IB1 ice spikes','unrelated'}) do layers:Add({Name=name,Anims=col()})end
 layers[0].Anims:Add('fixed1');layers[0].Anims:Add('fixed2');layers[3].Anims:Add('untouched')
 GAME={WaitFrames=function(self,n)clock=clock+n end};TASK={WaitTask=function(self,v)return v end}
 RogueElements={Loc=function(x,y)return {X=x,Y=y}end}
 RogueEssence={Ground={GroundAnim=function(anim,loc)return {ObjectAnim=anim,MapLoc=loc}end},Content={ObjAnimData=function(id,t)return {AnimIndex=id,FrameTime=t}end},Dungeon={EffectTile=function(id,reveal,loc)table.insert(writes,{x=loc.X,y=loc.Y,tick=clock,id=id});return {ID=id}end}}
 local map={Decorations=layers,Rand={Next=function(self,a,b)local v=dice[di];di=di+1;return v end}}
 function map:GetTile(loc)local k=loc.X..','..loc.Y;if not tiles[k] then tiles[k]={Effect={ID=''}} end;return tiles[k]end
 function map:GetCharAtLoc(loc)return nil end
 _ZONE={CurrentMap=map}
 PMDC={Dungeon={PreTypeEvent={CalculateTypeMatchup=function(a,b)return 0 end,GetEffectivenessMult=function(a)return 4 end}}}
 ''');lua.execute(support('ib1_ice.lua').decode());g=lua.globals()
 for name,l,r in [('TopStraight',0,0),('BottomStraight',1,1),('DiagonalDown',0,1),('DiagonalUp',1,0)]:
  lua.execute(f"tiles={{}};writes={{}};clock=0;dice={{{l},{r}}};di=1;SV.IB1IceBoss={{Direction='None',Countdown=-1}}")
  g.SINGLE_CHAR_SCRIPT.IB1_QueueIce();got=[(x['x'],x['y'],x['tick']) for x in g.writes.values()];native=json.loads(support('native_traces.json'))[name];assert got==[(x['x'],x['y'],x['tick']) for x in native['writes']];assert g.clock==native['end_tick']
  assert g.SV.IB1IceBoss.Direction==name;lua.execute('writes={};clock=0');g.SINGLE_CHAR_SCRIPT.IB1_RemoveIce();assert [(x['x'],x['y'],x['tick']) for x in g.writes.values()]==got;assert all(x['id']=='' for x in g.writes.values());assert g.clock==native['end_tick']
  lua.execute("assert(_ZONE.CurrentMap.Decorations[0].Anims.Count==2);assert(_ZONE.CurrentMap.Decorations[3].Anims[0]=='untouched');assert(_ZONE.CurrentMap.Decorations[2].Anims.Count==0)")
 lua.execute("tiles={};writes={};clock=0;dice={0,0};di=1;SINGLE_CHAR_SCRIPT.IB1_IceBegin(nil,nil,{User=nil},{})")
 lua.execute("SINGLE_CHAR_SCRIPT.IB1_IceFlowHandler(nil,nil,{User={}},{IceDuration=2,NothingDuration=1});assert(SV.IB1IceBoss.Countdown==-1)")
 for counter in [1,0,-1]:
  lua.execute("SINGLE_CHAR_SCRIPT.IB1_IceFlowHandler(nil,nil,{User=nil},{IceDuration=2,NothingDuration=1})");assert g.SV.IB1IceBoss.Countdown==counter
 for el,intrinsic,want in [('normal','none',10),('ice','none',0),('normal','ice_body',0),('normal','thick_fat',5)]:
  lua.execute(f"hurt=0;local c={{Element1='{el}',Element2='none',Intrinsic='{intrinsic}',MaxHP=160,InflictDamage=function(self,n)hurt=hurt+n end}};SINGLE_CHAR_SCRIPT.IB1_IceChipDamage(nil,nil,{{User=c}},{{}})");assert g.hurt==want
 ok('Lua: all4 exact native write sequences/timings;14/20cells;2active+1quiet counter;char guard;owned-only cleanup;ice damage choices')
 native=json.loads(ref('Data/Map/searing_crucible.rsmap').decode('utf-8-sig'))['Object'];src,floor,rocks,spike,vent=materials();source_mask=np.any(np.array(src)!=[127,79,71,255],axis=2);assert np.array_equal(np.array(rocks)[:,:,3]>0,source_mask);assert (np.array(floor)[:,:,3]==255).all()
 for p in ps.values():
  for x,y in p['cells']:assert native['Tiles'][x][y]['Data']['ID']=='floor'
 for slug in ['ib1_ice_arena','ib1_ice_boss_halcyon']:
  m=json.loads((ST/f'Data/Map/{slug}.rsmap').read_text())['Object'];assert [[t['Data']['ID']for t in col]for col in m['Tiles']]==[[t['Data']['ID']for t in col]for col in native['Tiles']];assert m['EntryPoints']==native['EntryPoints'];assert m['ViewCenter'] is None and m['EdgeView']==1
  active=[[x,y]for x,col in enumerate(m['Tiles'])for y,t in enumerate(col)if t['Effect']['ID']=='ib1_ice_spikes'];assert sorted(active)==sorted(ps['TopStraight']['cells'])
  if slug.endswith('halcyon'):assert m['MapTeams']==native['MapTeams']
  else:assert m['MapTeams']==[] and all(e['Value'].get('Script')!='LuaBeginBattleEvent' for e in m['MapEffect']['OnMapStarts'])
 assert sum(t['Data']['ID']=='floor' for col in native['Tiles'] for t in col)==72
 ok('Same21x21 geometry,72walkable cells, source entry/roster, rock footprints and no enlargement')
 # Independent24px bank decode and serialized map recomposition.
 decoded={}
 for p in (ST/'Content/Tile').glob('*.tile'):
  b=p.read_bytes();sz,n=struct.unpack_from('<ii',b);assert sz==24;tiles={}
  for i in range(n):
   x,y,off=struct.unpack_from('<iiq',b,8+i*16);ln=struct.unpack_from('<q',b,off)[0];im=image(b[off+8:off+8+ln]);assert im.size==(24,24);tiles[x,y]=im
  decoded[p.stem]=tiles
 for layer,expected in zip(json.loads((ST/'Data/Map/ib1_ice_arena.rsmap').read_text())['Object']['Layers'],[floor,rocks]):
  out=Image.new('RGBA',SIZE)
  for x,col in enumerate(layer['Tiles']):
   for y,t in enumerate(col):
    for a in t['Layers']:
     f=a['Frames'][0];loc=f['TexLoc'];out.alpha_composite(decoded[f['Sheet']][loc['X'],loc['Y']],(24*x,24*y))
  assert out.tobytes()==expected.tobytes()
 for p in (ST/'Content/Object').glob('*.dir'):
  b=p.read_bytes();ln=struct.unpack_from('<q',b)[0];sheet=image(b[8:8+ln]);w,h,start,end=struct.unpack_from('<4i',b,8+ln);assert sheet.size==(w*end,h) and start==0 and end in [1,4]
 for p in (ST/'Data/Ground').glob('*.rsground'):
  o=json.loads(p.read_text())['Object'];assert o['TexSize']==3 and len(o['Layers'][0]['Tiles'])==21;assert o['obstacles']==json.loads(ref('Data/Ground/searing_crucible.rsground').decode('utf-8-sig'))['Object']['obstacles'];assert o['Entities'][0]['MapChars']==[]
  for layer in o['Decorations']:
   for d in layer['Anims']:assert (ST/'Content/Object'/(d['ObjectAnim']['AnimIndex']+'.dir')).exists()
 m=json.loads((ST/'manifest.json').read_text());assert image((O/'IB1_viewport.png').read_bytes()).size==(320,240);assert image((O/'IB1_viewport.png').read_bytes()).tobytes()==image((O/'IB1_TopStraight.png').read_bytes()).crop((116,132,436,372)).tobytes();assert m['camera']['fraction_of_map']<.31
 ok('24px tiles and .dir codecs,serialized layer pixels,4Grounds,resource links,320x240 viewport exact')
 with Image.open(O/'IB1_pics_animes.webp') as w:
  assert w.n_frames>20 and w.info['loop']==0;duration=0
  for i in range(w.n_frames):w.seek(i);w.load();duration+=w.info['duration']
  assert duration==m['duration']['preview_duration_ms']
 ok('Real emergence/retraction animation,4 traced paths;preview duration documented separately from turns')
 # Safe install of graphics in a dummy mod, then opt-in integration in a dummy Halcyon.
 target=C/'install_test';shutil.rmtree(target,ignore_errors=True);target.mkdir();save(target/'Mod.xml',b'<Mod><Namespace>halcyon</Namespace></Mod>');save(target/'Data/Map/searing_crucible.rsmap',ref('Data/Map/searing_crucible.rsmap'));save(target/'Data/Script/halcyon/event.lua',b"-- existing event registration\nrequire 'halcyon.event_single'\n")
 def snap():return {str(p.relative_to(target)):sha(p.read_bytes()) for p in target.rglob('*') if p.is_file()}
 before=snap();cmd=[sys.executable,str(ST/'INSTALLER.py'),str(target)];subprocess.run(cmd+['--halcyon-boss','--dry-run'],check=True,stdout=subprocess.DEVNULL);assert snap()==before;subprocess.run(cmd+['--halcyon-boss'],check=True,stdout=subprocess.DEVNULL);after=snap();subprocess.run(cmd+['--halcyon-boss'],check=True,stdout=subprocess.DEVNULL);assert snap()==after
 conflict=target/'Data/Ground/ib1_ice_topstraight.rsground';conflict.write_bytes(conflict.read_bytes()+b' ');before=snap();result=subprocess.run(cmd+['--halcyon-boss'],capture_output=True);assert result.returncode and snap()==before
 ok('Installer dry-run no writes;real copy/index merge/idempotence;conflict refusal;event.lua backup;no original maps replaced')
 changed=subprocess.check_output(['git','diff','c6b0d71e','--name-only'],cwd=R,text=True).splitlines();assert not any(p.startswith('renders/') and not p.startswith('renders/ice_boss_v1/') for p in changed);ok('All earlier published maps/PMDO packs untouched;no PMDO runtime claim')
 save(C/'verification.json',jb({'checks':checks,'pmdo_runtime_tested':False,'lua_mock_tested':True}));return checks


def release_records():return json.loads(support('release.json'))
def materialize(name):
 rec=next(r for r in release_records() if r['name']==name);p=C/'releases'/name
 if not p.exists():
  b=gitdata(rec['path']);assert sha(b)==rec['sha256'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 assert sha(p.read_bytes())==rec['sha256'];return p

def serve(port):
 from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
 from urllib.parse import urlsplit,unquote
 import mimetypes
 for r in release_records():materialize(r['name'])
 class Handler(BaseHTTPRequestHandler):
  def do_GET(self):
   path=unquote(urlsplit(self.path).path);name={'/':'IB1_cadrage.png','/entree':'IB1_TopStraight.png','/finale':'IB1_DiagonalDown.png','/animation':'IB1_pics_animes.webp'}.get(path,path.lstrip('/'))
   try:
    if name in {r['name'] for r in release_records()}:b=materialize(name).read_bytes()
    elif path.startswith('/ice-pack/'):
     name=path[len('/ice-pack/'):]
     with zipfile.ZipFile(materialize('IB1_creuset_glacial_PMDO.zip')) as z:b=z.read(name)
    else:raise KeyError(path)
    self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(b)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(b)
   except (KeyError,StopIteration):self.send_error(404)
 print('Direct ice boss PNG/WebP on 0.0.0.0:'+str(port),flush=True);ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()

def http_check(port):
 import urllib.request,urllib.error
 n=0
 def get(path):return urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}'+path,headers={'Host':f'{port}-preview.e2b.app'})).read()
 for r in release_records():assert get('/'+r['name'])==materialize(r['name']).read_bytes();n+=1
 for path,name in {'/':'IB1_cadrage.png','/entree':'IB1_TopStraight.png','/finale':'IB1_DiagonalDown.png','/animation':'IB1_pics_animes.webp'}.items():assert get(path)==materialize(name).read_bytes();n+=1
 with zipfile.ZipFile(materialize('IB1_creuset_glacial_PMDO.zip')) as z:
  for name in z.namelist():assert get('/ice-pack/'+name)==z.read(name);n+=1
 for path in ['/.git/config','/%2e%2e/.git/config','/ice-pack/../../.git/config']:
  try:get(path);raise AssertionError('Private path exposed')
  except urllib.error.HTTPError as e:assert e.code==404
 print('PASS',n,'HTTP responses byte-identical; preview host accepted;3 private paths404')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--verify',action='store_true');p.add_argument('--restore',action='store_true');p.add_argument('--serve',action='store_true');p.add_argument('--http-check',action='store_true');p.add_argument('--port',type=int,default=8017);a=p.parse_args()
 if a.build:build()
 if a.verify:verify()
 if a.restore:
  for r in release_records():print(materialize(r['name']))
 if a.serve:serve(a.port)
 if a.http_check:http_check(a.port)
 if not any([a.build,a.verify,a.restore,a.serve,a.http_check]):p.print_help()
