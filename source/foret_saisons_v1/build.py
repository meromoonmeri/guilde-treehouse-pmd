from pathlib import Path
import sys,json
import numpy as np
from scipy import ndimage as nd
from PIL import Image
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'source/tours_saisons_v1'));from common import *
O=R/'renders/foret_saisons_v1';a=np.array(load(O/'bruts/printemps.png').resize((W,H),NN));yy,xx=np.mgrid[:H,:W];r,g,b=a[:,:,:3].astype(float).transpose(2,0,1)
rawpath=(r>g*1.07)&(g>b*1.25)&(r>180);labels,n=nd.label(rawpath);counts=np.bincount(labels.ravel());counts[0]=0;path=labels==counts.argmax();path=nd.binary_fill_holes(path)
# Continuous registered path mask shared by all seasons, including snow-covered sections.
for y in range(H):
 xs=np.flatnonzero(path[y]);assert len(xs)>0;path[y,xs[0]:xs[-1]+1]=True
veg=((g>r*1.07)&(g<188)&(b>35))|((r<70)&(g<120));veg=nd.binary_fill_holes(nd.binary_closing(veg,iterations=1));veg|=(r>g*.9)&(g<130)&nd.binary_dilation(veg,iterations=8);veg&=~path
rock=((xx-177)/24)**2+((yy-163)/24)**2<1;rock|=((xx-496)/27)**2+((yy-257)/26)**2<1
log=(xx>=124)&(xx<194)&(yy>=295)&(yy<354);veg&=~(rock|log)
structures=[('03_rochers',rock),('04_tronc_couche',log),('05_canopy_fond',veg&(yy<180)),('06_arbres_gauche',veg&(yy>=180)&(yy<395)&(xx<320)),('07_arbres_droite',veg&(yy>=180)&(yy<395)&(xx>=320)),('08_canopy_avant',veg&(yy>=395))]
Image.fromarray((path*255).astype('uint8')).save(O/'MASQUE_CHEMIN_COMMUN.png');entries=[]
for season in ['printemps','automne','hiver']:
 src=np.array(load(O/'bruts'/f'{season}.png').resize((W,H),NN));aligned=src.copy()
 # Generated seasonal edits retain the shared structure; do not warp rows, which would distort pixel clusters.
 masks=path|veg|rock|log;idx=nd.distance_transform_edt(masks,return_distances=False,return_indices=True);ground=aligned.copy();ground[masks]=aligned[idx[0][masks],idx[1][masks]]
 ls=[('01_sol_saisonnier',Image.fromarray(ground)),('02_chemin_commun',cut(aligned,path))]+[(n,cut(aligned,mask)) for n,mask in structures]
 assert np.array_equal(np.array(merge(ls)),aligned)
 for mode in ['jour','nuit']:
  layers=[(n,night(im) if mode=='nuit' else im) for n,im in ls];export_static(O/season/mode,f'fs1_{season}_{mode}',layers)
 entry=dict(id=season,size=[W,H],layers=[n for n,im in ls],path_mask_shared=True,generated=True,runtime_validated=False);entries.append(entry)
(O/'manifest.json').write_text(json.dumps(entries,indent=2));print('Forest:3seasons,shared path,6scenes,8layers')
