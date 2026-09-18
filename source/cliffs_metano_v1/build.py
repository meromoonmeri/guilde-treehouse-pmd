"""Export des falaises référencées Métano. Ne relance pas le générateur.
Python: Pillow, numpy, scipy. Exécuter depuis n'importe quel dossier.
Les helpers de détourage, CIELAB et nuit sont ceux des lots précédents.
"""
from pathlib import Path
import sys, json, hashlib, io, zipfile
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
OUT = ROOT / 'renders/cliffs_metano_v1'
sys.path.insert(0, str(ROOT / 'source/caps_terrasses_v4'))
from build import chroma, lab
sys.path.insert(0, str(ROOT / 'source/cote_v4_abyss'))
from night import night
sys.path.insert(0,str(ROOT/"source"))
import ciels_valides as approved

ITEMS = [
 ('01_cap_des_alizes', 'Cap des Alizés', 'Sprite isolé', '01_cap_des_alizes_corrige.png',
  'Plateau asymétrique et retour concave. Petite terrasse parasite retirée au second passage. Grain plus grossier que la référence native ; échelle à apprécier en jeu.'),
 ('02_balcon_du_levant', 'Balcon du Levant', 'Sprite isolé', '02_balcon_du_levant.png',
  'Long balcon courbe, ombre mauve sur le retour gauche. Sol continu ; face assez régulière, pas un module raccordable automatiquement.'),
 ('03_defile_des_explorateurs', 'Défilé des Explorateurs', 'Nouvelle zone', '03_cirque_des_explorateurs_corrige.png',
  'Le second passage a ouvert le mur central : défilé sud-nord entre deux hauteurs, escalier à droite. Ce n’est plus le cirque fermé initialement demandé au générateur. Accès visibles, collisions non fournies.'),
 ('04_terrasses_du_sillage', 'Terrasses du Sillage', 'Nouvelle zone', '04_terrasses_du_sillage.png',
  'Approche sud-ouest, grande volée centrale et plateau nord-est. Le générateur a ajouté des plages de sable et une banquette intermédiaire. Escalier dessiné, pas extrait du tileset natif.'),
]

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(im, path):
 path.parent.mkdir(parents=True, exist_ok=True)
 im.save(path, optimize=True)
def png_bytes(im):
 b = io.BytesIO(); im.save(b, format='PNG'); return b.getvalue()
def ora(path, layers):
 """layers = bottom -> top. ORA stores top -> bottom."""
 w,h=layers[0][1].size
 root=ET.Element('image', {'w':str(w),'h':str(h),'name':path.stem,'version':'0.0.3'})
 stack=ET.SubElement(root,'stack')
 merged=Image.new('RGBA',(w,h))
 with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED) as z:
  z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
  for i,(name,im) in enumerate(layers):
   merged.alpha_composite(im); z.writestr(f'data/layer{i}.png',png_bytes(im))
  for i,(name,im) in reversed(list(enumerate(layers))):
   ET.SubElement(stack,'layer',{'name':name,'src':f'data/layer{i}.png','x':'0','y':'0','opacity':'1.0','visibility':'visible','composite-op':'svg:src-over'})
  z.writestr('stack.xml',ET.tostring(root,encoding='utf-8'))
  z.writestr('mergedimage.png',png_bytes(merged))
  thumb=merged.copy();thumb.thumbnail((256,256),Image.Resampling.NEAREST)
  z.writestr('Thumbnails/thumbnail.png',png_bytes(thumb))


def main():
 OUT.mkdir(parents=True,exist_ok=True)
 cfg_path=ROOT/'source/caps_terrasses_v4/palette_canonique.json'
 cfg=json.loads(cfg_path.read_text())
 # Check that pinned native source bytes are still the ones used by V4.
 for source in cfg['source_files']:
  assert sha(ROOT/source['path'])==source['sha256'],source['path']
 pal=np.array(cfg['allowed_rgb'],dtype=np.uint8);tree=cKDTree(lab(pal))
 size=Image.open(OUT/'bruts'/ITEMS[0][3]).size
 assert size[0]%8==size[1]%8==0
 context=ROOT/'renders/caps_terrasses_v3'
 context_records=[]; background={}
 for mode in ['jour','nuit']:
  for name,im in [('ciel',approved.sky(size,mode)),('astres',approved.stars(size,mode,moon=True)),('nuages',approved.wrap(approved.clouds(mode),size))]:
   dest=OUT/'contexte'/f'METANO_CLIFFS_V1_{name}_{mode}.png'
   save(im,dest);background[mode,name]=im
   context_records.append({'approved_family':True,'kind':name,'mode':mode,'export':str(dest.relative_to(OUT)),'resampled':False})
  save(approved.clouds(mode),OUT/'contexte'/f'METANO_CLIFFS_V1_nuages_bande_{mode}.png')
  for frame in range(64):
   src=context/'ocean'/f'{mode}_{frame:02d}.png'
   dest=OUT/'contexte'/f'METANO_CLIFFS_V1_ocean_{mode}_{frame:02d}.png'
   im=Image.open(src).convert('RGBA').resize(size,Image.Resampling.NEAREST)
   save(im,dest)
   if frame==0:background[mode,'ocean']=im
   context_records.append({'source':str(src.relative_to(ROOT)),'sha256':sha(src),'export':str(dest.relative_to(OUT)),'resized_nearest_for_demonstration_only':True})
 records=[];audits=[]
 for slug,title,kind,filename,review in ITEMS:
  rawpath=OUT/'bruts'/filename; raw=Image.open(rawpath).convert('RGBA')
  assert raw.size==size
  a=chroma(raw);opaque=a[:,:,3]>0
  unique,inv=np.unique(a[opaque,:3],axis=0,return_inverse=True)
  delta,idx=tree.query(lab(unique));a[opaque,:3]=pal[idx][inv]
  a[~opaque]=0;a[opaque,3]=255
  im=Image.fromarray(a)
  folder=OUT/slug;folder.mkdir(exist_ok=True)
  prefix='METANO_CLIFFS_V1_'+slug
  files={}
  for mode,terrain in [('jour',im),('nuit',night(im))]:
   p=folder/f'{prefix}_terrain_{mode}.png';save(terrain,p);files['terrain_'+mode]=str(p.relative_to(OUT))
   layers=[('Ciel validé c16efe12',background[mode,'ciel']),('Astres natifs séparés',background[mode,'astres']),('Nuages — décor de démonstration',background[mode,'nuages']),('Océan — phase 00 du cycle V3',background[mode,'ocean']),('Terrain — herbe, roche et bordures réunies',terrain)]
   scene=Image.new('RGBA',size)
   for _,layer in layers:scene.alpha_composite(layer)
   p=folder/f'{prefix}_scene_{mode}.png';save(scene,p);files['scene_'+mode]=str(p.relative_to(OUT))
   p=folder/f'{prefix}_{mode}.ora';ora(p,layers);files['ora_'+mode]=str(p.relative_to(OUT))
  magenta=Image.new('RGBA',size,(255,0,255,255));magenta.alpha_composite(im)
  p=folder/f'{prefix}_magenta.png';save(magenta,p);files['magenta']=str(p.relative_to(OUT))
  bb=im.getbbox()
  records.append({'id':slug,'title':title,'kind':kind,'size':list(size),'opaque_bbox_xyxy':bb,'raw':str(rawpath.relative_to(OUT)),'raw_sha256':sha(rawpath),'terrain_sha256':sha(OUT/files['terrain_jour']),'files':files,'visual_review':review,'status':'Candidat inspecté — validation utilisateur et moteur à faire','resampled':False,'canonical_pixels':False,'layers':['ciel','astres','nuages','ocean','terrain']})
  audits.append({'id':slug,'visible_pixels':int(opaque.sum()),'allowed_palette_size':len(pal),'deltaE76_median':round(float(np.median(delta[inv])),3),'deltaE76_p95':round(float(np.percentile(delta[inv],95)),3),'outside_palette':0,'alpha_binary':bool(np.isin(a[:,:,3],[0,255]).all()),'transparent_rgb_zero':bool((a[~opaque]==0).all()),'removed_background_pixels':int((~opaque).sum())})
 manifest={'title':'Falaises Métano — premier lot','date':'2026-09-18','method':'Références natives → génération sur magenta → détourage V4 → couleurs de la palette Métano V4 → variante Abyss. Aucune reconstruction de tuiles natives.','palette':str(cfg_path.relative_to(ROOT)),'palette_sha256':sha(cfg_path),'references':[{'path':str(p.relative_to(ROOT)),'sha256':sha(p)} for p in [ROOT/'source/falaises_generees/reference_canonique.png',ROOT/'source/caps_terrasses_v4/reference_matiere_stricte.png',ROOT/'renders/caps_terrasses_v4/08_crochet_droit_terrain.png',ROOT/'renders/falaise_metano_temoin/01_crete_sillage_transparent.png']], 'ocean':{'frames':64,'duration_ms':50,'period_ms':3200,'origin':'Caps/Terrasses V3, interpolation de palette ; pas un nouveau cycle officiel extrait'},'approved_backgrounds':approved.provenance(),'backgrounds':context_records,'zones':records,'limits':['Terrain indivisible : herbe/roche/bordures dans le même calque, comme Caps/Terrasses V3-V4.','Les ORA contiennent cinq plans alignés : ciel validé, astres, nuages natifs, océan phase 0, terrain. Pas de sol caché reconstruit.','Échelle du générateur conservée, pas une échelle native certifiée.','Pas de Ground, autotile, collisions, raccords automatiques ou test PMDO.','Métano est la référence utilisée. Aucune nouvelle extraction spécifique de Bourg-Trésor.']}
 (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 (HERE/'audit_couleurs.json').write_text(json.dumps(audits,ensure_ascii=False,indent=2)+'\n')
 # Contact sheet: transparent sprites on dark checker, no misleading ocean coverage.
 W,H=1600,1240; board=Image.new('RGB',(W,H),'#101e28');d=ImageDraw.Draw(board)
 fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
 font=lambda n:ImageFont.truetype(fontpath,n) if Path(fontpath).exists() else ImageFont.load_default()
 d.text((38,24),'MÉTANO / FALAISES',font=font(32),fill='#e7efd7')
 d.text((40,72),'02 sprites isolés + 02 nouvelles zones  ·  PNG transparents  ·  Jour / nuit',font=font(18),fill='#aabeb3')
 for i,r in enumerate(records):
  x=30+(i%2)*790;y=125+(i//2)*520
  d.rounded_rectangle((x,y,x+760,y+493),radius=12,fill='#1d303b')
  d.text((x+20,y+16),r['title'],font=font(23),fill='#ebefdb')
  d.text((x+20,y+50),r['kind']+'  /  1264 × 848 px',font=font(15),fill='#afbdba')
  image=Image.open(OUT/r['files']['terrain_jour']);image.thumbnail((728,405),Image.Resampling.NEAREST)
  board.paste(image,(x+(760-image.width)//2,y+80),image)
 d.text((40,1180),'Créations générées d’après les références Métano ; couleurs natives, motifs non certifiés.',font=font(17),fill='#b6c7bd')
 save(board,OUT/'PLANCHE_FALAISES_METANO.png')
 print('4 compositions exportées, 8 ORA corrigés, ciel/nuages validés c16efe12, mer V3 conservée.')

if __name__=='__main__': main()
