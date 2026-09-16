"""Per-frame crown registration using anatomical markers, not whole-sprite bounding boxes."""
from pathlib import Path
import json,xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3]
DIRECTIONS=['D','DR','R','UR','U','UL','L','DL']

def load_profiles():
 doc=json.loads(Path(__file__).with_name('profiles.json').read_text());raw=doc['profiles'];result={}
 for name,cfg in raw.items():
  merged={**raw.get(cfg.get('inherits'),{}),**cfg};result[name]=merged
 return result

def marker(image,rgb):
 a=np.array(image.convert('RGBA'));yy,xx=np.where(np.all(a[:,:,:3]==rgb,axis=2)&(a[:,:,3]>0))
 return [int(xx[0]),int(yy[0])] if len(xx)==1 else None

def seat_from_markers(head,shadow,offset,scale=1):
 if head is None or shadow is None:raise ValueError('Missing or ambiguous head/shadow marker; no bounding-box fallback allowed')
 if scale<=0:raise ValueError('Scale must be positive')
 return [(head[i]-shadow[i]+offset[i])*scale for i in range(2)]

def resolve_nodes(root):
 nodes={n.findtext('Name'):n for n in root.findall('./Anims/Anim')}
 def resolve(name,trail=()):
  if name in trail:raise ValueError('CopyOf cycle: '+str(trail+(name,)))
  if name not in nodes:raise ValueError('Missing CopyOf target '+name)
  n=nodes[name];alias=n.findtext('CopyOf')
  return resolve(alias,trail+(name,)) if alias else (name,n)
 return nodes,resolve

def inspect_profile(name,profile):
 path=ROOT/profile['sprite_dir'];nodes,resolve=resolve_nodes(ET.parse(path/'AnimData.xml').getroot());records=[];skipped=[]
 for action in nodes:
  try:source,n=resolve(action)
  except ValueError as e:skipped.append({'action':action,'reason':str(e)});continue
  filenames=[path/f'{source}-{kind}.png' for kind in ['Anim','Offsets','Shadow']]
  if not all(p.exists() for p in filenames):
   skipped.append({'action':action,'reason':'reference XML declares action but local PNG triple is absent'});continue
  w,h=int(n.findtext('FrameWidth')),int(n.findtext('FrameHeight'));dur=[int(t.text) for t in n.findall('./Durations/Duration')]
  sprite,offset,shadow=[Image.open(p).convert('RGBA') for p in filenames]
  if sprite.size!=offset.size or sprite.size!=shadow.size or sprite.width!=w*len(dur) or sprite.height%h:
   skipped.append({'action':action,'reason':'malformed sheet geometry'});continue
  rows=sprite.height//h
  if rows not in [1,8]:skipped.append({'action':action,'reason':'unsupported direction count'});continue
  for row in range(rows):
   for frame,ticks in enumerate(dur):
    box=(frame*w,row*h,(frame+1)*w,(row+1)*h);head=marker(offset.crop(box),(0,0,0));ground=marker(shadow.crop(box),(255,255,255))
    base_dir=row if rows==8 else profile.get('single_row_direction',0)
    # Rotate's actual facing changes inside the row; don't stick the crown to row label.
    direction=(base_dir+frame)%8 if action=='Rotate' else base_dir
    key=f'{action}/{row}/{frame}';override=profile.get('frame_overrides',{}).get(key)
    state='fit_proposal_needs_visual_review'
    if head is None or ground is None:state='blocked_missing_anatomical_marker'
    elif action in profile.get('blocked_actions',[]) and override is None:state='blocked_pose_requires_manual_override'
    if override:direction=override.get('direction',direction)
    delta=override.get('seat_offset',profile['seat_offsets'][direction]) if override else profile['seat_offsets'][direction]
    width=override.get('head_width',profile['head_widths'][direction]) if override else profile['head_widths'][direction]
    record={'action':action,'source_action':source,'row':row,'frame':frame,'frame_size':[w,h],'ticks':ticks,'direction':direction,'head':head,'shadow':ground,'seat_offset':delta,'head_band_width':width,'front_overlap_px':profile.get('front_overlap_px',1),'state':state}
    if head is not None and ground is not None:record['seat_relative_to_ground']=seat_from_markers(head,ground,delta)
    records.append(record)
 return {'profile':name,'sprite_dir':profile['sprite_dir'],'active':profile['active'],'records':records,'skipped_actions':skipped}

def band_geometry(crown,kind):
 a=np.array(crown);m=(a[:,:,3]>0);m[:46]=False
 if kind=='fire':m &= (a[:,:,0]>110)&(a[:,:,1]<200)&(a[:,:,2]<150)
 yy,xx=np.where(m)
 if len(xx)==0:raise ValueError('Crown seat band not found')
 left,right=int(np.min(xx)),int(np.max(xx));bottom=int(np.max(yy))
 return {'seat':[(left+right)/2,bottom-1],'width':right-left+1,'band_bounds':[left,int(np.min(yy)),right+1,bottom+1]}

def place(crown,kind,record,ground_xy,character_scale=1):
 if record['state'].startswith('blocked'):raise ValueError(record['state'])
 geo=band_geometry(crown,kind);scale=record['head_band_width']*character_scale/geo['width']
 size=[max(1,round(crown.width*scale)),max(1,round(crown.height*scale))]
 c=crown.resize(size,Image.Resampling.NEAREST)
 # Account for integer raster scale separately on x and y to avoid seat drift.
 actual_scale=[size[0]/crown.width,size[1]/crown.height]
 seat=seat_from_markers(record['head'],record['shadow'],record['seat_offset'],character_scale)
 world=[ground_xy[i]+seat[i] for i in range(2)]
 pos=[round(world[i]-geo['seat'][i]*actual_scale[i]) for i in range(2)]
 return c,pos,{'seat_world':world,'crown_origin':pos,'crown_scale':actual_scale,'band_width_target':record['head_band_width']*character_scale,'direction':record['direction']}
