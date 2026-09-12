"""Independent tests for true palette cycling, cloud wrap and scene layer alignment."""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib,struct,math
R=Path(__file__).resolve().parents[1];S=R/'source/cote_v2';O=R/'sprites/cote_v2';M=json.loads((O/'manifest.json').read_text())
def sha(data):return hashlib.sha256(data).hexdigest()
def key(path):
    a=np.asarray(Image.open(path).convert('RGBA')).copy();r,g,b=[a[:,:,i].astype(float) for i in range(3)]
    mask=((r>160)&(b>145)&(r>g*1.35)&(b>g*1.35))|((r>100)&(b>100)&(r>g*1.8)&(b>g*1.8)&(b>r*.8)&(g<100));a[mask]=0;return Image.fromarray(a)
def idat(path):
    data=path.read_bytes();assert data[:8]==b'\x89PNG\r\n\x1a\n';pos=8;parts=[]
    while pos<len(data):
        length=struct.unpack_from('>I',data,pos)[0];kind=data[pos+4:pos+8]
        if kind==b'IDAT':parts.append(data[pos+8:pos+8+length])
        pos+=12+length
    return b''.join(parts)
for name,digest in M['source_hashes'].items():assert sha((S/name).read_bytes())==digest
C=M['clouds'];P=C['period_px'];tile=Image.open(O/C['tile']).convert('RGBA');assert tile.size==tuple(C['size_px']) and tile.width==P
assert P%8==tile.height%8==0
arr=np.asarray(tile);assert not arr[:,:32,3].any() and not arr[:,-32:,3].any()
source=key(S/'nuages_generes.png');expected=Image.new('RGBA',tile.size)
for i,(box,p) in enumerate(zip(C['source_boxes'],C['placements'])):
    crop=source.crop(tuple(box));original=Image.new('RGBA',(math.ceil(crop.width/8)*8,math.ceil(crop.height/8)*8));original.paste(crop,(0,0));sprite=Image.open(O/f'COTEV2_NUAGE_{i+1:02}.png').convert('RGBA');assert sprite.tobytes()==original.tobytes();assert sprite.size==original.size and sprite.width%8==sprite.height%8==0
    expected.paste(sprite,tuple(p['dest_px']))
assert expected.tobytes()==tile.tobytes()
def wrapped(w,h,offset):
    result=np.zeros((h,w,4),np.uint8);part=arr[:,(np.arange(w)+offset)%P];result[C['y']:C['y']+tile.height]=part;return Image.fromarray(result)
report={'status':'PASS','canonical_metano_terrain':False,'pmdo_runtime_tested':False,'clouds':{'source_sprites_preserved':4,'resizes':0,'period_px':P,'transparent_left_right_margin_at_least':32,'wrap_tests':'0=P, 1=P+1, -1=P-1, plus translation continuity at seam'},'zones':[]}
for zi,z in enumerate(M['zones']):
    d=O/z['id'];w,h=z['dimensions_px'];f=z['files'];terrain=Image.open(d/f['terrain']).convert('RGBA')
    orig=Image.open(R/'sprites/falaises_cotieres_nues/01_promontoire/COTE01_02_TERRAIN_GENERE.png').convert('RGBA') if zi==0 else key(S/'terrasse_roche_corrigee.png')
    assert terrain.size==orig.size==(w,h) and terrain.tobytes()==orig.tobytes() and sha(terrain.tobytes())==z['terrain_pixels_sha256']
    sky=Image.open(d/f['sky']).convert('RGBA');sk=Image.new('RGBA',(w,h));sk.paste(Image.open(S/'ciel_sans_nuages.png').convert('RGBA').resize((w,C['sky_horizon_px']),Image.Resampling.NEAREST),(0,0));assert sk.tobytes()==sky.tobytes()
    assert wrapped(w,h,0).tobytes()==wrapped(w,h,P).tobytes();assert wrapped(w,h,1).tobytes()==wrapped(w,h,P+1).tobytes();assert wrapped(w,h,-1).tobytes()==wrapped(w,h,P-1).tobytes()
    before=np.asarray(wrapped(w,h,P-1));after=np.asarray(wrapped(w,h,P));assert np.array_equal(before[:,1:],after[:,:-1])
    clouds=Image.open(d/f['clouds_static']).convert('RGBA');assert clouds.tobytes()==wrapped(w,h,0).tobytes()
    ims=[Image.open(d/n) for n in f['sea']];assert len(ims)==8 and all(im.mode=='P' and im.size==(w,h) for im in ims)
    indices=ims[0].tobytes();assert sha(indices)==z['sea_indices_sha256'];assert all(im.tobytes()==indices for im in ims)
    assert len({sha(idat(d/n)) for n in f['sea']})==1,'Pixel data chunks changed: not palette-only animation'
    assert len({sha(im.convert('RGBA').tobytes()) for im in ims})==8
    base=np.array(ims[0].getpalette()).reshape(256,3);cycle=z['cycle_indices'];assert len(cycle)==len(set(cycle))==8 and 0 not in cycle and z['static_background_index'] not in cycle
    for phase,im in enumerate(ims):
        pal=np.array(im.getpalette()).reshape(256,3);expected=base.copy()
        for j,idx in enumerate(cycle):expected[idx]=base[cycle[(j+phase)%8]]
        assert np.array_equal(pal,expected);assert im.info.get('transparency')==ims[0].info.get('transparency')
        assert pal[:z['sea_active_colors']].tolist()==z['sea_palette_frames_rgb'][phase]
    expected8=base.copy()
    for j,idx in enumerate(cycle):expected8[idx]=base[cycle[(j+8)%8]]
    assert np.array_equal(expected8,base)
    sea=Image.new('RGBA',(w,h));old=Image.open(R/'sprites/falaises_cotieres_nues'/z['id']/f'COTE{zi+1:02}_01_MER_01.png').convert('RGBA');sea.paste(old,(0,C['sky_horizon_px']-208))
    assert sea.tobytes()==ims[0].convert('RGBA').tobytes(),'Sea phase zero was quantized or altered'
    full=Image.alpha_composite(Image.alpha_composite(Image.alpha_composite(sky,clouds),sea),terrain);actual=Image.open(d/f'COTEV2_{zi+1:02}_COMPOSITION_00.png').convert('RGBA');assert full.tobytes()==actual.tobytes()
    report['zones'].append({'id':z['id'],'dimensions':[w,h],'cloud_wrap_pixel_differences':0,'terrain_resizes':0,'sea_quantization_pixel_differences':0,'sea_same_index_data_and_IDAT_for_8_phases':True,'only_palette_entries_changed':True,'alpha_and_dominant_background_unchanged':True,'phase_8_equals_phase_0':True,'distinct_sea_phases':8,'composition_pixel_differences':0})
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
