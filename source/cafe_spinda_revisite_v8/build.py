"""Partial V8 collection (generation quota) + complete five-room subtle night treatment."""
from pathlib import Path
import json,io,zipfile,hashlib,math,copy,sys
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;O=R/'renders/cafe_spinda_revisite_v8';V7=R/'renders/cafe_spinda_revisite_v7';sys.path.insert(0,str(S))
import importlib.util
spec=importlib.util.spec_from_file_location('archive_v8',S/'archive.py');arc=importlib.util.module_from_spec(spec);spec.loader.exec_module(arc)
FACTORS=[.42,.35,.40]
def rgba(p):return Image.open(p).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG',optimize=True);return b.getvalue()
def h(data):return hashlib.sha256(data).hexdigest()
def key(im):
 a=np.array(im);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);mask=(r>g*1.4+30)&(b>g*1.4+30)&(r>95)&(b>95);a[mask]=0;return Image.fromarray(a)
def grade(im,role=None):
 a=np.array(im);a[:,:,:3]=np.rint(a[:,:,:3]*np.array(FACTORS)).astype('uint8')
 if role=='lumieres':a[:,:,3]=np.rint(a[:,:,3]*.18).astype('uint8')
 a[a[:,:,3]==0]=0;return Image.fromarray(a)
def ambient(scene):
 a=np.array(scene);yy,xx=np.indices(a.shape[:2]);strength=np.zeros(a.shape[:2],float)
 for x,y,rx,ry,power in [(184,205,115,84,24),(416,205,115,84,24),(300,275,155,105,9)]:strength+=power*np.exp(-2*((xx-x)**2/rx**2+(yy-y)**2/ry**2))
 out=np.zeros_like(a);out[:,:,:3]=[246,182,108];out[:,:,3]=np.rint(np.minimum(strength,32)*(a[:,:,3]/255)).astype('uint8');out[out[:,:,3]==0]=0;return Image.fromarray(out)
def composite(layers,payloads):
 im=Image.new('RGBA',(600,448))
 for l in layers:im.alpha_composite(rgba(io.BytesIO(payloads[l['file']])))
 return im

def zip_entry(z,name,data):
 info=zipfile.ZipInfo(name,(2026,9,21,0,0,0));info.compress_type=zipfile.ZIP_STORED;z.writestr(info,data)
def writezip(path,files):
 with zipfile.ZipFile(path,'w',zipfile.ZIP_STORED) as z:
  for name,data in sorted(files.items()):zip_entry(z,name,data)
 with zipfile.ZipFile(path) as z:
  assert z.testzip() is None
  for name,data in files.items():assert z.read(name)==data

def build():
 O.mkdir(exist_ok=True);(O/'assets').mkdir(exist_ok=True);(O/'audit').mkdir(exist_ok=True)
 plan=json.loads((S/'plan.json').read_text());records=arc.entries();available={Path(r['path']).stem for r in records if r['path'].endswith('.webp')};items=[];assets=[];payloads={}
 for item in plan['items']:
  rec=copy.deepcopy(item);ident=item['id'];rec['native_output']=False;rec['reference_native']=rec.pop('native',True)
  if ident not in available:rec['status']='pending_generation'
  elif ident=='table_halcyon_vide':rec.update(status='rejected_camera',reason='Generated from underneath rather than the PMD overhead view; not included in production sheets.')
  else:
   raw=arc.image(S/'raws'/f'{ident}.webp');im=key(raw);box=im.getbbox();crop=im.crop(box);w,hg=item['target_size'];scale=min((w-4)/crop.width,(hg-4)/crop.height);size=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)));small=crop.resize(size,Image.Resampling.NEAREST);sprite=Image.new('RGBA',(w,hg));sprite.paste(small,((w-size[0])//2,hg-size[1]-2))
   files={}
   for mode,output in [('jour',sprite),('nuit',grade(sprite))]:
    name=f'assets/SpindaV8_{ident}_{mode}.png';output.save(O/name,optimize=True);payloads[name]=(O/name).read_bytes();files[mode]=name
   rec.update(status='generated_ready_for_review',files=files,size=[w,hg],visible_size=list(size),raw_rgba_sha256=h(raw.tobytes()),raw_crop=list(box),processing='Magenta key + aspect-preserving nearest normalization; generated art only.')
   assets.append({'id':ident,'title':item['title'],'files':files,'size':[w,hg],'visible_size':list(size),'reference':'../cafe_spinda_revisite_v7/'+item['file'] if item.get('scope','').startswith('V7') else '../../'+item['reference'],'native':False})
  items.append(rec)
 # Explicitly keep missing work out of the finished sheet.
 coverage={'status':'PARTIAL — image tool cap of 10 per turn reached','planned_furniture':len(items),'generated_attempts':len(available),'accepted':len(assets),'rejected':['table_halcyon_vide'],'pending':len(items)-len(assets),'items':items,'decor_pending':{'wall_ribbons':'Not generated. No empty layer presented as delivered ribbons.','wall_windows':'V7 32px windows retained temporarily; in-context generator revision pending.','appliques':'Not generated; current night uses soft indirect ambient light, not depicted fixtures or fire.'},'scope':plan['coverage'],'style':plan['style']}
 (O/'audit/coverage.json').write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+'\n')
 # One coherent collection, exported in day/night variants; no three separate themes.
 coords=[];x=y=8;rh=0
 for a in assets:
  w,hg=a['size']
  if x+w+8>512:x=8;y+=rh+8;rh=0
  coords.append({'id':a['id'],'rect':[x,y,w,hg]});x+=w+8;rh=max(rh,hg)
 size=(512,math.ceil((y+rh+8)/8)*8);sheets={}
 for mode in ['jour','nuit']:
  im=Image.new('RGBA',size)
  for rec in coords:
   a=next(a for a in assets if a['id']==rec['id']);x,y,w,hg=rec['rect'];obj=rgba(O/a['files'][mode]);im.paste(obj,(x,y));assert im.crop((x,y,x+w,y+hg)).tobytes()==obj.tobytes()
  file=f'assets/SpindaV8_collection_lot1_{mode}.png';im.save(O/file,optimize=True);payloads[file]=(O/file).read_bytes();sheets[mode]=file
 (O/'audit/tilesheet_index.json').write_text(json.dumps({'grid':8,'size':size,'files':sheets,'objects':coords},indent=2)+'\n')
 base=zipfile.ZipFile(V7/'SpindaV7_complet.zip');old=json.loads(base.read('manifest.json'));rooms=[];checks=[];scenes={}
 for room in old['rooms']:
  rec={k:copy.deepcopy(room[k]) for k in ['id','title','level','size','ports']};rec['modes']={};day=Image.new('RGBA',(600,448))
  for l in room['layers']:day.alpha_composite(rgba(io.BytesIO(base.read(l['file']))))
  for mode in ['jour','nuit']:
   layers=[]
   for l in room['layers']:
    src=rgba(io.BytesIO(base.read(l['file'])));im=src if mode=='jour' else grade(src,l['id']);file=f'calques/SpindaV8_{room["id"]}_{mode}_{l["id"]}.png';payloads[file]=png(im)
    title=l['title']
    if l['id']=='fenetres':title='Fenêtres V7 · nouvelle génération en attente'
    if l['id']=='lumieres' and mode=='nuit':title='Motifs du parquet · très atténués'
    layers.append({'id':l['id'],'title':title,'file':file,'default':True})
   if mode=='nuit':
    file=f'calques/SpindaV8_{room["id"]}_nuit_lumiere_tamisee.png';payloads[file]=png(ambient(day));layers.append({'id':'lumiere_tamisee','title':'Lumière chaude diffuse · indépendante','file':file,'default':True})
   rec['modes'][mode]={'layers':layers};scenes[room['id'],mode]=composite(layers,payloads)
  assert scenes[room['id'],'jour'].tobytes()==day.tobytes()
  a=np.array(day);b=np.array(scenes[room['id'],'nuit']);assert np.array_equal(a[:,:,3],b[:,:,3]);mask=a[:,:,3]>0;ratio=float(b[:,:,:3][mask].mean()/a[:,:,:3][mask].mean());assert .3<ratio<.55
  for p in room['ports'].values():
   x,y=p['point'];assert a[y,x,3]==b[y,x,3]==255
  checks.append({'room':room['id'],'day_exact_V7':True,'night_alpha_exact_day':True,'night_mean_rgb_ratio':ratio,'warm_overlay_max_alpha':int(np.array(ambient(day))[:,:,3].max())});rooms.append(rec)
 m={'version':'Spinda V8 · lot 1 / nuit','status':coverage['status'],'rooms':rooms,'assets':assets,'sheets':sheets,'coverage':'audit/coverage.json','pending':coverage['decor_pending'],'planned':len(items),'accepted':len(assets),'attempts':len(available),'pack':'SpindaV8_atelier_lot1.zip','packed_layers':True,'night':{'rgb_factors':FACTORS,'floor_motifs_alpha_factor':.18,'light':'Static subtle indirect warmth, separate RGBA layer; no flame or animation claimed.'},'runtime_PMDO':'NOT TESTED'}
 (O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n');template=(S/'viewer.html').read_text();page=template.replace('__DATA__',json.dumps(m,ensure_ascii=False));(O/'index.html').write_text(page)
 (R/'apercu_cafe_spinda_revisite_v8.html').write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=renders/cafe_spinda_revisite_v8/index.html"><a href="renders/cafe_spinda_revisite_v8/index.html">V8 : lot 1 et nuit</a></html>\n')
 files=dict(payloads);portable=copy.deepcopy(m);portable['packed_layers']=False
 for a in portable['assets']:
  ref='references/'+a['id']+'.png';files[ref]=(O/a['reference']).read_bytes();a['reference']=ref
 files['index.html']=template.replace('__DATA__',json.dumps(portable,ensure_ascii=False)).replace('id="pack"','hidden id="pack"').encode();files['manifest.json']=json.dumps(portable,ensure_ascii=False,indent=2).encode()
 for name in ['README.md','audit/coverage.json','audit/tilesheet_index.json']:files[name]=(O/name).read_bytes()
 writezip(O/m['pack'],files)
 small={name:data for name,data in payloads.items() if name.startswith('assets/')}
 small['audit/coverage.json']=(O/'audit/coverage.json').read_bytes();small['audit/tilesheet_index.json']=(O/'audit/tilesheet_index.json').read_bytes();small['README.md']=(O/'README.md').read_bytes();writezip(O/'SpindaV8_mobilier_lot1.zip',small)
 # Actual render, without adding unrequested furniture in the map.
 board=Image.new('RGB',(1200,500),'#1e1920');d=ImageDraw.Draw(board)
 for i,mode in enumerate(['jour','nuit']):
  im=scenes['cafe',mode];board.paste(im,(600*i,28),im);d.text((600*i+12,8),'CAFE - '+mode.upper(),fill='#e5d4b7')
 d.text((12,478),'Architecture V7 conservee. Fenetres heritees : regeneration en attente. Rubans non encore generes.',fill='#c1b6aa');board.save(O/'SpindaV8_jour_nuit.jpg',quality=82)
 board=Image.new('RGB',(1000,640),'#2c2630');d=ImageDraw.Draw(board)
 for i,a in enumerate(assets):
  x=(i%5)*200;y=(i//5)*280;im=rgba(O/a['files']['jour']);im.thumbnail((180,195),Image.Resampling.NEAREST);scale=min(3,180/im.width,195/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST);board.paste(im,(x+(200-im.width)//2,y+45),im);d.text((x+6,y+8),a['id'],fill='#f1d9b0');d.text((x+6,y+245),str(a['visible_size'])+' px - genere',fill='#c1b6aa')
 d.text((12,586),'Lot 1 : 9 objets retenus / 36 prevus. 10 generations : table vide rejetee (mauvais angle).',fill='#f1d9b0');board.save(O/'SpindaV8_mobilier_lot1.jpg',quality=84)
 report={'pass':True,'partial':True,'generated_attempts':len(available),'accepted':len(assets),'planned':len(items),'rooms_modes_tested':10,'rooms':checks,'png_layers':sum(len(mode['layers']) for r in rooms for mode in r['modes'].values()),'full_pack_entries':len(files),'full_pack_bytes':(O/m['pack']).stat().st_size,'native_assets_modified':False,'new_ribbons_delivered':False,'new_windows_delivered':False,'PMDO':'NOT TESTED'}
 (O/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return m
if __name__=='__main__':build()
