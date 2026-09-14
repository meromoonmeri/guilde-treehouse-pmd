from pathlib import Path
import json,hashlib,base64,io
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent/'references';O=R/'renders/ledian_dojo_v1';SIZE=(512,512)
def load(p):return Image.open(p).convert('RGBA')
def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
def cut(im):
 a=np.array(im);f=a[:,:,:3].astype(float);m=(f[:,:,0]>f[:,:,1]*1.4)&(f[:,:,2]>f[:,:,1]*1.4)&(f[:,:,2]>35);a[m]=0;return Image.fromarray(a)
def part(im,m):
 a=np.array(im);a[~m]=0;return Image.fromarray(a)
def poly(points):
 im=Image.new('L',SIZE);ImageDraw.Draw(im).polygon(points,fill=255);return np.array(im)>0
specs=[
 ('couloir_ns','Couloir nord–sud élargi','couloir_ns_corrige',['N','S'],[(221,0),(288,0),(288,106),(407,121),(406,425),(325,452),(325,512),(191,512),(191,449),(93,425),(93,124),(221,106)]),
 ('couloir_ew','Couloir est–ouest','couloir_ew',['E','W'],[(0,216),(73,192),(439,192),(512,216),(512,332),(433,370),(80,370),(0,332)]),
 ('couloir_t','Jonction en T','couloir_t',['N','E','W'],[(221,0),(288,0),(288,122),(359,170),(413,239),(512,239),(512,332),(389,332),(321,436),(219,436),(120,332),(0,332),(0,239),(135,239),(171,170),(221,122)]),
 ('salle_traversee','Salle traversante','salle_traversee',['N','S'],[(224,0),(288,0),(288,149),(381,174),(435,262),(428,355),(324,445),(324,512),(192,512),(192,445),(90,355),(81,262),(129,174),(224,149)]),
 ('salle_laterale','Salle latérale','salle_laterale',['W','S'],[(103,184),(381,184),(454,263),(446,351),(324,449),(324,512),(192,512),(192,445),(75,355),(0,312),(0,236),(75,236)]),
 ('salle_carrefour','Salle carrefour','salle_carrefour_corrige',['N','S','E','W'],[(224,0),(288,0),(288,135),(381,168),(423,230),(512,230),(512,298),(423,298),(388,361),(322,444),(322,512),(190,512),(190,444),(121,361),(82,298),(0,298),(0,230),(82,230),(130,168),(224,135)])]
# One actual native floor patch defines the common transition strip of each port.
patch=load(P/'Ledian_Dojo_Floor.png').crop((184,224,216,256));save(patch,O/'materiaux/sol_raccord_natif.png');p=np.array(patch.resize((64,64),Image.Resampling.NEAREST));stripe=p[:32].copy();stripe[:,:,3]=np.minimum(stripe[:,:,3],np.array([255]*16+[round(255*(31-y)/16) for y in range(16,32)],dtype='uint8')[:,None])
ladder=load(P/'layer_3.png').crop((192,48,216,120));save(ladder,O/'materiaux/echelle_native.png')
manifest={'reference':'Palikadude/Halcyon ledian_dojo.rsground','commit':(P/'halcyon_commit.txt').read_text().strip(),'size':list(SIZE),'port_width':64,'runtime_validated':False,'rooms':[]};yy,xx=np.mgrid[:512,:512]
portspec={'N':((224,0),(256,8)),'S':((224,480),(256,504)),'W':((0,224),(8,256)),'E':((480,224),(504,256))}
for slug,title,raw,dirs,polygon in specs:
 scene=cut(load(O/'bruts'/f'{raw}.png').resize(SIZE,Image.Resampling.NEAREST));a=np.array(scene);opaque=a[:,:,3]>0;fm=poly(polygon)&opaque;other=opaque&~fm
 masks={'01_sol_chemin':fm,'02_murs_fond':other&(yy<200),'03_roche_gauche':other&(yy>=200)&(xx<256)&(yy<400),'04_roche_droite':other&(yy>=200)&(xx>=256)&(yy<400),'05_roche_premier_plan':other&(yy>=400)}
 layers={n:part(scene,m) for n,m in masks.items()};entries=[]
 for d in dirs:
  port=Image.new('RGBA',SIZE);arr=stripe if d=='N' else stripe[::-1] if d=='S' else np.transpose(stripe,(1,0,2)) if d=='W' else np.transpose(stripe,(1,0,2))[:,::-1]
  pos,point=portspec[d];port.alpha_composite(Image.fromarray(arr.copy()),pos);layers['06_acces_'+d]=port;entries.append({'direction':d,'xy':list(point),'width':64,'layer':'06_acces_'+d+'.png'})
 optional=[]
 if slug=='salle_laterale':
  l=Image.new('RGBA',SIZE);l.alpha_composite(ladder,(244,132));layers['07_echelle_native']=l;optional=['07_echelle_native']
 out=O/slug;out.mkdir(exist_ok=True)
 for n,im in layers.items():save(im,out/(n+'.png'))
 recomposed=Image.new('RGBA',SIZE)
 for n in masks:recomposed.alpha_composite(layers[n])
 assert np.array_equal(np.array(recomposed),a)
 comp=recomposed.copy()
 for n,im in layers.items():
  if n.startswith('06'):comp.alpha_composite(im)
 save(comp,out/'composition.png');save(scene,out/'terrain_detoure.png')
 schema=Image.new('RGB',SIZE,'#191815');sd=ImageDraw.Draw(schema);sd.polygon(polygon,fill='#928565')
 for e in entries:
  x,y=e['xy'];sd.ellipse((x-13,y-13,x+13,y+13),fill='#93d6ca');sd.text((max(5,x-4),max(20,min(482,y-5))),e['direction'],fill='white')
 sd.text((12,12),title,fill='white');save(schema,out/'schema.png')
 arr=np.array(comp)
 for d in dirs:
  edge=arr[0,224:288] if d=='N' else arr[-1,224:288] if d=='S' else arr[224:288,0] if d=='W' else arr[224:288,-1]
  assert np.all(edge[:,3]==255),(slug,d)
  assert np.array_equal(edge,p[0]),(slug,d,'shared connector')
 manifest['rooms'].append({'id':slug,'title':title,'raw':raw+'.png','ports':entries,'layers':list(layers),'optional':optional,'checks':{'partitions_exact':True,'ports_opaque_and_identical':True}})
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
board=Image.new('RGB',(1200,840),'#191815');d=ImageDraw.Draw(board)
for i,e in enumerate(manifest['rooms']):
 im=load(O/e['id']/'composition.png').resize((392,392),Image.Resampling.NEAREST);x=i%3*400;y=i//3*420;board.paste(im,(x,y+24),im);d.text((x+8,y+5),e['title'],fill='white')
save(board,O/'PLANCHE.png')
print('6 rooms; exact terrain partitions; 15 opaque64px matching ports; native ladder separate')
