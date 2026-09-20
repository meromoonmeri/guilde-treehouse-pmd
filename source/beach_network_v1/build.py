"""Generated, canonical-referenced beach modules, Ledian-style ports and a moonless sky.
Preserves existing assets. No claim of pixel-identical canonical generated terrain or PMDO import.
"""
from pathlib import Path
import sys,json,math,io,hashlib,zipfile
import xml.etree.ElementTree as ET
import numpy as np
from scipy import ndimage as nd
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from source.cote_v4_abyss.night import night
from source.beach_layers_v1.build import animator,wave_guide
OUT=ROOT/'renders/beach_network_v1';BRUT=OUT/'bruts';SRC=ROOT/'DSVFS.png'
S=512;PORT=96;START=208;DEPTH=48;SKY_H=112;N=32;MS=100;PERIOD=64000
SPECS=[
 ('01_anse_ouest','Anse du couchant',['E','S'],[0,0],'01_anse_ouest.png'),
 ('02_carrefour_t','Carrefour des palmes · T',['W','E','S'],[1,0],'02_carrefour_t.png'),
 ('03_anse_est','Anse des roches rouges',['W','S'],[2,0],'03_anse_est_corrigee.png'),
 ('04_passage_ouest','Passage des écueils',['N','E'],[0,1],'04_passage_ouest.png'),
 ('05_carrefour_croix','Grand carrefour · croix',['N','E','S','W'],[1,1],'05_carrefour_croix.png'),
 ('06_passage_est','Anse des marées',['N','W'],[2,1],'06_passage_est.png')]
OPPOSITE={'N':'S','S':'N','E':'W','W':'E'};DELTAS={'N':(0,-1),'S':(0,1),'E':(1,0),'W':(-1,0)}
POINTS={'N':(256,8),'S':(256,504),'W':(8,256),'E':(504,256)}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):
 p=Path(p)
 if not p.exists() and p.parent==BRUT:p=p.with_suffix('.webp')
 return np.array(Image.open(p).convert('RGBA'))
def save(a,p):
 p.parent.mkdir(parents=True,exist_ok=True)
 im=Image.fromarray(a)
 # Use a lossless indexed PNG whenever it really preserves all RGBA values.
 if a.ndim==3 and im.getcolors(256) is not None:
  indexed=im.quantize(colors=256,method=Image.Quantize.FASTOCTREE)
  if np.array_equal(np.array(indexed.convert(im.mode)),a):im=indexed
 im.save(p,optimize=True)
def part(a,m):
 out=np.zeros_like(a);out[m]=a[m];return out
def grade(a,mode):return np.array(night(Image.fromarray(a))) if mode=='nuit' else a.copy()
def compose(layers,size):
 im=Image.new('RGBA',size)
 for a in layers:im.alpha_composite(Image.fromarray(a))
 return np.array(im)
def opaque_sand(a):
 r,g,b=np.moveaxis(a[:,:,:3].astype(float),2,0)
 return (r>190)&(g>180)&(b>90)&(b<205)&(r>g-8)

def sky_assets():
 raw=Image.open(BRUT/'ciel_nuit_sans_lune.png').convert('RGBA')
 height=round(raw.height*1536/raw.width)
 im=raw.resize((1536,height),Image.Resampling.NEAREST)
 y0=max(0,(height-192)//2-30);im=im.crop((0,y0,1536,y0+192))
 save(np.array(im),OUT/'fonds/BeachNetwork_ciel_nuit.png')
 day=Image.new('RGBA',(1536,192),(141,210,249,255));save(np.array(day),OUT/'fonds/BeachNetwork_ciel_jour.png')
 rawc=load(BRUT/'nuages_overlay_magenta.png');rgb=rawc[:,:,:3].astype(float)
 mask=(rgb[:,:,1]>65)&(rgb[:,:,1]>.55*rgb[:,:,0])&(rgb[:,:,2]>rgb[:,:,0]-15)
 labels,count=nd.label(mask);components=[]
 for i,box in enumerate(nd.find_objects(labels),1):
  if box is None:continue
  ys,xs=box;area=int((labels[box]==i).sum())
  if area>300 and xs.start>20 and xs.stop<rawc.shape[1]-20:
   a=rawc[box].copy();a[labels[box]!=i]=0;components.append((xs.start,a,[xs.start,ys.start,xs.stop,ys.stop]))
 components.sort(key=lambda r:r[0]);assert len(components)>=3
 strip=Image.new('RGBA',(512,SKY_H));placements=[]
 for (x,a,rect),(dx,dy) in zip(components[:3],[(36,18),(206,53),(373,28)]):
  cloud=Image.fromarray(a);scale=min(96/cloud.width,28/cloud.height);size=(max(1,round(cloud.width*scale)),max(1,round(cloud.height*scale)))
  cloud=cloud.resize(size,Image.Resampling.NEAREST);strip.alpha_composite(cloud,(dx,dy));placements.append({'source_rect':rect,'position':[dx,dy],'size':list(size)})
 a=np.array(strip);assert not a[:,:24,3].any() and not a[:,-24:,3].any()
 save(a,OUT/'fonds/BeachNetwork_nuages_nuit_wrap.png')
 daytime=a.copy();m=a[:,:,3]>0;daytime[m,:3]=np.minimum(daytime[m,:3].astype(int)+22,255)
 save(daytime,OUT/'fonds/BeachNetwork_nuages_jour_wrap.png')
 return {'source_size':list(raw.size),'uniform_resize':[1536,height],'crop':[0,y0,1536,y0+192],'moon':False,'generated':True,'cloud_placements':placements,'cloud_strip':[512,112],'cloud_speed_px_sec':8,'cloud_period_ms':PERIOD,'step_px':1,'step_ms':125,'alpha_margins_px':24}

def classify(a):
 h,w=a.shape[:2];y,x=np.mgrid[:h,:w];r,g,b=np.moveaxis(a[:,:,:3].astype(float),2,0)
 blue=(b>r+15)&(g>r+6)
 pale=(b>185)&(g>185)&(b>r-20)&nd.binary_dilation(blue,iterations=4)
 water=blue|pale
 labels,n=nd.label(water);counts=np.bincount(labels.ravel());keep=counts>12;keep[0]=False;water=keep[labels]
 foam=water&(r>132)&(g>180)&(b>180)
 green=(g>r*1.04)&(g>b*1.22)&~water
 rock=(r>g*1.16)&(g<160)&~green&~water
 sand=~(water|green|rock)
 return [('01_sable','Sable',sand),('02_roches_nord','Roches arrière',rock&(y<220)),('03_roches_cotes','Roches latérales',rock&(y>=220)&(y<400)),('04_roches_sud','Roches avant',rock&(y>=400)),('05_palmiers','Palmiers et plantes',green),('06_eau','Eau',water&~foam),('07_ecume','Écume',foam)],water,foam

def connectors(a,dirs):
 source=load(SRC)[168:216,296:392]
 assert source.shape==(48,96,4)
 weights=np.array([1.]*16+[max(0,(47-i)/31) for i in range(16,48)])
 layers=[]
 for d in dirs:
  patch=source if d=='N' else source[::-1] if d=='S' else source.transpose(1,0,2) if d=='W' else source.transpose(1,0,2)[:,::-1]
  weight=weights[:,None] if d=='N' else weights[::-1,None] if d=='S' else weights[None,:] if d=='W' else weights[None,::-1]
  x,y={'N':(208,0),'S':(208,464),'W':(0,208),'E':(464,208)}[d]
  h,w=patch.shape[:2];under=a[y:y+h,x:x+w]
  rgb=np.rint(under[:,:,:3]*(1-weight[:,:,None])+patch[:,:,:3]*weight[:,:,None]).clip(0,255).astype('uint8')
  l=np.zeros_like(a);m=np.broadcast_to(weight,(h,w))>0;l[y:y+h,x:x+w,:3][m]=rgb[m];l[y:y+h,x:x+w,3][m]=255
  layers.append((f'08_acces_{d}',f'Accès {d}',l))
 return layers,source

def contact_foam(rgb,water,foam):
 # New local run-up, not a recovery of the absent V2/V3 animation. Copy the
 # existing foam colours onto a <=3 px coastal band; never shift the rocks.
 yy,xx=np.mgrid[:water.shape[0],:water.shape[1]]
 shore=foam&(nd.distance_transform_edt(water)<=6)
 distance,nearest=nd.distance_transform_edt(~shore,return_indices=True)
 r,g,b=np.moveaxis(rgb.astype(float),2,0)
 plants=(g>r*1.04)&(g>b*1.22)
 sample=rgb[nearest[0],nearest[1]]
 gain=.65+.35*np.sin(xx/23+yy/29)**2
 def overlay(base,k,count):
  out=base.copy();run=np.rint(1.5*(1-math.cos(2*math.pi*(k%count)/count))*gain)
  wet=(distance<=run)&(distance>0)&~plants&(run>0)
  out[wet,:3]=sample[wet];out[wet,3]=255
  return out
 return overlay

def atlas(frames,p):
 boxes=[Image.fromarray(a).getbbox() for a in frames];boxes=[b for b in boxes if b]
 box=(min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)) if boxes else (0,0,1,1)
 x,y,x1,y1=box;w,h=x1-x,y1-y;cols=8
 im=Image.new('RGBA',(w*cols,h*math.ceil(len(frames)/cols)))
 for k,a in enumerate(frames):im.paste(Image.fromarray(a).crop(box),((k%cols)*w,(k//cols)*h))
 p.parent.mkdir(parents=True,exist_ok=True);im.save(p,lossless=True,method=4,exact=True)
 return {'file':str(p.relative_to(OUT)),'rect':[x,y,w,h],'columns':cols,'frames':len(frames)}

def ora(path,layers,scene):
 root=ET.Element('image',w=str(scene.shape[1]),h=str(scene.shape[0]),name=path.stem);stack=ET.SubElement(root,'stack')
 with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for ident,label,a in reversed(layers):
   name='data/'+ident+'.png';ET.SubElement(stack,'layer',name=label,src=name,x='0',y='0',opacity='1',visibility='visible',**{'composite-op':'svg:src-over'})
   b=io.BytesIO();Image.fromarray(a).save(b,format='PNG');z.writestr(name,b.getvalue())
  z.writestr('stack.xml',ET.tostring(root,encoding='utf-8',xml_declaration=True));b=io.BytesIO();Image.fromarray(scene).save(b,format='PNG');z.writestr('mergedimage.png',b.getvalue())

def path_check(scene,dirs):
 mask=opaque_sand(scene);dist=nd.distance_transform_edt(mask);labels,_=nd.label(dist>=8);centre=labels[256,256]
 assert centre>0,'Centre not walkable'
 checks={d:int(labels[POINTS[d][1],POINTS[d][0]])==int(centre) for d in dirs}
 assert all(checks.values()),checks
 return mask,checks

def render_scene(manifest,selection,mode,tick):
 tick=int(tick)%PERIOD
 if selection=='ensemble':rooms=manifest['rooms'];size=(1536,1136);head=112
 elif selection=='plage_reference':rooms=[manifest['reference_beach']];size=(702,578);head=112
 else:rooms=[next(r for r in manifest['rooms'] if r['id']==selection)];size=(512,512);head=0
 scene=Image.new('RGBA',size)
 if head:
  scene=Image.new('RGBA',size,(3,5,54,255) if mode=='nuit' else (141,210,249,255))
  scene.alpha_composite(Image.open(OUT/'fonds'/f'BeachNetwork_ciel_{mode}.png').convert('RGBA'))
  cloud=Image.open(OUT/'fonds'/f'BeachNetwork_nuages_{mode}_wrap.png').convert('RGBA')
  offset=(tick//125)%512
  for x in range(-offset,size[0],512):scene.alpha_composite(cloud,(x,0))
 for r in rooms:
  dx,dy=(r['position'][0]*512,r['position'][1]*512+112) if selection=='ensemble' else (0,head)
  rec=r['modes'][mode]
  for l in rec['layers']:
   if l['id'] in rec['animation']:
    a=rec['animation'][l['id']];x,y,w,h=a['rect'];k=(tick%3200)//rec['frame_ms'];col=k%a['columns'];row=k//a['columns']
    with Image.open(OUT/a['file']) as atlas_im:im=atlas_im.convert('RGBA').crop((col*w,row*h,(col+1)*w,(row+1)*h))
    scene.alpha_composite(im,(dx+x,dy+y))
   else:scene.alpha_composite(Image.open(OUT/l['file']).convert('RGBA'),(dx,dy))
 return scene

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 sky_meta=sky_assets();palette=Image.open(SRC).convert('P');height_guide=wave_guide()
 manifest={'size':[512,512],'port_width':96,'port_depth':48,'rooms':[],'sky':sky_meta,'period_ms':PERIOD,'runtime_PMDO':'NOT TESTED','generated_texture_not_native':True,
 'source':{'file':'DSVFS.png','sha256':sha(SRC)},'method_reference':'renders/ledian_dojo_v1/README.md','sources':{str(p.relative_to(ROOT)):sha(p) for p in sorted(list(BRUT.glob('*.png'))+list(BRUT.glob('*.webp')))},'initial_beach_source':'V1 files available in this restored checkout; no recovery of absent V2/V3 claimed.'}
 bygrid={tuple(pos):slug for slug,_,_,pos,_ in SPECS};byid={slug:dirs for slug,_,dirs,_,_ in SPECS}
 for slug,title,dirs,position,raw in SPECS:
  im=Image.fromarray(load(BRUT/raw)).convert('RGB');assert im.width==im.height;original_size=list(im.size)
  im=im.resize((512,512),Image.Resampling.NEAREST).quantize(palette=palette,dither=Image.Dither.NONE).convert('RGBA');a=np.array(im)
  defs,water,foam=classify(a)
  layers=[(i,l,part(a,m)) for i,l,m in defs]
  ports,patch=connectors(a,dirs);layers+=ports
  day=compose([p for _,_,p in layers],(512,512));walk,checks=path_check(day,dirs)
  save(np.uint8(walk)*255,OUT/slug/'controle_sol.png')
  save(patch,OUT/'materiaux/BeachNetwork_sable_raccord_source.png')
  render,_=animator(a[:,:,:3],water,foam,height_guide)
  daywater=[];dayfoam=[];contact=contact_foam(a[:,:,:3],water,foam)
  for k in range(N):
   w,f=render(2*k);daywater.append(w);dayfoam.append(contact(f,k,N))
  assert np.array_equal(compose([w if i=='06_eau' else f if i=='07_ecume' else layer for i,_,layer in layers for w,f in [(daywater[0],dayfoam[0])]],(512,512)),day)
  rec={'id':slug,'title':title,'size':[512,512],'position':position,'raw':raw,'ports':[],'modes':{},'connectivity':checks,'original_generated_size':original_size}
  for d in dirs:
   dx,dy=DELTAS[d];target=bygrid.get((position[0]+dx,position[1]+dy));linked=target is not None and OPPOSITE[d] in byid[target]
   rec['ports'].append({'direction':d,'point':list(POINTS[d]),'width':96,'target':target if linked else None,'reserved_extension':not linked})
  for mode in ['jour','nuit']:
   entries=[];layer_images=[]
   for ident,label,layer in layers:
    p=OUT/slug/mode/'calques'/f'BeachNetwork_{slug}_{mode}_{ident}.png';g=grade(layer,mode);save(g,p);layer_images.append((ident,label,g));entries.append({'id':ident,'label':label,'file':str(p.relative_to(OUT))})
   frames_w=[grade(w,mode) for w in daywater];frames_f=[grade(f,mode) for f in dayfoam]
   animations={}
   for ident,frames in [('06_eau',frames_w),('07_ecume',frames_f)]:
    for k,fr in enumerate(frames):save(fr,OUT/slug/mode/'animation'/ident/f'BeachNetwork_{slug}_{mode}_{ident}_{k:02d}.png')
    animations[ident]=atlas(frames,OUT/slug/mode/f'BeachNetwork_{ident}_atlas.webp')
   scene=grade(day,mode);save(scene,OUT/slug/mode/'composition.png');ora(OUT/slug/mode/f'BeachNetwork_{slug}_{mode}.ora',layer_images,scene)
   rec['modes'][mode]={'layers':entries,'animation':animations,'frame_ms':MS,'frames':N,'composition':str((OUT/slug/mode/'composition.png').relative_to(OUT))}
  manifest['rooms'].append(rec);print(slug,checks,flush=True)
 # Original beach with regenerated background; preserve actual source terrain and V1 animation.
 base={'id':'plage_reference','title':'Plage de référence · ciel corrigé','size':[702,466],'ports':[],'modes':{}}
 old=json.loads((ROOT/'renders/beach_layers_v1/manifest.json').read_text())
 original_rgb=load(SRC)[:,:,:3]
 original_water=np.array(Image.open(ROOT/'renders/beach_layers_v1/masques/mer.png'))>0
 original_foam=np.array(Image.open(ROOT/'renders/beach_layers_v1/masques/ecume.png'))>0
 original_contact=contact_foam(original_rgb,original_water,original_foam)
 for mode in ['jour','nuit']:
  entries=[]
  for l in old['layers']:
   if l['id']=='01_ciel':continue
   p=OUT/'plage_reference'/mode/'calques'/f'BeachNetwork_reference_{mode}_{l["id"]}.png';save(grade(load(ROOT/'renders/beach_layers_v1'/l['file']),mode),p)
   entries.append({'id':l['id'],'label':l['name'],'file':str(p.relative_to(OUT))})
  anim={}
  for ident,folder,prefix in [('03_mer','mer','mer'),('04_ecume','ecume','ecume')]:
   frames=[]
   for k in range(64):
    frame=load(ROOT/'renders/beach_layers_v1/animation'/folder/f'BeachV1_{prefix}_{k:02d}.png')
    if ident=='04_ecume':frame=original_contact(frame,k,64)
    frames.append(grade(frame,mode))
   anim[ident]=atlas(frames,OUT/'plage_reference'/mode/f'BeachNetwork_{ident}_atlas.webp')
  base['modes'][mode]={'layers':entries,'animation':anim,'frame_ms':50,'frames':64}
 manifest['reference_beach']=base
 manifest['foam_contact']={'new_animation':True,'max_run_up_px':3,'period_ms':3200,'source_colours':'nearest existing coastal foam','plants_excluded':True,'restores_absent_V2_V3':False,'reference_terrain_phase_zero_preserved':True}
 # Agglomerated terrain views and 15-port map. No repeated sky between adjacent modules.
 for mode in ['jour','nuit']:
  world=Image.new('RGBA',(1536,1024))
  for r in manifest['rooms']:
   world.paste(Image.open(OUT/r['modes'][mode]['composition']),(r['position'][0]*512,r['position'][1]*512))
  world.save(OUT/f'BeachNetwork_ensemble_{mode}.png',optimize=True)
 schematic=Image.new('RGB',(768,512),'#10212b');d=ImageDraw.Draw(schematic)
 for r in manifest['rooms']:
  x,y=r['position'][0]*256,r['position'][1]*256;d.rounded_rectangle((x+12,y+12,x+244,y+244),radius=26,fill='#344c54',outline='#74bec4',width=2)
  d.text((x+28,y+30),r['id'][:2]+'  '+r['title'],fill='white')
  for p in r['ports']:
   px,py=p['point'];pt=(x+px/2,y+py/2);d.line((x+128,y+128,*pt),fill='#e6d88c',width=16)
   d.ellipse((pt[0]-8,pt[1]-8,pt[0]+8,pt[1]+8),fill='#92e5cf' if p['target'] else '#eab383')
 schematic.save(OUT/'BeachNetwork_plan_connexions.png')
 manifest['edges']=[{'from':r['id'],'direction':p['direction'],'to':p['target']} for r in manifest['rooms'] for p in r['ports'] if p['target'] and r['id']<p['target']]
 manifest['limits']=['Generated PMD-referenced materials, not native pixel-identical tiles.','Common sand bands match; the entire rock perimeter is not certified seamless.','Connected sand masks are not PMDO collisions or warps.','Hidden surfaces under rocks/plants are not reconstructed.','Cloud animation is an explicit wrap translation on its own overlay, not cloud morphing.']
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 for mode in ['jour','nuit']:
  render_scene(manifest,'plage_reference',mode,0).save(OUT/f'BeachNetwork_plage_ciel_corrige_{mode}.png',optimize=True)
 page=(Path(__file__).parent/'viewer.html').read_text().replace('__DATA__',json.dumps(manifest,ensure_ascii=False))
 (ROOT/'apercu_reseau_plage_v1.html').write_text(page)
 (OUT/'index.html').write_text(page.replace('const ROOT="renders/beach_network_v1/"','const ROOT="./"').replace('href="renders/beach_network_v1/','href="'))
 print('Built six connected modules, 15 ports, 7 internal links, corrected original beach, moonless sky and 64-second wrap.')

if __name__=='__main__':main()
