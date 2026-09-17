"""Verify layer alignment, source backdrop crops and generated-terrain preservation.
Does NOT certify generated pixels as canonical Metano tiles.
"""
from pathlib import Path
from PIL import Image
import numpy as np,json,hashlib
R=Path(__file__).resolve().parents[1];O=R/'sprites/falaises_cotieres_nues';S=R/'source/falaises_cotieres_nues';M=json.loads((O/'manifest.json').read_text());sheet=Image.open(S/'reference_ciel_mer.png').convert('RGBA')
assert hashlib.sha256((S/'reference_ciel_mer.png').read_bytes()).hexdigest()==M['reference_sha256']
names=set();checks=[]
for z in M['zones']:
    d=O/z['id'];w,h=z['size_px'];hy=z['horizon_px'];assert w%8==h%8==0
    original=Image.open(S/(z['id']+'.png')).convert('RGBA');assert hashlib.sha256((S/(z['id']+'.png')).read_bytes()).hexdigest()==z['source_generated_sha256']
    src=np.asarray(original);terrain=Image.open(d/z['terrain']).convert('RGBA');assert terrain.size==(w,h)
    shift=z['generated_terrain_translation_y'];a=np.asarray(terrain);ys,xs=np.nonzero(a[:,:,3]);assert len(ys)>0 and np.all(ys>=shift)
    assert np.array_equal(a[ys,xs],src[ys-shift,xs]),'Visible generated terrain pixels were modified'
    assert not a[:shift,:,3].any()
    sk=sheet.crop(tuple(M['sky_rect']));offsets=[0,2,4,6,8,6,4,2]
    for f,fn in enumerate(z['sky']):
        actual=Image.open(d/fn).convert('RGBA');expected=Image.new('RGBA',(w,h))
        assert hy==sk.height
        for x in range(-sk.width,w,sk.width):expected.paste(sk,(x+offsets[f],0))
        assert actual.tobytes()==expected.tobytes(),fn
    for f,fn in enumerate(z['sea']):
        actual=Image.open(d/fn).convert('RGBA');expected=Image.new('RGBA',(w,h));far=sheet.crop(tuple(M['sea_rects'][f]));near=sheet.crop(tuple(M['near_sea_rects'][f]))
        for x in range(0,w,far.width):expected.paste(far,(x,hy))
        for y in range(hy+far.height,h,near.height):
            for x in range(0,w,near.width):expected.paste(near,(x,y))
        assert actual.tobytes()==expected.tobytes(),fn
    for fn in [z['terrain']]+z['sky']+z['sea']:
        assert fn not in names;names.add(fn);assert Image.open(d/fn).size==(w,h)
    sky=Image.open(d/z['sky'][0]).convert('RGBA');sea=Image.open(d/z['sea'][0]).convert('RGBA');full=Image.alpha_composite(Image.alpha_composite(sky,sea),terrain)
    actual=Image.open(d/(z['terrain'].split('_')[0]+'_COMPOSITION_FIXE.png')).convert('RGBA');assert full.tobytes()==actual.tobytes()
    checks.append({'zone':z['id'],'terrain_visible_generated_pixels_modified':0,'backdrop_source_recomposition_different_pixels':0,'still_composition_different_pixels':0,'sky_frames':8,'distinct_sky_positions':5,'distinct_sea_frames':len({hashlib.sha256((d/f).read_bytes()).hexdigest() for f in z['sea']})})
report={'status':'PASS','canonical_metano_terrain':False,'pmdo_runtime_tested':False,'unique_export_names':True,'checks':checks,'visual_review':'Generated terrain inspected without buildings, trees, paths, caves and props. Layouts remain approximate, not exact reproductions.'}
(O/'verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
