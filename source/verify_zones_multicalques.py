"""Read back PNG, Aseprite (including linked cels) and compressed Tiled independently."""
from pathlib import Path
from PIL import Image
import json,struct,zlib,base64,hashlib,subprocess,sys
R=Path(__file__).resolve().parents[1];O=R/'sprites/zones_guidees'
subprocess.run([sys.executable,str(R/'source/verify_zones_guidees.py')],check=True)
M=json.loads((O/'multicalques.json').read_text());P=json.loads((O/'provenance.json').read_text());A=P['atlas'];atlas=Image.open(O/(A['name']+'.png')).convert('RGBA');ts=json.loads((O/(A['name']+'.tsj')).read_text());animations={t['id']+1:[f['tileid']+1 for f in t['animation']] for t in ts['tiles']}
def compose(images):
    out=Image.new('RGBA',(2048,1536))
    for im in images:out=Image.alpha_composite(out,im)
    return out

def decode_ase(path):
    data=path.read_bytes();size,magic,count,w,h,depth,flags,speed=struct.unpack_from('<IHHHHHIH',data)
    assert size==len(data) and magic==0xA5E0 and (w,h,depth)==(2048,1536,32)
    assert struct.unpack_from('<hhHH',data,36)==(0,0,8,8)
    pos=128;frames=[];layer_names=[];history=[]
    for f in range(count):
        length,magic,n,duration=struct.unpack_from('<IHHH',data,pos);assert magic==0xF1FA and duration==167
        end=pos+length;pos+=16;cels={}
        for k in range(n):
            length,kind=struct.unpack_from('<IH',data,pos);p=data[pos+6:pos+length]
            if kind==0x2004:
                assert f==0;ln=struct.unpack_from('<H',p,16)[0];layer_names.append(p[18:18+ln].decode())
                assert struct.unpack_from('<H',p)[0]&1 and p[12]==255
            if kind==0x2005:
                idx,x,y,alpha,typ=struct.unpack_from('<HhhBH',p);assert alpha==255
                if typ==2:
                    cw,ch=struct.unpack_from('<HH',p,16);im=Image.frombytes('RGBA',(cw,ch),zlib.decompress(p[20:]))
                else:
                    assert typ==1;ref=struct.unpack_from('<H',p,16)[0];assert ref<f;im=history[ref][idx][2]
                cels[idx]=(x,y,im)
            pos+=length
        assert pos==end;history.append(cels);ims=[]
        assert sorted(cels)==list(range(len(layer_names)))
        for idx in sorted(cels):
            x,y,im=cels[idx];canvas=Image.new('RGBA',(w,h));canvas.paste(im,(x,y));ims.append(canvas)
        frames.append(ims)
    assert pos==len(data);return layer_names,frames

report={'status':'PASS','original_compositions_modified':False,'guild_reference_commit':M['guild_reference_commit'],'zones':[],'limits':['No interactive Aseprite/Tiled application validation','No gameplay or collision validation']}
for zone in M['zones']:
    root=R/zone['directory'];parent=root.parent
    for fn,sha in zone['reference_sha256'].items():assert hashlib.sha256((parent/fn).read_bytes()).hexdigest()==sha
    png_frames=[]
    for f in range(4):
        images=[]
        for layer in M['layers']:
            files=zone['files'][layer['id']];im=Image.open(root/files[f if layer['animated'] else 0]).convert('RGBA');assert im.size==(2048,1536);images.append(im)
        assert compose(images).tobytes()==Image.open(parent/f'canonique_eau_{f+1}.png').convert('RGBA').tobytes()
        png_frames.append(images)
    assert compose(png_frames[0][:3]).tobytes()==Image.open(parent/'canonique_sec.png').convert('RGBA').tobytes()
    for wet in [False,True]:
        n=6 if wet else 3;names,frames=decode_ase(root/('zone_eau_animee.aseprite' if wet else 'zone_seche.aseprite'))
        assert names==[l['name'] for l in M['layers'][:n]] and len(frames)==(4 if wet else 1)
        for f,images in enumerate(frames):
            for i,im in enumerate(images):assert im.tobytes()==png_frames[f][i].tobytes(),('Aseprite cel',zone['id'],f,i)
        tm=json.loads((root/('zone_eau.tmj' if wet else 'zone_seche.tmj')).read_text());assert (root/tm['tilesets'][0]['source']).resolve()==(O/(A['name']+'.tsj')).resolve();assert tm['width']==256 and tm['height']==192 and tm['tilewidth']==tm['tileheight']==8
        arrays=[]
        for layer in tm['layers']:
            assert layer['encoding']=='base64' and layer['compression']=='zlib';raw=zlib.decompress(base64.b64decode(layer['data']));assert len(raw)==49152*4;arrays.append(struct.unpack('<49152I',raw))
        assert len(arrays)==n
        src=json.loads((parent/'eau.tmj').read_text())['layers']
        assert list(arrays[0])==src[0]['data']
        assert all((a or b)==s and not(a and b) for a,b,s in zip(arrays[1],arrays[2],src[1]['data']))
        if wet:
            assert list(arrays[3])==src[2]['data']
            assert all((a or b)==s and not(a and b) for a,b,s in zip(arrays[4],arrays[5],src[3]['data']))
        for f in range(4 if wet else 1):
            for i,arr in enumerate(arrays):
                im=Image.new('RGBA',(2048,1536))
                for at,g in enumerate(arr):
                    if not g:continue
                    assert 1<=g<=A['used'];g=animations.get(g,[g]*4)[f];x,y=(g-1)%A['columns']*8,(g-1)//A['columns']*8
                    im.paste(atlas.crop((x,y,x+8,y+8)),(at%256*8,at//256*8))
                assert im.tobytes()==png_frames[f][i].tobytes(),('Tiled layer',zone['id'],f,i)
    report['zones'].append({'id':zone['id'],'layers_wet':6,'layers_dry':3,'water_frames':4,'png_aseprite_tiled_different_pixels':0,'tile_assignments_disjoint_and_source_identical':True})
(O/'verification_multicalques.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
