"""Maquette v2 : chemin droit sud -> clairière du temple, pelouse aux bords organiques, cadre de feuillage immersif."""
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
W,H=816,1152
rng=np.random.default_rng(11)
yy,xx=np.mgrid[0:H,0:W]
def noise(s,amp):
    n=ndi.gaussian_filter(rng.standard_normal((H,W)),s); return n/np.abs(n).max()*amp
PX0,PX1=360,456                       # chemin droit (96 px, grille 8)
CX,CY=408,260                         # clairière du temple
# pelouse : clairière + bande autour du chemin + deux baies décalées
lawn_d=np.minimum(np.hypot((xx-CX)/250,(yy-CY)/185)-1, 0)*0
clear=np.hypot((xx-CX)/250,(yy-CY)/190)<1
band=(np.abs(xx-408)<120+noise(18,26)+14*np.sin(yy/57))&(yy>300)
bayL=np.hypot((xx-250)/120,(yy-700)/80)<1
bayR=np.hypot((xx-570)/120,(yy-900)/80)<1
lawn=(clear|band|bayL|bayR)
lawn=ndi.gaussian_filter(lawn.astype(float)+noise(6,0.5),4)>0.5
carpet=((xx>=PX0)&(xx<PX1)&(yy>=330))|(np.hypot((xx-CX)/175,(yy-CY-20)/125)<1)
carpet&=lawn
# cadre de feuillage : bords gauche/droite, haut (trouée du rayon au centre), bas autour de l'entrée
edge=np.minimum(xx,W-1-xx).astype(float)
fl=(edge<150+noise(22,45))
top=(yy<70+noise(20,30)-95*np.exp(-((xx-CX)/85.0)**4))
bot=(yy>H-60+noise(15,20)+80*np.exp(-((xx-408)/120.0)**4))
fol=fl|top|bot
fol=ndi.gaussian_filter(fol.astype(float),3)>0.5
fol&=~carpet                         # jamais sur le chemin
# couleurs issues de secretgarden.png
C=dict(void=(47,87,55),lawn=(151,207,87),carpet=(159,207,55),fringe=(71,111,47),fol=(31,71,47),rim=(71,111,47))
img=np.zeros((H,W,3),np.uint8); img[:]=C['void']
rim=lawn&~ndi.binary_erosion(lawn,iterations=6,border_value=1); img[lawn]=C['lawn']; img[rim]=C['fringe']; img[carpet]=C['carpet']
Image.fromarray(img).save('guides/v2_guide_sol.png')
m=np.zeros((H,W,3),np.uint8); m[:]=(255,0,255); m[fol]=C['fol']; frim=fol&~ndi.binary_erosion(fol,iterations=5,border_value=1); m[frim]=C['rim']
Image.fromarray(m).save('guides/v2_guide_feuillage_magenta.png')
comp=img.copy(); comp[fol]=m[fol]; Image.fromarray(comp).save('guides/v2_maquette.png')
np.savez_compressed('travail/v2_masques.npz',lawn=lawn,carpet=carpet,fol=fol)
print('pelouse',lawn.sum(),'chemin',carpet.sum())
