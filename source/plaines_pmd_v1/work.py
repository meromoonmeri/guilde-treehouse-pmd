"""Two open H06P01 plains: native animated sky/distance + three generated planes."""
from pathlib import Path
from functools import lru_cache
import io,json,hashlib,subprocess,sys,zipfile,argparse
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage
R=Path(__file__).resolve().parents[2];S=R/'source/plaines_pmd_v1';C=R/'.cache/plaines_pmd_v1';O=C/'build';SIZE=(456,336)
REV=globals().get('REV','HEAD');RAW_REV='d808ecf5d5715107031f7abd23f73aec9a9d5697'
sys.path.insert(0,str(R/'source/dungeon_biomes_v1'))
from red import decode,palettes
from native_archive import native_source_archive
N=C/'native'
def sha(b):return hashlib.sha256(b).hexdigest()
def gitdata(path,rev=REV):return subprocess.check_output(['git','show',rev+':'+path],cwd=R)
@lru_cache(maxsize=16)
def support(name):
 p=S/name;return p.read_bytes() if p.exists() else gitdata(str(p.relative_to(R)))
def jb(j):return (json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode()
def img(b):return Image.open(io.BytesIO(b)).convert('RGBA')
def png(im):
 f=io.BytesIO();im.save(f,format='PNG',optimize=True);return f.getvalue()
@lru_cache(maxsize=8)
def raw(k):
 r=next(r for r in json.loads(support('raws/index.json')) if r['id']==k);b=gitdata(r['path'],RAW_REV);assert sha(b)==r['sha256'];im=img(b);assert sha(im.tobytes())==r['rgba_sha256'];return im

def source(k):
 a=np.array(raw(k).resize(SIZE,Image.Resampling.NEAREST));r,g,b=np.moveaxis(a[:,:,:3].astype(float),2,0);a[(r>120)&(b>100)&(g<130)&(r>g*1.6)&(b>g*1.5)]=0;return Image.fromarray(a)
def quant(im,cols):
 p=Image.new('P',(1,1));p.putpalette(np.vstack([cols,np.tile(cols[0],(256-len(cols),1))]).astype('uint8').tobytes());a=np.array(im);b=np.array(im.convert('RGB').quantize(palette=p,dither=Image.Dither.NONE).convert('RGBA'));b[:,:,3]=a[:,:,3];b[b[:,:,3]==0]=0;return Image.fromarray(b)
def native_init():
 N.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(native_source_archive()) as z:
  for s in ['.bpl','c.bpc','m.bma']:(N/('H06P01'+s)).write_bytes(z.read('data/map_bg/H06P01'+s))
 ims,meta,ix,_=decode('H06P01',0,N);assert not meta['bpa'];idx=ix[0];frames=np.stack([palettes((N/'H06P01.bpl').read_bytes(),i*4)[0].reshape(-1,4)[idx] for i in range(18)])
 sky=np.any((frames[:,:,:,2]>=frames[:,:,:,0])&(frames[:,:,:,2]>=frames[:,:,:,1])&(frames[:,:,:,3]>0),axis=0);sky[128:]=False
 return np.array(ims[0]),frames,sky,meta,idx

def generated(mode,ref):
 colors=np.unique(ref[:,:,:3].reshape(-1,3),axis=0);greens=colors[(colors[:,1]>colors[:,0])&(colors[:,1]>colors[:,2])&(colors[:,1]>90)];a=np.array(source('sol_'+mode));rgb=a[:,:,:3].astype(float)
 # Only the generated ground is colour-aligned at the distant boundary.
 for y in range(112,160):rgb[y]+=((160-y)/48)*(ref[y,:,:3].mean(0)-rgb[y].mean(0))
 a[:,:,:3]=np.clip(np.rint(rgb),0,255).astype('uint8');a[:112]=0;floor=quant(Image.fromarray(a),greens);rock=Image.new('RGBA',SIZE);src=source('rochers_'+mode);moves=[]
 specs=[((0,0,228,336),(56,40),(76,204)),((228,0,456,336),(56,40),(312,148))] if mode=='entree' else [((140,0,320,168),(80,56),(192,136)),((0,120,128,240),(32,24),(48,216))]
 for box,size,xy in specs:
  p=src.crop(box);tight=p.getbbox();assert tight;p=p.crop(tight);s=min(size[0]/p.width,size[1]/p.height);p=p.resize((round(p.width*s),round(p.height*s)),Image.Resampling.NEAREST);rock.alpha_composite(p,xy);moves.append({'source_box':box,'tight_bbox':tight,'output_size':p.size,'position':xy,'native':False})
 return [floor,quant(rock,colors),quant(source('herbes_'+mode),greens)],moves

def scene(files,rec,phase=0):
 im=Image.new('RGBA',SIZE)
 for l in rec['layers']:im.alpha_composite(img(files[l['frames'][phase%18] if 'frames' in l else l['file']]))
 return im

def duo(a,b):
 out=Image.new('RGB',(912,368),'#263c30');d=ImageDraw.Draw(out);d.text((12,10),'PLAINES SAUVAGES / ENTREE',fill='#e5ecc0');d.text((468,10),'PLAINES SAUVAGES / FINALE',fill='#e5ecc0');out.paste(a.convert('RGB'),(0,32));out.paste(b.convert('RGB'),(456,32));return out

def animate(frames,path):
 frames=[i.convert('RGB') for i in frames];dur=[round((i+1)*4000/60)-round(i*4000/60) for i in range(18)];frames[0].save(path,save_all=True,append_images=frames[1:],duration=dur,loop=0,lossless=True,method=6,minimize_size=True)

def build():
 O.mkdir(parents=True,exist_ok=True);ref,frames,sky,meta,idx=native_init();files={};tracks={}
 for role,title in [('ciel','Ciel et nuages natifs'),('collines','Collines et lointain natifs')]:
  paths=[]
  for f,a in enumerate(frames):
   b=a.copy()
   if role=='ciel':b[~sky]=0
   else:b[sky]=0;b[128:]=0
   name=f'fond_natif/WP1_{role}_{f:02d}.png';files[name]=png(Image.fromarray(b));paths.append(name)
  tracks[role]={'id':role,'title':title,'frames':paths,'frame_ticks':4,'period_ticks':72,'native_pixels':True,'scale':1,'clock':'same H06P01 BPL phase; do not desynchronize sky and distance'}
 for f,a in enumerate(frames):files[f'references/WP1_H06P01_natif_{f:02d}.png']=png(Image.fromarray(a))
 maps=[]
 for mode,tag in [('entree','E'),('fin','F')]:
  gen,moves=generated(mode,ref);rec={'id':mode,'tag':tag,'size':list(SIZE),'semantic_groups':5,'layers':[tracks['ciel'],tracks['collines']],'rock_placements':moves,'south':'arrival / return, open','north':'distant horizon, not an engine exit; entrance route reaches foreground y128'}
  for k,title,im in zip(['sol','rochers','herbes'],['Prairie continue','Rochers reperes','Herbes basses'],gen):
   name=f'calques/WP1_{tag}_{k}.png';files[name]=png(im);rec['layers'].append({'id':k,'title':title,'file':name,'native_pixels':False,'generation':k+'_'+mode})
  maps.append(rec);name='WP1_entree.png' if mode=='entree' else 'WP1_finale.png';out=scene(files,rec);files['apercus/'+name]=png(out);(O/name).write_bytes(png(out))
  board=Image.new('RGB',(912,1104),'#263c30');d=ImageDraw.Draw(board)
  panels=[(l['title'],img(files[l['frames'][0] if 'frames' in l else l['file']])) for l in rec['layers']]+[('Composition - CINQ groupes',out)]
  for j,(title,im) in enumerate(panels):
   x=j%2*456;y=j//2*368;d.text((x+8,y+8),title,fill='#e5ecc0');bg=Image.new('RGBA',SIZE,'#344939');bg.alpha_composite(im);board.paste(bg.convert('RGB'),(x,y+28))
  name=f'WP1_{tag}_calques.png';files['apercus/'+name]=png(board);(O/name).write_bytes(png(board));animate([scene(files,rec,f) for f in range(18)],O/f'WP1_{tag}_anime.webp')
 previews=[duo(scene(files,maps[0],f),scene(files,maps[1],f)) for f in range(18)];(O/'WP1_duo.png').write_bytes(png(previews[0]));files['apercus/WP1_duo.png']=png(previews[0]);animate(previews,O/'WP1_duo_anime.webp')
 audit=json.loads((R/'source/dungeon_biomes_v1/audit.json').read_text());manifest={'id':'WP1','canonical_place':'H06P01 wild plains','size':list(SIZE),'grid':8,'maps':maps,'native_metadata':meta,'native_weather':None,'animation':{'effective_period_ticks':72,'phase_ticks':4,'source_phases':18,'unique_native_states':len(set(a.tobytes() for a in frames)),'duration_ms':1200,'note':'BPL bank0 has10 declared entries but identical colours; banks1/7 have18 phases.72tick visible loop checked over declared360tick joint period. No cloud scrolling or grass animation invented.'},'processing':{'generated_floor':'Opaque fromy112 downward; generated RGB row means aligned to native distance betweeny112..159, then quantized to native grass colours. Native assets never altered.','native_background':'Fixed semantic mask; sky/white-blue pixels union across18 source phases, hills complement in top128rows. Exact source RGBA, shared bank between both maps.','generated_rocks':'Complete generated clumps proportionally normalized/repositioned, not native transformations.','sources':'2 full composition guides +6 separately generated planes'},'provenance':{'port':audit['port_commit'],'pret':audit['pret_commit'],'raw_commit':RAW_REV},'status':'technical checks only; not PMDO/artistically approved','progress':{'maps_on_published_branch_after_this_lot':16,'previous_MD1_maps_shown_but_not_present_on_recovered_remote':2,'remaining_new_duos':['foret_secrete','plaines_brulees'],'note':'MD1 previous push failed; its unpublished assets were absent from the restored checkout. Do not count them as published or silently replace them.'}}
 files['manifest.json']=jb(manifest);files['README.md']=support('README.md');files['assemble.py']=support('assemble.py');files['provenance/generations.json']=support('raws/index.json')
 for p in sorted(N.iterdir()):
  if p.name.startswith('H06P01'):files['native/data/map_bg/'+p.name]=p.read_bytes()
 files['native/decoder.py']=(R/'source/dungeon_biomes_v1/red.py').read_bytes();files['native/provenance.json']=jb({'port':audit['port_commit'],'pret':audit['pret_commit'],'files':{p.name:sha(p.read_bytes()) for p in sorted(N.iterdir()) if p.name.startswith('H06P01')}})
 with zipfile.ZipFile(O/'WP1_plaines_duo_calques.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,b in sorted(files.items()):
   info=zipfile.ZipInfo(name,(2026,9,21,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,b,compresslevel=9)
 print('Built',len(files),'portable files and9 direct previews/pack')


def verify():
 checks=[]
 def ok(s):checks.append(s);print('PASS',s)
 for r in json.loads(support('raws/index.json')):assert list(raw(r['id']).size)==r['size']
 ok('8 raw generations preserved losslessly and SHA/RGBA checked')
 ref,native,sky,meta,idx=native_init()
 with zipfile.ZipFile(R/'renders/dungeon_biomes_v1/DB1_cinq_duos_multicalques.zip') as old:assert img(old.read('references/DB1_native_H06P01.png')).tobytes()==ref.tobytes()
 for f in range(90):
  a=palettes((N/'H06P01.bpl').read_bytes(),f*4)[0].reshape(-1,4)[idx];assert np.array_equal(a,native[f%18])
 for f in range(18):assert decode('H06P01',f*4,N)[0][0].tobytes()==native[f].tobytes()
 ok('18 source phases decoded exactly;72tick visual period proved over all90 declared joint states')
 with zipfile.ZipFile(O/'WP1_plaines_duo_calques.zip') as z:
  assert z.testzip() is None;files={n:z.read(n) for n in z.namelist()};m=json.loads(files['manifest.json']);tracks=m['maps'][0]['layers'][:2]
  for f in range(18):
   skyim=img(files[tracks[0]['frames'][f]]);hill=img(files[tracks[1]['frames'][f]]);native_part=Image.alpha_composite(skyim,hill);expected=native[f].copy();expected[128:]=0;assert native_part.tobytes()==expected.tobytes();assert img(files[f'references/WP1_H06P01_natif_{f:02d}.png']).tobytes()==native[f].tobytes()
  ok('sky and hills36 PNGs exactly recompose native background1x;18 full reference frames unmodified')
  for rec in m['maps']:
   assert len(rec['layers'])==rec['semantic_groups']==5;a=[np.array(img(files[l['frames'][0] if 'frames' in l else l['file']])) for l in rec['layers']];assert (a[2][112:,:,3]==255).all();assert not a[2][:112,:,3].any();assert ((a[1][:,:,3]>0)&(a[2][:,:,3]>0)).any();assert (a[2][:,:,3][a[3][:,:,3]>0]==255).all();assert (a[2][:,:,3][a[4][:,:,3]>0]==255).all()
   obstacles=(a[3][:,:,3]>0)|(a[4][:,:,3]>0);free=(a[2][:,:,3]>0)&~obstacles;safe=ndimage.binary_erosion(free,np.ones((17,17)));labels,_=ndimage.label(safe);lab=labels[320,228];assert lab>0
   if rec['id']=='entree':assert labels[128,228]==lab
   else:assert not obstacles[216:304,120:336].any();assert labels[240,228]==lab
   for f in range(18):assert scene(files,rec,f).crop((0,0,456,100)).tobytes()==Image.fromarray(native[f]).crop((0,0,456,100)).tobytes()
   name='WP1_entree.png' if rec['id']=='entree' else 'WP1_finale.png';assert scene(files,rec).tobytes()==img((O/name).read_bytes()).tobytes()
  ok('5 semantic groups each, true continuous ground under scenery, real overlap, south route and216x88 finale arena,8px conservative clearance')
  names=[]
  for name,b in files.items():
   if not name.endswith('.png'):continue
   im=img(b);assert im.width%8==im.height%8==0;a=np.array(im);assert not ((a[:,:,0]>220)&(a[:,:,1]<45)&(a[:,:,2]>220)&(a[:,:,3]>0)).any();names.append(Path(name).name)
  assert len(names)==len(set(names));ok(f'{len(names)} PNGs Ground8, unique basenames, no visible magenta')
  dest=C/'verify_pack';dest.mkdir(exist_ok=True);z.extractall(dest);subprocess.run([sys.executable,str(dest/'assemble.py'),'--tick','28','--out',str(dest/'assembled')],check=True)
  for rec in m['maps']:assert img((dest/'assembled'/f"WP1_{rec['id']}_tick28.png").read_bytes()).tobytes()==scene(files,rec,7).tobytes()
  ok('standalone assembler exact at nonzero tick28')
  for name,rec in [('WP1_E_anime.webp',m['maps'][0]),('WP1_F_anime.webp',m['maps'][1]),('WP1_duo_anime.webp',None)]:
   with Image.open(O/name) as w:
    assert w.n_frames>1 and w.info['loop']==0;elapsed=0
    for f in range(w.n_frames):
     w.seek(f);w.load();phase=max(i for i in range(18) if round(i*4000/60)<=elapsed);expected=scene(files,rec,phase) if rec else duo(scene(files,m['maps'][0],phase),scene(files,m['maps'][1],phase));assert w.convert('RGB').tobytes()==expected.convert('RGB').tobytes();elapsed+=w.info['duration']
    assert elapsed==1200
  ok('3 lossless animated WebP files: decoded frames exact, full1200ms loop, native holds preserved')
 changed=subprocess.check_output(['git','diff','2368b715','--name-only'],cwd=R,text=True).splitlines();assert not any(p.startswith('renders/') and not p.startswith('renders/plaines_pmd_v1/') for p in changed);ok('all previously published renders, jungle/forest/cafe/Beach unchanged; no claim MD1 was pushed')
 (C/'verification.json').write_bytes(jb({'checks':checks,'engine_validation':False,'artistic_approval':False}));return checks


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
   path=unquote(urlsplit(self.path).path);name={'/':'WP1_duo.png','/entree':'WP1_entree.png','/finale':'WP1_finale.png','/animation':'WP1_duo_anime.webp'}.get(path,path.lstrip('/'))
   try:
    if name in {r['name'] for r in release_records()}:b=materialize(name).read_bytes()
    elif path.startswith('/plaines-pack/'):
     name=path[len('/plaines-pack/'):]
     with zipfile.ZipFile(materialize('WP1_plaines_duo_calques.zip')) as z:b=z.read(name)
    else:raise KeyError(path)
    self.send_response(200);self.send_header('Content-Type',mimetypes.guess_type(name)[0] or 'application/octet-stream');self.send_header('Content-Length',str(len(b)));self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(b)
   except (KeyError,StopIteration):self.send_error(404)
 print('Direct plaines PNG/WebP on 0.0.0.0:'+str(port),flush=True);ThreadingHTTPServer(('0.0.0.0',port),Handler).serve_forever()

def http_check(port):
 import urllib.request,urllib.error
 n=0
 def get(path):return urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}'+path,headers={'Host':f'{port}-preview.e2b.app'})).read()
 for r in release_records():assert get('/'+r['name'])==materialize(r['name']).read_bytes();n+=1
 for path,name in {'/':'WP1_duo.png','/entree':'WP1_entree.png','/finale':'WP1_finale.png','/animation':'WP1_duo_anime.webp'}.items():assert get(path)==materialize(name).read_bytes();n+=1
 with zipfile.ZipFile(materialize('WP1_plaines_duo_calques.zip')) as z:
  for name in z.namelist():assert get('/plaines-pack/'+name)==z.read(name);n+=1
 for path in ['/.git/config','/%2e%2e/.git/config','/plaines-pack/../../.git/config']:
  try:get(path);raise AssertionError('Private path exposed')
  except urllib.error.HTTPError as e:assert e.code==404
 print('PASS',n,'HTTP responses byte-identical; preview host accepted;3 private paths404')

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--build',action='store_true');p.add_argument('--verify',action='store_true');p.add_argument('--restore',action='store_true');p.add_argument('--serve',action='store_true');p.add_argument('--http-check',action='store_true');p.add_argument('--port',type=int,default=8016);a=p.parse_args()
 if a.build:build()
 if a.verify:verify()
 if a.restore:
  for r in release_records():print(materialize(r['name']))
 if a.serve:serve(a.port)
 if a.http_check:http_check(a.port)
 if not any([a.build,a.verify,a.restore,a.serve,a.http_check]):p.print_help()
