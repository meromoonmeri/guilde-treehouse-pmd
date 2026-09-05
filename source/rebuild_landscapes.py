from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json
D=Path(__file__).resolve().parents[1];S=D/'source/paysage_reference';OUT=D/'exterieur';OUT.mkdir(exist_ok=True)
W,H=648,432

def load(mode,i):
 p=next(S.glob(f'{mode}_{i:02d}_*.png'));return Image.open(p).convert('RGBA')
def grade(im,mul,add,sat=1.):
 a=np.array(im);v=a[:,:,:3].astype(float);l=(v@np.array([.2126,.7152,.0722]))[:,:,None];v=l*(1-sat)+v*sat;v=v*np.array(mul)+np.array(add);a[:,:,:3]=np.rint(v).clip(0,255).astype('uint8');a[a[:,:,3]==0]=0;return Image.fromarray(a,'RGBA')
def sky(top,bottom):
 y=np.linspace(0,1,H)[:,None,None];v=(np.array(top)[None,None,:]*(1-y)+np.array(bottom)[None,None,:]*y);a=np.repeat(np.rint(v).astype('uint8'),W,axis=1);return Image.fromarray(a,'RGB').convert('RGBA')
def composite(mode):
 im=Image.new('RGBA',(W,H))
 for i in range(1,10):im.alpha_composite(load(mode,i))
 return im
allm={'jour':composite('jour'),'nuit':composite('nuit')}
specs={
 'aube':{'top':(74,99,147),'bottom':(247,187,145),'mul':(.80,.78,.87),'add':(14,9,17),'sat':.80,'cloud':((.89,.72,.71),(28,12,16)), 'sun':(548,101)},
 'soir':{'top':(86,121,160),'bottom':(255,177,94),'mul':(1.03,.82,.62),'add':(17,8,8),'sat':.90,'cloud':((1.0,.75,.54),(20,11,5)), 'sun':(98,104)},
 'crepuscule':{'top':(32,37,75),'bottom':(156,105,134),'mul':(.46,.46,.64),'add':(15,10,26),'sat':.78,'cloud':((.44,.36,.50),(30,17,34)), 'sun':None},
 'orageux':{'top':(33,45,62),'bottom':(96,113,125),'mul':(.53,.63,.74),'add':(6,12,19),'sat':.57,'cloud':((.31,.39,.48),(20,24,30)), 'sun':None}}
for mode,sp in specs.items():
 im=sky(sp['top'],sp['bottom'])
 if sp['sun']:
  sun=Image.new('RGBA',(W,H));d=ImageDraw.Draw(sun);x,y=sp['sun'];d.ellipse((x-8,y-8,x+8,y+8),fill=(255,232,159,255));d.ellipse((x-11,y-11,x+11,y+11),outline=(250,190,117,110));im.alpha_composite(sun)
 cl=grade(load('jour',3),*sp['cloud'],sat=.85)
 if mode=='orageux':
  q=cl.resize((W*2,160),Image.Resampling.NEAREST)
  im.alpha_composite(q,(-155,-20));im.alpha_composite(q,(-465,20));im.alpha_composite(cl,(0,28))
 else:im.alpha_composite(cl)
 for i in range(4,9):im.alpha_composite(grade(load('jour',i),sp['mul'],sp['add'],sp['sat']))
 if mode=='crepuscule':
  lights=load('nuit',9);a=np.array(lights);a[:,:,3]=np.rint(a[:,:,3]*.55).astype('uint8');im.alpha_composite(Image.fromarray(a,'RGBA'))
 if mode=='aube':
  yy,xx=np.indices((H,W));fog=np.exp(-((yy-173)/58)**2)*18;a=np.zeros((H,W,4),np.uint8);a[:,:,:3]=[207,210,219];a[:,:,3]=fog.astype('uint8');im.alpha_composite(Image.fromarray(a,'RGBA'))
 if mode=='orageux':
  rain=Image.new('RGBA',(W,H));draw=ImageDraw.Draw(rain);rng=np.random.default_rng(808)
  for _ in range(220):
   x=int(rng.integers(0,W+5));y=int(rng.integers(20,H));length=int(rng.integers(2,5));draw.line((x,y,x-2,y+length),fill=(169,192,213,45),width=1)
  im.alpha_composite(rain)
 allm[mode]=im
for mode,im in allm.items():im.save(OUT/(mode+'.png'),optimize=True)
(OUT/'ambiances.json').write_text(json.dumps({'ordre':['jour','nuit','crepuscule','aube','soir','orageux'],'source':'Panorama approuvé de la terrasse nord; même géographie et mêmes plans, palettes/ciel/météo variables','fixe':True,'dimensions':[W,H],'soleil_aube':'est/droite','soleil_soir':'ouest/gauche'},ensure_ascii=False,indent=2))
board=Image.new('RGB',(1296,756),(18,20,47));draw=ImageDraw.Draw(board)
for i,mode in enumerate(['jour','nuit','crepuscule','aube','soir','orageux']):
 q=allm[mode].resize((432,288),Image.Resampling.NEAREST);x=i%3*432;y=i//3*378;board.paste(q,(x,y+24),q);draw.text((x+12,y+6),mode.upper(),fill=(238,223,184))
board.save(D/'apercus/paysages_six_ambiances.png',optimize=True)
print('Six aligned landscape ambiances generated from the approved panorama.')
