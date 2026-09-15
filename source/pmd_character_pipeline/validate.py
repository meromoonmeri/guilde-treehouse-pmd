"""Strict local preflight, not SpriteBot approval nor artistic/runtime validation.
Usage: validate.py portrait sheet.png [--level minimum|full] [--asymmetric]
       validate.py sprite MULTISHEET_DIR [--level minimum|dungeon|full]
"""
from pathlib import Path
import argparse,json,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
C=json.loads(Path(__file__).with_name('contract.json').read_text())
def pixels(p):
 with Image.open(p) as im:
  if im.format!='PNG':raise ValueError(f'{p.name}: expected PNG')
  return np.array(im.convert('RGBA'))
def palette(a):return set(map(tuple,a[:,:,:3][a[:,:,3]>0].tolist()))
def portrait(path,level='minimum',asymmetric=False):
 errors=[];a=pixels(path);h,w=a.shape[:2];present={};counts={}
 if w%40 or h%40 or not(0<w<=200 and 0<h<=320):return ['Dimensions must be multiples of 40, at most 200x320'],{},[]
 for y in range(h//40):
  for x in range(w//40):
   i=y*5+x;name=C['portrait']['emotions'][i%20]+('^' if i>=20 else '');tile=a[y*40:(y+1)*40,x*40:(x+1)*40];alpha=tile[:,:,3]
   if np.all(alpha==0):continue
   present[name]=True
   if not np.all(alpha==255):errors.append(f'{name}: occupied cell must be fully opaque (no holes or partial alpha)')
   count=len(palette(tile));counts[name]=count
   if count>15:errors.append(f'{name}: {count} visible colors, maximum 15 including background')
 required=C['portrait']['required_full'] if level=='full' else ['Normal']
 for name in required:
  if name not in present:errors.append(f'Missing required emotion: {name}')
 flipped=any(n.endswith('^') for n in present)
 for name in present:
  if name.endswith('^') and name[:-1] not in present:errors.append(f'{name}: missing original')
  if not name.endswith('^') and (asymmetric or flipped) and name+'^' not in present:errors.append(f'{name}: missing reverse view')
 return errors,dict(size=[w,h],emotions=counts),['Expression, composition, background and asymmetrical anatomy require visual review.']
def sprite(path,level='minimum'):
 errors=[];warnings=[];stats={};palette_all=set();root=ET.parse(path/'AnimData.xml').getroot();shadow=int(root.findtext('ShadowSize','-1'))
 if shadow not in [0,1,2]:errors.append('ShadowSize must be 0, 1 or 2')
 nodes=root.findall('./Anims/Anim');names={};indices={};expected={'AnimData.xml'}
 for n in nodes:
  name=n.findtext('Name','');alias=n.findtext('CopyOf');idx=int(n.findtext('Index','-1'))
  if name not in C['sprite']['actions']:errors.append(f'Unknown action: {name}')
  if name.lower() in [x.lower() for x in names]:errors.append(f'Duplicate action: {name}')
  names[name]=n
  if idx>=0:
   if idx in indices:errors.append(f'Duplicate XML index {idx}')
   indices[idx]=name
  if not alias and idx<0:errors.append(f'{name}: concrete animation needs a nonnegative Index')
  for key,value in C['sprite']['fixed_xml_indices'].items():
   if name==value and idx!=int(key):errors.append(f'{name}: expected XML Index {key}, not {idx}')
  if alias:continue
  fw=int(n.findtext('FrameWidth','0'));fh=int(n.findtext('FrameHeight','0'));dur=[int(d.text or '0') for d in n.findall('./Durations/Duration')]
  if fw<=0 or fh<=0 or not dur or any(d<=0 for d in dur):errors.append(f'{name}: positive frame dimensions and positive durations required');continue
  if fw%8 or fh%8:warnings.append(f'{name}: frame not a multiple of 8; allowed by repository but inspect alignment')
  for tag in ['RushFrame','HitFrame','ReturnFrame']:
   if n.find(tag) is not None and not(-1<=int(n.findtext(tag))<len(dur)):errors.append(f'{name}: invalid {tag}')
  sheets=[]
  for kind in ['Anim','Offsets','Shadow']:
   file=f'{name}-{kind}.png';expected.add(file)
   if not (path/file).is_file():errors.append(f'Missing {file}');sheets.append(None);continue
   a=pixels(path/file);sheets.append(a)
   if not np.isin(a[:,:,3],[0,255]).all():errors.append(f'{file}: alpha must be binary')
   if kind!='Anim' and not np.isin(a[:,:,:3][a[:,:,3]>0],[0,255]).all():errors.append(f'{file}: technical marker channels must be 0 or 255')
  if any(a is None for a in sheets):continue
  a,offset,sdw=sheets
  if any(im.shape!=a.shape for im in sheets):errors.append(f'{name}: Anim/Offsets/Shadow dimensions differ');continue
  h,w=a.shape[:2];rows=h//fh
  if w!=fw*len(dur) or h%fh or rows not in [1,8]:errors.append(f'{name}: dimensions incompatible with duration count or 1/8 direction rows');continue
  palette_all|=palette(a);stats[name]=dict(frame=[fw,fh],columns=len(dur),directions=rows,ticks=sum(dur),colors=len(palette(a)))
  if rows==1 and name in ['Idle','Walk','Attack','Hurt']:warnings.append(f'{name}: single-direction sheet; check intended gameplay coverage')
  for y in range(rows):
   for x in range(len(dur)):
    cell=a[y*fh:(y+1)*fh,x*fw:(x+1)*fw];of=offset[y*fh:(y+1)*fh,x*fw:(x+1)*fw];sh=sdw[y*fh:(y+1)*fh,x*fw:(x+1)*fw];solid=of[:,:,3]>0
    channels=[int(((of[:,:,i]==255)&solid).sum()) for i in range(3)];heads=int(((of[:,:,:3]==0).all(axis=2)&solid).sum());white=int(((sh[:,:,:3]==255).all(axis=2)&(sh[:,:,3]>0)).sum())
    if any(c>1 for c in channels) or heads>1:errors.append(f'{name} [{y},{x}]: duplicate body-part marker')
    if np.any(cell[:,:,3]>0) or channels[1] or white:
     if channels[1]!=1:errors.append(f'{name} [{y},{x}]: one green body-center marker required')
     if white!=1:errors.append(f'{name} [{y},{x}]: one white shadow-center marker required')
 for name,node in names.items():
  seen={name};alias=node.findtext('CopyOf')
  while alias:
   if alias not in names:errors.append(f'{name}: CopyOf target {alias} absent');break
   if alias in seen:errors.append(f'{name}: CopyOf cycle');break
   seen.add(alias);alias=names[alias].findtext('CopyOf')
 for name in C['sprite']['completion_levels'][level]:
  if name not in names:errors.append(f'Missing {level} action: {name}')
 for entry in path.iterdir():
  if entry.name not in expected:errors.append(f'Unexpected export entry: {entry.name}; documentation and credits belong outside this folder')
 if len(palette_all)>15:errors.append(f'Global sprite palette has {len(palette_all)} visible colors; maximum 15')
 warnings.append('Body-part anatomy, duplicate-frame offset equivalence, protected-asset locks, motion quality and PMDO import still require authoritative/manual checks.')
 return errors,dict(actions=stats,global_visible_colors=len(palette_all)),warnings

def run(kind,path,level='minimum',asymmetric=False):
 try:
  if kind=='portrait' and level=='dungeon':raise ValueError('Portrait levels are minimum or full')
  e,s,w=portrait(Path(path),level,asymmetric) if kind=='portrait' else sprite(Path(path),level)
 except (ValueError,OSError,ET.ParseError,IndexError,TypeError) as ex:e,s,w=[str(ex)],{},[]
 return dict(technical_precheck='FAIL' if e else 'PASS',errors=e,warnings=w,measurements=s,artistic_review='NOT_EVALUATED',runtime_PMDO='NOT_TESTED',SpriteCollab_acceptance='NOT_EVALUATED')
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('kind',choices=['portrait','sprite']);ap.add_argument('path',type=Path);ap.add_argument('--level',choices=['minimum','dungeon','full'],default='minimum');ap.add_argument('--asymmetric',action='store_true');ap.add_argument('--report',type=Path);args=ap.parse_args();result=run(args.kind,args.path,args.level,args.asymmetric);text=json.dumps(result,indent=2,ensure_ascii=False);print(text)
 if args.report:args.report.write_text(text)
 raise SystemExit(result['technical_precheck']!='PASS')
