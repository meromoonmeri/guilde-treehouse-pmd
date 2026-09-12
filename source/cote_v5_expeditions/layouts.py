"""Explicit organic layouts interpreted from the concept study, not copied textures.
Closed Catmull-Rom contours rasterized at native resolution; no artwork resampling.
"""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'sprites/cote_v5_expeditions';SIZE=(1168,912)

def shape(points):
 im=Image.new('1',SIZE);curve=[]
 for i in range(len(points)):
  p0,p1,p2,p3=[np.array(points[j%len(points)],float) for j in [i-1,i,i+1,i+2]]
  for t in np.linspace(0,1,24,endpoint=False):
   q=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t);curve.append(tuple(q))
 ImageDraw.Draw(im).polygon(curve,fill=1);return np.array(im,dtype=bool)

def oval(box):
 im=Image.new('1',SIZE);ImageDraw.Draw(im).ellipse(box,fill=1);return np.array(im,dtype=bool)

def extrude(a,depth):
 out=a.copy()
 for dy in range(1,depth+1):out[dy:]|=a[:-dy]
 return out

# Components are back-to-front. Each grassy shelf occludes what is behind it.
CONFIG=[
 ('01_crete_sillage','La crête du Sillage','falaise',[(520,[(-96,180),(160,128),(400,220),(760,128),(1264,200),(1220,430),(900,480),(680,340),(430,500),(100,420),(-96,480)])]),
 ('02_caps_relies','Les caps reliés','falaise',[(480,[(-96,240),(120,128),(370,152),(544,300),(820,152),(1264,200),(1264,520),(950,620),(740,430),(570,392),(400,620),(112,600),(-96,420)])]),
 ('03_eventail_strates','L’éventail des strates','falaise',[(480,[(-96,160),(1264,144),(1264,390),(900,430),(450,340),(-96,440)]),(200,(-100,520,1230,792)),(128,(120,352,1048,576)),(112,(320,192,848,352))]),
 ('04_lagune_occident','La lagune d’Occident','falaise',[(500,[(-96,128),(400,144),(760,128),(1264,168),(1264,640),(920,700),(776,456),(600,304),(240,300),(-96,304)]),(280,[(-96,664),(200,584),(520,600),(800,568),(1040,680),(1100,820),(680,800),(280,776),(-96,832)])]),
 ('05_cote_quatre_pointes','La côte aux quatre pointes','falaise',[(500,[(-96,128),(1264,136),(1264,240),(1024,400),(848,320),(720,512),(544,408),(400,616),(224,512),(64,704),(-96,616)])]),
 ('06_sommet_balcon','Le sommet au balcon','falaise',[(500,[(-96,168),(1264,168),(1264,384),(940,400),(500,312),(-96,408)]),(320,(-120,400,1240,704)),(224,(240,192,984,496))]),
 ('07_cap_chenal','Le cap du Chenal','falaise',[(560,[(-96,160),(1264,176),(1264,528),(1016,624),(736,560),(560,392),(320,664),(48,600),(-96,448)])]),
 ('08_antre_crochu','L’antre Crochu','donjon',[(360,[(-96,168),(1264,168),(1264,400),(864,376),(744,296),(424,296),(272,400),(-96,400)]),(240,[(128,624),(336,552),(480,488),(640,488),(832,568),(1040,624),(1264,704),(1264,840),(-96,840),(-96,720)])]),
 ('09_grotte_marees','La grotte des Marées','donjon',[(400,[(-96,168),(1264,160),(1264,424),(1040,424),(912,376),(704,384),(560,296),(208,360),(-96,448)]),(264,[(-96,640),(304,584),(608,600),(760,560),(928,560),(1096,640),(1264,744),(1264,864),(800,824),(368,832),(-96,848)])]),
 ('10_defile_brume','Le défilé de Brume','donjon',[(280,[(-96,704),(288,624),(464,440),(504,-80),(664,-80),(704,440),(896,624),(1264,704),(1264,900),(-96,900)]),(280,(-200,120,504,392)),(304,(664,72,1360,392))])]
DOORS={'08_antre_crochu':{'module':'portail','position':[544,360],'threshold':[576,496],'spawn':[576,704],'layout_reference':'Crooked Cavern: vestibule central et epaules enveloppantes'},
 '09_grotte_marees':{'module':'portail','position':[784,432],'threshold':[816,568],'spawn':[576,720],'layout_reference':'Brine Cave: corniche asymetrique et acces recule'},
 '10_defile_brume':{'module':'passage','position':[456,336],'threshold':[576,208],'spawn':[576,752],'layout_reference':'Drenched Bluff: corridor ouvert entre deux epaules'}}

def main():
 OUT.mkdir(exist_ok=True);records=[]
 for slug,title,kind,components in CONFIG:
  land=np.zeros((SIZE[1],SIZE[0]),bool);grass=land.copy()
  for depth,geometry in components:
   a=oval(geometry) if isinstance(geometry,tuple) else shape(geometry)
   body=extrude(a,depth);grass[body]=False;grass|=a;land|=body
  if slug=='04_lagune_occident':
   cut=shape([(-120,380),(200,384),(432,440),(560,512),(384,584),(104,536),(-120,568)])
   land[cut]=False;grass[cut]=False
  if slug=='07_cap_chenal':
   cut=shape([(560,440),(616,496),(608,624),(672,752),(608,992),(512,992),(552,792),(512,640),(544,544)])
   land[cut]=False;grass[cut]=False
  dest=OUT/slug;dest.mkdir(exist_ok=True)
  for name,a in [('MASQUE_TERRE',land),('MASQUE_HERBE',grass)]:Image.fromarray(a.astype('uint8')*255).save(dest/(name+'.png'))
  contacts={k:int(v.sum()) for k,v in [('W',land[:,0]),('E',land[:,-1]),('S',land[-1])]}
  assert all(contacts.values()),(slug,contacts)
  rec={'id':slug,'title':title,'kind':kind,'size':SIZE,'source_size':SIZE,'crop':[0,0,*SIZE],'exits':['W','E','S'],'edge_contact_pixels':contacts,'door':DOORS.get(slug)}
  if rec['door']:
   x,y=rec['door']['threshold'];assert grass[y:y+16,x:x+16].all(),slug
   x,y=rec['door']['spawn'];assert grass[y:y+16,x:x+16].all(),slug
  records.append(rec)
 (OUT/'layouts.json').write_text(json.dumps({'method':'explicit organic native-resolution contours; layouts inspired by reference studies; not pixel-identical generated proposals','zones':records},ensure_ascii=False,indent=2))
 print('10 new layouts: 7 cliffs, 3 entrances; all W/E/S contacts and entrance landings checked.')
if __name__=='__main__':main()
