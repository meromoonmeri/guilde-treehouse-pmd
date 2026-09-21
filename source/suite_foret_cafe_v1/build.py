"""One related forest finale and four generated, import-scale furniture proposals.
Only newly generated art is normalized. Previous scenes and native pixels stay intact.
"""
from pathlib import Path
import io,json,zipfile,sys,importlib.util
import numpy as np
from PIL import Image,ImageDraw
from storage import R,S,C,sha,raw
O=C/'build';SIZE=(480,336);IDS=['table_halcyon_vide','table_auberge','coffre','plante_auberge']
def image(b):return Image.open(io.BytesIO(b)).convert('RGBA')
def png(im):
 b=io.BytesIO();im.save(b,format='PNG',optimize=True);return b.getvalue()
def text(j):return (json.dumps(j,ensure_ascii=False,indent=2)+'\n').encode()
def key(im):
 a=np.array(im);r,g,b=np.moveaxis(a[:,:,:3].astype(float),2,0)
 matte=(r>g*1.4+10)&(b>g*1.4+10)&(b>r*.50)
 a[matte]=0;return Image.fromarray(a)
def previous():
 p=R/'source/lisiere_pmd_v1/release.py';sp=importlib.util.spec_from_file_location('le1_release',p);mod=importlib.util.module_from_spec(sp);sp.loader.exec_module(mod)
 return zipfile.ZipFile(mod.materialize('LE1_lisiere_calques_et_effets.zip'))
def palette():
 with zipfile.ZipFile(R/'renders/dungeon_biomes_v1/DB1_cinq_duos_multicalques.zip') as z:a=np.array(image(z.read('references/DB1_native_H07P03.png')))
 colors=np.unique(a[:,:,:3][a[:,:,3]>0],axis=0);p=Image.new('P',(1,1));p.putpalette(np.vstack([colors,np.tile(colors[0],(256-len(colors),1))]).astype('uint8').tobytes());return p,colors

def scene(files,m,t=64,light=True):
 out=Image.new('RGBA',SIZE,(4,44,12,255))
 for name in m['static_layers']:out.alpha_composite(image(files[name]))
 if light:
  effect=Image.new('RGBA',SIZE)
  for k in ['rayons','particules']:
   a=m['animations'][k];effect.alpha_composite(image(files[a['frames'][(t//a['frame_ticks'])%len(a['frames'])]]))
  b=np.array(out).astype('uint16');a=np.array(effect).astype('uint16');b[:,:,:3]=np.minimum((b[:,:,:3]>>3)+(a[:,:,:3]>>3)*(a[:,:,3:4]>0),31)*255//31;out=Image.fromarray(b.astype('uint8'))
 return out

def pack(name,files):
 with zipfile.ZipFile(O/name,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for path,data in sorted(files.items()):
   info=zipfile.ZipInfo(path,(2026,9,21,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data,compresslevel=9)
 with zipfile.ZipFile(O/name) as z:assert z.testzip() is None

def forest():
 files={};m={'id':'LF1','size':list(SIZE),'grid':8,'canonical_place':'H07P03 — seconde clairière de la même forêt que LE1','semantic_groups':6,'static_layers':[],'provenance':[],'rock_moves':[],'status':'proposition — pas de validation moteur ou artistique','entry':'sud, retour vers la lisière','north':'limite de racines, pas de sortie prévue','animations':{}}
 with previous() as z:
  old=json.loads(z.read('manifest.json'))
  for i,path in enumerate(old['static_layers']):
   out=path.replace('LE1_','LF1_');b=z.read(path);method='réemploi RGBA et fichier identiques à entrée approuvée'
   if i==2:
    src=image(b);im=Image.new('RGBA',SIZE)
    for before,size,after in [((128,192),(40,32),(96,152)),((312,192),(40,32),(344,152)),((64,224),(32,64),(56,224)),((384,224),(32,64),(392,224))]:
     x,y=before;w,h=size;part=src.crop((x,y,x+w,y+h));im.alpha_composite(part,after);m['rock_moves'].append({'before':list(before),'size':list(size),'after':list(after)})
    b=png(im);method='quatre groupes générés complets de LE1 déplacés sans nouvelle mise à échelle'
   if i==3:
    im=key(image(raw('finale_arbres_ouverts')).resize(SIZE,Image.Resampling.NEAREST));a=np.array(im);pal,_=palette();rgb=np.array(im.convert('RGB').quantize(palette=pal,dither=Image.Dither.NONE).convert('RGBA'));rgb[:,:,3]=a[:,:,3];rgb[rgb[:,:,3]==0]=0;b=png(Image.fromarray(rgb));method='nouvelle génération de toute la bordure arbres/racines; nearest480×336 et palette H07P03; non natif'
   files[out]=b;m['static_layers'].append(out);m['provenance'].append({'file':out,'method':method,'entry_file':path,'entry_sha256':sha(z.read(path)),'sha256':sha(b)})
  for k in ['rayons','particules']:
   rec=dict(old['animations'][k]);rec['frames']=[p.replace('LE1_','LF1_') for p in rec['frames']]
   for src,dst in zip(old['animations'][k]['frames'],rec['frames']):files[dst]=z.read(src)
   m['animations'][k]=rec
  m['animations'].update(combined_forest_period_ticks=12544,preview_hz=60,source='H07P04W réemployé; H07P03 ne possède pas cette météo native',blend='add RGB555 16/16, pas alpha50%')
  m['preview']={'ticks':list(range(0,256,8)),'duration_ms':4267,'loop':1,'note':'extrait à lecture unique, pas boucle intégrale209s'}
  entry=image((R/'renders/lisiere_pmd_v1/LE1_lisiere.png').read_bytes())
 main=scene(files,m);(O/'LF1_finale.png').write_bytes(png(main));files['apercus/LF1_finale.png']=png(main);files['apercus/LF1_sans_lumiere.png']=png(scene(files,m,light=False))
 ticks=m['preview']['ticks'];frames=[scene(files,m,t).convert('RGB') for t in ticks];frames[0].save(O/'LF1_finale_animee.webp',save_all=True,append_images=frames[1:],duration=[round((t+8)*1000/60)-round(t*1000/60) for t in ticks],loop=1,quality=65,method=6,minimize_size=True)
 board=Image.new('RGB',(960,1128),'#14291d');d=ImageDraw.Draw(board)
 panels=[(Path(p).stem,image(files[p])) for p in m['static_layers']]
 panels.append(('LF1_06_lumiere_native_additive',Image.alpha_composite(image(files[m['animations']['rayons']['frames'][8]]),image(files[m['animations']['particules']['frames'][9]]))))
 for i,(name,im) in enumerate(panels):
  x=i%2*480;y=i//2*376;d.text((x+12,y+10),name,fill='#dceabc');bg=Image.new('RGBA',SIZE,'#244030');bg.alpha_composite(im);board.paste(bg.convert('RGB'),(x,y+32))
 files['apercus/LF1_six_calques.png']=png(board);(O/'LF1_six_calques.png').write_bytes(png(board))
 duo=Image.new('RGB',(960,368),'#14291d');d=ImageDraw.Draw(duo);d.text((12,10),'ENTREE APPROUVEE / LE1',fill='#dceabc');d.text((492,10),'FINALE / LF1 - nouvelle proposition',fill='#dceabc');duo.paste(entry.convert('RGB'),(0,32));duo.paste(main.convert('RGB'),(480,32));(O/'LF1_duo.png').write_bytes(png(duo))
 files['manifest.json']=text(m);files['README.md']=(S/'README.md').read_bytes();files['assemble.py']=(R/'source/lisiere_pmd_v1/assemble.py').read_bytes().replace(b'LE1_',b'LF1_');pack('LF1_finale_calques.zip',files)
 return m

def furniture():
 plan={r['id']:r for r in json.loads((R/'source/cafe_spinda_revisite_v8/plan.json').read_text())['items']};files={};items=[];sprites={};refs={}
 with zipfile.ZipFile(R/'renders/cafe_spinda_revisite_v7/SpindaV7_complet.zip') as z:
  for ident in IDS:
   rec=plan[ident];im=key(image(raw(ident+'_complet')));box=im.getbbox();crop=im.crop(box);w,h=rec['target_size'];vw,vh=rec['visible_size'];scale=min(vw/crop.width,vh/crop.height);size=(round(crop.width*scale),round(crop.height*scale));obj=crop.resize(size,Image.Resampling.NEAREST);sp=Image.new('RGBA',(w,h));sp.alpha_composite(obj,((w-size[0])//2,(h-size[1])//2));sprites[ident]=sp
   outputs={}
   for mode in ['jour','nuit']:
    a=np.array(sp)
    if mode=='nuit':a[:,:,:3]=np.rint(a[:,:,:3]*np.array([.42,.35,.40])).astype('uint8')
    a[a[:,:,3]==0]=0;name=f'objets/FC1_{ident}_{mode}.png';files[name]=png(Image.fromarray(a));outputs[mode]=name
   refpath=rec['file'];refname=f'references/FC1_natif_{ident}.png';files[refname]=z.read(refpath);refs[ident]=image(files[refname]);raw_size=im.size
   items.append({'id':ident,'title':rec['title'],'files':outputs,'canvas':[w,h],'visible_size':list(size),'native_target_visible':[vw,vh],'native_reference':refname,'native_reference_sha256':sha(files[refname]),'native_source_file':refpath,'generated':True,'raw_id':ident+'_complet','raw_size':list(raw_size),'raw_crop':list(box),'raw_edges_touched':[edge for edge,hit in zip(['left','top','right','bottom'],[box[0]==0,box[1]==0,box[2]==raw_size[0],box[3]==raw_size[1]]) if hit],'normalization':'magenta key; aspect-preserving nearest; only generated pixels; alpha-centred import canvas','status':'generated_at_scale_ready_for_review'})
 atlas_rows=[];x=8
 for rec in items:
  w,h=rec['canvas'];atlas_rows.append({'id':rec['id'],'rect':[x,8,w,h]});x+=w+8
 sheets={}
 for mode in ['jour','nuit']:
  im=Image.new('RGBA',(x,64))
  for rec,pos in zip(items,atlas_rows):im.alpha_composite(image(files[rec['files'][mode]]),tuple(pos['rect'][:2]))
  name=f'objets/FC1_tilesheet_{mode}.png';files[name]=png(im);sheets[mode]=name
 board=Image.new('RGB',(800,384),'#302725');d=ImageDraw.Draw(board);d.text((12,10),'CAFE / QUATRE CREATIONS A TAILLE D\'IMPORT - lecture agrandie en bas',fill='#f0d8a0')
 for i,rec in enumerate(items):
  x=i*200;ident=rec['id'];sp=sprites[ident];ref=refs[ident];d.text((x+8,35),ident,fill='#f0d8a0');d.text((x+8,53),f"{sp.width}x{sp.height} px / visible {rec['visible_size'][0]}x{rec['visible_size'][1]}",fill='#d6cbb8');d.text((x+14,77),'natif 1x   creation 1x',fill='#b9c7a8');board.paste(ref,(x+22,98),ref);board.paste(sp,(x+122,98),sp);big=sp.resize((sp.width*4,sp.height*4),Image.Resampling.NEAREST);board.paste(big,(x+(200-big.width)//2,158),big);d.text((x+12,365),'4x : apercu uniquement',fill='#b9c7a8')
 files['apercus/FC1_mobilier.png']=png(board);(O/'FC1_mobilier.png').write_bytes(png(board))
 basepath='renders/spinda_decor_v1/apercus/SpindaDecor_cafe_demonstration.png';base=(R/basepath).read_bytes();demo=image(base);overlay=Image.new('RGBA',demo.size);positions=[(120,200),(432,256),(160,280),(432,184)]
 for ident,xy in zip(IDS,positions):overlay.alpha_composite(sprites[ident],xy)
 demo.alpha_composite(overlay);files['apercus/FC1_cafe_echelle1x.png']=png(demo);files['demonstration/FC1_objets_seuls.png']=png(overlay);(O/'FC1_cafe_echelle1x.png').write_bytes(png(demo))
 m={'id':'FC1','grid':8,'status':'4 propositions generees / controle de taille; pas une approbation utilisateur','items':items,'atlas':{'size':[x,64],'files':sheets,'objects':atlas_rows},'progress':{'planned':36,'previous_v8':9,'additional_proposals':4,'total_proposals':13,'remaining':23,'windows':'toujours a reprendre; aucune fenetre nouvelle ici'},'generation_limit':'outil sans parametre de taille de sortie exacte; gabarits dans prompts puis normalisation des creations uniquement','demo':{'base':basepath,'base_sha256':sha(base),'size':list(demo.size),'positions':{k:list(p) for k,p in zip(IDS,positions)},'note':'apercu1x uniquement; aucune salle ou graphe d acces modifie'},'native_policy':'references1x byte-identiques; jamais recolorees ou redimensionnees en import'}
 # x was reused for display columns: atlas width must come from its actual PNG.
 m['atlas']['size']=list(image(files[sheets['jour']]).size)
 files['manifest.json']=text(m);files['README.md']=(S/'README.md').read_bytes();pack('FC1_mobilier_taille_import.zip',files)
 return m

def main():
 O.mkdir(parents=True,exist_ok=True);forest();furniture();print('Built isolated forest/furniture packs and PNG/WebP previews in',O)
if __name__=='__main__':main()
