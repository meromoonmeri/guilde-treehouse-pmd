"""Return to renders/layouts_magenta_v1 method: whole generated terrain, clean floor,
aligned depth layers and separate background animation. No map-chunk terrain assembly.
"""
from pathlib import Path
import json,hashlib,base64,io,zipfile,shutil,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];O=R/'renders/arene_glace_generee_v2';W,H=512,640;OLD=R/'exports/ice_arena_aurora_v1'
def load(p):return Image.open(p).convert('RGBA')
def blank():return Image.new('RGBA',(W,H))
def key(im):
 a=np.array(im);r,g,b=a[:,:,:3].astype(float).transpose(2,0,1);mag=(r>70)&(b>65)&(r>g*1.5)&(b>g*1.5);a[mag]=0;a[~mag,3]=255;return Image.fromarray(a)
def masked(im,m):
 a=np.array(im);a[~m]=0;return Image.fromarray(a)
def poly(points):
 im=Image.new('L',(W,H));ImageDraw.Draw(im).polygon([(round(x*W),round(y*H)) for x,y in points],fill=255);return np.array(im)>0
def ora(path,layers):
 root=ET.Element('image',w=str(W),h=str(H),name='Arène glacée générée V2');stack=ET.SubElement(root,'stack');comp=blank()
 with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for i,(name,im) in reversed(list(enumerate(layers.items()))):
   fn=f'data/layer{i}.png';ET.SubElement(stack,'layer',name=name,src=fn,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'});b=io.BytesIO();im.save(b,format='PNG');z.writestr(fn,b.getvalue())
  for im in layers.values():comp.alpha_composite(im)
  b=io.BytesIO();comp.save(b,format='PNG');z.writestr('mergedimage.png',b.getvalue());z.writestr('stack.xml',ET.tostring(root,encoding='utf-8',xml_declaration=True))
def build():
 for name in ['calques','masques','animation/aurores','animation/etoiles','review']:(O/name).mkdir(parents=True,exist_ok=True)
 terrain=key(load(O/'bruts/terrain_magenta.png').resize((W,H),Image.Resampling.NEAREST));floor=key(load(O/'bruts/sol_complet.png').resize((W,H),Image.Resampling.NEAREST));a=np.array(terrain);valid=a[:,:,3]>0;yy,xx=np.mgrid[:H,:W]
 ground=poly([(.397,.325),(.579,.320),(.603,.391),(.718,.475),(.748,.528),(.749,.584),(.702,.610),(.645,.646),(.632,.743),(.643,.841),(.748,.916),(.846,1),(.150,1),(.253,.921),(.345,.842),(.349,.717),(.350,.678),(.261,.599),(.258,.534),(.245,.467),(.310,.420),(.397,.381)])&valid
 objects=poly([(.278,.451),(.329,.438),(.381,.494),(.305,.506),(.278,.478)])|poly([(.324,.628),(.398,.614),(.462,.684),(.347,.693)])|poly([(.578,.574),(.648,.594),(.675,.658),(.603,.692),(.562,.668)])
 objects &=ground
 path=ground&(yy>=round(H*.64))&~objects;visible=ground&~path&~objects
 left=poly([(0,.22),(.08,.33),(.162,.362),(.241,.453),(.258,.527),(.261,.599),(.349,.678),(.345,.842),(.253,.921),(.150,1),(0,1)])
 right=poly([(1,.21),(.85,.29),(.76,.36),(.744,.49),(.749,.584),(.645,.646),(.632,.743),(.643,.841),(.748,.916),(.846,1),(1,1)])
 structure=valid&~ground;left&=structure;right&=structure&~left;rear=structure&~left&~right
 masks={'02_sol_visible':visible,'03_chemin_sud':path,'04_reliefs_arriere':rear,'05_reliefs_avant_gauche':left,'06_reliefs_avant_droit':right,'07_petits_reliefs':objects}
 layers={'01_sol_complet_genere':masked(floor,valid)}
 for name,m in masks.items():layers[name]=masked(terrain,m);Image.fromarray(np.uint8(m)*255).save(O/'masques'/f'{name}.png')
 for name,im in layers.items():im.save(O/'calques'/f'AreneGenV2_{name}.png')
 terrain.save(O/'review/terrain_detoure.png');floor.save(O/'review/sol_genere_detoure.png')
 # A deliberately bounded background asset, not a source of terrain modules.
 sky=Image.new('RGBA',(W,H),load(R/'aurorepmdsky.png').getpixel((0,0)));sky.save(O/'calques/AreneGenV2_00_ciel.png')
 haze=blank();haze.alpha_composite(load(R/'exports/zones_relayout_v2/aurora/ZonesV2_aurora_04_distant_haze.png'),(120,0));haze.save(O/'calques/AreneGenV2_00b_brume_lointaine.png')
 auroras=[];stars=[]
 for f in range(64):
  for typ,folder,label in [('aurores','aurora_frames','Ribbons'),('etoiles','star_frames','Stars')]:
   src=OLD/folder/f'IceAuroraV1_{label}_{f:02}.png';dst=O/'animation'/typ/f'AreneGenV2_{typ}_{f:02}.png';shutil.copyfile(src,dst)
   (auroras if typ=='aurores' else stars).append(load(dst))
 scenes=[]
 for f in range(64):
  im=sky.copy();im.alpha_composite(auroras[f],(120,0));im.alpha_composite(stars[f],(120,0));im.alpha_composite(haze)
  for layer in layers.values():im.alpha_composite(layer)
  scenes.append(im)
  if f in [0,16,32,48]:im.save(O/'review'/f'scene_{f:02}.png')
 scenes[0].save(O/'review/animation.webp',save_all=True,append_images=scenes[1:],duration=100,loop=0,lossless=True)
 pal=scenes[0].convert('RGB').quantize(colors=256);gif=[im.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE) for im in scenes];gif[0].save(O/'review/animation.gif',save_all=True,append_images=gif[1:],duration=100,loop=0,disposal=1,optimize=False)
 ora_layers={'00_ciel':sky,'00a_aurores_phase0':blank(),'00b_etoiles_phase0':blank(),'00c_brume_lointaine':haze,**layers};ora_layers['00a_aurores_phase0'].alpha_composite(auroras[0],(120,0));ora_layers['00b_etoiles_phase0'].alpha_composite(stars[0],(120,0));ora(O/'arene_generee_editable.ora',ora_layers)
 report={'size':[W,H],'workflow':'Whole terrain generation on magenta -> alpha cleanup -> generated full floor underlay -> aligned depth/ground/path layers -> independent background animation','previous_workflow_reference':['source/layouts_magenta_v1/WORKFLOW.md','source/layouts_magenta_v1/build.py','source/corrections_northern_v1/build.py'],'terrain_origin':'NEW GENERATED DRAWING referenced to PMD materials. Not pixel-exact canonical terrain and not a collage of cropped maps.','terrain_inputs':[{'file':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [O/'bruts/terrain_magenta.png',O/'bruts/sol_complet.png']],'normalization':'Whole generated images normalized to512x640 with nearest-neighbor; no individual map pieces pasted or tiled.','layers':[{'id':name,'file':'calques/AreneGenV2_'+name+'.png'} for name in layers],'background_layers':['calques/AreneGenV2_00_ciel.png','calques/AreneGenV2_00b_brume_lointaine.png'],'animation':{'frames':64,'milliseconds':100,'seconds':6.4,'origin':'Reuse of NEW AUTHORED motion on canonical aurora art from previous batch; not a recovered official cycle.','position':[120,0],'folders':['animation/aurores','animation/etoiles']},'layer_limit':'Depth partitions of one coherent render. Hidden floor is separately generated; hidden backs/sides of relief masses are not completed for arbitrary repositioning.','supersedes':'exports/ice_arena_aurora_v1 terrain method, rejected as map-piece assembly. Old files preserved.','runtime_PMDO':'NOT TESTED','art_approved':False,'other_zones_complete':False}
 (O/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 def uri(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
 data={'static':[{ 'id':'00_ciel','uri':uri(O/'calques/AreneGenV2_00_ciel.png')},{'id':'00b_brume_lointaine','uri':uri(O/'calques/AreneGenV2_00b_brume_lointaine.png')}]+[{'id':name,'uri':uri(O/'calques'/f'AreneGenV2_{name}.png')} for name in layers],'aurores':[uri(O/'animation/aurores'/f'AreneGenV2_aurores_{f:02}.png') for f in range(64)],'etoiles':[uri(O/'animation/etoiles'/f'AreneGenV2_etoiles_{f:02}.png') for f in range(64)]}
 page='''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Arène · retour au rendu généré</title><style>body{background:#101e2b;color:#e6edf1;font:16px system-ui;max-width:1160px;margin:32px auto;padding:20px}p{color:#beced9;line-height:1.6}h1{font-size:36px}.grid{display:flex;gap:26px;flex-wrap:wrap}canvas{background:#252333;image-rendering:pixelated;max-width:100%}aside{max-width:520px}label{display:block;padding:7px}button{background:#cae5ea;color:#18303e;padding:10px 20px;border:0;border-radius:6px}input[type=range]{width:100%}.note{border-left:3px solid #d9c78d;padding-left:14px}small{color:#c8d8a8}</style><h1>Une scène générée, pas un assemblage de maps</h1><p>Retour à la méthode de <code>renders/layouts_magenta_v1</code> : décor complet sur magenta, sol complet généré séparément, détourage et plans alignés. Le terrain ci-dessous est le dessin généré, pas une mosaïque de pixels prélevés dans les maps.</p><div class="grid"><canvas id="scene" width="512" height="640"></canvas><aside><h2>Calques & animation</h2><button id="play">Pause</button><p id="frame"></p><input id="seek" type="range" min="0" max="63" value="0"><div id="controls"></div><p class="note">Matières PMD utilisées comme références : le terrain est redessiné, pas certifié natif pixel-exact. Les aurores gardent leur dessin canonique ; le mouvement réutilisé est une création proposée, pas le cycle original du jeu.</p><p>Le sol caché est complété par une génération pleine image. Les reliefs sont des plans de profondeur : leurs faces cachées ne sont pas reconstruites pour les déplacer librement. ORA éditable, PNG, GIF/WebP et ZIP fournis. Pas d’import ou de collision PMDO validés.</p></aside></div><script>const data=__DATA__;const canvas=document.getElementById('scene'),ctx=canvas.getContext('2d'),controls=document.getElementById('controls'),seek=document.getElementById('seek'),frame=document.getElementById('frame');let running=true,f=0,start=performance.now();function image(uri){const im=new Image();im.src=uri;return im}const staticImgs=data.static.map(s=>image(s.uri)),aurores=data.aurores.map(image),etoiles=data.etoiles.map(image),checks={};for(const id of ['00_ciel','aurores','etoiles',...data.static.slice(1).map(s=>s.id)]){const label=document.createElement('label'),ch=document.createElement('input');ch.type='checkbox';ch.checked=true;checks[id]=ch;label.append(ch,document.createTextNode(id));controls.append(label)}function draw(){ctx.clearRect(0,0,512,640);function paint(id,im,x=0,y=0){if(checks[id].checked&&im.complete&&im.naturalWidth)ctx.drawImage(im,x,y)}paint('00_ciel',staticImgs[0]);paint('aurores',aurores[f],120,0);paint('etoiles',etoiles[f],120,0);for(let i=1;i<staticImgs.length;i++)paint(data.static[i].id,staticImgs[i]);frame.textContent='Étape '+(f+1)+' / 64 · boucle 6,4 s';seek.value=f}seek.oninput=()=>{running=false;f=+seek.value;document.getElementById('play').textContent='Lecture';draw()};document.getElementById('play').onclick=()=>{running=!running;start=performance.now()-f*100;document.getElementById('play').textContent=running?'Pause':'Lecture'};function tick(t){if(running)f=Math.floor((t-start)/100)%64;draw();requestAnimationFrame(tick)}requestAnimationFrame(tick)</script></html>'''
 (R/'apercu_arene_glace_generee_v2.html').write_text(page.replace('__DATA__',json.dumps(data,ensure_ascii=False)));print('Generated coherent terrain,7terrain layers,2BG layers,128animated PNGs,ORA,GIF/WebP,interactive gallery.')
if __name__=='__main__':build()
