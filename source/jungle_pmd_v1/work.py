"""Jungle H14P01: two new five-layer maps. Run via restore.py after publication.
Implementation, sources and deliverables are pinned in Git, not external storage.
"""
from pathlib import Path
import io,json,hashlib,subprocess,sys,zipfile,argparse,shutil
from functools import lru_cache
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
R=Path(__file__).resolve().parents[2];S=R/'source/jungle_pmd_v1';C=R/'.cache/jungle_pmd_v1';O=C/'build';SIZE=(456,336)
REV=globals().get('REV','HEAD');RAW_REV='66f2dcc40b5e32ed852eb314bb787bb8afc87ac9'
sys.path.insert(0,str(R/'source/dungeon_biomes_v1'))
from red import decode,palettes
from native_archive import native_source_archive
N=C/'native/data/map_bg'
def sha(b):return hashlib.sha256(b).hexdigest()
def gitdata(path,rev=REV):return subprocess.check_output(['git','show',rev+':'+path],cwd=R)
@lru_cache(maxsize=16)
def support(name):
 p=S/name;return p.read_bytes() if p.exists() else gitdata(str(p.relative_to(R)))
def jsonbytes(j):return (json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode()
def img(b):return Image.open(io.BytesIO(b)).convert('RGBA')
def png(im):
 f=io.BytesIO();im.save(f,format='PNG',optimize=True);return f.getvalue()
@lru_cache(maxsize=12)
def raw(k):
 rec=next(r for r in json.loads(support('raws/index.json')) if r['id']==k);b=gitdata(rec['path'],RAW_REV);assert sha(b)==rec['sha256'];im=img(b);assert sha(im.tobytes())==rec['rgba_sha256'];return im

def source(k):
 a=np.array(raw(k).resize(SIZE,Image.Resampling.NEAREST));r,g,b=np.moveaxis(a[:,:,:3].astype(float),2,0);a[(r>120)&(b>100)&(g<130)&(r>g*1.6)&(b>g*1.5)]=0;return Image.fromarray(a)
def fit(im,size):
 im=im.crop(im.getbbox());scale=min(size[0]/im.width,size[1]/im.height);return im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
def components(im,predicate):
 a=np.array(im);labels,n=ndimage.label(a[:,:,3]>0,np.ones((3,3)));keep=[];report=[]
 for i,s in enumerate(ndimage.find_objects(labels),1):
  y,x=s;box=[x.start,y.start,x.stop,y.stop];selected=bool(predicate(box));report.append({'bbox':box,'pixels':int((labels==i).sum()),'selected':selected})
  if selected:keep.append(i)
 a[~np.isin(labels,keep)]=0;return Image.fromarray(a),report

def native_init():
 N.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(native_source_archive()) as z:
  for suffix in ['.bpl','c.bpc','m.bma']:(N/('H14P01'+suffix)).write_bytes(z.read('data/map_bg/H14P01'+suffix))
 return decode('H14P01',0,N)[0][0]
def palette_image(colors):
 p=Image.new('P',(1,1));p.putpalette(np.vstack([colors,np.tile(colors[0],(256-len(colors),1))]).astype('uint8').tobytes());return p

def quant(im,colors,factor=1):
 a=np.array(im);rgb=np.rint(a[:,:,:3]*factor).astype('uint8');q=np.array(Image.fromarray(rgb).quantize(palette=palette_image(colors),dither=Image.Dither.NONE).convert('RGBA'));q[:,:,3]=a[:,:,3];q[q[:,:,3]==0]=0;return Image.fromarray(q)
def geometry(mode):
 layers={};layers['sol']=source('sol');layers['fond'],report=components(source('fond_palmes'),lambda b:b[3]<=120 or b[2]<=72 or b[0]>=380)
 tree=fit(source('arbre_'+mode),(264,192) if mode=='entree' else (248,184));layers['arbre']=Image.new('RGBA',SIZE);layers['arbre'].alpha_composite(tree,((456-tree.width)//2,0));water=Image.new('RGBA',SIZE)
 if mode=='entree':
  for box,xy in [((0,0,228,336),(92,112)),((228,0,456,336),(260,112))]:
   # Only whole GENERATED pools are rotated/normalized; no native pixel transformed.
   part=fit(source('eau_entree').crop(box).transpose(Image.Transpose.ROTATE_90),(104,80));water.alpha_composite(part,xy)
  layers['fleurs']=source('fleurs_entree');front_report=[]
 else:
  part=fit(source('eau_fin'),(288,116));water.alpha_composite(part,(84,72));front,front_report=components(source('fleurs_fin'),lambda b:b[3]==336);layers['fleurs']=Image.new('RGBA',SIZE)
  for box,x in [((0,0,228,336),0),((228,0,456,336),328)]:
   part=fit(front.crop(box),(128,240));layers['fleurs'].alpha_composite(part,(x,336-part.height))
 layers['eau']=water
 return layers,{'back_component_selection':report,'front_component_selection':front_report,'tree_size':list(tree.size),'tree_position':[(456-tree.width)//2,0],'note':'Complete generated groups normalized/repositioned; extra middle garland and interior background plants omitted as complete connected groups. Border objects remain frame-anchored, not recovered offscreen sprites.'}

def scene(files,rec,tick=0):
 im=Image.new('RGBA',SIZE)
 for layer in rec['layers']:
  path=layer['frames'][(tick//layer['frame_ticks'])%len(layer['frames'])] if 'frames' in layer else layer['file'];im.alpha_composite(img(files[path]))
 return im

def duo(a,b):
 out=Image.new('RGB',(912,368),'#132b1d');d=ImageDraw.Draw(out);d.text((12,10),'JUNGLE / ENTREE',fill='#dcedb5');d.text((468,10),'JUNGLE / FINALE',fill='#dcedb5');out.paste(a.convert('RGB'),(0,32));out.paste(b.convert('RGB'),(456,32));return out

def zipwrite(path,files):
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,b in sorted(files.items()):
   info=zipfile.ZipInfo(name,(2026,9,21,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b,compresslevel=9)

def build():
 O.mkdir(parents=True,exist_ok=True);ref=native_init();a=np.array(ref);colors=np.unique(a[:,:,:3][a[:,:,3]>0],axis=0);ground=np.unique(a[176:264,144:312,:3].reshape(-1,3),axis=0);files={};maps=[];geo={};pals=[]
 for f in range(13):
  pal,spec=palettes((N/'H14P01.bpl').read_bytes(),f*6);pals.append(pal[4]);files[f'references/JG1_H14P01_natif_{f:02d}.png']=png(decode('H14P01',f*6,N)[0][0])
 assert [(i,*v) for i,v in enumerate(spec) if v[1]]==[(2,6,13),(4,6,13),(8,6,13)]
 files['references/JG1_palette_eau.json']=jsonbytes({'bank':4,'indices':[1,4,6,9,11],'frame_ticks':6,'period_ticks':78,'frames_rgba':[p.tolist() for p in pals]})
 for mode,tag in [('entree','E'),('fin','F')]:
  layout,geo[mode]=geometry(mode);rec={'id':mode,'prefix':tag,'size':list(SIZE),'semantic_groups':5,'layers':[],'arrivee':'sud','nord':'grotte du grand arbre' if mode=='entree' else 'tronc plein et bassin, sans sortie','validation':'proposition, pas de collisions/warps/scripts PMDO'}
  for k,title in [('sol','Sol herbeux continu'),('fond','Bordures boisees et palmes'),('eau','Eau adaptee, cycle BPL natif'),('arbre','Grand tronc / racines / acces'),('fleurs','Fleurs et vegetation basse')]:
   if k=='eau':
    a=np.array(layout[k]);indices=[1,4,6,9,11];wc=pals[0][indices,:3].astype(int);dist=((a[:,:,:3].astype(int)[:,:,None,:]-wc[None,None,:,:])**2).sum(-1);ix=np.array(indices,dtype='uint8')[np.argmin(dist,axis=2)];ix[a[:,:,3]==0]=0
    ip=f'donnees/JG1_{tag}_eau_indices.png';files[ip]=png(Image.fromarray(ix));frames=[]
    for f,pal in enumerate(pals):
     name=f'eau/JG1_{tag}_eau_{f:02d}.png';files[name]=png(Image.fromarray(pal[ix]));frames.append(name)
    rec['layers'].append({'id':k,'title':title,'frames':frames,'frame_ticks':6,'period_ticks':78,'index_image':ip,'native_pixels':False,'native_palette_bank':4,'source':'H14P01 BPL: exact palette values and timing, adapted geometry; not native water pixels'})
   else:
    im=quant(layout[k],ground if k=='sol' else colors,.86 if k=='sol' else 1);name=f'calques/JG1_{tag}_{k}.png';files[name]=png(im);rec['layers'].append({'id':k,'title':title,'file':name,'native_pixels':False,'source_generation':k if k=='sol' else 'fond_palmes' if k=='fond' else k+'_'+mode})
  maps.append(rec);name='JG1_entree.png' if mode=='entree' else 'JG1_finale.png';files['apercus/'+name]=png(scene(files,rec));(O/name).write_bytes(files['apercus/'+name])
  board=Image.new('RGB',(912,1104),'#17281f');d=ImageDraw.Draw(board)
  for i,l in enumerate(rec['layers']+[{'title':'Composition - CINQ groupes','composite':True}]):
   x=i%2*456;y=i//2*368;d.text((x+8,y+8),l['title'],fill='#dcebad');im=scene(files,rec) if l.get('composite') else img(files[l['frames'][0] if 'frames' in l else l['file']]);bg=Image.new('RGBA',SIZE,'#263d32');bg.alpha_composite(im);board.paste(bg.convert('RGB'),(x,y+28))
  name=f'JG1_{tag}_calques.png';(O/name).write_bytes(png(board));files['apercus/'+name]=png(board)
  frames=[scene(files,rec,f*6).convert('RGB') for f in range(13)];frames[0].save(O/f'JG1_{tag}_anime.webp',save_all=True,append_images=frames[1:],duration=100,loop=0,lossless=False,quality=75,method=6,minimize_size=True)
 frames=[duo(scene(files,maps[0],t*6),scene(files,maps[1],t*6)) for t in range(13)];(O/'JG1_duo.png').write_bytes(png(frames[0]));files['apercus/JG1_duo.png']=png(frames[0]);frames[0].save(O/'JG1_duo_anime.webp',save_all=True,append_images=frames[1:],duration=100,loop=0,lossless=False,quality=75,method=6,minimize_size=True)
 audit=json.loads((R/'source/dungeon_biomes_v1/audit.json').read_text());m={'id':'JG1','reference':'H14P01','size':list(SIZE),'grid':8,'maps':maps,'native_weather':None,'palette_cycles':[[2,6,13],[4,6,13],[8,6,13]],'water_note':'Generated shapes, indexed against native bank4; not native geometry. Full thirteen native reference frames stay1x untouched. No fake scrolling. Palette animation only, not wave deformation.','shared_layers':['sol','fond'],'new_generations':8,'layout_guides':2,'generated_ground':'RGBx0.86 then nearest quantization to seven reference grass colours; no changes to native reference','geometry':geo,'progress':{'delivered_duos':7,'delivered_maps':14,'planned_maps':22,'remaining_duos':['mont_discipline','plaines_sauvages','foret_secrete','plaines_brulees']},'port_commit':audit['port_commit'],'pret_commit':audit['pret_commit'],'native_rgba_is_not_gpu_capture':True}
 files['manifest.json']=jsonbytes(m);files['README.md']=support('README.md');files['assemble.py']=support('assemble.py');files['provenance/generations.json']=support('raws/index.json')
 for p in sorted(N.iterdir()):
  if p.name.startswith('H14P01'):files['native/data/map_bg/'+p.name]=p.read_bytes()
 files['native/decoder.py']=(R/'source/dungeon_biomes_v1/red.py').read_bytes();files['native/provenance.json']=jsonbytes({'port':audit['port_commit'],'pret':audit['pret_commit'],'files':{p.name:sha(p.read_bytes()) for p in sorted(N.iterdir()) if p.name.startswith('H14P01')}})
 zipwrite(O/'JG1_jungle_duo_calques.zip',files);print('Built',len(files),'portable files and 9 direct previews/packs in',O)


def verify():
 checks=[]
 def ok(s):checks.append(s);print('PASS',s)
 for r in json.loads(support('raws/index.json')):assert list(raw(r['id']).size)==r['size']
 ok('10 raw generations losslessly retrievable, RGBA SHA256')
 native_init()
 with zipfile.ZipFile(O/'JG1_jungle_duo_calques.zip') as z:
  assert z.testzip() is None;files={n:z.read(n) for n in z.namelist()};m=json.loads(files['manifest.json']);assert len(m['maps'])==2
  reference=decode('H14P01',0,N)[0][0]
  with zipfile.ZipFile(R/'renders/dungeon_biomes_v1/DB1_cinq_duos_multicalques.zip') as old:assert reference.tobytes()==img(old.read('references/DB1_native_H14P01.png')).tobytes()
  for f in range(13):assert img(files[f'references/JG1_H14P01_natif_{f:02d}.png']).tobytes()==decode('H14P01',f*6,N)[0][0].tobytes()
  assert decode('H14P01',78,N)[0][0].tobytes()==reference.tobytes();ok('13 native456x336 reference frames exact, full78tick cycle; prior native reference unchanged')
  for a,b in zip(m['maps'][0]['layers'],m['maps'][1]['layers']):
   if a['id'] in ['sol','fond']:assert files[a['file']]==files[b['file']]
  for rec in m['maps']:
   assert len(rec['layers'])==rec['semantic_groups']==5;ims=[];water=next(l for l in rec['layers'] if l['id']=='eau');ix=np.array(Image.open(io.BytesIO(files[water['index_image']])));distinct=[]
   assert set(np.unique(ix))<={0,1,4,6,9,11}
   for f,path in enumerate(water['frames']):
    p,_=palettes((N/'H14P01.bpl').read_bytes(),f*6);a=np.array(img(files[path]));assert np.array_equal(a,p[4][ix]);distinct.append(sha(a.tobytes()))
   assert len(set(distinct))>1;assert water['frame_ticks']==6 and water['period_ticks']==78
   for l in rec['layers']:ims.append(np.array(img(files[l['frames'][0] if 'frames' in l else l['file']])))
   assert (ims[0][:,:,3]==255).all();assert (ims[0][:,:,3][ims[3][:,:,3]>0]==255).all();assert ((ims[2][:,:,3]>0)&(ims[3][:,:,3]>0)).any()
   obstacle=np.logical_or.reduce([a[:,:,3]>0 for a in ims[1:]]);safe=ndimage.binary_erosion(~obstacle,structure=np.ones((17,17)));labels,_=ndimage.label(safe);lab=labels[320,228];assert lab>0
   if rec['id']=='entree':assert labels[144,228]==lab;assert not (ix[:,196:260]>0).any();assert not obstacle[200:,196:260].any()
   else:assert not obstacle[224:312,128:328].any();assert labels[240,228]==lab;assert np.argwhere(labels==lab)[:,0].min()>=120
   name='JG1_entree.png' if rec['id']=='entree' else 'JG1_finale.png';assert scene(files,rec).tobytes()==img((O/name).read_bytes()).tobytes()
  ok('5 semantic layers each; opaque floors UNDER scenery; real overlap; dry south-to-door route and200x88 final arena, conservative8px clearance')
  ok('26 adapted water PNGs equal native-bank indexed lookup, fixed shapes, true native6tick cadence; generated geometry explicitly distinct')
  basenames=[]
  for name,b in files.items():
   if not name.endswith('.png'):continue
   im=img(b);assert im.width%8==im.height%8==0;basenames.append(Path(name).name);a=np.array(im);assert not ((a[:,:,0]>220)&(a[:,:,1]<45)&(a[:,:,2]>220)&(a[:,:,3]>0)).any()
  assert len(basenames)==len(set(basenames));ok(f'{len(basenames)} PNGs Ground8, unique basenames, no visible magenta')
  extracted=C/'verify_pack';extracted.mkdir(exist_ok=True);z.extractall(extracted);subprocess.run([sys.executable,str(extracted/'assemble.py'),'--out',str(extracted/'assembled')],check=True,cwd=R)
  for rec in m['maps']:assert img((extracted/'assembled'/f"JG1_{rec['id']}_tick0.png").read_bytes()).tobytes()==scene(files,rec).tobytes()
  ok('standalone ZIP assembler reproduces both map pixels exactly')
 for name in ['JG1_E_anime.webp','JG1_F_anime.webp','JG1_duo_anime.webp']:
  with Image.open(O/name) as im:
   assert im.n_frames==13 and im.info['loop']==0;dur=0
   for f in range(im.n_frames):im.seek(f);im.load();dur+=im.info['duration']
   assert dur==1300
 ok('3 direct WebP animations,13 frames,1300ms complete loop')
 changed=subprocess.check_output(['git','diff','fda2014b','--name-only'],cwd=R,text=True).splitlines();assert not any(p.startswith('renders/') and not p.startswith('renders/jungle_pmd_v1/') for p in changed);ok('all previous renders, forest duo, cafe and Beach unchanged')
 (C/'verification.json').write_bytes(jsonbytes({'checks':checks,'PMDO_tested':False,'artistic_approval':False}));return checks


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
   path=unquote(urlsplit(self.path).path);name={'/':'JG1_duo.png','/entree':'JG1_entree.png','/finale':'JG1_finale.png','/animation':'JG1_duo_anime.webp'}.get(path,path.lstrip('/'))
   try:
    if name in {r['name'] for r in release_records()}:b=materialize(name).read_bytes()
    elif path.startswith('/jungle-pack/'):
     name=path[len('/jungle-pack/'):]
     with zipfile.ZipFile(materialize('JG1_jungle_duo_calques.zip')) as z:b=z.read(name)
    else:raise KeyError(path)
    self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(b)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(b)
   except (KeyError,StopIteration):self.send_error(404)
 print('Direct jungle PNG/WebP on 0.0.0.0:'+str(port),flush=True);ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()

def http_check(port):
 import urllib.request,urllib.error
 n=0
 def get(path):return urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}'+path,headers={'Host':f'{port}-preview.e2b.app'})).read()
 for r in release_records():assert get('/'+r['name'])==materialize(r['name']).read_bytes();n+=1
 for path,name in {'/':'JG1_duo.png','/entree':'JG1_entree.png','/finale':'JG1_finale.png','/animation':'JG1_duo_anime.webp'}.items():assert get(path)==materialize(name).read_bytes();n+=1
 with zipfile.ZipFile(materialize('JG1_jungle_duo_calques.zip')) as z:
  for name in z.namelist():assert get('/jungle-pack/'+name)==z.read(name);n+=1
 for path in ['/.git/config','/%2e%2e/.git/config','/jungle-pack/../../.git/config']:
  try:get(path);raise AssertionError('Private path exposed')
  except urllib.error.HTTPError as e:assert e.code==404
 print('PASS',n,'HTTP responses byte-identical; preview host accepted;3 private paths404')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--verify',action='store_true');p.add_argument('--restore',action='store_true');p.add_argument('--serve',action='store_true');p.add_argument('--http-check',action='store_true');p.add_argument('--port',type=int,default=8014);a=p.parse_args()
 if a.build:build()
 if a.verify:verify()
 if a.restore:
  for r in release_records():print(materialize(r['name']))
 if a.serve:serve(a.port)
 if a.http_check:http_check(a.port)
 if not any([a.build,a.verify,a.restore,a.serve,a.http_check]):p.print_help()
