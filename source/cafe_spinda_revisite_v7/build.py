"""V7 additive correction delta + native-size furniture library. Previous exports stay unchanged."""
from pathlib import Path
import sys,json,io,zipfile,copy,math,hashlib
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;O=R/'renders/cafe_spinda_revisite_v7';V6=R/'renders/cafe_spinda_revisite_v6';sys.path.insert(0,str(S))
from archive import image as raw_image
from native import make as native_library

def rgba(p):return Image.open(p).convert('RGBA')
def sha(data):return hashlib.sha256(data).hexdigest()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG',optimize=True);return b.getvalue()
def key(im):
 a=np.array(im);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);mask=(r>g*1.4+30)&(b>g*1.4+30)&(r>95)&(b>95);a[mask]=0;return Image.fromarray(a)
def layer_image(layer,base):
 if layer['file'].startswith('calques/'):im=rgba(io.BytesIO(base.read(layer['file'])))
 else:im=rgba(O/layer['file'])
 full=Image.new('RGBA',(600,448));full.alpha_composite(im,tuple(layer.get('position',[0,0])))
 if layer.get('erase_rect'):ImageDraw.Draw(full).rectangle([*layer['erase_rect'][:2],layer['erase_rect'][2]-1,layer['erase_rect'][3]-1],fill=(0,0,0,0))
 return full

def compose(room,base,windows=True):
 out=Image.new('RGBA',(600,448))
 for l in room['layers']:
  if windows or l['id']!='fenetres':out.alpha_composite(layer_image(l,base))
 return out

def sheets(assets):
 results=[]
 for group,title in [('spinda','Spinda / Qulbutoké · natifs 1×'),('halcyon','Halcyon · mobilier natif 1×'),('kirlia','Kirlia · créations'),('alcremie','Charmilly · créations')]:
  selected=[a for a in assets if a.get('group')==group];x=y=8;rowh=0;positions=[]
  for a in selected:
   w,h=a['size']
   if x+w+8>512:x=8;y+=rowh+8;rowh=0
   positions.append((a,x,y));x+=w+8;rowh=max(rowh,h)
  height=math.ceil((y+rowh+8)/8)*8;out=Image.new('RGBA',(512,height));mapping=[]
  for a,x,y in positions:
   im=rgba(O/a['file']);out.paste(im,(x,y));assert out.crop((x,y,x+im.width,y+im.height)).tobytes()==im.tobytes();mapping.append({'id':a['id'],'rect':[x,y,im.width,im.height]})
  file='tilesheets/SpindaV7_'+group+'.png';(O/'tilesheets').mkdir(exist_ok=True);out.save(O/file,optimize=True)
  rec={'id':'sheet_'+group,'title':'Tilesheet · '+title,'file':file,'size':list(out.size),'native':group in ['spinda','halcyon'],'objects':mapping,'grid':8};results.append(rec)
 (O/'tilesheets/index.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n');return results

def package_full(m,base):
 portable=copy.deepcopy(m);portable['packed_layers']=False;files={}
 for room in portable['rooms']:
  for l in room['layers']:
   im=layer_image(l,base);dest=l['png'];files[dest]=png(im);l['file']=dest;l.pop('position',None);l.pop('erase_rect',None)
 for a in portable['assets']:files[a['file']]=(O/a['file']).read_bytes()
 for anim in portable['animations'].values():
  frames=[]
  for f in anim['frames']:
   dest='assets/'+Path(f).name;files[dest]=(O/f).read_bytes();frames.append(dest)
  dest='assets/'+Path(anim['sheet']).name;files[dest]=(O/anim['sheet']).read_bytes();anim.update(frames=frames,sheet=dest)
 files['manifest.json']=(json.dumps(portable,ensure_ascii=False,indent=2)+'\n').encode()
 files['index.html']=(S/'viewer.html').read_text().replace('__DATA__',json.dumps(portable,ensure_ascii=False)).replace('id="pack" href=','hidden id="pack" href=').replace('id="objects-pack" href=','hidden id="objects-pack" href=').encode()
 for name in ['README.md','audit/AUDIT.md','audit/native_sizes.json','audit/native_sizes.csv','tilesheets/index.json']:files[name]=(O/name).read_bytes()
 with zipfile.ZipFile(O/'SpindaV7_complet.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,data in sorted(files.items()):z.writestr(name,data)
 with zipfile.ZipFile(O/'SpindaV7_complet.zip') as z:
  assert z.testzip() is None
  for room in portable['rooms']:
   expected=compose(next(r for r in m['rooms'] if r['id']==room['id']),base);actual=Image.new('RGBA',(600,448))
   for l in room['layers']:actual.alpha_composite(rgba(io.BytesIO(z.read(l['file']))))
   assert actual.tobytes()==expected.tobytes()
 return len(files)

def build():
 O.mkdir(exist_ok=True);(O/'corrections').mkdir(exist_ok=True);assets,audit=native_library();assets=copy.deepcopy(assets);base=zipfile.ZipFile(V6/'SpindaV6_pack.zip');old=json.loads((V6/'manifest.json').read_text());m=copy.deepcopy(old)
 # Generated sprites are normalized to the measured furniture scale; native sprites are never resized.
 generated=[]
 for name,title,maxsize,group in [('kirlia_counter_front','Comptoir Kirlia · création',(120,96),'kirlia'),('alcremie_counter_front','Comptoir Charmilly · création',(120,96),'alcremie'),('kirlia_bench','Banquette Kirlia · création',(56,40),'kirlia'),('alcremie_trolley','Desserte Charmilly · création',(40,48),'alcremie')]:
  raw=raw_image(S/'raws'/f'{name}.webp');clean=key(raw);box=clean.getbbox();crop=clean.crop(box);scale=min(maxsize[0]/crop.width,maxsize[1]/crop.height);size=(max(1,round(crop.width*scale)),max(1,round(crop.height*scale)))
  small=crop.resize(size,Image.Resampling.NEAREST);canvas=Image.new('RGBA',(math.ceil((size[0]+8)/8)*8,math.ceil((size[1]+8)/8)*8));canvas.paste(small,(4,4));file='assets/SpindaV7_'+name+'.png';canvas.save(O/file,optimize=True)
  rec={'id':name,'title':title,'file':file,'native':False,'group':group,'size':list(canvas.size),'visible_size':list(size),'source_crop':list(box),'source_size':list(raw.size),'source_rgba_sha256':sha(raw.tobytes()),'normalization':'Nearest, generated art only; aspect ratio retained','raw_archive':'source/cafe_spinda_revisite_v7/raws/archive.json'};generated.append(rec);assets.append(rec)
 (O/'audit/generated_provenance.json').write_text(json.dumps(generated,ensure_ascii=False,indent=2)+'\n')
 # Much smaller café-designed windows; their old centres are preserved.
 big=rgba(V6/'assets/SpindaV6_oculus_cafe.png');small=big.crop(big.getbbox()).resize((28,28),Image.Resampling.NEAREST);window=Image.new('RGBA',(32,32));window.paste(small,(2,2));window.save(O/'assets/SpindaV7_oculus_32.png');assets.insert(0,{'id':'window','title':'Oculus café réduit · 32 × 32','file':'assets/SpindaV7_oculus_32.png','size':[32,32],'native':False})
 correction=key(raw_image(S/'raws/north_corrected.webp').resize((200,184),Image.Resampling.NEAREST));reports=[]
 for room in m['rooms']:
  original=compose(room,base,False)
  room['raw_in_repository']=str((V6/room.pop('raw')).resolve().relative_to(R))
  for l in room['layers']:l['png']=l['png'].replace('SpindaV6_','SpindaV7_')
  if room['id'] in ['accueil','casino']:
   patch=np.array(correction).copy();oldcrop=np.array(original.crop((200,0,400,184)));yy,xx=np.indices((184,200));weight=np.minimum.reduce([np.clip(xx/4,0,1),np.clip((199-xx)/4,0,1),np.clip((183-yy)/8,0,1)])[:,:,None]
   solid=(patch[:,:,3]==255)&(oldcrop[:,:,3]==255);mixed=np.round(patch.astype(float)*weight+oldcrop.astype(float)*(1-weight)).astype('uint8');patch[solid]=mixed[solid]
   file='corrections/SpindaV7_'+room['id']+'_nord.png';Image.fromarray(patch).save(O/file,optimize=True)
   for l in room['layers']:
    if l['id']=='acces_N':l.update(file=file,position=[200,0],title='Montée N · mur occultant, bordure corrigée')
    else:l['erase_rect']=[200,0,400,184]
   current=compose(room,base,False);a=np.array(current);b=np.array(original);outside=np.ones((448,600),bool);outside[:184,200:400]=False;assert np.array_equal(a[outside],b[outside]);assert a[52:76,280:320,:3].mean()<90
   # Former upper landing is replaced by shadow/occluding wall; no bright floor beyond the flight.
   rgb=a[:80,268:336,:3];gold=(rgb[:,:,0]>205)&(rgb[:,:,1]>155)&(rgb[:,:,2]<170);assert gold.sum()<20
   reports.append({'room':room['id'],'edit_rect':[200,0,400,184],'outside_rgba_identical':True,'upper_opening_mean_rgb':float(a[52:76,280:320,:3].mean()),'bright_upper_landing_pixels':int(gold.sum())})
  if room['windows']:
   positions=[[x+16,y+16] for x,y in room['windows']];layer=Image.new('RGBA',(600,448))
   for pos in positions:layer.alpha_composite(window,tuple(pos))
   file='corrections/SpindaV7_'+room['id']+'_petites_fenetres.png';layer.save(O/file,optimize=True);next(l for l in room['layers'] if l['id']=='fenetres').update(file=file,title='Petits oculus café · 32 px');room['windows']=positions
  for p in room['ports'].values():
   x,y=p['point'];assert compose(room,base,False).getpixel((x,y))[3]==255
 m.update(title='Spinda · petites fenêtres, montées occultées, mobilier 1×',assets=assets+sheets(assets),base_layers_archive='../cafe_spinda_revisite_v6/SpindaV6_pack.zip',pack='SpindaV7_complet.zip',packed_layers=True,window='Generated café oculus: 32×32 canvas, 28 px visible, no guild sprite',layers_storage='Inherited V6 PNGs plus explicit 200×184 correction deltas; standalone full PNG pack materializes all layers independently of V6',runtime_PMDO='NOT TESTED')
 (O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
 template=(S/'viewer.html').read_text();(O/'index.html').write_text(template.replace('__DATA__',json.dumps(m,ensure_ascii=False)))
 (R/'apercu_cafe_spinda_revisite_v7.html').write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=renders/cafe_spinda_revisite_v7/index.html"><a href="renders/cafe_spinda_revisite_v7/index.html">Atelier Spinda V7</a></html>\n')
 count=package_full(m,base)
 with zipfile.ZipFile(O/'SpindaV7_objets_tilesheets.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for a in m['assets']:z.write(O/a['file'],a['file'])
  for name in ['audit/AUDIT.md','audit/native_sizes.json','audit/native_sizes.csv','audit/generated_provenance.json','tilesheets/index.json']:z.write(O/name,name)
 with zipfile.ZipFile(O/'SpindaV7_objets_tilesheets.zip') as z:assert z.testzip() is None
 report={'pass':True,'native_objects':len(audit['objects']),'generated_furniture':len(generated),'tilesheets':4,'windows_canvas':[32,32],'window_visible':[28,28],'stairs':reports,'full_pack_entries':count,'full_pack_rgba_matches_viewer_layers':True,'native_assets_no_resampling_recolour_rotation':True,'PMDO':'NOT TESTED','artistic_approval':'Pending user review'}
 (O/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
 # Review sheet: actual new rooms, not a conceptual illustration.
 board=Image.new('RGB',(1200,950),'#261e1b');d=ImageDraw.Draw(board)
 for i,id in enumerate(['accueil','casino','cafe']):
  room=next(r for r in m['rooms'] if r['id']==id);im=Image.new('RGBA',(600,448),'magenta');im.alpha_composite(compose(room,base));x=(i%2)*600;y=(i//2)*475;board.paste(im,(x,y+20));d.text((x+10,y+3),id.upper()+' - correction V7',fill='#f1d6a6')
 y=520
 for a,x in [(assets[0],646),(next(a for a in assets if a['id']=='table_spinda_tasses'),760)]:
  im=rgba(O/a['file']).resize((a['size'][0]*2,a['size'][1]*2),Image.Resampling.NEAREST);board.paste(im,(x,y),im)
 d.text((626,495),'ECHELLE x2 : oculus 32px / table native 43px',fill='#f1d6a6');d.text((626,640),'Comptoirs natifs : 120 x 96 px, a 1x',fill='#f1d6a6')
 for j,id in enumerate(['comptoir_spinda','comptoir_qulbutoke']):
  a=next(a for a in assets if a['id']==id);im=rgba(O/a['file']).resize((240,192),Image.Resampling.NEAREST);board.paste(im,(620+j*275,665),im)
 board.save(O/'SpindaV7_corrections.jpg',quality=78)
 board=Image.new('RGB',(1024,768),'#272c33');d=ImageDraw.Draw(board)
 ids=['comptoir_spinda','comptoir_qulbutoke','kirlia_counter_front','alcremie_counter_front','table_spinda_tasses','table_halcyon_vide','kirlia_bench','alcremie_trolley']
 for i,id in enumerate(ids):
  a=next(a for a in assets if a['id']==id);im=rgba(O/a['file']).resize((a['size'][0]*2,a['size'][1]*2),Image.Resampling.NEAREST);x=(i%4)*256;y=(i//4)*340;board.paste(im,(x+8,y+40),im);d.text((x+8,y+8),id.replace('_front',''),fill='#ecdfc3');d.text((x+8,y+275),str(a['visible_size'])+' px / '+('NATIF 1x' if a['native'] else 'CREATION'),fill='#c6cfd7')
 d.text((12,708),'Taille affichee x2 pour tous : aucun meuble natif agrandi dans les PNG.',fill='#ecdfc3');board.save(O/'SpindaV7_mobilier.jpg',quality=83)
 print(json.dumps(report,indent=2));return m
if __name__=='__main__':build()
