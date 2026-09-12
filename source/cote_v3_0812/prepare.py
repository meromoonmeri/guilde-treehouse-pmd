"""Keep approved V2 silhouettes; use real Metano rock pixels under separate lighting.
Only crop at declared map exits, never scale the approved terrain.
Generated rock-retouch trials are NOT used as canonical texture.
"""
from pathlib import Path
import hashlib
import io
import json
import struct

import numpy as np
from PIL import Image, ImageFilter

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'sprites/cote_v3_0812'
CLIFF=ROOT/'source/falaises_metano/natifs/Metano_Town_Cliffs.tile'
ROCK_RECT=(912,464,976,512)
CONFIG=[
 ('01_cap_large','Le grand cap','WS'),
 ('02_terrasse_croissant','La terrasse en croissant','ES'),
 ('03_double_belvedere','Le double belvédère','WES'),
 ('04_pointe_sinueuse','La pointe sinueuse','WS'),
 ('05_grande_mesa','La grande mesa','S'),
 ('06_crique_profonde','La crique profonde','ES'),
 ('07_balcon_haut','Le haut balcon','ES'),
 ('08_terrasses_decalees','Les terrasses décalées','ES'),
 ('09_cap_eventail','Le cap en éventail','WS'),
 ('10_esplanade_arrondie','L’esplanade arrondie','ES'),
]


def opaque(a):
    a=a.astype('int16')
    return ~((a[:,:,0]>180)&(a[:,:,2]>140)&(a[:,:,1]<a[:,:,0]-75)&(a[:,:,1]<a[:,:,2]-60))


def large_components(mask,minimum=3000):
    # Run-length connected components: no scipy/OpenCV dependency.
    parent=[];area=[];runs=[];previous=[]
    def find(i):
        while parent[i]!=i:
            parent[i]=parent[parent[i]];i=parent[i]
        return i
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:
            if area[a]<area[b]:a,b=b,a
            parent[b]=a;area[a]+=area[b]
    for y,row in enumerate(mask):
        changes=np.flatnonzero(np.diff(np.pad(row.astype('int8'),(1,1))))
        current=[];j=0
        for x0,x1 in zip(changes[::2],changes[1::2]):
            i=len(parent);parent.append(i);area.append(int(x1-x0));current.append((x0,x1,i));runs.append((y,x0,x1,i))
            while j<len(previous) and previous[j][1]<=x0:j+=1
            k=j
            while k<len(previous) and previous[k][0]<x1:
                union(i,previous[k][2]);k+=1
        previous=current
    out=np.zeros_like(mask)
    for y,x0,x1,i in runs:
        if area[find(i)]>=minimum:out[y,x0:x1]=True
    return out


def grass_mask(a,land):
    v=a.astype('int16')
    return large_components(land&(v[:,:,1]>115)&(v[:,:,0]-v[:,:,1]<26)&(v[:,:,1]-v[:,:,2]>80))


def native_material():
    raw=CLIFF.read_bytes();size,count=struct.unpack_from('<ii',raw);assert size==8
    x0,y0,x1,y1=ROCK_RECT
    out=Image.new('RGBA',(x1-x0,y1-y0))
    for i in range(count):
        x,y,offset=struct.unpack_from('<iiq',raw,8+i*16)
        if x0//8<=x<x1//8 and y0//8<=y<y1//8:
            n,=struct.unpack_from('<q',raw,offset)
            tile=Image.open(io.BytesIO(raw[offset+8:offset+8+n])).convert('RGBA')
            assert tile.getchannel('A').getextrema()==(255,255)
            out.paste(tile,(x*8-x0,y*8-y0))
    assert out.getchannel('A').getextrema()==(255,255)
    return out


def save(image,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    image.save(path,optimize=True)


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    material=native_material();save(material,OUT/'METANO_ROCHE_NATIVE_64x48.png')
    record={'target_pmdo':'0.8.12','serializer_version':'0.8.12.0',
            'rock_source':{'file':str(CLIFF.relative_to(ROOT)),'sha256':hashlib.sha256(CLIFF.read_bytes()).hexdigest(),
                           'rect':ROCK_RECT,'scale':1,'file_control':'METANO_ROCHE_NATIVE_64x48.png'},
            'lighting':'separate translucent layer; derived from approved macro shading, not baked into native material',
            'runtime_tested':False,'zones':[]}
    tex=np.array(material)
    for slug,title,designed_exits in CONFIG:
        edges='WES'  # Trim exterior margins on both sides and below; keep the sky above.
        raw=Image.open(HERE/(slug+'.png')).convert('RGBA');a=np.array(raw)
        land=opaque(a);grass=grass_mask(a,land)
        # Preserve a two-pixel contact fringe around the approved grassy surface.
        expanded=np.array(Image.fromarray((grass*255).astype('uint8')).filter(ImageFilter.MaxFilter(5)))>0
        fringe=expanded&land&~grass
        rock=land&~grass&~fringe
        assert rock.sum()>10000 and grass.sum()>20000
        h,w=land.shape
        ground=a.copy();ground[~grass]=0;ground[grass,3]=255
        cleaned=0
        if slug=='09_cap_eventail':
            # Remove generated building-plot marks, not the landform, using the
            # cleanup proposal only inside three bounded grass-only rectangles.
            edit=np.array(Image.open(HERE/'corrections'/f'{slug}.png').convert('RGBA'))
            assert edit.shape==a.shape
            valid=grass_mask(edit,opaque(edit))
            coverage=np.zeros((h,w),dtype='uint8')
            for x0,y0,x1,y1 in [(64,88,480,340),(432,224,936,484),(40,360,480,616)]:
                coverage[y0:y1,x0:x1]=255
            coverage=np.array(Image.fromarray(coverage).filter(ImageFilter.GaussianBlur(12))).astype(float)/255
            coverage*=grass&valid
            changed=coverage>0
            ground[:,:,:3]=np.rint(ground[:,:,:3]*(1-coverage[:,:,None])+edit[:,:,:3]*coverage[:,:,None]).astype('uint8')
            ground[~grass]=0;cleaned=int(changed.sum())
        rim=a.copy();rim[~fringe]=0;rim[fringe,3]=255
        stone=tex[(np.arange(h)%48)[:,None],(np.arange(w)%64)[None,:]].copy()
        stone[~rock]=0
        # Normalized blur excludes magenta and grass, so neither bleeds into light.
        lum=a[:,:,:3]@np.array([.2126,.7152,.0722])
        weights=Image.fromarray((rock*255).astype('uint8')).filter(ImageFilter.GaussianBlur(24))
        weighted=Image.fromarray(np.rint(lum*rock).astype('uint8')).filter(ImageFilter.GaussianBlur(24))
        smooth=np.array(weighted).astype(float)*255/np.maximum(np.array(weights).astype(float),1)
        tint=np.array([57,26,63]);target=smooth*.82
        native_lum=float((tex[:,:,:3]@np.array([.2126,.7152,.0722])).mean())
        tint_lum=float(tint@np.array([.2126,.7152,.0722]))
        alpha=np.rint(np.clip((native_lum-target)/(native_lum-tint_lum),0,.72)*255).astype('uint8')
        shade=np.zeros_like(a);shade[:,:,:3]=tint;shade[:,:,3]=alpha*rock
        shade[shade[:,:,3]==0]=0
        ys,xs=np.where(land)
        left=((int(xs.min())+7)//8)*8 if 'W' in edges else 0
        right=int(xs.max())+1 if 'E' in edges else w
        bottom=int(ys.max())+1 if 'S' in edges else h
        # Crop inwards (<=7 extra pixels) to an 8px grid, never add padding.
        width=(right-left)//8*8;height=bottom//8*8
        crop=(left,0,left+width,height)
        layers=[('00_HERBE',Image.fromarray(ground)),('01_ROCHE_METANO',Image.fromarray(stone)),
                ('02_LISIERE',Image.fromarray(rim)),('03_OMBRES',Image.fromarray(shade))]
        directory=OUT/slug
        comp=Image.new('RGBA',(width,height))
        names=[]
        for name,image in layers:
            image=image.crop(crop);filename=name+'.png';save(image,directory/filename);names.append(filename)
            comp=Image.alpha_composite(comp,image)
        save(comp,directory/'TERRAIN.png')
        old=a.copy();old[~land]=0;old[land,3]=255
        save(Image.fromarray(old).crop(crop),directory/'AVANT_ROCHE.png')
        save(Image.fromarray((grass*255).astype('uint8')).crop(crop),directory/'MASQUE_HERBE.png')
        final_alpha=np.array(comp)[:,:,3]>0
        expected=land[:height,left:left+width]
        assert np.array_equal(final_alpha,expected)
        touch={'W':bool(final_alpha[:,0].any()),'E':bool(final_alpha[:,-1].any()),'S':bool(final_alpha[-1,:].any())}
        assert all(touch[e] for e in edges),(slug,touch)
        edge_lengths={'W':int(final_alpha[:,0].sum()),'E':int(final_alpha[:,-1].sum()),'S':int(final_alpha[-1,:].sum())}
        record['zones'].append({'id':slug,'title':title,'source_size':raw.size,'size':[width,height],
                                'crop':crop,'exits':list(edges),'original_land_connections':list(designed_exits),'edge_contact_pixels':edge_lengths,
                                'layers':names,'grass_cleanup_pixels':cleaned,
                                'shape_differences_after_crop':0,'rock_reference_scale':1})
        print(slug,(width,height),edges,edge_lengths,flush=True)
    (OUT/'preparation.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
    return record


if __name__=='__main__':prepare()
