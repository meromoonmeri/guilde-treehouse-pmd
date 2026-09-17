"""Scene pack: exact canonical Pose + front-only generated/cleaned Nod candidate.
No invented eight-direction coverage or PMDO runtime approval.
"""
from pathlib import Path
import sys,shutil,json,hashlib,copy,base64
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2];SRC=Path(__file__).parent
REF=ROOT/'source/guild_members_audit/references';OUT=ROOT/'exports/guild_scene_animations_v1'
sys.path.insert(0,str(ROOT))
from source.pokemon_custom.politoed_portraits_v1.build import key_magenta

def preview(folder,name,node,dest):
 w=int(node.findtext('FrameWidth'));h=int(node.findtext('FrameHeight'))
 sheet=Image.open(folder/f'{name}-Anim.png').convert('RGBA');frames=[]
 durations=[int(v.text) for v in node.findall('./Durations/Duration')]
 for i in range(len(durations)):
  canvas=Image.new('RGBA',(w+16,h+16),(35,47,60,255));canvas.alpha_composite(sheet.crop((i*w,0,(i+1)*w,h)),(8,8));frames.append(canvas.convert('RGB').resize(((w+16)*5,(h+16)*5),Image.Resampling.NEAREST))
 frames[0].save(dest,save_all=True,append_images=frames[1:],duration=[max(20,round(v*1000/60/10)*10) for v in durations],loop=0,disposal=2)

def main():
 pack=OUT/'gardevoir_candidate';review=OUT/'review';pack.mkdir(parents=True,exist_ok=True);review.mkdir(parents=True,exist_ok=True)
 base=REF/'0282/sprite';cut=REF/'0282/0002/sprite';native_hashes={}
 for p in base.glob('*.png'):
  shutil.copyfile(p,pack/p.name);native_hashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 shutil.copyfile(base/'credits.txt',OUT/'Gardevoir_base_credits.txt');shutil.copyfile(cut/'credits.txt',OUT/'Gardevoir_Cutscene_credits.txt')
 if (pack/'credits.txt').exists():(pack/'credits.txt').unlink()
 root=ET.parse(base/'AnimData.xml').getroot();anims=root.find('Anims')
 cut_nodes={n.findtext('Name'):n for n in ET.parse(cut/'AnimData.xml').getroot().findall('./Anims/Anim')}
 canonical_additions=['StandingUp','Special0','Special1','Special2','Special3','Pose','Jump']
 for name in canonical_additions:
  original=cut_nodes[name];target=original.findtext('CopyOf') or name;node=copy.deepcopy(cut_nodes[target])
  node.find('Name').text=name;node.find('Index').text=original.findtext('Index')
  # Special1 aliases CUTSCENE Appeal, which differs from BASE Appeal. Materialize it,
  # otherwise an apparently valid CopyOf would silently select the wrong choreography.
  anims.append(node)
  for kind in ['Anim','Offsets','Shadow']:
   p=cut/f'{target}-{kind}.png';dest=pack/f'{name}-{kind}.png';shutil.copyfile(p,dest);native_hashes[dest.name]=hashlib.sha256(p.read_bytes()).hexdigest()
  preview(pack,name,node,review/f'Gardevoir_{name}_native.gif')
 pose=next(n for n in anims if n.findtext('Name')=='Pose')
 native=Image.open(base/'Idle-Anim.png').convert('RGBA').crop((0,0,32,40));a=np.array(native)
 palette=np.unique(a[a[:,:,3]>0,:3],axis=0).astype(np.int32)
 raw=Image.open(SRC/'generation/gardevoir_nod_front.png');poses=[]
 # Only front-row heads are usable. Other seven generated view sequences are rejected.
 for i in range(3):
  keyed,_=key_magenta(raw.crop((i*232,0,(i+1)*232,288)))
  scaled=keyed.resize((21,26),Image.Resampling.NEAREST);aligned=Image.new('RGBA',(32,40));aligned.alpha_composite(scaled,(5,1))
  b=np.array(aligned);rgb=b[:,:,:3].astype(np.int32)
  b[:,:,:3]=palette[np.argmin(((rgb[:,:,None,:]-palette[None,None,:,:])**2).sum(axis=3),axis=2)];b[b[:,:,3]==0]=0
  final=a.copy();final[:14]=b[:14];poses.append(Image.fromarray(final))
 sequence=[0,1,2,1,0];durations=[10,5,9,5,12]
 for kind in ['Anim','Offsets','Shadow']:
  sheet=Image.new('RGBA',(32*len(sequence),40))
  for j,k in enumerate(sequence):
   im=poses[k] if kind=='Anim' else Image.open(base/f'Idle-{kind}.png').convert('RGBA').crop((0,0,32,40))
   sheet.paste(im,(j*32,0))
  sheet.save(pack/f'Nod-{kind}.png')
 nod=ET.SubElement(anims,'Anim')
 for k,v in [('Name','Nod'),('Index',20),('FrameWidth',32),('FrameHeight',40)]:ET.SubElement(nod,k).text=str(v)
 ds=ET.SubElement(nod,'Durations')
 for v in durations:ET.SubElement(ds,'Duration').text=str(v)
 ET.indent(root);ET.ElementTree(root).write(pack/'AnimData.xml',encoding='utf-8',xml_declaration=True)
 preview(pack,'Pose',pose,review/'Gardevoir_Pose_native.gif');preview(pack,'Nod',nod,review/'Gardevoir_Nod_front_candidate.gif')
 contact=Image.new('RGB',(5*160,220),(35,47,60));d=ImageDraw.Draw(contact)
 for j,k in enumerate(sequence):
  tile=Image.new('RGBA',(32,40),(35,47,60,255));tile.alpha_composite(poses[k]);contact.paste(tile.convert('RGB').resize((160,200),Image.Resampling.NEAREST),(j*160,20));d.text((j*160+5,4),f'{j+1}: {durations[j]} ticks',fill='white')
 contact.save(review/'Nod_frames.png')
 # Review authentic Weavile cutscene specials without relabeling them as missing generic actions.
 weavile=REF/'0461/0001/sprite';weabase=REF/'0461/sprite';weapack=OUT/'weavile_canonical';weapack.mkdir(parents=True,exist_ok=True)
 wearoot=ET.parse(weabase/'AnimData.xml').getroot();weahashes={}
 for p in weabase.glob('*.png'):
  shutil.copyfile(p,weapack/p.name);weahashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
 for src,label in [(weabase,'base'),(weavile,'Cutscene')]:shutil.copyfile(src/'credits.txt',OUT/f'Weavile_{label}_credits.txt')
 for name in ['Special0','Special1']:
  node=next(n for n in ET.parse(weavile/'AnimData.xml').getroot().findall('./Anims/Anim') if n.findtext('Name')==name)
  wearoot.find('Anims').append(copy.deepcopy(node))
  for kind in ['Anim','Offsets','Shadow']:
   p=weavile/f'{name}-{kind}.png';shutil.copyfile(p,weapack/p.name);weahashes[p.name]=hashlib.sha256(p.read_bytes()).hexdigest()
  preview(weavile,name,node,review/f'Weavile_{name}_native.gif')
 ET.indent(wearoot);ET.ElementTree(wearoot).write(weapack/'AnimData.xml',encoding='utf-8',xml_declaration=True)
 report={'source_pin':'3609a86be2a4c8ad7cf255bd2255f044daafe24f','native_png_sha256':native_hashes,'base_actions_preserved':[n.findtext('Name') for n in ET.parse(base/'AnimData.xml').getroot().findall('./Anims/Anim')],'additions':{'Pose':{'provenance':'Exact Gardevoir Cutscene 0282/0002 triple and XML action; credit file retained separately','directions':1,'durations': [4,4,6],'state':'technical_pass'},'Nod':{'provenance':'Generated front-row heads, native palette cleanup and native stationary body/markers; NOT all-generator pixels','directions':1,'remaining_directions':7,'frames':len(sequence),'unique_drawings':len(set(p.tobytes() for p in poses)),'durations':durations,'state':'generated','art_review':'Front-only candidate; not accepted as finished eight-direction animation'}},'rejected_studies':'All seven non-front generated direction sequences: direction/robe inconsistency. Never exported as eight-direction Nod.','weavile':'Special0/1 previewed as authentic cutscene gestures; not relabeled as Nod/Pose or used to close generic action gaps.','PMDO_runtime':'NOT TESTED','art_approved':False,'completed_global_backlog':False}
 for name,sha in native_hashes.items():assert hashlib.sha256((pack/name).read_bytes()).hexdigest()==sha
 assert np.array_equal(np.array(poses[0])[14:],np.array(poses[2])[14:])
 assert len(set(p.tobytes() for p in poses))>=2
 sys.path.insert(0,str(ROOT/'source/pmd_character_pipeline'))
 from validate import run
 report['gardevoir_canonical_additions']=canonical_additions
 report['Special1_alias_safety']='Cutscene Appeal materialized as Special1, not incorrectly redirected to base Appeal.'
 report['weavile_native_png_sha256']=weahashes
 report['technical_checks']={}
 for name,folder in [('gardevoir',pack),('weavile',weapack)]:
  report['technical_checks'][name]=run('sprite',folder,'dungeon')
  assert report['technical_checks'][name]['technical_precheck']=='PASS',report['technical_checks'][name]['errors']
 report['weavile']='Native base plus authentic Cutscene Special0/1, exact triples and XML actions; neither relabeled as generic Nod/Pose nor counted as closing those gaps.'
 (OUT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
 print('Native files preserved:',len(native_hashes),'Nod unique drawings:',report['additions']['Nod']['unique_drawings'])

if __name__=='__main__':main()
