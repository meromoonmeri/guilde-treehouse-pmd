"""Native 8px tiles only. Used by the guided-zone reconstruction, never by image generation."""
from pathlib import Path
from PIL import Image
import struct,io,hashlib,math
ROOT=Path(__file__).resolve().parents[2]
BASE='Metano_Town_Base';CLIFF='Metano_Town_Cliffs';ANIM='Metano_Town_Animation_Tileset'
RIVERS=[f'Metano_Town_River_Animation_{i}' for i in range(1,5)]
PATHS={BASE:ROOT/'source/falaises_metano/natifs'/f'{BASE}.tile',CLIFF:ROOT/'source/falaises_metano/natifs'/f'{CLIFF}.tile'}
PATHS.update({n:ROOT/'source/eau_metano/natifs'/f'{n}.tile' for n in [ANIM]+RIVERS})

def straight(raw):
    im=raw.copy();im.putdata([(round(r*255/a),round(g*255/a),round(b*255/a),a) if 0<a<255 else (r,g,b,a) for r,g,b,a in raw.getdata()]);return im

class Bank:
    def __init__(self):
        self.sources={};self.source_info={};self.images=[];self.origins=[];self.ids={};self.animations={};self.proxies={};self.png={}
        for name,path in PATHS.items():
            raw=path.read_bytes();size,n=struct.unpack_from('<II',raw);assert size==8
            tiles={};offsets={}
            for i in range(n):
                x,y,o=struct.unpack_from('<IIQ',raw,8+16*i)
                if o not in offsets:
                    ln=struct.unpack_from('<q',raw,o)[0];offsets[o]=Image.open(io.BytesIO(raw[o+8:o+8+ln])).convert('RGBA')
                tiles[x,y]=offsets[o]
            self.sources[name]=tiles
            self.source_info[name]={'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(raw).hexdigest(),'git_blob_sha1':hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()}
    def get(self,name,x,y):
        key=(name,x,y)
        if key not in self.ids:
            im=self.sources[name].get((x,y))
            if im is None:self.ids[key]=0
            else:
                self.images.append(im);self.origins.append({'sheet':name,'texloc':[x,y],'role':'native'});self.ids[key]=len(self.images)
        return self.ids[key]
    def animated(self,refs):
        seq=tuple(self.get(*r) for r in refs)
        if len(set(seq))==1:return seq[0]
        assert all(seq)
        if seq not in self.proxies:
            self.images.append(self.images[seq[0]-1]);ref=dict(self.origins[seq[0]-1]);ref['role']='animation_first_frame';self.origins.append(ref)
            gid=len(self.images);self.proxies[seq]=gid;self.animations[gid]=seq
        return self.proxies[seq]
    def image(self,gid):
        if gid not in self.png:self.png[gid]=straight(self.images[gid-1])
        return self.png[gid]
    def render(self,data,frame=0):
        out=Image.new('RGBA',(2048,1536))
        for i,gid in enumerate(data):
            if gid:
                gid=self.animations.get(gid,[gid]*4)[frame];out.paste(self.image(gid),((i%256)*8,(i//256)*8))
        return out
    def save(self,out,name):
        cols=64;rows=math.ceil(len(self.images)/cols);count=cols*rows
        atlas=Image.new('RGBA',(cols*8,rows*8));payload=bytearray();entries=[];offsets={};blank=Image.new('RGBA',(8,8))
        for i in range(count):
            raw=self.images[i] if i<len(self.images) else blank
            if i<len(self.images):atlas.paste(self.image(i+1),((i%cols)*8,(i//cols)*8))
            key=raw.tobytes()
            if key not in offsets:
                offsets[key]=8+16*count+len(payload);b=io.BytesIO();raw.save(b,format='PNG');v=b.getvalue();payload.extend(struct.pack('<q',len(v))+v)
            entries.append(struct.pack('<IIQ',i%cols,i//cols,offsets[key]))
        atlas.save(out/(name+'.png'));(out/(name+'.tile')).write_bytes(struct.pack('<II',8,count)+b''.join(entries)+payload)
        return {'columns':cols,'tilecount':count,'imagewidth':atlas.width,'imageheight':atlas.height}
