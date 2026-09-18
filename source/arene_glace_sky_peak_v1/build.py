"""Arène neuve sur magenta + panorama neigeux ; ciel/astres des sources validées.
Pas de reconstruction de tuiles natives pour les dessins générés.
"""
from pathlib import Path
import sys,json,hashlib,io,zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'renders/arene_glace_sky_peak_v1'
sys.path.insert(0,str(ROOT/'source'));import ciels_valides as climate
SIZE=(960,720);PREFIX='ARENE_SKYPEAK_V1';GRADE=np.array([.72,.80,.96])
FLOOR=[(154,493),(154,452),(194,407),(273,376),(362,348),(453,337),(655,327),(829,342),(970,365),(1055,411),(1101,465),(1110,533),(1074,600),(1004,640),(917,673),(824,690),(780,714),(764,773),(789,848),(489,848),(504,785),(496,736),(469,704),(379,684),(258,650),(198,607),(154,549)]

def load(p):return Image.open(p).convert('RGBA')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def blank():return Image.new('RGBA',SIZE)
def save(im,p):p.parent.mkdir(parents=True,exist_ok=True);im.save(p,optimize=True)
def key(im):
 a=np.array(im);r,g,b=a[:,:,:3].astype(int).transpose(2,0,1)
 a[(r>g*1.6)&(b>g*1.6)&(r>160)&(b>160)]=0
 a[a[:,:,3]==0]=0
 return Image.fromarray(a)
def select(im,mask):
 a=np.array(im);a[~mask]=0;return Image.fromarray(a)
def grade(im):
 a=np.array(im);a[:,:,:3]=np.rint(a[:,:,:3]*GRADE).astype('uint8');a[a[:,:,3]==0]=0;return Image.fromarray(a)
def place(im,width,xy):
 new=(width,round(im.height*width/im.width));out=blank();out.alpha_composite(im.resize(new,Image.Resampling.NEAREST),xy)
 return out,{'input_size':list(im.size),'resized_size':list(new),'scale':width/im.width,'offset_xy':list(xy),'resampling':'nearest uniforme','cropping':'bord inférieur du terrain volontairement hors cadre pour un premier plan attaché au bas'}
def moon_native():
 source=climate.load('astres_nuit_native');a=np.array(source)[24:80,312:368].copy()
 labels,_=ndimage.label(a[:,:,3]>0,np.ones((3,3)));counts=np.bincount(labels.ravel());counts[0]=0
 a[labels!=counts.argmax()]=0;im=Image.fromarray(a);bbox=im.getbbox();im=im.crop(bbox)
 return im,{'source':'source/cote_dix_zones/reference_autre_agent/source__falaise__astres_nuit_native.png','source_roi':[312,24,368,80],'component_bbox_in_roi':list(bbox),'method':'Plus grande composante alpha8connexe dans le ROI ; pixelsRGBA inchangés, pas de resampling ni recoloration.','size':list(im.size),'opaque_pixels':int((np.array(im)[:,:,3]>0).sum()),'placement':[800,64]}
def png(im):
 b=io.BytesIO();im.save(b,format='PNG');return b.getvalue()
def ora(path,layers):
 tree=ET.Element('image',w='960',h='720',name='Arène du Croissant — Sky Peak',version='0.0.3');stack=ET.SubElement(tree,'stack');scene=blank()
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for i,(name,im) in enumerate(layers.items()):z.writestr(f'data/layer{i}.png',png(im));scene.alpha_composite(im)
  for i,(name,im) in reversed(list(enumerate(layers.items()))):ET.SubElement(stack,'layer',name=name,src=f'data/layer{i}.png',x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
  z.writestr('stack.xml',ET.tostring(tree,encoding='utf-8'));z.writestr('mergedimage.png',png(scene));scene.thumbnail((256,256),Image.Resampling.NEAREST);z.writestr('Thumbnails/thumbnail.png',png(scene))

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 sky=np.array(climate.sky(SIZE,'nuit'))
 # Repeating a noisy scanline creates vertical rain-like streaks. Extend with
 # its most frequent existing RGB instead; no invented averaged color.
 colors,counts=np.unique(sky[64,:,:3],axis=0,return_counts=True)
 dark_rgb=colors[counts.argmax()];sky[65:,:,:3]=dark_rgb;sky[65:,:,3]=255
 layers={'01_ciel_bleu_noir':Image.fromarray(sky),'02_etoiles_natives':climate.stars(SIZE,'nuit')}
 moon,moon_meta=moon_native();save(moon,OUT/'sprites'/f'{PREFIX}_croissant_natif.png');ml=blank();ml.paste(moon,(800,64));layers['03_lune_canonique']=ml
 mountains=key(load(OUT/'bruts/montagnes_lointaines_magenta.png'));mountain_layer,mountain_norm=place(mountains,960,(0,45));layers['04_montagnes_lointaines']=mountain_layer
 original=key(load(OUT/'bruts/arene_magenta.png'));raw=np.array(original);valid=raw[:,:,3]>0
 maskim=Image.new('L',original.size);ImageDraw.Draw(maskim).polygon(FLOOR,fill=255);floor=np.array(maskim)>0;floor&=valid
 # Partition visible pixels; the complete underlay is independently generated.
 yy,xx=np.indices(valid.shape);remaining=valid&~floor;front=remaining&(yy>=670)
 masks={'06_reliefs_arriere':remaining&~front,'07_immersion_gauche':front&(xx<original.width/2),'08_immersion_droite':front&(xx>=original.width/2)}
 assert np.array_equal(sum(m.astype('uint8') for m in [floor,*masks.values()]),valid.astype('uint8'))
 base=load(OUT/'bruts/sol_glace_complet.png');assert base.size==original.size
 a=np.array(base);a[~valid]=0;a[floor]=raw[floor];full_floor=Image.fromarray(a)
 terrain_planes={'05_sol_complet_et_acces_sud':full_floor}
 for name,mask in masks.items():terrain_planes[name]=select(original,mask)
 terrain_norm=None
 for name,im in terrain_planes.items():layers[name],terrain_norm=place(grade(im),960,(0,140))
 expected,_=place(grade(original),960,(0,140));terrain=blank()
 for name in terrain_planes:terrain.alpha_composite(layers[name])
 assert terrain.tobytes()==expected.tobytes()
 save(terrain,OUT/f'{PREFIX}_terrain_seul.png')
 visible_floor,_=place(Image.fromarray((floor*255).astype('uint8')).convert('RGBA'),960,(0,140))
 # Mask exported as L, outside its transformed original field is zero.
 save(visible_floor.getchannel('R'),OUT/'controle'/f'{PREFIX}_sol_visible_masque.png')
 files={};scene=blank()
 for name,im in layers.items():
  path=OUT/'calques'/f'{PREFIX}_{name}.png';save(im,path);files[name]=str(path.relative_to(OUT));scene.alpha_composite(im)
 save(scene,OUT/f'{PREFIX}_composition_nuit.png');ora(OUT/f'{PREFIX}_editable.ora',layers)
 source_paths=[ROOT/'pmdskyicearena.png',ROOT/'iceroadpmdsky.png',ROOT/'source/sky_peak_v1/232233_reference.png',ROOT/'source/sky_peak_v1/sommet_reference.png',climate.REF/'source__falaise__ciel_nuit_native.png',climate.REF/'source__falaise__astres_nuit_native.png']
 manifest={'title':'Arène du Croissant — panorama Sky Peak','date':'2026-09-18','canvas':list(SIZE),'layers':files,'composition':f'{PREFIX}_composition_nuit.png','ora':f'{PREFIX}_editable.ora','terrain':f'{PREFIX}_terrain_seul.png','moon':moon_meta,'sky':{'source_commit':'c16efe12d74361df5ba8625abb68260f5f8fc6dd','method':'Recette climate.sky validée ; seules les65lignes supérieures sombres sont conservées, puis prolongement uni avec la couleur RGB existante la plus fréquente de la ligne64. Cela évite les stries verticales du bruit répété et supprime la partie turquoise pour le bleu-noir demandé. Ni palette nouvelle ni nouveau ciel généré.','unchanged_full_approved_sky':False},'stars':'Recette climate.stars, pixels natifs et positions du bandeau conservés. Pas de nouvelles étoiles peintes.','terrain_normalization':terrain_norm,'mountain_normalization':mountain_norm,'terrain_grade':{'rgb_multipliers':GRADE.tolist(),'method':'Atténuation moonlit choisie pour les nouveaux dessins, pas filtre Abyss ni palette native certifiée.'},'raws':[{'path':str(p.relative_to(OUT)),'sha256':sha(p)} for p in sorted((OUT/'bruts').glob('*.png'))],'references':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in source_paths],'floor_mask_polygon_source_px':FLOOR,'route_check':{'centerline':[[480,719],[480,650],[480,550]],'width_px':16,'meaning':'Contrôle géométrique de l’approche sud sur le masque du sol, pas données de collisions PMDO.'},'limits':['Arène et panorama : dessins générés guidés par PMD/IceRoad/SkyPeak, pas tuiles natives certifiées.','Lune : sprite33×36 pixels de la feuille native du dépôt, aucun redessin ni agrandissement.','Sous-couche cachée du sol générée ; faces cachées des reliefs non reconstituées.','Scène fixe, sans aurore, sans nuages ajoutés, sans animation prétendue.','Pas de Ground, collision, warp ou validation moteur.']}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 board=Image.new('RGB',(1280,1100),'#101e2c');d=ImageDraw.Draw(board);font=lambda n:ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',n)
 d.text((24,14),'ARÈNE DU CROISSANT / PANORAMA SKY PEAK',font=font(27),fill='#e4eff6')
 d.text((24,56),'Glace · montagnes enneigées lointaines · lune native · huit calques',font=font(17),fill='#aec4d0')
 for i,(name,im) in enumerate(layers.items()):
  x=20+(i%4)*315;y=115+(i//4)*315
  d.rounded_rectangle((x,y,x+304,y+287),radius=7,fill='#233848');thumb=im.copy();thumb.thumbnail((296,222),Image.Resampling.NEAREST);board.paste(thumb,(x+4,y+36),thumb)
  d.text((x+8,y+8),name.replace('_',' '),font=font(13),fill='white')
 preview=scene.copy();preview.thumbnail((420,315),Image.Resampling.NEAREST);board.paste(preview,(22,752))
 d.text((475,784),'PNG / 960 × 720 / grille8px',font=font(23),fill='#e4eff6')
 d.text((475,831),'Lune native33×36, sans resampling.',font=font(19),fill='#aec4d0')
 d.text((475,872),'Sol complet, approche sud et reliefs séparés.',font=font(19),fill='#aec4d0')
 d.text((475,927),'Dessins référencés PMD ; pas un Ground intégré.',font=font(17),fill='#aec4d0')
 save(board,OUT/'PLANCHE_CALQUES.png')
 print('Arène et panorama composés ; lune native33×36 ; huit calques960×720.')
if __name__=='__main__':main()
