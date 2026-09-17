"""Original generated structures, native-scale cleanup, explicit visible-surface layers.
Not a canonical texture reconstruction or a tested PMDO map.
"""
from pathlib import Path
import json,hashlib,base64,zipfile
import numpy as np
from scipy import ndimage as nd
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];S=Path(__file__).parent;O=R/'exports/guild_structures_v1'
REF=R/'source/amp_plains_fleurie_v1/references/Metano_Town_Objects.png'
NN=Image.Resampling.NEAREST
SPECS=[('hq','QG treehouse','hq',(0,0,1102,960),(256,256),(240,232)),('dormitory','Dortoir','annexes',(0,0,600,448),(128,128),(112,104)),('refectory','Réfectoire','annexes',(600,0,1200,448),(128,128),(112,104)),('infirmary','Infirmerie','annexes',(0,448,600,896),(128,128),(104,104)),('workshop','Atelier / réserve','annexes',(600,448,1200,896),(128,128),(112,104))]
LAYERS=['01_shadow','02_architecture','03_roof_foliage','04_smoke_study']
def part(a,m):
 b=a.copy();b[~m]=0;return Image.fromarray(b)
def uri(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
def build():
 O.mkdir(parents=True,exist_ok=True)
 # Native RGB palette, not a claim that generated grain is canonical pixel texture.
 ref=Image.open(S/'references/native_treehouse.png').convert('RGBA');a=np.array(ref);colors,counts=np.unique(a[a[:,:,3]>0,:3],axis=0,return_counts=True);palette=colors[np.argsort(counts)[-96:]].astype('int32')
 warm=np.array(Image.open(R/'source/cafe_multietage_v3/references/guild_second_floor_reference.png').convert('RGBA'));wc,wn=np.unique(warm[warm[:,:,3]>0,:3],axis=0,return_counts=True);palette=np.unique(np.concatenate([palette,wc[np.argsort(wn)[-48:]]]),axis=0).astype('int32')
 (S/'references/palette.json').write_text(json.dumps(palette.tolist()))
 result=[]
 for ident,label,file,box,canvas,target in SPECS:
  raw=Image.open(S/'generation'/f'{file}.png').convert('RGBA');assert raw.size==((1102,960) if file=='hq' else (1200,896))
  a=np.array(raw.crop(box));rgb=a[:,:,:3].astype('int32');rr,gg,bb=rgb.transpose(2,0,1);matte=(rr>gg*1.5)&(bb>gg*1.5)&(rr>75)&(bb>65);a[matte]=0
  # Separate the generated chimney puff, not a false smoke animation.
  yy,xx=np.mgrid[:a.shape[0],:a.shape[1]];smoke=(yy<64)&(xx>360)&(a[:,:,3]>0) if ident=='refectory' else np.zeros(a.shape[:2],bool)
  obj=Image.fromarray(a);bbox=obj.getbbox();obj=obj.crop(bbox);smokeim=Image.fromarray(np.uint8(smoke)*255).crop(bbox)
  factor=min(target[0]/obj.width,target[1]/obj.height);size=(round(obj.width*factor),round(obj.height*factor));obj=obj.resize(size,NN);smokeim=smokeim.resize(size,NN)
  a=np.array(obj);opaque=a[:,:,3]>0;rgb=a[:,:,:3].astype('int32');a[:,:,:3]=palette[np.argmin(((rgb[:,:,None,:]-palette[None,None,:,:])**2).sum(3),axis=2)];a[~opaque]=0;a[opaque,3]=255
  labs,n=nd.label(opaque,np.ones((3,3)));counts=np.bincount(labs.ravel());keep=counts>=3;keep[0]=False;a[~keep[labs]]=0
  base=Image.new('RGBA',canvas);pos=((canvas[0]-size[0])//2,canvas[1]-16-size[1]);base.alpha_composite(Image.fromarray(a),pos);a=np.array(base);opaque=a[:,:,3]>0
  sm=Image.new('L',canvas);sm.paste(smokeim,pos);smoke=(np.array(sm)>0)&opaque
  yy,xx=np.mgrid[:canvas[1],:canvas[0]];rgb=a[:,:,:3].astype(int)
  green=(rgb[:,:,1]>rgb[:,:,0]*1.08)&(rgb[:,:,1]>rgb[:,:,2]*1.2)&opaque
  if ident=='hq':roof=nd.binary_dilation(green,iterations=1)&opaque&(yy<pos[1]+round(size[1]*.61))
  else:
   # Roof mask hand-authored as a continuous silhouette region, including leaf outlines/brown leaves.
   m=Image.new('L',size);d=ImageDraw.Draw(m);points=[(0,0),(size[0],0),(size[0],int(size[1]*.46)),(int(size[0]*.7),int(size[1]*.60)),(int(size[0]*.35),int(size[1]*.60)),(0,int(size[1]*.46))];d.polygon(points,fill=255)
   roofcanvas=Image.new('L',canvas);roofcanvas.paste(m,pos);roof=(np.array(roofcanvas)>0)&opaque
  roof &= ~smoke;body=opaque&~roof&~smoke
  shadow=Image.new('RGBA',canvas);d=ImageDraw.Draw(shadow);cx=canvas[0]//2;baseline=canvas[1]-16
  # Narrow side lobes, not a solid shadow filling the door approach.
  for sign in [-1,1]:
   x=cx+sign*round(size[0]*.24);d.ellipse((x-size[0]//5,baseline-9,x+size[0]//5,baseline+3),fill=(32,40,24,85))
  layers=[shadow,part(a,body),part(a,roof),part(a,smoke)];folder=O/ident;folder.mkdir(exist_ok=True)
  composite=Image.new('RGBA',canvas)
  for name,im in zip(LAYERS,layers):im.save(folder/f'GuildStructuresV1_{ident}_{name}.png');composite.alpha_composite(im)
  base.save(folder/f'GuildStructuresV1_{ident}_object.png');composite.save(folder/f'GuildStructuresV1_{ident}_composite.png')
  part(np.dstack([np.full(canvas[::-1],255,dtype='uint8')]*4),roof).getchannel('A').save(folder/'roof_mask.png')
  entry={'id':ident,'label':label,'canvas_px':canvas,'anchor_px':[cx,baseline],'entry_approach_px':[cx-8,baseline-8,16,24],'entry_status':'Placement guide only, not collision or warp data','origin':'Original generated design, keyed, nearest-neighbor reduced and mapped to native reference RGBs','layers':[{ 'id':name,'file':f'{ident}/GuildStructuresV1_{ident}_{name}.png','empty':im.getbbox() is None} for name,im in zip(LAYERS,layers)],'composite':f'{ident}/GuildStructuresV1_{ident}_composite.png','object':f'{ident}/GuildStructuresV1_{ident}_object.png','source_crop':box,'native_size':size}
  result.append(entry)
 manifest={'grid_px':8,'structures':result,'art_approved':False,'runtime_PMDO':'NOT TESTED','layer_limit':'Visible-surface separation, not reconstructed interiors behind removable roofs. Do not use roof-hidden mode as a playable interior.','textures':'Generated architecture texture informed by native references; native RGB palette, NOT pixel-exact canonical texture reconstruction. Map relayout batch must use actual canonical pixels separately.','reuse_existing':['sprites/ponts_pmdo','exports/vegetation_treehouse_v1'],'source_reference':{'path':str(REF.relative_to(R)),'sha256':hashlib.sha256(REF.read_bytes()).hexdigest(),'repository':'https://github.com/Palikadude/Halcyon','credit':'Native reference belongs to its original PMD / Halcyon contributors, not authored here.'},'pending':'Additional retained proposals, interiors, integration, collisions and scene layout remain pending.'}
 (O/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 html='''<!doctype html><html lang="fr"><meta charset="utf-8"><title>Structures de la guilde</title><style>body{background:#15231f;color:#ebdfba;font:16px system-ui;max-width:1250px;margin:40px auto;padding:20px}h1{font-size:38px}p{line-height:1.6;color:#c1cdbb}.grid{display:flex;flex-wrap:wrap;gap:24px}article{background:#22372e;padding:20px;border:1px solid #425e47;border-radius:12px}canvas{display:block;image-rendering:pixelated;background:repeating-conic-gradient(#2a4035 0% 25%,#30493c 0% 50%) 0/16px 16px}label{display:block;margin:8px}small{color:#b2c9ac}a{color:#e1c97a}</style><h1>Guilde · QG & annexes</h1><p>Premier lot : QG treehouse, dortoir, réfectoire, infirmerie et atelier/réserve. Créations proposées à l’échelle native, palette issue de la référence Métano. Les textures générées ne sont pas des extractions canoniques pixel-exactes.</p><p>Calques indépendants : ombres, architecture visible, toiture/feuillage et étude de fumée fixe. Masquer le toit sert à inspecter les calques : aucun intérieur caché n’est reconstruit. Aucun import PMDO ou collision validés.</p><div class="grid" id="grid"></div><script>const data=DATA;for(const s of data){const card=document.createElement('article');card.innerHTML='<h2>'+s.label+'</h2><small>'+s.canvas_px.join(' × ')+' px · grille 8 px</small>';const c=document.createElement('canvas');c.width=s.canvas_px[0];c.height=s.canvas_px[1];c.style.width=c.width*2+'px';c.style.height=c.height*2+'px';card.append(c);const ctx=c.getContext('2d'),imgs=[],checks=[];function draw(){ctx.clearRect(0,0,c.width,c.height);imgs.forEach((im,i)=>{if(checks[i].checked&&im.complete)ctx.drawImage(im,0,0)})}s.layers.forEach((l,i)=>{const label=document.createElement('label'),ch=document.createElement('input');ch.type='checkbox';ch.checked=true;ch.onchange=draw;checks.push(ch);label.append(ch,document.createTextNode(l.id+(l.empty?' (vide)':'')));card.append(label);const im=new Image();imgs.push(im);im.onload=draw;im.src=l.uri});document.getElementById('grid').append(card)}</script><h2>Suite : les zones importées</h2><p>L’inventaire des références et des BG est livré dans <b>apercu_zones_bg_audit_v1.html</b>. Les prochains relayouts utiliseront les vrais pixels des textures canoniques, sans repeindre les matériaux.</p></html>'''
 data=[{**s,'layers':[{**l,'uri':uri(O/l['file'])} for l in s['layers']]} for s in result]
 (R/'apercu_structures_guilde_v1.html').write_text(html.replace('const data=DATA;', 'const data='+json.dumps(data,ensure_ascii=False)+';'))
 board=Image.new('RGB',(1024,650),'#283d30');d=ImageDraw.Draw(board)
 for i,entry in enumerate(result):
  im=Image.open(O/entry['composite']).convert('RGBA');im=im.resize((im.width*2,im.height*2),NN);xy=(0,0) if i==0 else (512+(i-1)%2*256,(i-1)//2*300);board.paste(im,xy,im);d.text((xy[0]+10,xy[1]+im.height),entry['label'])
 board.save(O/'review.png')
 with zipfile.ZipFile(R/'exports/guild_structures_v1_pack.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(O.rglob('*')):
   if p.is_file():z.write(p,p.relative_to(O))
 print('5 structures; 20 independent layer PNGs (empty optional layers explicit).')
if __name__=='__main__':build()
