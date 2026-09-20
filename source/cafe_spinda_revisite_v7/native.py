"""Measured native furniture, 1x. No rotation, resampling, recolouring, or AI reconstruction."""
from pathlib import Path
import sys,json,hashlib,math,csv
from PIL import Image,ImageDraw
import numpy as np
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;O=R/'renders/cafe_spinda_revisite_v7';REF=R/'source/cafe_multietage_v1/references'
sys.path.insert(0,str(R/'source/cote_v5_expeditions'));from audit_references import tiles,straight

def h(data):return hashlib.sha256(data).hexdigest()
def decode(p):
 size,bank,_=tiles(p);im=Image.new('RGBA',((max(x for x,y in bank)+1)*size,(max(y for x,y in bank)+1)*size))
 for (x,y),tile in bank.items():im.paste(straight(tile),(x*size,y*size))
 return im,size

def make():
 (O/'assets').mkdir(parents=True,exist_ok=True);(O/'audit').mkdir(exist_ok=True);sources={};banks={};items=[]
 names=['SpindaCafe1','SpindaCafe2','Metano_Town_Cafe_Objects','Metano_Town_Cafe_Objects_Over','Metano_Inn_Objects','Metano_Inn_Objects_Over','Guild_Dining_Room_Objects','Guild_Dining_Room_Objects_Over']
 for name in names:
  p=REF/(name+'.tile')
  if not p.exists():p=S/'references'/(name+'.tile')
  im,size=decode(p);banks[name]=im;raw=p.read_bytes();sources[name]={'file':str(p.relative_to(R)),'grid':size,'atlas_size':list(im.size),'sha256':h(raw),'git_blob':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest(),'rgba_sha256':h(im.tobytes()),'repo':'Minemaker0430/ExplorersOfSkyOrigins' if name.startswith('Spinda') else 'Palikadude/Halcyon','commit':(REF/('eoso_commit.txt' if name.startswith('Spinda') else 'halcyon_commit.txt')).read_text().strip()}
  # Audit the pinned upstream blobs, not just previously rendered local previews.
  tree=json.loads((R/'.cache/sky_canon'/('eoso_tree.json' if name.startswith('Spinda') else 'tree.json')).read_text()) if (R/'.cache/sky_canon'/('eoso_tree.json' if name.startswith('Spinda') else 'tree.json')).exists() else None
  if tree:assert sources[name]['git_blob']==next(x['sha'] for x in tree['tree'] if x['path']=='Content/Tile/'+name+'.tile')
 def store(id,title,im,source,box,group='halcyon',extra=None):
  bbox=im.getbbox();assert bbox
  # Import canvas is grid-aligned; visible pixels remain unscaled and unmodified.
  canvas=Image.new('RGBA',(math.ceil(im.width/8)*8,math.ceil(im.height/8)*8));canvas.paste(im,(0,0));file='assets/SpindaV7_'+id+'.png';canvas.save(O/file,optimize=True)
  rec={'id':id,'title':title,'file':file,'native':True,'size':list(canvas.size),'visible_size':[bbox[2]-bbox[0],bbox[3]-bbox[1]],'source_rect':list(box),'source':source,'group':group,'scale':1,'rotation':0,'recolour':False,'rgba_sha256':h(canvas.tobytes()),'grid_cells':[canvas.width//8,canvas.height//8],'collision':'not audited; visual bounds only'}
  if extra:rec.update(extra)
  items.append(rec);return rec
 # Counter masks define visible prefab silhouettes. Pixel values come directly from the actual native Ground composition.
 base=banks['SpindaCafe1'];scene=base.copy();scene.alpha_composite(banks['SpindaCafe2'])
 native_scene=Image.open(REF/'spinda_cafe_reference.png').convert('RGBA');assert scene.tobytes()==native_scene.tobytes()
 polyS=[(218,95),(218,92),(220,88),(228,88),(233,91),(235,95),(236,99),(240,101),(243,96),(260,96),(267,100),(272,93),(276,89),(282,88),(287,91),(289,95),(289,100),(283,105),(280,108),(284,111),(282,116),(276,120),(269,120),(263,116),(239,116),(231,120),(222,118),(216,115),(214,111),(224,105),(220,101),(217,97)]
 polyW=[(403,102),(406,98),(410,95),(413,98),(419,105),(423,109),(426,102),(430,98),(431,93),(434,89),(438,87),(443,87),(447,89),(451,94),(452,99),(458,103),(464,109),(467,103),(471,98),(475,96),(478,99),(482,102),(481,107),(475,111),(474,119),(412,121),(408,115),(405,110)]
 for ident,title,x,poly in [('comptoir_spinda','Comptoir Spinda · pixels du Ground',192,polyS),('comptoir_qulbutoke','Comptoir Qulbutoké · pixels du Ground',384,polyW)]:
  box=(x,80,x+120,176);mask=Image.new('L',scene.size);d=ImageDraw.Draw(mask);d.polygon(poly,fill=255)
  # Do not include ribbon fragments outside the canopy, but retain every native object below it.
  a=np.array(mask)>0;overlay=np.zeros((scene.height,scene.width),np.uint8);oa=np.array(banks['SpindaCafe2'])[:,:,3];overlay[:oa.shape[0],:oa.shape[1]]=oa
  a&=overlay>0;a[118:176,x:x+120]|=overlay[118:176,x:x+120]>0
  if ident=='comptoir_qulbutoke':
   rgb=np.array(scene)[:,:,:3];a[:118]&=(rgb[:118,:,2]>=rgb[:118,:,1])&(rgb[:118,:,2]>rgb[:118,:,0])
   a[108:176,x:x+120]|=overlay[108:176,x:x+120]>0
  if ident=='comptoir_qulbutoke':a[108:115,x+117:x+120]=False # isolated hanging-ribbon remnant, not furniture
  a[120:152,x+32:x+88]=True;a[152:176,x:x+120]=True
  pixels=np.array(scene.crop(box));keep=a[80:176,x:x+120];pixels[~keep]=0;im=Image.fromarray(pixels)
  reference=np.array(native_scene.crop(box));assert np.array_equal(pixels[keep],reference[keep])
  store(ident,title,im,['SpindaCafe1','SpindaCafe2'],box,'spinda',{'mask_polygon_absolute':poly,'exact_visible_rgba_vs_ground':True,'method':'Native Ground visible-furniture mask, no hidden pixels invented. Includes original shelf, front plinth and contact pixels; no NPC sprite.'})
 # Complete small props selected with enough transparent separation to retain disconnected details.
 selections=[
 ('table_spinda_tasses','Table Spinda · tasses','SpindaCafe2',(194,190,237,233),'spinda'),('table_spinda_vide','Table Spinda · vide','SpindaCafe2',(243,239,286,282),'spinda'),('plante_spinda','Plante Spinda','SpindaCafe2',(153,231,193,275),'spinda'),('petite_plante_spinda','Petite plante Spinda','SpindaCafe2',(185,275,212,300),'spinda'),
 ('ruban_spinda','Ruban nord · section native','SpindaCafe2',(240,56,304,96),'spinda'),
 ('tonneaux','Paire de tonneaux','Metano_Town_Cafe_Objects',(174,67,216,112),'halcyon'),('plante_cafe','Plante haute du café','Metano_Town_Cafe_Objects',(369,82,409,136),'halcyon'),('menu','Chevalet de menu','Metano_Town_Cafe_Objects',(45,107,80,152),'halcyon'),('tapis_vert','Tapis vert','Metano_Town_Cafe_Objects',(96,138,192,178),'halcyon'),('table_halcyon_tasses','Table Halcyon · tasses','Metano_Town_Cafe_Objects',(337,155,383,199),'halcyon'),('table_halcyon_vide','Table Halcyon · vide','Metano_Town_Cafe_Objects',(57,180,103,224),'halcyon'),('caisses','Caisses empilées','Metano_Town_Cafe_Objects',(376,216,426,272),'halcyon'),('etagere','Étagère bois','Metano_Town_Cafe_Objects',(120,48,168,96),'halcyon'),('bar_jus','Bar à jus complet · Halcyon','Metano_Town_Cafe_Objects_Over',(83,100,204,137),'halcyon'),
 ('plante_auberge','Plante de l’auberge','Metano_Inn_Objects',(124,50,164,94),'halcyon'),('tonneau_auberge','Tonneau','Metano_Inn_Objects',(280,66,304,95),'halcyon'),('tabouret','Petit tabouret','Metano_Inn_Objects',(305,72,319,88),'halcyon'),('coffre','Coffre','Metano_Inn_Objects',(99,83,120,106),'halcyon'),('lit_paille','Grand couchage de paille','Metano_Inn_Objects',(227,97,334,151),'halcyon'),('coussin_paille','Coussin de paille','Metano_Inn_Objects',(104,112,143,140),'halcyon'),('table_auberge','Table de souche','Metano_Inn_Objects',(288,234,336,278),'halcyon'),('caisse_pommes','Caisse et pommes','Metano_Inn_Objects',(200,160,244,196),'halcyon'),('bouquet','Bouquet de l’auberge','Metano_Inn_Objects_Over',(232,184,256,212),'halcyon'),
 ('banniere','Bannière de réfectoire','Guild_Dining_Room_Objects',(194,32,222,121),'halcyon'),('liane','Liane murale','Guild_Dining_Room_Objects',(65,64,94,120),'halcyon'),('fleurs_bleues','Petit vase bleu','Guild_Dining_Room_Objects',(62,157,80,176),'halcyon'),('tapis_dore','Tapis doré','Guild_Dining_Room_Objects',(119,151,296,208),'halcyon'),('banquet','Table de banquet garnie','Guild_Dining_Room_Objects_Over',(124,153,291,204),'halcyon')]
 for ident,title,bank,box,group in selections:
  im=banks[bank].crop(box);rec=store(ident,title,im,bank,box,group)
  check=Image.open(O/rec['file']).convert('RGBA').crop((0,0,im.width,im.height));assert check.tobytes()==im.tobytes()
 result={'sources':sources,'objects':items,'scope':'Spinda Café EoSO; café Metano, auberge et réfectoire Halcyon. Not all objects in Halcyon.','native_transforms':'NONE; transparent padding to multiples of 8 only','windows_comparison':{'previous_generated_visible_diameter':64,'new_generated_visible_diameter':28,'new_canvas':[32,32],'native_spinda_table':[43,43],'halcyon_window_reference_only':[52,59],'guild_window_reused':False},'counter_ground_reference_sha256':h(native_scene.tobytes())}
 (O/'audit/native_sizes.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 with (O/'audit/native_sizes.csv').open('w') as f:
  w=csv.writer(f,lineterminator="\n");w.writerow(['id','visible_w','visible_h','canvas_w','canvas_h','grid_w','grid_h','source'])
  for r in items:w.writerow([r['id'],*r['visible_size'],*r['size'],*r['grid_cells'],r['source']])
 return items,result
if __name__=='__main__':make()
