"""Guild-style layered exports, preserving the approved guided zones byte-for-byte.
Does not regenerate the guides or alter any native tile. Tiled uses the existing atlas.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
import json,struct,zlib,base64,hashlib,io
R=Path(__file__).resolve().parents[1];O=R/'sprites/zones_guidees'
M=json.loads((O/'provenance.json').read_text());A=M['atlas'];AT=Image.open(O/(A['name']+'.png')).convert('RGBA')
TS=json.loads((O/(A['name']+'.tsj')).read_text());AN={t['id']+1:[f['tileid']+1 for f in t['animation']] for t in TS['tiles']}
LABELS=[('01_sol','Sol — herbe Métano'),('02_parois','Parois rocheuses'),('03_bordures','Bordures et retours de falaises'),('04_berges','Berges et fond de rivière'),('05_riviere','Surface de rivière animée'),('06_cascades','Cascades animées')]
CACHE={}
def tile(g):
    if g not in CACHE:
        x,y=(g-1)%A['columns']*8,(g-1)//A['columns']*8;CACHE[g]=AT.crop((x,y,x+8,y+8))
    return CACHE[g]
def render(data,f=0):
    im=Image.new('RGBA',(2048,1536))
    for i,g in enumerate(data):
        if g:im.paste(tile(AN.get(g,[g]*4)[f]),(i%256*8,i//256*8))
    return im

def save_png(im,path):
    raw=io.BytesIO();im.save(raw,format='PNG',optimize=True)
    if im.getcolors(256) is not None:
        values,indices=np.unique(np.asarray(im).reshape(-1,4).copy().view('<u4'),return_inverse=True)
        colors=values.view('uint8').reshape(-1,4)
        indexed=Image.fromarray(indices.reshape(im.height,im.width).astype('uint8'),'P')
        palette=np.zeros((256,3),dtype=np.uint8);palette[:len(colors)]=colors[:,:3];indexed.putpalette(palette.ravel());indexed.info['transparency']=bytes(colors[:,3])
        assert indexed.convert('RGBA').tobytes()==im.tobytes()
        packed=io.BytesIO();indexed.save(packed,format='PNG',optimize=True)
        if packed.tell()<raw.tell():raw=packed
    path.write_bytes(raw.getvalue())

def chunk(kind,data):return struct.pack('<IH',len(data)+6,kind)+data
def astr(s):b=s.encode();return struct.pack('<H',len(b))+b

def ase(path,frames,labels):
    # Same layer/cel structure as source/rebuild_kit.py; static layers link to frame 0.
    all_frames=[]
    for f,images in enumerate(frames):
        chunks=[]
        if f==0:
            for name in labels:chunks.append(chunk(0x2004,struct.pack('<HHHHHHB',3,0,0,0,0,0,255)+b'\0'*3+astr(name)))
        for i,im in enumerate(images):
            box=im.getbbox();x,y=(box[:2] if box else (0,0))
            link=f>0 and i<4
            cel=struct.pack('<HhhBHh',i,x,y,255,1 if link else 2,0)+b'\0'*5
            if link:cel+=struct.pack('<H',0)
            else:
                q=im.crop(box) if box else Image.new('RGBA',(1,1));cel+=struct.pack('<HH',q.width,q.height)+zlib.compress(q.tobytes(),9)
            chunks.append(chunk(0x2005,cel))
        data=b''.join(chunks);all_frames.append(struct.pack('<IHHH2sI',len(data)+16,0xF1FA,len(chunks),167,b'\0\0',len(chunks))+data)
    body=b''.join(all_frames);header=bytearray(128);struct.pack_into('<IHHHHHIH',header,0,len(body)+128,0xA5E0,len(frames),2048,1536,32,1,167);struct.pack_into('<HBBhhHH',header,32,0,1,1,0,0,8,8);path.write_bytes(header+body)

manifest={'method':'Keep the approved guide -> canonical tile method; split existing tile cells into disjoint layers, without regenerating or repainting.', 'guild_reference_commit':'6c4ac5aad90da4f670d4965ec3d37a3ea38b5c78','branch_reference_commit':'7f1e82b','dimensions':[2048,1536],'grid':8,'layers':[{'id':id,'name':name,'animated':i>=4,'wet_only':i>=3} for i,(id,name) in enumerate(LABELS)],'zones':[],'limits':['Border layer is the one-cell peripheral band of the rock mask, including top, feet and side returns; not an autotile classification','River banks include native static water pixels; hide all three wet layers for a dry scene','No added palette for night: source textures remain unchanged','No collisions, transitions, or runtime PMDO validation']}
board=Image.new('RGB',(1512,820),'#192d24');d=ImageDraw.Draw(board);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',16)
d.text((22,14),'MÉTANO · LES DEUX ZONES VALIDÉES, EN SIX CALQUES',font=font,fill='#eedb9e')
for zi,zone in enumerate(M['zones']):
    parent=O/zone['id'];out=parent/'multicalques';out.mkdir(exist_ok=True)
    original=json.loads((parent/'eau.tmj').read_text());src=[l['data'] for l in original['layers']]
    mask=np.array(src[1]).reshape(192,256)>0
    padded=np.pad(mask,1,constant_values=True);inside=mask.copy()
    for dy in range(3):
        for dx in range(3):inside&=padded[dy:dy+192,dx:dx+256]
    inside=inside.ravel();body=[g if inside[i] else 0 for i,g in enumerate(src[1])];edge=[g if not inside[i] else 0 for i,g in enumerate(src[1])]
    river=[];falls=[]
    for g in src[3]:
        cascade=bool(g) and A['entries'][AN.get(g,[g])[0]-1]['sheet']=='Metano_Town_Animation_Tileset'
        river.append(0 if cascade else g);falls.append(g if cascade else 0)
    arrays=[src[0],body,edge,src[2],river,falls]
    assert all((body[i] or edge[i])==src[1][i] and not(body[i] and edge[i]) for i in range(49152))
    assert all((river[i] or falls[i])==src[3][i] and not(river[i] and falls[i]) for i in range(49152))
    frames=[];files={}
    for f in range(4):
        images=[]
        for i,((id,name),data) in enumerate(zip(LABELS,arrays)):
            im=render(data,f);images.append(im)
            filename=id+(f'_phase_{f+1}' if i>=4 else '')+'.png'
            if i>=4 or f==0:save_png(im,out/filename)
            files.setdefault(id,[])
            if filename not in files[id]:files[id].append(filename)
        frames.append(images)
        composed=Image.new('RGBA',(2048,1536))
        for im in images:composed=Image.alpha_composite(composed,im)
        assert composed.tobytes()==Image.open(parent/f'canonique_eau_{f+1}.png').convert('RGBA').tobytes()
    dry=Image.new('RGBA',(2048,1536))
    for im in frames[0][:3]:dry=Image.alpha_composite(dry,im)
    assert dry.tobytes()==Image.open(parent/'canonique_sec.png').convert('RGBA').tobytes()
    ase(out/'zone_seche.aseprite',[frames[0][:3]],[n for _,n in LABELS[:3]])
    ase(out/'zone_eau_animee.aseprite',frames,[n for _,n in LABELS])
    for wet in [False,True]:
        count=6 if wet else 3;tm={k:v for k,v in original.items() if k not in ['layers','tilesets','nextlayerid']};tm['nextlayerid']=count+1;tm['tilesets']=[{'firstgid':1,'source':'../../'+A['name']+'.tsj'}];tm['layers']=[]
        for i in range(count):
            data=base64.b64encode(zlib.compress(struct.pack('<'+'I'*49152,*arrays[i]),9)).decode()
            tm['layers'].append({'id':i+1,'name':LABELS[i][1],'type':'tilelayer','width':256,'height':192,'x':0,'y':0,'opacity':1,'visible':True,'encoding':'base64','compression':'zlib','data':data})
        (out/('zone_eau.tmj' if wet else 'zone_seche.tmj')).write_text(json.dumps(tm,ensure_ascii=False,indent=2))
    rec={'id':zone['id'],'name':zone['name'],'directory':str(out.relative_to(R)),'files':files,'reference_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [parent/'canonique_sec.png']+[parent/f'canonique_eau_{f}.png' for f in range(1,5)]},'aseprite':['zone_seche.aseprite','zone_eau_animee.aseprite'],'tiled':['zone_seche.tmj','zone_eau.tmj']};manifest['zones'].append(rec)
    y=68+zi*365;d.text((22,y),zone['name'],font=small,fill='#eedb9e')
    for i,im in enumerate(frames[0]):
        bg=Image.new('RGBA',(240,180),'#30483b');bg=Image.alpha_composite(bg,im.resize((240,180),Image.Resampling.NEAREST));board.paste(bg.convert('RGB'),(22+i*247,y+35));d.text((22+i*247,y+224),LABELS[i][0].replace('_',' '),font=small,fill='#e1e9d2')
    d.text((22,y+267),'Même composition · tuiles natives inchangées · PNG RGBA + Aseprite + Tiled',font=small,fill='#b4c6b3')
d.text((22,782),'Aperçus réduits sur fond vert de contrôle. Les exports transparents conservent les pixels natifs.',font=small,fill='#b4c6b3');board.save(O/'planche_multicalques.png')
(O/'multicalques.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('Built 2 zones × 6 layers; dry + four-frame Aseprite; compressed Tiled maps; original composites unchanged.')
