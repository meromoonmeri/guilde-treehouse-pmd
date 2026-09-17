from pathlib import Path
import json,hashlib,sys
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent;O=R/'renders/references_54d3731';B=O/'bruts';N=Image.Resampling.NEAREST
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night
specs=[('01_murky_entree','01_murky_entree_corrigee','Entree forestiere verte',(400,320)),('02_murky_clairiere','02_murky_clairiere','Clairiere de Murky Forest',(336,500)),('03_armaldo_interieur','03_armaldo_interieur','Interieur Armaldo',(480,320)),('04_plage','04_plage','Plage',(768,432)),('05_chemin_plage','05_chemin_plage','Chemin vers la plage',(400,400)),('06_mont_foudre','06_mont_foudre','Mont Foudre - arene',(432,352)),('07_foret_energetique','07_foret_energetique_entree','Lisiere - foret energetique',(480,336)),('08_foret_champignons','08_foret_champignons_entree','Entree du sous-bois champignon',(456,360)),('09_lac_cascade','09_lac_cascade_entree','Grotte derriere la cascade',(456,304)),('10_foret_neige','10_foret_neige_corrigee','Passage forestier enneige',(456,500))]
def load(p):return Image.open(p).convert('RGBA')
def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
def key(im):
 a=np.array(im);r,g,b=[a[:,:,i].astype(int) for i in range(3)];a[(r>35)&(b>35)&(r>g*1.8)&(b>g*1.8)]=0;return Image.fromarray(a)
def poly(size,points):
 m=Image.new('L',size);w,h=size;ImageDraw.Draw(m).polygon([(int(x*w),int(y*h)) for x,y in points],fill=255);return np.array(m)>0
manifest={'reference_commit':'54d3731','static':True,'scenes':[],'notes':['10 scenes derives de 7 fichiers uniques; Energetic Forest (1) est un doublon exact.','Partitions de profondeur conservant la recomposition; surfaces masquees non reconstruites.','Versions source/jour et nuit Abyss; aucune animation ajoutee.']}
board=Image.new('RGB',(1600,1240),'#172a31');d=ImageDraw.Draw(board)
for index,(slug,rawname,title,size) in enumerate(specs):
 im=load(B/(rawname+'.png'))
 # Remove blank white credit-like margin produced on Mushroom correction, never crop the drawing.
 if index==7:
  ar=np.array(im);valid=(np.mean(np.all(ar[:,:,:3]>240,axis=2),axis=1)<.85);ys=np.where(valid)[0];im=im.crop((0,int(ys.min()),im.width,int(ys.max()+1)))
 im=im.resize(size,N)
 if index in [3,5]:im=key(im)
 a=np.array(im);w,h=size;y,x=np.mgrid[:h,:w];X=x/w;Y=y/h;labels=np.zeros((h,w),dtype='uint8');names={0:'sol_visible',1:'decor_arriere',2:'premier_plan',3:'entree',4:'elements'}
 sky_scene=index in [3,5,9]
 if index in [0,1]:
  labels[Y<.43]=1
  corridor=poly(size,[(.34,.43),(.68,.41),(.81,.61),(.67,.80),(.62,1),(.38,1),(.32,.81),(.23,.65)])
  labels[(~corridor)&(Y>.30)]=2
  entry=poly(size,[(.43,.23),(.58,.23),(.60,.40),(.42,.42)]) if index==0 else poly(size,[(.31,0),(.65,0),(.67,.3),(.31,.34)])
  labels[entry]=3;names[1]='roche_et_racines_arriere';names[2]='feuillage_avant';names[3]='grotte_axiale' if index==0 else 'racines_du_fond'
 elif index==2:
  labels[:]=1;inside=poly(size,[(.3,.25),(.62,.19),(.80,.30),(.85,.59),(.65,.8),(.40,.81),(.25,.63),(.21,.43)]);labels[inside]=0;labels[Y>.7]=2
  labels[((X>.59)&(X<.82)&(Y>.16)&(Y<.48))|((X>.36)&(X<.52)&(Y>.69)&(Y<.85))]=4
  labels[((X-.57)**2+((Y-.57)*1.5)**2)<.0022]=3
  names={0:'sol_de_la_piece',1:'parois_racines_arriere',2:'parois_avant',3:'foyer_non_anime',4:'mobilier_et_raccords'}
 elif index==3:
  labels[Y<.40]=1;labels[Y>.73]=2
  rgb=a[:,:,:3].astype(int);water=(Y<.44)&(rgb[:,:,2]>rgb[:,:,0]*1.12)&(rgb[:,:,1]>100);water|=(Y>.26)&(Y<.42)&(rgb.min(axis=2)>205);labels[water]=3
  names={0:'sable_visible',1:'rochers_arriere',2:'rochers_palmiers_avant',3:'mer_et_ecume_fixe'}
 elif index==4:
  labels[:]=2;path=poly(size,[(.45,0),(.64,0),(.57,.25),(.73,.4),(.6,.7),(.55,1),(.33,1),(.38,.7),(.39,.42),(.36,.25)])
  labels[path]=0;labels[(Y<.33)&(~path)]=1;names={0:'chemin_et_sol_visible',1:'arbres_arriere',2:'arbres_et_rochers_avant'}
 elif index==5:
  labels[:]=1;arena=poly(size,[(.24,.15),(.75,.13),(.82,.25),(.82,.7),(.70,.77),(.27,.77),(.17,.67),(.17,.28)]);labels[arena]=0;labels[(Y>.73)&(~arena)]=2;names={0:'arene_centrale',1:'rochers_et_aiguilles',2:'paroi_du_plateau'}
 elif index==6:
  labels[Y<.62]=1;labels[((X<.29)|(X>.73))&(Y>.33)]=2;labels[(X>.45)&(X<.56)&(Y>.32)&(Y<.63)]=3
  names={0:'clairiere_et_chemin',1:'troncs_arriere',2:'feuillage_avant',3:'passage_entre_racines'}
 elif index==7:
  labels[Y<.44]=1;labels[(X<.24)|(X>.76)|(Y>.86)]=2;labels[(X>.42)&(X<.58)&(Y>.25)&(Y<.44)]=3;labels[(X>.02)&(X<.22)&(Y>.64)&(Y<.79)]=4
  names={0:'clairiere_visible',1:'grands_champignons_arriere',2:'champignons_avant',3:'entree_sous_le_chapeau',4:'tronc_couche'}
 elif index==8:
  labels[:]=2;labels[Y<.31]=1;rgb=a[:,:,:3].astype(int);water=(rgb[:,:,2]>rgb[:,:,0]*1.6)&((rgb[:,:,2]>rgb[:,:,1]*1.12)|((rgb[:,:,1]>140)&(rgb[:,:,2]>140)));labels[water]=0
  entry=(X>.412)&(X<.59)&(Y<.205);labels[entry]=3
  curtain=entry&((rgb[:,:,2]>rgb[:,:,0]*1.35)|(rgb.min(axis=2)>205));labels[curtain]=4
  island=((X-.5)/.05)**2+((Y-.56)/.075)**2<1;labels[island]=5
  names={0:'eau_du_lac_fixe',1:'berge_rocheuse_arriere',2:'arbres_berges_avant',3:'grotte_derriere_cascade',4:'rideau_eau_ecume_fixe',5:'ilot_central'}
 elif index==9:
  # Empty sky top preserved on its own layer, no stars/clouds baked into generated terrain.
  skycut=int(h*.245);a[:skycut,:,3]=0;a[:skycut,:,:3]=0
  labels[Y<.46]=1;path=poly(size,[(.47,.43),(.58,.43),(.58,.65),(.7,.76),(.61,1),(.28,1),(.42,.77),(.39,.61)])
  labels[(~path)&(Y>.42)]=2;labels[path]=0
  names={0:'chemin_enneige',1:'montagnes_et_sapins_arriere',2:'sapins_avant'}
 pieces={}
 for code in sorted(np.unique(labels)):
  aa=a.copy();aa[labels!=code]=0;aa[aa[:,:,3]==0]=0
  if np.any(aa[:,:,3]):pieces[f'{int(code)+5:02}_{names[int(code)]}']=Image.fromarray(aa)
 joined=Image.new('RGBA',size)
 for piece in pieces.values():joined.alpha_composite(piece)
 assert np.array_equal(np.array(joined),a)
 save(joined,O/slug/'terrain_recompose.png');save(Image.fromarray(labels),O/slug/'plan_calques.png')
 notes=[]
 if index==0:notes.append('Grotte dans axe du chemin, vert/terre brun, aucun decor ajoute volontairement.')
 if index in [6,7,8]:notes.append('Friend Area convertie en entree naturelle; aucun batiment ni pont ajoute.')
 if index==8:notes.append('Acces a la grotte depuis le lac: navigation non definie, pas de collision/runtime valide.')
 if index==2:notes.append('Interieur: variante source + nuit, aucun astre ajoute a la piece.')
 mode_specs={}
 for mode in ['jour','nuit']:
  layers={}
  if sky_scene:
   top=np.array([69,144,204] if mode=='jour' else [13,21,57]);bottom=np.array([191,220,235] if mode=='jour' else [54,69,116]);u=np.linspace(0,1,h)[:,None,None];sky=np.zeros((h,w,4),dtype='uint8');sky[:,:,:3]=top[None,None,:]*(1-u)+bottom[None,None,:]*u;sky[:,:,3]=255
   if index==9:
    orig=np.array(night(im) if mode=='nuit' else im);cut=int(h*.245);sky[:cut]=orig[:cut];sky[cut:]=sky[cut-1:cut]
   layers['01_ciel']=Image.fromarray(sky);stars=Image.new('RGBA',size);astro=Image.new('RGBA',size)
   if mode=='nuit':
    rng=np.random.default_rng(540+index);ds=ImageDraw.Draw(stars)
    for sx,sy in zip(rng.integers(2,w-2,65),rng.integers(2,max(3,int(h*.22)),65)):ds.point((int(sx),int(sy)),fill=(219,230,255,215))
    moon=load(R/'renders/references_calques_v1/nuit/04_lune_halo.png').crop((650,65,850,265));sz=max(40,int(w*.14));astro.alpha_composite(moon.resize((sz,sz),N),(w//2-sz//2,int(h*.025)))
   layers['02_etoiles']=stars;layers['03_lune_halo']=astro
  if index==5:
   src=load(P/'thunder.png');ar=np.array(src);edge=np.concatenate([ar[:,:18,:3].reshape(-1,3),ar[:,-18:,:3].reshape(-1,3)]);pal=np.unique(edge,axis=0);colors={tuple(c) for c in pal if c.max()-c.min()<30 and c.max()>35};mask=np.array([[tuple(c) in colors for c in row] for row in ar[:,:,:3]])
   ar[~mask]=0;rear=ar.copy();rear[int(src.height*.82):]=0;rear[:,:,3]=(rear[:,:,3]*.75).astype('uint8');front=ar.copy();front[:int(src.height*.82)]=0
   # Restore the sheet's black corner padding to the neighboring overcast tone.
   rear[:45,:24]=[64,57,68,190];rear[:45,-24:]=[64,57,68,190]
   # Fill only the lower cloud body, preserving its native upper contour.
   full=np.array(src)
   for cx in range(src.width):
    col=full[:,:, :3][:,cx];cloud=(col.max(axis=1)-col.min(axis=1)<14)&(col.min(axis=1)>145)&(np.arange(src.height)>int(src.height*.76))
    hits=np.where(cloud)[0]
    if len(hits):
     start=int(hits[0]);front[start:,cx]=[225,225,228,255]
     good=cloud[start:];front[start:,cx][good]=full[start:,cx][good]
   layers['04_nuages_arriere']=Image.fromarray(rear).resize(size,N)
  for n,piece in pieces.items():layers[n]=night(piece) if mode=='nuit' else piece
  if index==5:layers['12_nuages_avant']=Image.fromarray(front).resize(size,N)
  comp=Image.new('RGBA',size)
  for n,piece in layers.items():save(piece,O/slug/mode/(n+'.png'));comp.alpha_composite(piece)
  save(comp,O/slug/mode/'composition.png');mode_specs[mode]=list(layers)
  if mode=='jour':
   thumb=comp.copy();thumb.thumbnail((310,340),N);xx=(index%5)*320+(320-thumb.width)//2;yy=(index//5)*620+40;board.paste(thumb,(xx,yy),thumb);d.text(((index%5)*320+10,(index//5)*620+10),title,fill='white')
   # Small night view underneath the day one is added below after night render.
  else:
   thumb=comp.copy();thumb.thumbnail((260,205),N);xx=(index%5)*320+(320-thumb.width)//2;yy=(index//5)*620+400;board.paste(thumb,(xx,yy),thumb)
 manifest['scenes'].append({'id':slug,'title':title,'size':list(size),'raw':rawname+'.png','layers':mode_specs,'notes':notes})
save(board,O/'PLANCHE_10_SCENES.png');(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('10 scenes, 20 compositions, static independent layers built')
