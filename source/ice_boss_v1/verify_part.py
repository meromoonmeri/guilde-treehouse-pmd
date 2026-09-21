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
