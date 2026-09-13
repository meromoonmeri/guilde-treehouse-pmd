"""Scene-aligned semantic cutouts from EXISTING generated proposals.
No new image-model generation; hidden ground is filled from a source texture patch.
Masks are explicit/editable and original visible pixels recompose exactly.
"""
from pathlib import Path
import sys,json,hashlib,zipfile
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'source/cote_v4_abyss'))
from night import night
OUT=ROOT/'renders/entrees_calques_v6'
CONFIG={
 'foret_racines':{'source':'04_foret_racines.png','patch':[612,618,676,650],
 'ground':[(370,383),(395,365),(453,342),(508,350),(535,376),(548,425),(607,453),(661,477),(742,478),(813,439),(860,414),(904,403),(961,408),(989,437),(1063,443),(1108,429),(1140,433),(1107,474),(1060,506),(1100,549),(1153,573),(1197,571),(1221,587),(1190,621),(1237,658),(1230,681),(1191,713),(1177,744),(1152,768),(902,768),(891,737),(841,735),(821,708),(780,722),(761,714),(746,680),(711,703),(665,694),(612,672),(592,696),(558,684),(547,671),(522,659),(476,671),(433,670),(406,650),(404,625),(369,602),(363,570),(321,550),(299,525),(280,512),(330,486),(335,467),(368,453),(387,418)],
 'path':[(933,768),(936,700),(922,649),(884,618),(817,607),(718,603),(619,610),(522,609),(476,584),(446,558),(426,529),(400,470),(388,436),(379,400),(356,369),(403,338),(492,339),(531,350),(530,399),(550,433),(556,469),(587,500),(618,512),(704,502),(760,507),(783,501),(842,512),(898,510),(934,522),(981,539),(1009,570),(1023,598),(1063,638),(1088,686),(1090,768)],'foreground_y':610},
 'grotte_encaissee':{'source':'01_antre_encaisse.png','patch':[220,700,284,764],
 'path':[(546,944),(505,900),(504,844),(464,814),(404,771),(397,712),(373,686),(441,647),(482,617),(497,563),(445,551),(424,494),(461,463),(519,428),(527,398),(613,396),(638,433),(696,465),(705,515),(691,541),(645,554),(598,571),(596,610),(659,638),(715,648),(763,688),(734,745),(704,783),(657,803),(635,841),(630,901),(638,944)],'foreground_y':650}
}

def polygon(size,points):
 im=Image.new('L',size);ImageDraw.Draw(im).polygon(points,fill=255);return np.array(im)>0

def save(im,path):
 path.parent.mkdir(parents=True,exist_ok=True);im.save(path,optimize=True)

def main():
 OUT.mkdir(parents=True,exist_ok=True);records=[];board=Image.new('RGB',(1400,600),'#122533');d=ImageDraw.Draw(board)
 for row,(slug,c) in enumerate(CONFIG.items()):
  source=ROOT/'renders/entrees_pmd_collection'/c['source'];original=Image.open(source).convert('RGBA');w,h=original.size;size=((w+7)//8*8,(h+7)//8*8)
  src=Image.new('RGBA',size);src.paste(original,(0,0));a=np.array(src);valid=a[:,:,3]>0;rgb=a[:,:,:3].astype('int16')
  path=polygon(size,c['path']) & valid
  if 'ground' in c:ground=polygon(size,c['ground']) | path
  else:ground=((rgb[:,:,1]>rgb[:,:,0]-18)&(rgb[:,:,1]>rgb[:,:,2]+35))|path
  ground &=valid
  from scipy.ndimage import label, binary_dilation, binary_fill_holes
  if slug=='grotte_encaissee':
   nearby=binary_dilation(path,iterations=18)
   path=binary_fill_holes(nearby & (rgb[:,:,0]>rgb[:,:,1]+8) & (rgb[:,:,2]>55)) & valid
   ground |= path
  # Small isolated floor marks must not float on the rear cliff plane.
  labels,n=label(valid & ~ground);counts=np.bincount(labels.ravel())
  small=(labels>0)&(counts[labels]<2000);ground|=small
  # Two scene depth planes; not independently movable object sprites.
  back=valid & ~ground;front=back.copy();front[:c['foreground_y']]=False;back &=~front
  tile=original.crop(c['patch']);floor=Image.new('RGBA',size)
  for y in range(0,h,tile.height):
   for x in range(0,w,tile.width):floor.paste(tile,(x,y))
  b=np.array(floor);b[ground & ~path]=a[ground & ~path];b[~valid]=0
  layers=[Image.fromarray(b)]
  for mask in [path,back,front]:
   b=np.zeros_like(a);b[mask]=a[mask];layers.append(Image.fromarray(b))
  names=['00_sol','01_chemin','02_entree_arriere','03_premier_plan'];dest=OUT/slug
  for name,im in zip(names,layers):save(im,dest/(name+'.png'));save(night(im),dest/(name+'_nuit.png'))
  scene=Image.new('RGBA',size)
  for im in layers:scene=Image.alpha_composite(scene,im)
  assert scene.tobytes()==src.tobytes(),slug
  save(scene,dest/'composition.png');save(night(scene),dest/'composition_nuit.png')
  dry=layers[0].copy()
  for im in layers[2:]:dry=Image.alpha_composite(dry,im)
  save(dry,dest/'sans_chemin.png')
  for name,mask in [('MASQUE_CHEMIN',path),('MASQUE_SOL_VISIBLE',ground),('MASQUE_PREMIER_PLAN',front)]:save(Image.fromarray(mask.astype('uint8')*255),dest/(name+'.png'))
  # Portable OpenRaster with real named, ordered layers and full-size preview.
  import io,xml.etree.ElementTree as E
  image=E.Element('image',w=str(size[0]),h=str(size[1]),name=slug);stack=E.SubElement(image,'stack')
  with zipfile.ZipFile(dest/(slug+'.ora'),'w',zipfile.ZIP_DEFLATED) as z:
   z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
   for i in reversed(range(4)):
    E.SubElement(stack,'layer',name=names[i],src=f'data/layer{i}.png',x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
    z.write(dest/(names[i]+'.png'),f'data/layer{i}.png')
   z.writestr('stack.xml',E.tostring(image));z.write(dest/'composition.png','mergedimage.png')
  for col,(label,im) in enumerate([('COMPOSITION',scene),('SOL',layers[0]),('CHEMIN',layers[1]),('ENTREE / ARRIERE',layers[2]),('PREMIER PLAN',layers[3])]):
   thumb=im.copy();thumb.thumbnail((272,240),Image.Resampling.NEAREST);x=col*280;y=row*300
   check=Image.new('RGB',thumb.size,'#394b56');dd=ImageDraw.Draw(check)
   for yy in range(0,thumb.height,12):
    for xx in range(0,thumb.width,12):
     if (xx//12+yy//12)%2:dd.rectangle((xx,yy,xx+11,yy+11),fill='#263743')
   check.paste(thumb,(0,0),thumb);board.paste(check,(x,y+55));d.text((x+5,y+6),slug,fill='white');d.text((x+5,y+28),label,fill='white')
  records.append({'id':slug,'source':str(source.relative_to(ROOT)),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'original_size':[w,h],'canvas':size,'padding_right_bottom':[size[0]-w,size[1]-h],'resampled':False,'layers':names,'rgba_recomposition_exact':True,'hidden_ground':'repeated source texture patch, not generative inpainting','mask_method':'explicit hand-defined scene polygons; cave grass color classification','native_pmdo':False})
 save(board,OUT/'PLANCHE_CALQUES.png');(OUT/'manifest.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
 (ROOT/'source/retouches_v6/layer_masks.json').write_text(json.dumps(CONFIG,ensure_ascii=False,indent=2))
 print('PASS: two 4-layer kits, exact original visible pixels, 8px-divisible canvases, no resampling.')
if __name__=='__main__':main()
