"""New N/S generations + café-designed window. PNG layers live in a portable ZIP (no duplicates)."""
from pathlib import Path
import sys,json,hashlib,io,zipfile,copy
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;O=R/'renders/cafe_spinda_revisite_v6';OLD=R/'renders/cafe_spinda_reseau_v4';SIZE=(600,448)
import importlib.util
_spec=importlib.util.spec_from_file_location('spinda_v4_build',R/'source/cafe_spinda_reseau_v4/build.py');_old=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_old);SPECS=_old.SPECS;oldbase=_old.base
# Running this file as __main__ imports the historical build module under its own name.
def rgba(p):return Image.open(p).convert('RGBA')
def digest(b):return hashlib.sha256(b).hexdigest()
def png(im):
 b=io.BytesIO();im.save(b,format='PNG',optimize=True);return b.getvalue()
def key(im):
 a=np.array(im);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);mag=(r>g*1.4+30)&(b>g*1.4+30)&(r>95)&(b>95);a[mag]=0
 labels,n=nd.label(a[:,:,3]>0,np.ones((3,3)));counts=np.bincount(labels.ravel());keep=counts>=10;keep[0]=False;a[~keep[labels]]=0;return a

def archive():
 records=[]
 for name in ['accueil','casino','cafe','fenetre_cafe']:
  p=O/'bruts'/f'{name}.webp';source=R/'.cache/spinda6'/f'{name}.png'
  if not p.exists():
   im=rgba(source);im.save(p,lossless=True,exact=True,method=6);assert rgba(p).tobytes()==im.tobytes()
  im=rgba(p);records.append({'original_png_sha256':digest(source.read_bytes()) if source.exists() else next((x.get('original_png_sha256') for x in json.loads((O/'generation_provenance.json').read_text())['generations'] if x['file']==str(p.relative_to(O))),None),'file':str(p.relative_to(O)),'size':list(im.size),'rgba_sha256':digest(im.tobytes()),'webp_sha256':digest(p.read_bytes()),'native':False})
 (O/'generation_provenance.json').write_text(json.dumps({'generations':records,'references':['renders/cafe_spinda_revisite_v5/audit/exports/SpindaV5_audit_*_magenta.png','source/cafe_spinda_revisite_v5/references/escalier_entree_accueil.png','source/cafe_spinda_reseau_v4/references/spinda_design_reference.png'],'window_reference':'Spinda design and V4 café architecture only; Guild_Heros_Room_Objects not used','stairs':'Generated interpretation of the approved reference, NOT pixel-identical native stairs','artistic_approval':'Awaiting user review of these new generations'},indent=2)+'\n')

def build():
 O.mkdir(exist_ok=True);(O/'bruts').mkdir(exist_ok=True);archive();payloads={};old=json.loads((OLD/'manifest.json').read_text());rooms=[]
 raw=Image.fromarray(key(rgba(O/'bruts/fenetre_cafe.webp')));crop=raw.crop(raw.getbbox());height=64;width=round(crop.width*height/crop.height);width=min(width,72)
 window=Image.new('RGBA',(72,72));window.alpha_composite(crop.resize((width,height),Image.Resampling.NEAREST),((72-width)//2,4));(O/'assets').mkdir(exist_ok=True);window.save(O/'assets/SpindaV6_oculus_cafe.png')
 assets=[{'id':'window','title':'Oculus du café · bois miel, vitrage doux, croisillon','file':'assets/SpindaV6_oculus_cafe.png','native':False,'size':[72,72],'placement':'Independent overlay; two in café, three in upper lounge'}]
 for a in old['assets']:
  if a['id'] in ['window','stairs']:continue
  a=copy.deepcopy(a);a['file']='../cafe_spinda_reseau_v4/'+a['file'];a['title']='Hérité V4 · '+a['title'];assets.append(a)
 animations=copy.deepcopy(old['animations'])
 for a in animations.values():
  a['frames']=['../cafe_spinda_reseau_v4/'+f for f in a['frames']];a['sheet']='../cafe_spinda_reseau_v4/'+a['sheet']
 yy,xx=np.indices((448,600))
 for ident,title,level,rawstem,positions,poly in SPECS:
  layers=[]
  def add(code,label,im,role='generated_visible_surface'):
   file=f'calques/{ident}/SpindaV6_{ident}_{code}.png';payloads[file]=png(im);layers.append({'id':code,'title':label,'file':file,'png':file,'role':role,'default':True})
  ports={}
  if ident in ['salon_bas','salon_haut']:
   previous=next(r for r in old['rooms'] if r['id']==ident);a=oldbase(ident,rawstem)
   for l in previous['layers']:
    if l['id'] in ['sol','lumieres','parois','bordures']:add(l['id'],l['title'],rgba(OLD/l['file']))
   ports={'W':copy.deepcopy(previous['ports']['W'])};source='../cafe_spinda_reseau_v4/bruts/'+rawstem+'.webp'
  else:
   a=key(rgba(O/'bruts'/f'{ident}.webp').resize(SIZE,Image.Resampling.NEAREST));source='bruts/'+ident+'.webp';solid=a[:,:,3]>0;r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
   access={}
   if ident in ['accueil','casino']:
    mask=Image.new('1',SIZE);ImageDraw.Draw(mask).polygon([(232,0),(368,0),(380,176),(220,176)],fill=1);access['N']=np.array(mask)&solid
    ports['N']={'point':[304,88],'arrival_spawn':[304,200],'arrival_facing':'S','kind':'stairs_up','action':'montee'}
   if ident in ['accueil','cafe']:
    mask=Image.new('1',SIZE);ImageDraw.Draw(mask).polygon([(244,312),(356,312),(388,448),(212,448)],fill=1);access['S']=np.array(mask)&solid
    ports['S']={'point':[304,384],'arrival_spawn':[304,280],'arrival_facing':'N','kind':'stairs_down','action':'descente'}
   taken=np.zeros(solid.shape,bool)
   for mask in access.values():taken|=mask
   guide=Image.new('1',SIZE);ImageDraw.Draw(guide).polygon(poly,fill=1);guide=np.array(guide)
   floor=solid&~taken&guide&(yy>140);glow=floor&(g>180)&(b>110)&(r-g<60);unlit=a.copy()
   for y in range(448):
    targets=np.flatnonzero(glow[y]);donors=np.flatnonzero(floor[y]&~glow[y])
    if len(targets) and len(donors):
     z=np.searchsorted(donors,targets);left=donors[np.maximum(0,z-1)];right=donors[np.minimum(len(donors)-1,z)];pick=np.where(targets-left<=right-targets,left,right);unlit[y,targets]=a[y,pick]
    elif len(targets):glow[y,targets]=False
   defs=[('sol','Parquet · sous les lumières',floor,unlit),('lumieres','Motifs lumineux statiques',glow,a),('parois','Boiseries et bordure arrière',solid&~taken&~floor&(yy<196),a),('bordures','Bordure basse et passages latéraux',solid&~taken&~floor&(yy>=196),a)]
   defs += [('acces_'+d,'Accès '+d+' · marches, joues et raccord',mask,a) for d,mask in access.items()]
   for code,label,mask,data in defs:
    part=data.copy();part[~mask]=0;add(code,label,Image.fromarray(part))
   if ident in ['casino','cafe']:
    gold=solid[:,-1]&(r[:,-1]>180)&(g[:,-1]>125)&(b[:,-1]>40);lab,n=nd.label(gold);counts=np.bincount(lab);counts[0]=0;run=np.flatnonzero(lab==counts.argmax());assert len(run)>8,(ident,run)
    py=int(round((run[0]+run[-1])/16)*8);ports['E']={'point':[584,py],'arrival_spawn':[528,py],'kind':'level_door','edge_interval':[int(run[0]),int(run[-1])+1]}
  # Verify generated architectural layers before adding window instances.
  recomposed=Image.new('RGBA',SIZE)
  for l in layers:recomposed.alpha_composite(rgba(io.BytesIO(payloads[l['file']])))
  assert recomposed.tobytes()==Image.fromarray(a).tobytes(),ident
  if positions:
   w=Image.new('RGBA',SIZE)
   for x,y in positions:w.alpha_composite(window,(x-4,y-4))
   add('fenetres','Oculus café · dessin nouveau',w,'generated_cafe_windows')
  rooms.append({'id':ident,'title':title,'level':level,'size':list(SIZE),'raw':source,'layers':layers,'ports':ports,'windows':positions,'furniture_instances':[],'fire_instances':[],'npc_instances':[]})
 links=[['accueil','N','cafe','S'],['accueil','S','casino','N'],['casino','E','salon_bas','W'],['cafe','E','salon_haut','W']]
 for aa,pa,bb,pb in links:
  for rid,p,t,tp in [(aa,pa,bb,pb),(bb,pb,aa,pa)]:next(r for r in rooms if r['id']==rid)['ports'][p].update(target=t,target_port=tp)
 by_id={r['id']:r for r in rooms}
 assert set(by_id['accueil']['ports'])=={'N','S'}
 for room in rooms:
  for direction,port in room['ports'].items():
   target=by_id[port['target']];back=target['ports'][port['target_port']]
   assert back['target']==room['id'] and back['target_port']==direction
   delta=target['level']-room['level']
   if direction in ['N','S']:assert delta==(1 if port['kind']=='stairs_up' else -1) and port['target_port']==('S' if direction=='N' else 'N')
   else:assert delta==0
 m={'title':'Spinda · génération N/S, oculus café','rooms':rooms,'links':links,'assets':assets,'animations':animations,'grid':8,'pack':'SpindaV6_pack.zip','packed_layers':True,'external_access':'Not defined; no third exit added','native_stairs':False,'window':'New generated café design; not copied from Guild_Heros_Room_Objects','runtime_PMDO':'NOT TESTED','layer_limits':'Visible surface partitions and full access modules, not reconstructed wall volumes or collision masks; light beneath thresholds stays attached to access module.'}
 (O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
 template=(S/'viewer.html').read_text();(O/'index.html').write_text(template.replace('__DATA__',json.dumps(m,ensure_ascii=False)))
 (R/'apercu_cafe_spinda_revisite_v6.html').write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=renders/cafe_spinda_revisite_v6/index.html"><a href="renders/cafe_spinda_revisite_v6/index.html">Spinda N/S</a></html>\n')
 # All PNG layers and catalogue assets in a self-contained archive. Stored entries enable a tiny browser reader.
 portable=copy.deepcopy(m);portable['packed_layers']=False
 for a in portable['assets']:
  dest='assets/'+Path(a['file']).name;payloads[dest]=(O/a['file']).read_bytes();a['file']=dest
 for a in portable['animations'].values():
  for f in a['frames']+[a['sheet']]:payloads['assets/'+Path(f).name]=(O/f).read_bytes()
  a['frames']=['assets/'+Path(f).name for f in a['frames']];a['sheet']='assets/'+Path(a['sheet']).name
 payloads['manifest.json']=(json.dumps(portable,ensure_ascii=False,indent=2)+'\n').encode();payloads['index.html']=template.replace('__DATA__',json.dumps(portable,ensure_ascii=False)).replace('id="pack" href=','hidden id="pack" href=').encode()
 for f in ['README.md','generation_provenance.json']:payloads[f]=(O/f).read_bytes()
 with zipfile.ZipFile(O/m['pack'],'w',compression=zipfile.ZIP_STORED) as z:
  for name,data in sorted(payloads.items()):z.writestr(zipfile.ZipInfo(name,(2026,9,21,0,0,0)),data)
 with zipfile.ZipFile(O/m['pack']) as z:
  assert z.testzip() is None
  for name,data in payloads.items():assert z.read(name)==data
  for room in m['rooms']:
   for p in room['ports'].values():
    x,y=p['point'];assert x%8==y%8==0
   if room['id'] in ['accueil','casino','cafe']:
    a=key(rgba(O/room['raw']).resize(SIZE,Image.Resampling.NEAREST))
    for p in room['ports'].values():
     x,y=p['point'];assert a[y,x,3]==255,(room['id'],p)
     if 'arrival_spawn' in p:
      x,y=p['arrival_spawn'];assert np.all(a[y-8:y+9,x-8:x+9,3]==255)
  for a in portable['assets']:assert a['file'] in z.namelist()
 report={'pass':True,'rooms':5,'new_generations':3,'new_window':True,'layers':sum(len(r['layers']) for r in rooms),'reciprocal_links':4,'architecture_recomposition':'RGBA exact for all 5 rooms','raw_generations':'4 complete original RGBA rasters archived losslessly in WebP','package_crc':True,'package_entries':len(payloads),'package_bytes':(O/m['pack']).stat().st_size,'native_pixel_identity_for_stairs':False,'PMDO_runtime':'NOT TESTED','artistic_approval':'Pending'}
 (O/'verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));return m,payloads
if __name__=='__main__':build()
