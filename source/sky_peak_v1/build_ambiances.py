from pathlib import Path
import json,math,sys
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];V=R/'renders/sky_peak_canonique_v1';O=R/'renders/sky_peak_ambiances_v2';S=(504,504);N=Image.Resampling.NEAREST
sys.path.insert(0,str(R/'source/cote_v4_abyss'));from night import night

def load(p):return Image.open(p).convert('RGBA')
def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p)
# Small layout change only: inner walls open outwards by at most twelve native pixels.
src=np.array([0,142,174,330,362,503]);dst=np.array([0,136,162,342,368,503]);columns=np.rint(np.interp(np.arange(504),dst,src)).astype(int)
def reshape(im):return Image.fromarray(np.array(im)[:,columns])
def grade(im,mode):
 if mode=='jour':return im.copy()
 if mode=='nuit':return night(im)
 a=np.array(im);rgb=a[:,:,:3].astype(float)
 mult,add={'aube':([.94,.79,.84],[16,7,12]),'crepuscule':([.80,.63,.67],[22,7,9]),'heure_bleue':([.43,.52,.82],[5,9,19])}[mode]
 a[:,:,:3]=np.clip(rgb*np.array(mult)+np.array(add),0,255).astype('uint8');a[a[:,:,3]==0]=0;return Image.fromarray(a)
base={n:load(V/'jour'/(n+'.png')) for n in ['04a_nuages_lointains_wrap','04b_montagnes','04c_nuages_proches_wrap','05_sol_et_rebord_herbeux','06_paroi_et_rochers']}
for n in ['05_sol_et_rebord_herbeux','06_paroi_et_rochers']:base[n]=reshape(base[n])
flowers=[reshape(load(V/'fleurs/jour'/f'{f:02}.png')) for f in range(32)]
specs=[('aube','Aube',[74,73,145],[255,195,149]),('jour','Jour',[25,96,233],[198,235,255]),('crepuscule','Crépuscule',[75,55,124],[255,161,95]),('heure_bleue','Heure bleue',[20,32,84],[128,137,184]),('nuit','Nuit',[6,14,43],[44,63,111])]
manifest={'canvas':list(S),'layout_reference':'2cwdrrs469f61.gif au commit8b7e760','layout_change':{'source_x':src.tolist(),'destination_x':dst.tolist(),'max_horizontal_displacement_px':12,'vertical_displacement_px':0,'method':'Redistribution horizontale nearest des pixels natifs : prairie centrale élargie, relief existant conservé, aucune nouvelle terrasse'},'flower_frames':32,'flower_frame_ms':50,'flower_period_ms':1600,'clouds':{'width':504,'far_px_s':-2,'near_px_s':-6},'modes':[]}
board=Image.new('RGB',(1512,1100),'#152432');d=ImageDraw.Draw(board)
for j,(mode,title,top,bottom) in enumerate(specs):
 sky=np.zeros((504,504,4),dtype='uint8');t=np.clip(np.arange(504)/150,0,1)[:,None,None];sky[:,:,:3]=np.array(top)*(1-t)+np.array(bottom)*t;sky[:,:,3]=255
 layers={'01_ciel':Image.fromarray(sky)};stars=Image.new('RGBA',S);astro=Image.new('RGBA',S)
 if mode in ['aube','heure_bleue','nuit']:
  rng=np.random.default_rng(87);ds=ImageDraw.Draw(stars);alpha={'aube':45,'heure_bleue':130,'nuit':215}[mode]
  for xx,yy in zip(rng.integers(3,501,65),rng.integers(3,106,65)):ds.point((int(xx),int(yy)),fill=(225,233,255,alpha))
 if mode in ['heure_bleue','nuit']:
  moon=load(R/'renders/references_calques_v1/nuit/04_lune_halo.png').crop((650,65,850,265)).resize((66,66),N);astro.alpha_composite(moon,(383,10))
 else:
  sun=load(R/'renders/soleil_spring_v1/soleil/frames/00.png').resize((60,60),N);xy={'aube':(50,55),'jour':(386,5),'crepuscule':(327,61)}[mode];astro.alpha_composite(sun,xy)
 layers['02_etoiles']=stars;layers['03_astre_halo']=astro
 for n,im in base.items():layers[n]=grade(im,mode)
 frames=[]
 for f,im in enumerate(flowers):save(grade(im,mode),O/mode/'fleurs'/f'{f:02}.png')
 layers['07_fleurs']=grade(flowers[0],mode)
 for n,im in layers.items():save(im,O/mode/(n+'.png'))
 for f in range(32):
  comp=Image.new('RGBA',S)
  for n,im in layers.items():comp.alpha_composite(grade(flowers[f],mode) if n=='07_fleurs' else im)
  frames.append(comp)
 save(frames[0],O/mode/'composition.png');frames[0].save(O/mode/'fleurs_animation.webp',save_all=True,append_images=frames[1:],duration=50,loop=0,lossless=True)
 manifest['modes'].append({'id':mode,'title':title,'layers':list(layers)})
 x=(j%3)*504;y=(j//3)*550;board.paste(frames[0],(x,y+32));d.text((x+12,y+8),title,fill='white')
save(board,O/'PLANCHE_5_AMBIANCES.png')
# Compare same lighting to show only the deliberately small layout edit.
before=Image.new('RGBA',S)
for n in manifest['modes'][1]['layers']:
 before.alpha_composite(load(V/'jour'/(n+'.png')) if n in ['05_sol_et_rebord_herbeux','06_paroi_et_rochers','07_fleurs'] else load(O/'jour'/(n+'.png')))
after=load(O/'jour/composition.png');proof=Image.new('RGB',(1008,538),'#182d39');proof.paste(before,(0,34));proof.paste(after,(504,34));pd=ImageDraw.Draw(proof);pd.text((12,10),'Avant : layout source',fill='white');pd.text((516,10),'Apres : prairie legerement elargie',fill='white');save(proof,O/'AVANT_APRES_LAYOUT.png')
(O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('Five ambiances; reference layout altered by at most12px horizontally, zero vertical displacement')
