"""Four additive beach modules. Shared V1 images are referenced, never rewritten."""
from pathlib import Path
import sys,json,copy,hashlib,math
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from source.beach_network_v1 import build as b
OUT=ROOT/'renders/beach_extension_v2';OLD=ROOT/'renders/beach_network_v1'
SPECS=[('07_carrefour_dunes','Carrefour des dunes','NES',[1,2],'07_carrefour_dunes_corrige.webp'),('08_carrefour_lagon','Carrefour du lagon','WES',[2,2],'08_carrefour_lagon.webp'),('09_place_palmes','Place des palmes','NESW',[1,3],'09_place_palmes.webp'),('10_baie_abritee','Baie abritée','NW',[2,3],'10_baie_abritee.webp')]

def atlas(frames,path):
 boxes=[Image.fromarray(a).getbbox() for a in frames];boxes=[x for x in boxes if x]
 x=min(z[0] for z in boxes);y=min(z[1] for z in boxes);right=max(z[2] for z in boxes);bottom=max(z[3] for z in boxes);w=right-x;h=bottom-y
 im=Image.new('RGBA',(w*8,h*math.ceil(len(frames)/8)))
 for k,frame in enumerate(frames):im.paste(Image.fromarray(frame).crop((x,y,right,bottom)),((k%8)*w,(k//8)*h))
 path.parent.mkdir(parents=True,exist_ok=True);im.save(path,lossless=True,method=6,exact=True)
 return {'file':str(path.relative_to(OUT)),'rect':[x,y,w,h],'columns':8,'frames':len(frames)}

def rewrite_paths(room):
 for desc in room['modes'].values():
  for layer in desc['layers']:layer['file']='../beach_network_v1/'+layer['file']
  for a in desc['animation'].values():a['file']='../beach_network_v1/'+a['file']
  if 'composition' in desc:desc['composition']='../beach_network_v1/'+desc['composition']
 return room

def layout_rooms(data,key):
 spec=data['layouts'][key];return [r for r in data['rooms'] if r['id'] in spec['rooms']]

def composed_layout(data,key,mode):
 layout=data['layouts'][key];im=Image.new('RGBA',(layout['cols']*512,layout['rows']*512));ox,oy=layout['origin']
 for r in layout_rooms(data,key):im.alpha_composite(Image.open(OUT/r['modes'][mode]['composition']).convert('RGBA'),((r['position'][0]-ox)*512,(r['position'][1]-oy)*512))
 return im

def plan(data,key):
 layout=data['layouts'][key];ox,oy=layout['origin'];im=Image.new('RGB',(layout['cols']*256,layout['rows']*256),'#10242e');d=ImageDraw.Draw(im)
 for r in layout_rooms(data,key):
  x=(r['position'][0]-ox)*256;y=(r['position'][1]-oy)*256
  d.rounded_rectangle((x+12,y+12,x+244,y+244),radius=22,fill='#36545a' if r.get('new') else '#253c49',outline='#80d8c7',width=2)
  d.text((x+24,y+30),r['id'][:2]+'  '+r['title'],fill='#f3e9c2')
  for p in r['ports']:
   px,py=p['point'];pt=(x+px/2,y+py/2);d.line((x+128,y+128,*pt),fill='#e6d48e',width=12);d.ellipse((pt[0]-6,pt[1]-6,pt[0]+6,pt[1]+6),fill='#88ddc3' if p['target'] else '#edb275')
 return im

def render_viewers(data):
 template=(Path(__file__).parent/'viewer.html').read_text();page=template.replace('__DATA__',json.dumps(data,ensure_ascii=False))
 (ROOT/'apercu_extension_plage_v2.html').write_text(page)
 (OUT/'index.html').write_text(page.replace('const ROOT="renders/beach_extension_v2/"','const ROOT="./"'))

def main():
 from source.beach_network_v1.restore_exports import restore_exports
 restore_exports(OLD)
 OUT.mkdir(parents=True,exist_ok=True);original=json.loads((OLD/'manifest.json').read_text());shared=set()
 for r in original['rooms']+[original['reference_beach']]:
  for mode,rec in r['modes'].items():
   shared.update(x['file'] for x in rec['layers']);shared.update(x['file'] for x in rec['animation'].values())
   if 'composition' in rec:shared.add(rec['composition'])
 for mode in ['jour','nuit']:
  shared.update([f'fonds/BeachNetwork_ciel_{mode}.png',f'fonds/BeachNetwork_nuages_{mode}_wrap.png'])
 before={f:b.sha(OLD/f) for f in sorted(shared)};before['manifest.json']=b.sha(OLD/'manifest.json');before['BeachNetwork_pack.zip']=b.sha(OLD/'BeachNetwork_pack.zip')
 data={'version':'Beach Extension V2','scope':'combined','rooms':[], 'reference_beach':rewrite_paths(copy.deepcopy(original['reference_beach'])),'period_ms':64000,'source':original['source'],'sky':original['sky'],'foam_contact':original['foam_contact'],'generated_texture_not_native':True,'runtime_PMDO':'NOT TESTED','preserved_v1_hashes':before,'generation_archive':json.loads((OUT/'bruts/provenance.json').read_text())}
 data['sky_assets']={mode:{'sky':f'../beach_network_v1/fonds/BeachNetwork_ciel_{mode}.png','cloud':f'../beach_network_v1/fonds/BeachNetwork_nuages_{mode}_wrap.png'} for mode in ['jour','nuit']}
 for r in original['rooms']:
  r=rewrite_paths(copy.deepcopy(r));r['new']=False;data['rooms'].append(r)
 palette=Image.open(b.SRC).convert('P');heights=b.wave_guide()
 for slug,title,dirs,pos,raw in SPECS:
  im=Image.open(OUT/'bruts'/raw).convert('RGB').resize((512,512),Image.Resampling.NEAREST).quantize(palette=palette,dither=Image.Dither.NONE).convert('RGBA');a=np.array(im)
  definitions,water,foam=b.classify(a);layers=[(ident,label,b.part(a,mask)) for ident,label,mask in definitions]
  connectors,_=b.connectors(a,dirs);layers+=connectors;day=b.compose([x[2] for x in layers],(512,512));walk,checks=b.path_check(day,dirs)
  render,_=b.animator(a[:,:,:3],water,foam,heights);contact=b.contact_foam(a[:,:,:3],water,foam);waters=[];foams=[]
  for k in range(32):
   w,f=render(k*2);waters.append(w);foams.append(contact(f,k,32))
  assert all(len({hashlib.sha256(x.tobytes()).hexdigest() for x in arr})>1 for arr in [waters,foams])
  rec={'id':slug,'title':title,'new':True,'size':[512,512],'position':pos,'ports':[{'direction':d,'point':list(b.POINTS[d]),'width':96} for d in dirs],'modes':{},'connectivity':checks,'raw':raw}
  for mode in ['jour','nuit']:
   entries=[]
   for ident,label,arr in layers:
    path=OUT/slug/mode/'calques'/f'BeachExt_{slug}_{mode}_{ident}.png';b.save(b.grade(arr,mode),path);entries.append({'id':ident,'label':label,'file':str(path.relative_to(OUT))})
   animations={}
   for ident,frames in [('06_eau',waters),('07_ecume',foams)]:
    frames=[b.grade(x,mode) for x in frames];animations[ident]=atlas(frames,OUT/slug/mode/f'BeachExt_{slug}_{mode}_{ident}_atlas.webp')
   path=OUT/slug/mode/f'BeachExt_{slug}_{mode}_composition.webp';Image.fromarray(b.grade(day,mode)).save(path,lossless=True,method=6,exact=True)
   rec['modes'][mode]={'layers':entries,'animation':animations,'frame_ms':100,'frames':32,'composition':str(path.relative_to(OUT))}
  data['rooms'].append(rec);print(slug,checks,flush=True)
 bygrid={tuple(r['position']):r for r in data['rooms']}
 for r in data['rooms']:
  for p in r['ports']:
   dx,dy=b.DELTAS[p['direction']];target=bygrid.get((r['position'][0]+dx,r['position'][1]+dy));linked=target and any(q['direction']==b.OPPOSITE[p['direction']] for q in target['ports'])
   p['target']=target['id'] if linked else None;p['reserved_extension']=not bool(linked)
 data['edges']=[{'from':r['id'],'direction':p['direction'],'to':p['target']} for r in data['rooms'] for p in r['ports'] if p['target'] and r['id']<p['target']]
 data['layouts']={'extension':{'title':'Extension sud · 4 nouvelles cartes','origin':[1,2],'cols':2,'rows':2,'rooms':[r['id'] for r in data['rooms'] if r['new']]},'reseau':{'title':'Réseau complet · 10 cartes','origin':[0,0],'cols':3,'rows':4,'rooms':[r['id'] for r in data['rooms']]}}
 data['limits']=['Generated PMD-referenced maps, not certified native tiles.','Common sand bands match exactly, but complete rock outlines are not certified seamless.','Visible-surface partitions, not complete movable objects or rebuilt hidden ground.','Sand checks are not collision or warp implementation.','Empty grid slots are not maps; reserved exits have no target.']
 assert len(data['edges'])==12 and sum(len(r['ports']) for r in data['rooms'])==27
 for key in data['layouts']:
  if key=='extension':composed_layout(data,key,'jour').save(OUT/'BeachExt_extension_jour.png',optimize=True)
  else:composed_layout(data,key,'jour').resize((768,1024),Image.Resampling.NEAREST).save(OUT/'BeachExt_reseau_apercu_50pct.webp',lossless=True,method=6,exact=True)
  plan(data,key).save(OUT/f'BeachExt_plan_{key}.png',optimize=True)
 (OUT/'manifest.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 for f,h in before.items():assert b.sha(OLD/f)==h,f
 render_viewers(data)
 print('10 rooms, 12 links, 27 ports, 3 reserved exits; V1 files unchanged.')

if __name__=='__main__':main()
