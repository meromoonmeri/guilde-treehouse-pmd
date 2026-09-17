"""Reconstruct lost scene cycles from native views and retained V1/V2 studies.
Explicit pixel-authored reconstruction, not recovered original V3/V4 files.
Food/emotes are separate scene entities, never baked into character sheets.
"""
from pathlib import Path
import copy,json,hashlib,shutil,sys,math,base64,io,struct
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[2];SRC=Path(__file__).parent
OUT=ROOT/'exports/guild_scene_recovery_v5';REF=ROOT/'source/guild_members_audit/references'
DIRS=['D','DR','R','UR','U','UL','L','DL']
COLORS={'body':(0,255,0,255),'head':(0,0,0,255),'right':(255,0,0,255),'left':(0,0,255,255)}
EASE=[0,0,.12,.28,.48,.72,.9,1,1,.9,.72,.48,.28,.12,0,0]
EAT_TICKS=[10,6,4,4,4,4,5,7,8,5,4,4,4,4,6,12]
BEND=[0,0,1,1,2,2,3,3,2,2,1,1,0,0,0,0]
NOD_TICKS=[8,4,3,3,4,4,5,6,4,3,3,3,4,4,4,8]
# Native-view-specific: active hand, shoulder, resting elbow, folded elbow, mouth-side wrist.
RIG=[
 ('right',(12,14),(10,16),(10,17),(14,14)),
 ('right',(18,14),(20,15),(22,16),(21,13)),
 ('left',(17,14),(17,17),(21,17),(22,12)),
 ('left',(17,14),(19,16),(23,16),(22,12)),
 ('right',(18,14),(19,16),(22,14),(18,12)),
 ('left',(13,14),(11,16),(7,16),(8,12)),
 ('left',(13,14),(13,17),(9,17),(8,12)),
 ('right',(12,14),(10,15),(8,16),(9,13)),
]
def lerp(a,b,t):return tuple(round(a[k]*(1-t)+b[k]*t) for k in range(2))
def points(im):
 a=np.array(im);p={}
 for part,c in COLORS.items():
  matches=np.argwhere(np.all(a==c,axis=2));assert len(matches)==1
  y,x=matches[0];p[part]=(int(x),int(y))
 return p

def markers(size,p):
 im=Image.new('RGBA',size);used=set();actual={}
 for part in COLORS:
  x,y=p[part]
  pos=next((q for q in [(x,y),(x+1,y),(x-1,y),(x,y+1),(x,y-1)] if q not in used and 0<=q[0]<size[0] and 0<=q[1]<size[1]),None)
  assert pos is not None;used.add(pos);im.putpixel(pos,COLORS[part]);actual[part]=pos
 return im,actual

def native(slot):
 folder=REF/slot/'sprite';root=ET.parse(folder/'AnimData.xml').getroot()
 n=next(a for a in root.findall('./Anims/Anim') if a.findtext('Name')=='Idle');w=int(n.findtext('FrameWidth'));h=int(n.findtext('FrameHeight'))
 sheets=[Image.open(folder/f'Idle-{k}.png').convert('RGBA') for k in ['Anim','Offsets','Shadow']]
 return [[s.crop((0,d*h,w,(d+1)*h)) for s in sheets] for d in range(8)]

def gardevoir(views,action):
 rows=[];landmarks=[]
 for di,(normal,offset,shadow) in enumerate(views):
  a=np.array(normal);p=points(offset);part,shoulder,elbow,fold,target=RIG[di];wrist=p[part]
  mask=Image.new('L',normal.size);ImageDraw.Draw(mask).line([shoulder,elbow,wrist],fill=255,width=4)
  rgb=a[:,:,:3].astype(int);green=(rgb[:,:,1]>rgb[:,:,0]+20)&(rgb[:,:,1]>rgb[:,:,2]+20)
  erase=(np.array(mask)>0)&(green|np.all(rgb==0,axis=2))&(a[:,:,3]>0);erase[:14]=False;erase[22:]=False
  body=a.copy();body[erase]=0;row=[];poses=[]
  for fi in range(16):
   im=normal.copy();q=copy.deepcopy(p)
   if action=='Eat':
    t=EASE[fi]
    if t:
     hand=lerp(wrist,target,t);bend=lerp(elbow,fold,t);im=Image.fromarray(body)
     arm=Image.new('RGBA',normal.size);d=ImageDraw.Draw(arm)
     d.line([shoulder,bend,hand],fill=(0,0,0,255),width=3)
     d.line([shoulder,bend,hand],fill=(95,199,55,255),width=1);d.point(hand,fill=(143,255,103,255));im.alpha_composite(arm);q[part]=hand
     if di in [3,4,5]:
      b=np.array(im);head=a[:,:,3]>0;head[14:]=False;b[head]=a[head];im=Image.fromarray(b)
    if fi in [8,9] and di in [0,1,2,6,7]:
     b=np.array(im);eyes=np.all(a==[231,63,103,255],axis=2);eyes[12:]=False;b[eyes]=[127,143,151,255];im=Image.fromarray(b)
   else:
    bend=BEND[fi]
    if bend:
     head=normal.crop((0,0,32,14)).resize((32,14-bend),Image.Resampling.NEAREST)
     im.paste((0,0,0,0),(0,0,32,14));im.alpha_composite(head,(0,bend))
     x,y=q['head'];q['head']=(x,min(13,bend+round(y*(14-bend)/14)))
     if bend>=2 and di in [0,1,2,6,7]:
      b=np.array(im);eyes=np.all(b==[231,63,103,255],axis=2);eyes[13:]=False;b[eyes]=[127,143,151,255];im=Image.fromarray(b)
   off,actual=markers(im.size,q);row.append([im,off,shadow.copy()]);poses.append(actual)
  rows.append(row);landmarks.append(poses)
 return rows,landmarks

def shroomish(views):
 vectors=[(0,1),(.75,.85),(1,.8),(.75,.5),(0,.45),(-.75,.5),(-1,.8),(-.75,.85)];rows=[];landmarks=[]
 for di,(normal,offset,shadow) in enumerate(views):
  p=points(offset);vx,vy=vectors[di];row=[];poses=[]
  for t in EASE:
   actor=Image.new('RGBA',(32,32))
   def project(x,y):
    weight=max(0,math.sin(math.pi*(y+1)/18)) if y<17 else 0
    return x+round(vx*3*t*weight)+4,y+round(vy*2*t*weight)+4
   if not t:actor.alpha_composite(normal,(4,4))
   else:
    mapped=[project(0,y)[1]-4 for y in range(18)]
    for dy in range(18):
     sy=min(range(18),key=lambda y:abs(mapped[y]-dy))
     if dy<min(mapped):continue
     shift=project(0,sy)[0];actor.alpha_composite(normal.crop((0,sy,24,sy+1)),(shift,4+dy))
    actor.paste(normal.crop((0,15,24,24)),(4,19))
   q={k:project(*xy) for k,xy in p.items()};off,actual=markers((32,32),q)
   sd=Image.new('RGBA',(32,32));sd.alpha_composite(shadow,(4,4));row.append([actor,off,sd]);poses.append(actual)
  rows.append(row);landmarks.append(poses)
 return rows,landmarks

def export_action(pack,root,name,rows,ticks):
 w,h=rows[0][0][0].size
 for k,kind in enumerate(['Anim','Offsets','Shadow']):
  sheet=Image.new('RGBA',(16*w,8*h))
  for d,row in enumerate(rows):
   for f,triple in enumerate(row):sheet.paste(triple[k],(f*w,d*h))
  sheet.save(pack/f'{name}-{kind}.png')
 anims=root.find('Anims');old=next((n for n in anims if n.findtext('Name')==name),None)
 index=int(old.findtext('Index')) if old is not None else max(int(n.findtext('Index','-1')) for n in anims)+1
 if old is not None:anims.remove(old)
 n=ET.SubElement(anims,'Anim')
 for tag,val in [('Name',name),('Index',index),('FrameWidth',w),('FrameHeight',h)]:ET.SubElement(n,tag).text=str(val)
 durations=ET.SubElement(n,'Durations')
 for t in ticks:ET.SubElement(durations,'Duration').text=str(t)
 ET.indent(root);ET.ElementTree(root).write(pack/'AnimData.xml',encoding='utf-8',xml_declaration=True)

def preview(prefix,rows,ticks):
 folder=OUT/'review';folder.mkdir(exist_ok=True);dur=[round(t*1000/60/10)*10 for t in ticks];boards=[]
 for f in range(16):
  board=Image.new('RGB',(640,448),(35,47,60));draw=ImageDraw.Draw(board)
  for d,row in enumerate(rows):
   actor=row[f][0];tile=Image.new('RGBA',(32,40),(35,47,60,255));tile.alpha_composite(actor,(0,40-actor.height))
   x=d%4*160;y=d//4*224;board.paste(tile.convert('RGB').resize((160,200),Image.Resampling.NEAREST),(x,y+24));draw.text((x+6,y+6),DIRS[d],fill='white')
  boards.append(board)
 boards[0].save(folder/f'{prefix}_8directions.gif',save_all=True,append_images=boards[1:],duration=dur,loop=0,disposal=2)
 for d,row in enumerate(rows):
  images=[]
  for actor,_,_ in row:
   tile=Image.new('RGBA',actor.size,(35,47,60,255));tile.alpha_composite(actor);images.append(tile.convert('RGB').resize((actor.width*6,actor.height*6),Image.Resampling.NEAREST))
  images[0].save(folder/f'{prefix}_{DIRS[d]}.gif',save_all=True,append_images=images[1:],duration=dur,loop=0,disposal=2)
 board=Image.new('RGB',(640,8*166),(35,47,60));draw=ImageDraw.Draw(board)
 for d,row in enumerate(rows):
  for col,f in enumerate([0,4,7,11]):
   actor=row[f][0];tile=Image.new('RGBA',(32,40),(35,47,60,255));tile.alpha_composite(actor,(0,40-actor.height));board.paste(tile.convert('RGB').resize((128,160),Image.Resampling.NEAREST),(col*160+25,d*166+6));draw.text((col*160+2,d*166+2),DIRS[d]+'/'+str(f),fill='white')
 board.save(folder/f'{prefix}_keyframes.png')

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 gv=native('0282');sh=native('0285')
 tasks=[('gardevoir','0282',ROOT/'exports/guild_scene_animations_v2/gardevoir_eat_candidate',[('Eat',gardevoir(gv,'Eat'),EAT_TICKS),('Nod',gardevoir(gv,'Nod'),NOD_TICKS)]),('shroomish','0285',REF/'0285/sprite',[('Eat',shroomish(sh),EAT_TICKS)])]
 report={'reconstruction':'Lost V3/V4 commits could not be recovered. New reconstruction from native anatomy, retained V1/V2 gesture studies and recorded articulation parameters. Not byte-identical recovery of missing files.','food_in_sprite':False,'art_approved':False,'runtime_PMDO':'NOT TESTED','source_pin':'3609a86be2a4c8ad7cf255bd2255f044daafe24f','actions':{},'packs':{}}
 sys.path.insert(0,str(ROOT/'source/pmd_character_pipeline'))
 from validate import run
 for who,slot,base,actions in tasks:
  pack=OUT/(who+'_candidate');pack.mkdir(exist_ok=True)
  for p in base.iterdir():
   if p.suffix in ['.png','.xml']:shutil.copyfile(p,pack/p.name)
  root=ET.parse(base/'AnimData.xml').getroot()
  for name,(rows,landmarks),ticks in actions:
   export_action(pack,root,name,rows,ticks);preview(who+'_'+name,rows,ticks)
   unique=[len({frame[0].tobytes() for frame in row}) for row in rows]
   for row in rows:assert row[0][0].tobytes()==row[-1][0].tobytes()
   assert min(unique)>=3
   report['actions'][who+'/'+name]={'directions':8,'frames_per_direction':16,'unique_drawings_per_direction':unique,'durations_ticks':ticks,'cycle_complete':True,'state':'technical_pass','landmarks':landmarks}
  check=run('sprite',pack,'dungeon');assert check['technical_precheck']=='PASS',check['errors']
  hashes={}
  for p in (REF/slot/'sprite').glob('*.png'):
   assert p.read_bytes()==(pack/p.name).read_bytes();hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
  report['packs'][who]={'technical_check':check,'native_png_sha256':hashes};shutil.copyfile(REF/slot/'sprite/credits.txt',OUT/f'{who}_native_credits.txt')
 shutil.copyfile(REF/'0282/0002/sprite/credits.txt',OUT/'gardevoir_cutscene_credits.txt')
 (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 gallery(report);print({k:v['unique_drawings_per_direction'] for k,v in report['actions'].items()})

def gallery(report):
 def uri(p):return 'data:image/gif;base64,'+base64.b64encode(p.read_bytes()).decode()
 html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Guilde · Cycles reconstruits sans nourriture</title><style>body{font:16px system-ui;max-width:1100px;margin:32px auto;padding:0 24px;background:#141d2b;color:#edf4fa}p,li{line-height:1.7;color:#bed0df}img{max-width:100%;image-rendering:pixelated}section{padding:22px;background:#232f3c;border-radius:14px;margin:24px 0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px}.note{border-left:3px solid #f4c477;padding:16px}details{margin-top:20px}summary{cursor:pointer}</style><h1>Guilde · Trois cycles reconstruits</h1><p>Eat et Nod de Gardevoir, Eat de Balignon. Huit vues natives indépendantes,16étapes par vue, retour au repos. Aucune nourriture intégrée aux sprites : geste, repas et émote sont des éléments distincts.</p><p class="note">Reconstruction des lots perdus, pas récupération byte-identique des anciens commits. Les trois cycles passent les contrôles locaux ; art et runtime PMDO restent non approuvés. Les autres manques de la guilde ne sont pas terminés.</p>'''
 titles={'gardevoir/Eat':('Gardevoir — Eat raffiné','Bras fin rapproché du visage, pause discrète puis retour. Le casque masque la main en vue arrière.'),'gardevoir/Nod':('Gardevoir — Nod','Inclinaison retenue de la tête autour du cou, sans rebond de la robe ou du corps.'),'shroomish/Eat':('Balignon — Eat sans bras','Inclinaison du corps au-dessus des pieds ancrés, courte pause puis retour. Aucun membre ou aliment inventé.')}
 for key in report['actions']:
  prefix=key.replace('/','_');title,desc=titles[key];html+='<section><h2>'+title+'</h2><p>'+desc+'</p><img alt="'+title+' huit directions" src="'+uri(OUT/'review'/f'{prefix}_8directions.gif')+'"><details><summary>Les huit GIFs individuels</summary><div class="grid">'
  for direction in DIRS:html+='<div><h3>'+direction+'</h3><img alt="'+title+' '+direction+'" src="'+uri(OUT/'review'/f'{prefix}_{direction}.gif')+'"></div>'
  html+='</div></details></section>'
 html+='<p>27GIFs de nos cycles sous exports/guild_scene_recovery_v5/review/. Les anims natives, leurs crédits et les lots V1/V2 restent préservés.16étapes comprennent des maintiens : ce ne sont pas forcément16dessins uniques.</p></html>'
 (ROOT/'apercu_guilde_reconstruction_v5.html').write_text(html)
if __name__=='__main__':main()
