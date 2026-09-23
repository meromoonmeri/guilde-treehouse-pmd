"""Five separately generated Spinda rooms; actual native windows and editor assets."""
from pathlib import Path
import json,hashlib,sys,shutil,io,importlib.util
import numpy as np
from PIL import Image,ImageDraw
from scipy import ndimage as nd
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent;O=R/'renders/cafe_spinda_reseau_v4';OLD=R/'source/cafe_multietage_v1/references';SIZE=(600,448)
SPECS=[
 ('accueil','Accueil de Spinda',0,'accueil_spinda_fidele',[],[(160,128),(440,128),(536,192),(536,270),(440,334),(160,334),(64,270),(64,192)]),
 ('casino','Casino souterrain',-1,'casino_spinda_fidele',[],[(160,130),(440,130),(536,192),(599,220),(599,252),(536,252),(536,278),(440,346),(160,346),(64,280),(64,192)]),
 ('salon_bas','Salon des jeux',-1,'salon_bas_spinda_fidele',[],[(176,148),(448,148),(536,196),(536,340),(480,390),(280,390),(240,364),(112,406),(0,406),(0,354),(92,328),(96,202)]),
 ('cafe','Café à l’étage',1,'cafe_spinda_corrige',[[192,56],[344,56]],[(160,132),(440,132),(536,198),(599,222),(599,254),(536,254),(536,280),(440,346),(160,346),(64,280),(64,198)]),
 ('salon_haut','Salon des croisillons',1,'salon_haut_spinda_corrige',[[176,56],[264,56],[352,56]],[(160,132),(440,132),(536,198),(536,280),(440,346),(160,346),(64,280),(64,254),(0,254),(0,222),(64,222),(64,198)]),
]

_arc_spec=importlib.util.spec_from_file_location('v4_study_archive',S/'archive_studies.py');_arc=importlib.util.module_from_spec(_arc_spec);_arc_spec.loader.exec_module(_arc)
def load(p):return Image.open(io.BytesIO(_arc.read_bytes(p))).convert('RGBA')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(im,p):
 p.parent.mkdir(parents=True,exist_ok=True)
 if p.suffix=='.webp':im.save(p,lossless=True,exact=True,method=6)
 else:im.save(p,optimize=True)
def base(ident,raw):
 im=load(O/'bruts'/f'{raw}.webp');assert im.size==(1200,896)
 a=np.array(im.resize(SIZE,Image.Resampling.NEAREST));r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
 mag=(r>g*1.4+30)&(b>g*1.4+30)&(r>95)&(b>95);a[mag]=0
 labels,_=nd.label(a[:,:,3]>0,np.ones((3,3)));counts=np.bincount(labels.ravel());keep=counts>=10;keep[0]=False;a[~keep[labels]]=0
 # Unrequested generated wall notice: only this local rectangle is repaired.
 if ident=='accueil':
  y,x=np.mgrid[86:126,266:338];weight=np.minimum.reduce([(x-266)/8,(337-x)/8,(y-86)/6,(125-y)/6]).clip(0,1)[:,:,None]
  old=a[86:126,266:338].astype(float);donor=a[86:126,202:274].astype(float)
  a[86:126,266:338]=np.rint(old*(1-weight)+donor*weight).astype('uint8')
 return a

def native_assets():
 A=O/'assets';A.mkdir(exist_ok=True)
 window=load(S/'references/Guild_Heros_Room_Objects.png').crop((176,56,240,120));save(window,A/'SpindaV4_fenetre_croisillon_native.png')
 # Native staircase is an independent editor proposal, NOT baked in the floors.
 sys.path.insert(0,str(R/'source/cote_v5_expeditions'));from audit_references import tiles,straight
 p=R/'source/cafe_multietage_v3/references/Guild_Second_Floor_Objects.tile';size,bank,_=tiles(p);stair=Image.new('RGBA',(96,72))
 for y in range(16,25):
  for x in range(26,38):
   if (x,y) in bank:stair.alpha_composite(straight(bank[x,y]),((x-26)*8,(y-16)*8))
 save(stair,A/'SpindaV4_escalier_spirale_natif.png')
 assets=[{'id':'window','title':'Fenêtre ronde à croisillons · native','file':'assets/SpindaV4_fenetre_croisillon_native.png','native':True,'size':[64,64]}, {'id':'stairs','title':'Escalier natif · à placer','file':'assets/SpindaV4_escalier_spirale_natif.png','native':True,'size':[96,72],'source':str(p.relative_to(R)),'source_crop':[208,128,304,200]}]
 for name,source,title,native in [
  ('decor_spinda',OLD/'SpindaCafe2.png','Mobilier, comptoirs et rubans Spinda',True),
  ('materiaux_spinda',OLD/'SpindaCafe1.png','Planche native : matières et façades de comptoir',True),
  ('kiosque_arriere',R/'renders/casino_network_v1/editeur/Casino_kiosque_arriere.png','Kiosque vide · arrière (généré)',False),
  ('kiosque_avant',R/'renders/casino_network_v1/editeur/Casino_kiosque_avant.png','Kiosque vide · comptoir avant (généré)',False),
  ('fourneau',R/'renders/casino_network_v1/objets/fourneau.png','Fourneau sans feu (généré)',False),
  ('support',R/'renders/casino_network_v1/objets/brasero_support.png','Support sans flamme · natif',True)]:
  target=A/f'SpindaV4_{name}.png';im=load(source);save(im,target);assets.append({'id':name,'title':title,'file':str(target.relative_to(O)),'size':list(im.size),'native':native,'source':str(source.relative_to(R)),'source_rgba_sha256':hashlib.sha256(im.tobytes()).hexdigest(),'placement':None})
 anim={}
 for kind,h,old in [('flamme',40,'flamme_native'),('brasero',64,'brasero_natif')]:
  paths=[];sheet=Image.new('RGBA',(128,h))
  for i in range(4):
   im=load(R/'renders/casino_network_v1/animations'/f'Casino_{old}_{i:02d}.png');p=A/f'SpindaV4_{kind}_{i:02d}.png';save(im,p);paths.append(str(p.relative_to(O)));sheet.alpha_composite(im,(i*32,0))
  p=A/f'SpindaV4_{kind}_4poses.png';save(sheet,p);anim[kind]={'frames':paths,'sheet':str(p.relative_to(O)),'frame_ms':100,'source_ticks':6,'size':[32,h],'placement':None}
 shutil.copyfile(R/'renders/casino_network_v1/flammes_provenance.json',O/'flammes_provenance.json');shutil.copyfile(S/'references/fenetre_provenance.json',O/'fenetre_provenance.json')
 return assets,anim

def main():
 O.mkdir(exist_ok=True,parents=True);assets,anim=native_assets();rooms=[]
 for ident,title,level,raw,windows,poly in SPECS:
  a=base(ident,raw);solid=a[:,:,3]>0;mask=Image.new('L',SIZE);ImageDraw.Draw(mask).polygon(poly,fill=255);floor=(np.array(mask)>0)&solid
  # Partition visible surfaces; this mask is not a PMDO collision mesh.
  yy,xx=np.mgrid[:SIZE[1],:SIZE[0]];r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
  # Snap the geometric guide to the bright visible floor, excluding dark rim stones.
  region=nd.binary_dilation(floor,iterations=8)&solid
  candidate=region&(r>=175)&(g>=145)
  candidate=(nd.binary_closing(candidate,structure=np.ones((3,3)))|candidate)&region
  labels,_=nd.label(candidate,np.ones((3,3)));counts=np.bincount(labels.ravel());counts[0]=0
  floor=nd.binary_fill_holes(labels==counts.argmax())&region
  glow=floor&(g>180)&(b>110)&(r-g<60)
  # Reconstruct only covered glow pixels from the nearest unlit board in same row.
  unlit=a.copy()
  for y in range(SIZE[1]):
   targets=np.flatnonzero(glow[y]);donors=np.flatnonzero(floor[y]&~glow[y])
   if len(targets) and len(donors):
    where=np.searchsorted(donors,targets);left=donors[np.maximum(0,where-1)];right=donors[np.minimum(len(donors)-1,where)];pick=np.where(targets-left<=right-targets,left,right);unlit[y,targets]=a[y,pick]
   elif len(targets):glow[y,targets]=False
  defs=[('sol','Plancher (sous les lumières)',floor,unlit),('lumieres','Spirales et lumières statiques',glow,a),('parois','Boiseries et bordure arrière',solid&~floor&(yy<196),a),('bordures','Bordures latérales / avant et seuil',solid&~floor&(yy>=196),a)]
  layers=[]
  for code,label,m,data in defs:
   part=data.copy();part[~m]=0;p=O/'calques'/ident/f'SpindaV4_{ident}_{code}.webp';save(Image.fromarray(part),p);layers.append({'id':code,'title':label,'file':str(p.relative_to(O)),'png':str(p.relative_to(O).with_suffix('.png')),'role':'generated_terrain','default':True})
  w=Image.new('RGBA',SIZE)
  for pos in windows:w.alpha_composite(load(O/assets[0]['file']),tuple(pos))
  if windows:
   p=O/'calques'/ident/f'SpindaV4_{ident}_fenetres.webp';save(w,p);layers.append({'id':'fenetres','title':'Fenêtres natives à croisillons','file':str(p.relative_to(O)),'png':str(p.relative_to(O).with_suffix('.png')),'role':'native_windows','default':True})
  ports={}
  if ident=='accueil':ports={'sortie':{'point':[300,378],'kind':'exterior'},'descente':{'point':[176,232],'kind':'stair_proposal'},'montee':{'point':[424,232],'kind':'stair_proposal'}}
  else:
   side='E' if ident in ['casino','cafe'] else 'W';col=599 if side=='E' else 0
   gold=solid[:,col]&(r[:,col]>210)&(g[:,col]>175)&(b[:,col]>50)
   gold=nd.binary_closing(gold,structure=np.ones(3))&solid[:,col]
   ls,n=nd.label(gold);cs=np.bincount(ls);cs[0]=0;run=np.flatnonzero(ls==cs.argmax());assert len(run)>12,(ident,run)
   ports[side]={'point':[584 if side=='E' else 16,int(round((run[0]+run[-1])/16)*8)],'kind':'door','edge_interval':[int(run[0]),int(run[-1])+1]}
   if ident=='casino':ports['retour']={'point':[176,232],'kind':'stair_proposal'}
   if ident=='cafe':ports['retour']={'point':[176,232],'kind':'stair_proposal'}
  stair_plane=Image.new('RGBA',SIZE);stair_positions=[]
  for key,port in ports.items():
   if port['kind']=='stair_proposal':
    x,y=port['point'];pos=[x-48,y-64];stair_plane.alpha_composite(load(O/'assets/SpindaV4_escalier_spirale_natif.png'),tuple(pos));stair_positions.append({'port':key,'position':pos})
  if stair_positions:
   p=O/'calques'/ident/f'SpindaV4_{ident}_escaliers_proposes.webp';save(stair_plane,p);layers.append({'id':'escaliers','title':'Escaliers natifs proposés (option)','file':str(p.relative_to(O)),'png':str(p.relative_to(O).with_suffix('.png')),'role':'native_stair_proposals','default':False})
  rooms.append({'id':ident,'title':title,'level':level,'size':list(SIZE),'raw':'bruts/'+raw+'.webp','layers':layers,'windows':windows,'stair_positions':stair_positions,'ports':ports,'floor_guide_polygon':poly,'furniture_instances':[],'fire_instances':[],'npc_instances':[]})
 links=[['accueil','descente','casino','retour'],['casino','E','salon_bas','W'],['accueil','montee','cafe','retour'],['cafe','E','salon_haut','W']]
 for aa,pa,bb,pb in links:
  for room,port,target,tp in [(aa,pa,bb,pb),(bb,pb,aa,pa)]:next(x for x in rooms if x['id']==room)['ports'][port].update({'target':target,'target_port':tp})
 m={'title':'Café & Casino Spinda · réseau V4','rooms':rooms,'links':links,'assets':assets,'animations':anim,'grid':8,'native_window':'fenetre_provenance.json','selected_direction':'accueil_spinda_fidele.webp, option 1 chosen by user','generation':'Five individual model generations referenced to the actual Spinda Cafe, not strip enlargement. Generated terrain is NOT native pixel-identical art.','processing':{'generated_size':[1200,896],'export_size':list(SIZE),'generated_scale':0.5,'resampling':'nearest only on generated art','native_scale':1,'key':'magenta','floor_partition':'Expanded geometric guide snapped to bright floor component; internal dark grain retained. Visible surface only, not collision mask.','notice_repair':{'room':'accueil','destination':[266,86,338,126],'donor':[202,86,274,126],'blend':'6–8px edge ramp, full replacement over the notice'},'unlit_floor':'Only below extracted static light pixels: nearest unlit pixel in same floor row. Complete lit terrain recomposes exactly.'},'runtime_PMDO':'NOT TESTED','links_status':'Reciprocal design/placement guides, no engine warps, collisions or native Ground installed. Side rooms use discrete transitions, not a seamless tile mosaic.','preserved':'Earlier deliveries and unselected studies retained separately.'}
 (O/'manifest.json').write_text(json.dumps(m,ensure_ascii=False,indent=2)+'\n')
 page=(S/'viewer.html').read_text().replace('__DATA__',json.dumps(m,ensure_ascii=False));(O/'index.html').write_text(page)
 (R/'apercu_cafe_spinda_reseau_v4.html').write_text('<!doctype html><html lang="fr"><meta charset="utf-8"><meta http-equiv="refresh" content="0;url=renders/cafe_spinda_reseau_v4/index.html"><a href="renders/cafe_spinda_reseau_v4/index.html">Ouvrir le réseau Spinda</a></html>\n')
 preview=compose(m,'accueil');bg=Image.new('RGBA',SIZE,'magenta');bg.alpha_composite(preview);save(bg,O/'SpindaV4_accueil_magenta.webp')
 preview=compose(m,'cafe');bg=Image.new('RGBA',SIZE,'magenta');bg.alpha_composite(preview);save(bg,O/'SpindaV4_cafe_croisillons_magenta.webp')
 print('Built 5 separately generated rooms, 3 levels, 4 reciprocal links, native windows and separate editor assets.')

def compose(m,room_id,root=O):
 room=next(r for r in m['rooms'] if r['id']==room_id);out=Image.new('RGBA',tuple(room['size']))
 for l in room['layers']:
  if l['default']:out.alpha_composite(load(root/l['file']))
 return out
if __name__=='__main__':main()
