"""Mega Clefable V3 — every animation sheet DRAWN by the image generator frame by frame (gen/raw_<Anim>.png), prompted with
the canonical CHUNSOFT Clefable sheet of that animation (gen/guide_<Anim>.png) + a design lock (official LPZA art).
Pipeline per animation:
  1. segment the characters of the generated sheet (magenta keying, connected components);
  2. assign them to the canonical grid cells (rows = 8 directions, cols = frames) by nearest normalised centre — the generator keeps
     the grid but not exact cell positions; missing cells fall back to the nearest drawn cell of the same row;
  3. per cell: scale the drawing to the canonical character height of that frame, quantize to the shared 16-colour palette,
     1 px black outline, place it so that its feet/centre match the canonical frame's body centre (green marker of Offsets.png);
  4. Offsets.png and Shadow.png are copied from the canonical sheet (same frame size, same body centre, hands, head, shadow);
  5. AnimData.xml is the canonical file (same durations, sizes, Rush/Hit/Return frames).
Animations whose raw sheet is missing (Double, Withdraw: image budget) are listed in the manifest and left out of AnimData.xml."""
from pathlib import Path
import json,zipfile,hashlib,shutil
import numpy as np
from PIL import Image
from scipy import ndimage
import xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent;G=S/'gen';REF=R/'source/mega_clefable_sprite_v1/references/spritecollab_0036';O=R/'renders/mega_clefable_sprite_v4';OUT=O/'sprite/0036/0001';OUT.mkdir(parents=True,exist_ok=True)
G3=R/"source/mega_clefable_sprite_v3/gen";guides=json.load(open(G3/"guides.json"))
# Idle and Walk: reuse the V3 raw sheets (kept on user request); all other anims: V4 strict-design sheets
PIN_V3={'Idle','Walk'}          # kept from V3 on user request
SOURCE_OVERRIDE={'Attack':('Double',16)}  # V4 Attack sheet came out as a turnaround: use the first strike of the strict Double sheet
def raw_path(name):
    if name in PIN_V3:return G3/f"raw_{name}.png"
    if name in SOURCE_OVERRIDE:return G/f"raw_{SOURCE_OVERRIDE[name][0]}.png"
    return G/f"raw_{name}.png"
# shared palette (15 colours + outline) extracted once from the Idle drawing
def keyed(path):
    a=np.array(Image.open(path).convert('RGB')).astype(int);bg=np.array([255,0,255])
    m=(np.abs(a-bg).sum(axis=2)>90);m=ndimage.binary_opening(m,iterations=1);m=ndimage.binary_fill_holes(m)
    # drop shadows drawn by the generator (dark magenta) are keyed out with the background
    shadow=(a[...,1]<90)&(a[...,0]>90)&(a[...,2]>90)&(a[...,0]<215);m&=~shadow;m=ndimage.binary_opening(m,iterations=1)
    # magenta halo: pixels near bg hue (high R, low G, high B) at the mask edge -> eroded away
    halo=(a[...,0]>150)&(a[...,1]<120)&(a[...,2]>150)&m;m&=~halo;m=ndimage.binary_fill_holes(m);return a,m
# fixed 16-colour palette (official LPZA design): body peach ×3, wing rose ×3, yellow tips ×2, white cap ×2, cuff black/grey, cheeks, mouth, ear tip, outline
PAL=np.array([[255,226,208],[246,196,176],[214,152,138],   # body light / mid / shade
 [236,110,140],[204,72,110],[150,44,80],                  # wings light / mid / dark
 [250,220,110],[228,180,70],                              # yellow tips
 [255,255,255],[222,222,232],                             # white cap / shade
 [40,32,40],[96,84,96],                                   # cuffs
 [250,150,170],[120,40,60],[214,120,130],                 # cheeks / mouth / ear
 [0,0,0]])

def quant(rgb):
    d=((rgb[...,None,:].astype(int)-PAL[None,None,:,:])**2).sum(-1);return PAL[d.argmin(-1)].astype('uint8')
def components(m):
    lab,n=ndimage.label(m);objs=ndimage.find_objects(lab);out=[]
    for i,s in enumerate(objs):
        h=s[0].stop-s[0].start;w=s[1].stop-s[1].start
        if h<25 or w<15:continue
        out.append(dict(box=(s[1].start,s[0].start,s[1].stop,s[0].stop),cx=(s[1].start+s[1].stop)/2,cy=(s[0].start+s[0].stop)/2,mask=(lab[s]==i+1)))
    return out
def canon_info(name):
    fw,fh=guides[name]['fw'],guides[name]['fh'];cols,rows=guides[name]['cols'],guides[name]['rows']
    an=np.array(Image.open(REF/f'{name}-Anim.png').convert('RGBA'));of=np.array(Image.open(REF/f'{name}-Offsets.png').convert('RGBA'));info={}
    for r in range(rows):
        for c in range(cols):
            fr=an[r*fh:(r+1)*fh,c*fw:(c+1)*fw];o=of[r*fh:(r+1)*fh,c*fw:(c+1)*fw];al=fr[...,3]>0;ys,xs=np.nonzero(al)
            g=np.nonzero((o[...,1]==255)&(o[...,3]>0));gy,gx=(int(g[0][0]),int(g[1][0])) if len(g[0]) else (fh//2,fw//2)
            info[(r,c)]=dict(h=int(ys.max()-ys.min()+1) if len(ys) else fh//2,bottom=int(ys.max()) if len(ys) else fh-1,cx=gx,cy=gy)
    return fw,fh,cols,rows,info
def render_cell(a,comp,target_h):
    x0,y0,x1,y1=comp['box'];rgb=a[y0:y1,x0:x1].astype('uint8');m=comp['mask'];s=target_h/(y1-y0)
    pre=np.dstack([rgb*m[...,None],(m*255).astype('uint8')]).astype('uint8');im=Image.fromarray(pre,'RGBA').resize((max(2,round((x1-x0)*s)),max(2,target_h)),Image.BOX)
    arr=np.array(im).astype(float);al=arr[...,3]>100;rgb2=np.zeros_like(arr[...,:3]);rgb2[al]=arr[...,:3][al]*255/arr[...,3:4][al];q=quant(np.clip(rgb2,0,255).astype('uint8'));out=np.dstack([q,(al*255).astype('uint8')]);out[~al]=0
    edge=al&~ndimage.binary_erosion(al);out[edge,:3]=0;return out
report={};missing=[]
xml_src=ET.parse(REF/'AnimData.xml');root=xml_src.getroot();anims_el=root.find('Anims')
for an in list(anims_el):
    name=an.find('Name').text
    if an.find('CopyOf') is not None:continue
    raw=raw_path(name)
    if not raw.exists():missing.append(name);anims_el.remove(an);continue
    fw,fh,cols,rows,info=canon_info(name);a,m=keyed(raw);comps=components(m);H,W=m.shape
    # assign components to cells by normalised centre (cell = round(centre / cell size in generated image))
    src_cols=SOURCE_OVERRIDE.get(name,(None,cols))[1];cw,ch=W/src_cols,H/rows;cells={}
    for comp in comps:
        c=min(src_cols-1,max(0,int(comp['cx']//cw)));r=min(rows-1,max(0,int(comp['cy']//ch)))
        if c>=cols:continue
        key=(r,c)
        if key not in cells or (comp['box'][3]-comp['box'][1])>(cells[key]['box'][3]-cells[key]['box'][1]):cells[key]=comp
    anim=np.zeros((rows*fh,cols*fw,4),'uint8');filled=0;fallback=0
    for r in range(rows):
        for c in range(cols):
            comp=cells.get((r,c))
            if comp is None:
                cands=[cells[k] for k in cells if k[0]==r] or list(cells.values())
                if not cands:continue
                comp=min(cands,key=lambda k:abs(k['cx']/cw-c));fallback+=1
            else:filled+=1
            ci=info[(r,c)];cell=render_cell(a,comp,min(fh-2,max(8,ci['h'])));h,w=cell.shape[:2]
            if w>fw-2:  # drawing wider than the frame (wings): rescale to fit width with 1px margin
                s_=(fw-2)/w;cell=render_cell(a,comp,max(8,int(h*s_)));h,w=cell.shape[:2]
            x=int(round(ci['cx']-w/2));y=ci['bottom']-h+1;x=min(max(x,1),fw-w-1);y=min(max(y,1),fh-h-1)
            anim[r*fh+y:r*fh+y+h,c*fw+x:c*fw+x+w]=cell
    Image.fromarray(anim).save(OUT/f'{name}-Anim.png');shutil.copy(REF/f'{name}-Offsets.png',OUT/f'{name}-Offsets.png');shutil.copy(REF/f'{name}-Shadow.png',OUT/f'{name}-Shadow.png')
    report[name]=dict(cells=rows*cols,drawn_cells=filled,fallback_cells=fallback,components_found=len(comps),frame=[fw,fh],durations=[d.text for d in an.findall('Durations/Duration')])
    print(name,report[name])
# Strike stays as CopyOf Attack
xml_src.write(OUT/'AnimData.xml',encoding='utf-8',xml_declaration=True)
(OUT/'credits.txt').write_text('2026-09-22 00:00:00.000000\tarena-agent (AI-drawn sheets per animation, regridded on CHUNSOFT frames; Mega proposal)\tCUR\tCC_BY-NC_4\t'+','.join(list(report)+['Strike'])+'\n')
with zipfile.ZipFile(O/'0036_0001_mega_clefable_v4_spritecollab.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(OUT.iterdir()):z.write(p,p.name)
# review boards + animated previews
for name in report:
    im=Image.open(OUT/f'{name}-Anim.png').convert('RGBA');b=Image.new('RGBA',im.size,(90,90,90,255));b.alpha_composite(im);s=3 if im.width<600 else 2;b.resize((im.width*s,im.height*s),Image.NEAREST).save(O/f'planche_{name}_x{s}.png')
fw,fh=guides['Walk']['fw'],guides['Walk']['fh'];walk=Image.open(OUT/'Walk-Anim.png').convert('RGBA');durs=[int(d) for d in report['Walk']['durations']];frames=[];dd=[]
for r in range(8):
    for c in range(8):
        f=Image.new('RGBA',(fw,fh),(120,150,120,255));f.alpha_composite(walk.crop((c*fw,r*fh,(c+1)*fw,(r+1)*fh)));frames.append(f.resize((fw*4,fh*4),Image.NEAREST));dd.append(durs[c]*1000//60)
frames[0].save(O/'apercu_walk_8_directions.webp',save_all=True,append_images=frames[1:],duration=dd,loop=0,lossless=True)
(O/'manifest.json').write_text(json.dumps(dict(base_xml_offsets_shadows='CHUNSOFT sprite/0036 @aae4cee2 (unchanged)',palette=PAL.tolist(),anims=report,missing_anims=missing,raw_sheets={str(raw_path(n).relative_to(R)):hashlib.sha256(raw_path(n).read_bytes()).hexdigest() for n in report},generated=True,runtime_validated=False),indent=1))
print('missing',missing)
