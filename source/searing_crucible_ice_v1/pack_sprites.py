"""Package the 4 ice animations as real sprites:
 1. PMDO Object `.dir` files (Content/Object) with the EXACT container layout of the native lava .dir
    (same PNG sheet size, same column grid, same 4 int32 header values, premultiplied RGBA).
 2. A SpriteCollab-format zip per object (AnimData.xml + <Name>-Anim.png / -Offsets.png / -Shadow.png),
    following the PMDOWiki "PMD Sprite Format": even frame dimensions, frames left->right, one direction row,
    Durations in 1/60 s, Offsets green = body centre, Shadow white = sprite centre.
Also an rsmap patch snippet renaming the 8 decorations to the new AnimIndex names.
"""
from pathlib import Path
import sys,json,struct,io,zipfile,hashlib
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;REF=S/'references/nev5';O=R/'renders/searing_crucible_ice_v1'
sys.path.insert(0,str(S));from decode import rsmap
m=json.loads((O/'manifest.json').read_text())
NAMES={'Spring_Cave_Pit_Big_Lava_Stream':'Ice_Peak_Big_Frost_Stream','Spring_Cave_Pit_Small_Lava_Stream':'Ice_Peak_Small_Frost_Stream','Spring_Cave_Pit_Lava_Pool_Connected':'Ice_Peak_Frost_Pool_Connected','Spring_Cave_Pit_Lava_Pool_Disconnected':'Ice_Peak_Frost_Pool_Disconnected'}
DIR=O/'pmdo_object_dir';SC=O/'spritecollab';DIR.mkdir(exist_ok=True);SC.mkdir(exist_ok=True)
def premultiply(im):
    a=np.array(im).astype(float);al=a[...,3:4]/255;a[...,:3]=np.rint(a[...,:3]*al);return Image.fromarray(a.astype('uint8'))
report={}
for src,name in NAMES.items():
    d=(REF/f'Content/Object/{src}.dir').read_bytes();n=struct.unpack('<q',d[:8])[0];sheet=Image.open(io.BytesIO(d[8:8+n]));hdr=struct.unpack('<4i',d[8+n:8+n+16]);w,h,dirs,frames=hdr
    strip=Image.open(O/'objets_animes'/f'{name}_{w}x{h}_{frames}f.png').convert('RGBA');cols=sheet.width//w
    # 1. .dir with the identical container layout
    new=Image.new('RGBA',sheet.size)
    for i in range(frames):new.paste(strip.crop((i*w,0,i*w+w,h)),((i%cols)*w,(i//cols)*h))
    buf=io.BytesIO();premultiply(new).save(buf,'PNG');png=buf.getvalue()
    out=DIR/f'{name}.dir';out.write_bytes(struct.pack('<q',len(png))+png+struct.pack('<4i',*hdr))
    # 2. SpriteCollab-style package (single direction, 63 frames)
    anim=Image.new('RGBA',(w*frames,h));anim.paste(strip,(0,0))
    off=Image.new('RGBA',anim.size);sh=Image.new('RGBA',anim.size)
    for i in range(frames):
        cx,cy=i*w+w//2,h//2;off.putpixel((cx,cy),(0,255,0,255));sh.putpixel((cx,cy),(255,255,255,255))
    durations=''.join('<Duration>4</Duration>' for _ in range(frames))
    xml=f'<?xml version="1.0" ?>\n<AnimData>\n <ShadowSize>0</ShadowSize>\n <Anims>\n  <Anim>\n   <Name>Idle</Name>\n   <Index>7</Index>\n   <FrameWidth>{w}</FrameWidth>\n   <FrameHeight>{h}</FrameHeight>\n   <Durations>{durations}</Durations>\n  </Anim>\n </Anims>\n</AnimData>\n'
    folder=SC/name;folder.mkdir(exist_ok=True)
    anim.save(folder/'Idle-Anim.png');off.save(folder/'Idle-Offsets.png');sh.save(folder/'Idle-Shadow.png');(folder/'AnimData.xml').write_text(xml)
    with zipfile.ZipFile(SC/f'{name}.zip','w',zipfile.ZIP_DEFLATED) as z:
        for f in ['AnimData.xml','Idle-Anim.png','Idle-Offsets.png','Idle-Shadow.png']:z.write(folder/f,f)
    report[name]=dict(source_dir=src,dir_header=dict(tile_w=w,tile_h=h,dirs=dirs,frames=frames),sheet=list(sheet.size),columns=cols,frame_even_dims=(w%2==0 and h%2==0),
        spritecollab=dict(anim=f'Idle-Anim.png {anim.size}',durations_60ths=4,directions=1,frames=frames),sha256_dir=hashlib.sha256(out.read_bytes()).hexdigest())
# 3. rsmap decoration patch (AnimIndex renamed; everything else untouched)
o=rsmap();patch=[]
for dl in o['Decorations']:
    for a in dl['Anims']:
        oa=a['ObjectAnim'];patch.append(dict(MapLoc=a['MapLoc'],ObjectAnim=dict(oa,AnimIndex=NAMES[oa['AnimIndex']])))
(O/'rsmap_decorations_glace.json').write_text(json.dumps(patch,indent=1))
(O/'sprites_manifest.json').write_text(json.dumps(dict(objects=report,rsmap_patch='rsmap_decorations_glace.json',format_refs=['https://wiki.pmdo.pmdcollab.org/Tutorial:PMD_Sprite_Format','PMDO DirSheet: int64 png length + PNG + int32 tileW,tileH,dirs,frames (premultiplied RGBA)'],runtime_validated=False),indent=1))
print(json.dumps(report,indent=1))
