"""Species-specific Eat study: generated arm choreography cleaned on native Gardevoir.
Front-only candidate; does not certify missing directions, art acceptance, or PMDO runtime.
"""
from pathlib import Path
import sys,json,shutil,copy,xml.etree.ElementTree as ET,base64
import numpy as np
from scipy.ndimage import binary_dilation
from PIL import Image,ImageDraw,ImageOps
ROOT=Path(__file__).resolve().parents[2];SRC=Path(__file__).parent
OUT=ROOT/'exports/guild_scene_animations_v2';REF=ROOT/'source/guild_members_audit/references/0282/sprite'
sys.path.insert(0,str(ROOT))
from source.pokemon_custom.politoed_portraits_v1.build import key_magenta

def main():
 OUT.mkdir(parents=True,exist_ok=True);review=OUT/'review';review.mkdir(exist_ok=True)
 pack=OUT/'gardevoir_eat_candidate';pack.mkdir(exist_ok=True)
 base=ROOT/'exports/guild_scene_animations_v1/gardevoir_candidate'
 for p in base.iterdir():
  if p.suffix in ['.png','.xml']:shutil.copyfile(p,pack/p.name)
 normal=np.array(Image.open(REF/'Idle-Anim.png').convert('RGBA').crop((0,0,32,40)))
 palette=np.unique(normal[normal[:,:,3]>0,:3],axis=0).astype(np.int32)
 palette=np.vstack([palette,[[232,135,40],[255,192,79]]])
 raw=Image.open(SRC/'generation/gardevoir_eat_front.png');assert raw.size==(1264,848)
 # Generator returned 4x2, not requested 3x2. Explicitly review/crop the ACTUAL layout.
 guides=[]
 for i in range(8):
  im=raw.crop((i%4*316,i//4*424,i%4*316+316,i//4*424+424))
  if i==0:im=ImageOps.mirror(im) # Correct the generated wrong-hand switch, not a new direction.
  keyed,_=key_magenta(im);scaled=keyed.resize((21,28),Image.Resampling.NEAREST)
  canvas=Image.new('RGBA',(32,40));canvas.alpha_composite(scaled,(5,0));a=np.array(canvas)
  rgb=a[:,:,:3].astype(np.int32);a[:,:,:3]=palette[np.argmin(((rgb[:,:,None,:]-palette[None,None,:,:])**2).sum(axis=3),axis=2)];a[a[:,:,3]==0]=0;guides.append(a)
 # Remove native active-arm greens and adjacent black outline only, never the white robe.
 rgb=normal[:,:,:3].astype(int);green=(rgb[:,:,1]>rgb[:,:,0]+20)&(rgb[:,:,1]>rgb[:,:,2]+20)&(normal[:,:,3]>0)
 region=np.zeros((40,32),bool);region[14:22,:14]=True
 black=np.all(rgb==0,axis=2)&(normal[:,:,3]>0)
 erase=(green| (binary_dilation(green)&black))&region
 body=normal.copy();body[erase]=0
 sequence=[(0,0),(1,2),(1,0),(3,0),(4,0),(5,1),(6,0),(7,0)]
 labels=['Petite baie, main basse','Lever doucement','Porter a la bouche','Petite bouchee','Savourer, yeux fermes','Abaisser la main','Relacher le bras','Repos']
 durations=[16,8,8,8,12,8,8,20];frames=[];hands=[]
 for stage,(idx,dy) in enumerate(sequence):
  a=guides[idx];rgb=a[:,:,:3].astype(int)
  green=(rgb[:,:,1]>rgb[:,:,0]+20)&(rgb[:,:,1]>rgb[:,:,2]+20)&(a[:,:,3]>0)
  food=(rgb[:,:,0]>210)&(rgb[:,:,1]>100)&(rgb[:,:,1]<210)&(rgb[:,:,2]<90)&(a[:,:,3]>0)
  region=np.zeros((40,32),bool);region[14:23,5:15]=True
  mask=(green&region)|food
  mask|=binary_dilation(mask)&np.all(rgb==0,axis=2)&(a[:,:,3]>0)
  arm=np.zeros_like(a);arm[mask]=a[mask]
  if dy:
   shifted=np.zeros_like(arm);shifted[dy:]=arm[:-dy];arm=shifted
  if stage>=3:
   food=(arm[:,:,0]>210)&(arm[:,:,1]>100)&(arm[:,:,1]<210)&(arm[:,:,2]<90);arm[food]=0
  f=body.copy()
  if stage in [4,5]:
   # Small native eyelid edits, no generated humanized face or enlarged eyes.
   for x,y in [(12,10),(18,10)]:f[y,x]=(127,143,151,255)
   for x,y in [(13,11),(17,11)]:f[y,x]=(0,0,0,255)
  visible=arm[:,:,3]>0;f[visible]=arm[visible]
  if stage==7:f=normal.copy()
  frames.append(Image.fromarray(f))
  hands.append([(12,19),(13,16),(14,14),(14,14),(13,15),(13,16),(10,19),(8,18)][stage])
 for kind in ['Anim','Offsets','Shadow']:
  sheet=Image.new('RGBA',(32*8,40))
  for j,f in enumerate(frames):
   if kind=='Anim':im=f
   else:
    im=Image.open(REF/f'Idle-{kind}.png').convert('RGBA').crop((0,0,32,40))
    if kind=='Offsets':
     a=np.array(im);red=np.all(a==[255,0,0,255],axis=2);a[red]=0
     x,y=hands[j];assert a[y,x,3]==0,(j,'marker collision');a[y,x]=[255,0,0,255];im=Image.fromarray(a)
   sheet.paste(im,(j*32,0))
  sheet.save(pack/f'Eat-{kind}.png')
 root=ET.parse(base/'AnimData.xml').getroot();node=ET.SubElement(root.find('Anims'),'Anim')
 for k,v in [('Name','Eat'),('Index',21),('FrameWidth',32),('FrameHeight',40)]:ET.SubElement(node,k).text=str(v)
 ds=ET.SubElement(node,'Durations')
 for t in durations:ET.SubElement(ds,'Duration').text=str(t)
 ET.indent(root);ET.ElementTree(root).write(pack/'AnimData.xml',encoding='utf-8',xml_declaration=True)
 board=Image.new('RGB',(640,454),(35,47,60));d=ImageDraw.Draw(board);gif=[]
 for j,f in enumerate(frames):
  tile=Image.new('RGBA',(32,40),(35,47,60,255));tile.alpha_composite(f);tile=tile.convert('RGB').resize((160,200),Image.Resampling.NEAREST)
  x=j%4*160;y=j//4*227;board.paste(tile,(x,y+22));d.text((x+3,y+4),f'{j+1}. '+labels[j],fill='white');gif.append(tile)
 board.save(review/'Gardevoir_Eat_frames.png')
 gif[0].save(review/'Gardevoir_Eat_front.gif',save_all=True,append_images=gif[1:],duration=[round(t*1000/60/10)*10 for t in durations],loop=0,disposal=2)
 sys.path.insert(0,str(ROOT/'source/pmd_character_pipeline'))
 from validate import run
 check=run('sprite',pack,'dungeon');assert check['technical_precheck']=='PASS',check['errors']
 report={'action':'Eat','pokemon':'Gardevoir','state':'technical_pass','art_approved':False,'runtime_PMDO':'NOT TESTED','directions':1,'remaining_directions':7,'frames':8,'durations_ticks':durations,'choreography':labels,'active_hand_offsets':hands,'generated_source':'generation/gardevoir_eat_front.png','cleanup':'Actual generated layout 4x2. Wrong-hand first pose corrected; enlarged generated eyes/facial drift rejected. Generated green forearm and tiny berry isolated, intermediate arm positions adjusted; native face/body/robe and inactive hand restored; active red hand marker animated. Final pose exact native Idle. Not an untouched generated sheet.','technical_check':check,'inherited_v1':'Base plus canonical Cutscene actions and front Nod retained without rewriting their PNGs.'}
 (OUT/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 for src in (ROOT/'exports/guild_scene_animations_v1').glob('Gardevoir*credits.txt'):shutil.copyfile(src,OUT/src.name)
 def uri(p):return 'data:image/'+('gif' if p.suffix=='.gif' else 'png')+';base64,'+base64.b64encode(p.read_bytes()).decode()
 html='''<!doctype html><html lang="fr"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gardevoir · Manger avec délicatesse</title><style>body{font:16px system-ui;max-width:960px;margin:32px auto;padding:0 24px;background:#141d2b;color:#edf4fa}p{line-height:1.65;color:#bed0df}img{max-width:100%;image-rendering:pixelated}section{background:#232f3c;padding:20px;border-radius:14px;margin:20px 0}.gif{width:240px}.note{border-left:3px solid #f4c477;padding:15px}</style><h1>Gardevoir · manger avec délicatesse</h1><p>Une action manquante, pas un Special renommé : petite baie portée près de la bouche, bouchée discrète, paupières fermées puis main abaissée. Bras fin, visage et robe natifs conservés ; pas de grandes mâchoires ou de doigts humains inventés.</p><section><img class="gif" alt="Candidat Eat de face" src="'''+uri(review/'Gardevoir_Eat_front.gif')+'"></section><section><img alt="Huit étapes de la gestuelle" src="'+uri(review/'Gardevoir_Eat_frames.png')+'"></section><p class="note">Candidat de face uniquement : huit étapes, format XML/triples techniquement contrôlé. Sept autres directions, approbation artistique et test PMDO restent à faire. Ce lot ne termine pas les animations des membres de guilde.</p><p>La génération comportait un changement de main et des yeux trop grands : ces parties ne sont pas acceptées. Nettoyage des bras sur l’anatomie native, robe stabilisée et repère de main animé. Crédits originaux conservés dans exports/guild_scene_animations_v2/.</p></html>'
 (ROOT/'apercu_gardevoir_eat_v2.html').write_text(html)
 print('Eat front: 8 frames; technical precheck PASS; art/runtime pending.')

if __name__=='__main__':main()
