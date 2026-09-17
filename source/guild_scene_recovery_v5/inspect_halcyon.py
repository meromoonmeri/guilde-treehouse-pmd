"""Read-only extraction of the base-form Eat sequence from real Halcyon .chara files."""
from pathlib import Path
import io,struct,json,hashlib,base64,xml.etree.ElementTree as ET
from PIL import Image,ImageOps,ImageDraw
ROOT=Path(__file__).resolve().parents[2];SRC=Path(__file__).parent/'halcyon';OUT=ROOT/'exports/guild_scene_recovery_v5/halcyon_review'

def decode(path):
 data=path.read_bytes();stream=io.BytesIO(data)
 def read(fmt):
  fmt='<'+fmt;return struct.unpack(fmt,stream.read(struct.calcsize(fmt)))
 def index():
  pos,count=read('qi');return {'position':pos,'children':{read('i')[0]:index() for _ in range(count)}}
 tree=index();pos=tree['position'];assert pos>0;stream.seek(pos)
 length,=read('q');png=stream.read(length);assert png.startswith(b'\x89PNG\r\n\x1a\n')
 atlas=Image.open(io.BytesIO(png)).convert('RGBA');w,h,shadow,count=read('iiii')
 assert w>0 and h>0 and atlas.width%w==0 and atlas.height%h==0
 offsets=[read('iiiiiiii') for _ in range(count)];count,=read('i');groups={}
 for _ in range(count):
  key,internal,alias=read('iii');group={'internal_index':internal,'copy_of':alias};groups[key]=group
  if alias>=0:continue
  group['events']=read('iii');seq_count,=read('i');seq=[]
  for _ in range(seq_count):
   n,=read('i');frames=[read('iii?iiii') for _ in range(n)]
   for x,y,t,*rest in frames:assert 0<=x<atlas.width//w and 0<=y<atlas.height//h and t>0
   seq.append(frames)
  group['sequences']=seq
 positions=[]
 def walk(n):
  if n['position']>pos:positions.append(n['position'])
  for child in n['children'].values():walk(child)
 walk(tree);assert stream.tell()==min(positions,default=len(data)),(path,stream.tell(),positions)
 return atlas,(w,h),groups,tree

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 names=[n.findtext('Name') for n in ET.parse(SRC/'GFXParams.xml').findall('./Actions/Action')];eat=names.index('Eat');assert eat==48 and names[0]=='None'
 result={'halcyon_pin':'da6c2130d641507447e6386a5e47a296e8cb4c71','engine_pin':'8b7eafafa73ff0c10b9e8fd9348559ee1b5dfe8b','gfxparams_pin':'3e767571f9dd94270b848b3a73de9bec2553a2eb','scope':'Three real Halcyon guild members, base-form first Eat sequences. Not all candidates/forms, not a runtime test.','scene_separation':'Eat: init.lua lines141-152; eating emote:154-165; independent Food_* objects:168-180.','examples':[]}
 contact=Image.new('RGB',(768,570),(35,47,60));draw=ImageDraw.Draw(contact)
 for ri,(num,name) in enumerate([(286,'Chapignon'),(408,'Kranidos'),(531,'Nanmeouie')]):
  path=SRC/f'Content__Chara__{num}.chara';atlas,(w,h),groups,tree=decode(path);group=groups[eat];assert group['copy_of']==-1
  seq=group['sequences'][0];frames=[]
  for x,y,t,flip,ox,oy,sx,sy in seq:
   sprite=atlas.crop((x*w,y*h,(x+1)*w,(y+1)*h))
   if flip:sprite=ImageOps.mirror(sprite)
   canvas=Image.new('RGBA',(64,64),(35,47,60,255));canvas.alpha_composite(sprite,(32-w//2+ox,32-h//2+oy));frames.append(canvas.convert('RGB').resize((256,256),Image.Resampling.NEAREST))
  gif=OUT/f'Halcyon_{num}_Eat.gif';frames[0].save(gif,save_all=True,append_images=frames[1:],duration=[max(20,round(f[2]*1000/60/10)*10) for f in seq],loop=0,disposal=2)
  draw.text((5,ri*190+4),name+' / Eat natif Halcyon',fill='white')
  for fi,im in enumerate(frames[:4]):contact.paste(im.resize((176,176),Image.Resampling.NEAREST),(fi*192,ri*190+16))
  result['examples'].append({'species':num,'name':name,'engine_action':eat,'internal_index':group['internal_index'],'base_position':tree['position'],'tile':[w,h],'sequences':len(group['sequences']),'first_sequence':seq,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'gif':gif.name,'visual_review':'No food drawn in the inspected four-frame sequence.'})
 contact.save(OUT/'native_eat_comparison.png');(OUT/'inspection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
 # Add reference evidence after the three reconstructed actions; source assets stay outside character packs.
 gallery=ROOT/'apercu_guilde_reconstruction_v5.html';html=gallery.read_text();marker='<section id="halcyon-evidence">'
 if marker in html:html=html[:html.index(marker)]+'</html>'
 section=marker+'<h2>Vérification sur les vrais sprites Halcyon</h2><p>Eat de Chapignon, Kranidos et Nanméouïe : aucun aliment dessiné dans les séquences inspectées. Halcyon affiche indépendamment les objets Food_* et l’émote eating. Ces extraits sont des références Halcyon/Palikadude et de leurs artistes, pas nos créations.</p><div class="grid">'
 for item in result['examples']:
  data=base64.b64encode((OUT/item['gif']).read_bytes()).decode();section+='<div><h3>'+item['name']+'</h3><img alt="Eat natif Halcyon" src="data:image/gif;base64,'+data+'"></div>'
 section+='</div><p>Trois exemples réels, pas un audit exhaustif ou un test moteur. Les fichiers natifs et crédits ne sont pas remplacés par les reconstructions.</p></section>'
 gallery.write_text(html.replace('</html>',section+'</html>'))
 print('Real Halcyon Eat48 inspected:',[x['name'] for x in result['examples']])
if __name__=='__main__':main()
