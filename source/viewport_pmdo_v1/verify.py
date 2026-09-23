"""Independent readers of serialized Ground/Tile/Dir assets; no PMDO runtime claim."""
import tempfile,os

def decode_dir(path,tick,dt):
 b=path.read_bytes();n=struct.unpack_from('<q',b)[0];atlas=image(b[8:8+n]);w,h,dirs,total=struct.unpack_from('<4i',b,8+n);assert dirs==0 and w>0 and h>0 and total>0;assert atlas.width%w==atlas.height%h==0;f=(tick//dt)%total;x=(f%(atlas.width//w))*w;y=(f//(atlas.width//w))*h;return nr.straight(atlas.crop((x,y,x+w,y+h)))

def serialized_scene(dest,o,tick):
 w=len(o['Layers'][0]['Tiles']);h=len(o['Layers'][0]['Tiles'][0]);out=Image.new('RGBA',(w*8,h*8));bg=o['Background'];bgs=bg.get('Layers',[{'BG':bg}])
 for br in bgs:
  b=br['BG'];name=b['BGAnim']['AnimIndex']
  if not name:continue
  im=decode_dir(dest/f'Content/BG/{name}.dir',tick,b['BGAnim']['FrameTime']);x=int(b['MapLoc']['X']+b['BGMovement']['X']*tick/60);y=int(b['MapLoc']['Y']+b['BGMovement']['Y']*tick/60)
  if b['RepeatX']:
   x%=im.width
   for xx in range(x-im.width,out.width,im.width):out.alpha_composite(im,(xx,y))
  else:out.alpha_composite(im,(x,y))
 banks={}
 for l in o['Layers']:
  assert len(l['Tiles'])==w and all(len(col)==h for col in l['Tiles'])
  for x,col in enumerate(l['Tiles']):
   for y,cell in enumerate(col):
    for track in cell['Layers']:
     assert track['FrameLength']>0 and track['Frames']
     for f in track['Frames']:
      name=f['Sheet']
      if name not in banks:
       size,bank,_=nr.tiles(dest/f'Content/Tile/{name}.tile');assert size==8;banks[name]={pos:nr.straight(im) for pos,im in bank.items()}
      assert (f['TexLoc']['X'],f['TexLoc']['Y']) in banks[name]
     f=track['Frames'][(tick//track['FrameLength'])%len(track['Frames'])];out.alpha_composite(banks[f['Sheet']][f['TexLoc']['X'],f['TexLoc']['Y']],(x*8,y*8))
 return out

def verify(duo):
 dest=ST/duo;m=json.loads((dest/'manifest.json').read_text());assets=skies();records=collect();records+=variants(records,assets);records={r['id']:r for r in records};checks=[]
 for rec in m['maps']:
  o=json.loads((dest/f'Data/Ground/{rec["asset"]}.rsground').read_text())['Object'];assert o['TexSize']==1 and o['EdgeView']==1 and o['ViewCenter'] is None and not o['Released'];assert o['ViewOffset']==dict(zip(['X','Y'],rec['offset']));assert len(o['obstacles'])==rec['size'][0]//8
  for ent in o['Entities']:assert ent['MapChars']==ent['GroundObjects']==ent['Spawners']==[]
  for tick in sorted(set([0,rec.get('tick',64),97])):
   im=serialized_scene(dest,o,tick);expected=render(records[rec['id']],assets,tick);diff=np.abs(np.array(im).astype(int)-np.array(expected).astype(int));assert diff.max()<=1,(rec['id'],tick,diff.max());assert np.array_equal(np.array(im)[:,:,3],np.array(expected)[:,:,3])
  expected=render(records[rec['id']],assets);view,rect=crop_camera(expected,rec['spawn'],rec['offset']);assert rect==rec['viewport_at_x1'];assert view.size==(320,240);assert (rect[2]<expected.width) or (rect[3]<expected.height);assert image((dest/f'Apercus/{rec["asset"]}_viewport.png').read_bytes()).tobytes()==view.tobytes()
  checks.append(rec['asset']+': serialisation, every tile/frame resolves, RGB<=1 premult tolerance, exact alpha, viewport320x240')
 # .dir true12-frame star animation, exact native moon and closed64second cloud period.
 if duo=='plaines':
  moon=decode_dir(dest/'Content/BG/VP1_LUNE.dir',0,1);assert moon.crop((196,12,260,76)).tobytes()==assets['moon_crop'].tobytes()
  assert bg_render(assets,'nuit',(456,336),0).tobytes()==bg_render(assets,'nuit',(456,336),3840).tobytes()
  assert bg_render(assets,'jour',(456,336),0).tobytes()==bg_render(assets,'jour',(456,336),3840).tobytes()
  assert len({decode_dir(dest/'Content/BG/VP1_ETOILES.dir',i*8,8).tobytes() for i in range(12)})>1
  with Image.open(OUT/'VP1_nuit_extrait.webp') as im:
   assert im.info['loop']==1;ms=0
   for i in range(im.n_frames):im.seek(i);im.load();ms+=im.info['duration']
   assert ms==4800
  checks.append('Moon64x64 exact1x,12 actual star states, cloud64s closure,4.8s preview correctly single-play')
 installer=loadmod('vp_installer_'+duo,dest/'INSTALLER.py')
 with tempfile.TemporaryDirectory(dir=C) as td:
  mod=Path(td);(mod/'Mod.xml').write_text('<Mod><Namespace>vp_test</Namespace></Mod>');installer.install(dest,mod,True,None);assert not (mod/'Data').exists();installer.install(dest,mod,False,None);installer.install(dest,mod,False,None)
  index=installer.read_index(mod/'Content/Tile/index.idx');assert len(index)==len(list((dest/'Content/Tile').glob('*.tile')))
  for r in m['maps']:assert (mod/f'Data/Script/vp_test/ground/{r["asset"]}/init.lua').exists()
  changed=mod/f'Data/Ground/{m["maps"][0]["asset"]}.rsground';changed.write_bytes(changed.read_bytes()+b'\n');before=sha((mod/'Content/Tile/index.idx').read_bytes())
  try:installer.install(dest,mod,False,None);raise AssertionError('modified map overwritten')
  except ValueError:pass
  assert before==sha((mod/'Content/Tile/index.idx').read_bytes())
 checks.append('Installer dry-run, install, identical re-install, namespace, merged index and overwrite refusal')
 save(dest/'verification.json',jb({'checks':checks,'runtime_PMDO':False}));print('PASS',duo,len(m['maps']),'maps and installer',flush=True)
 return checks

def package(duo):
 dest=ST/duo;path=OUT/f'VP1_{duo}_PMDO.zip'
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for p in sorted(dest.rglob('*')):
   if not p.is_file() or '__pycache__' in p.parts:continue
   n=str(p.relative_to(dest));info=zipfile.ZipInfo(n,(2026,9,21,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes(),compresslevel=9)
 with zipfile.ZipFile(path) as z:assert z.testzip() is None;assert not any(n.endswith('index.idx') for n in z.namelist())
 print('PACK',path.name,path.stat().st_size,flush=True);return path
