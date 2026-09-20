"""Northern sky proposal: two generated panoramic poses, controlled inbetweens,
native-source star motifs and approved Guilde/Sharpedo clouds. V3 terrain untouched.
No claim of official animation frames or engine/GPU validation.
"""
from pathlib import Path
import sys, io, json, math, hashlib, shutil, struct, zipfile, base64
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage
R = Path(__file__).resolve().parents[2]
S = Path(__file__).resolve().parent
O = R / 'renders/ice_arena_northern_sky_v4'
sys.path.insert(0, str(R / 'source'))
import ciels_valides as cv
P = 'NorthernSkyV4'
N = 64
SIZE = (512, 720)
FX = (512, 240)
STAR_SIZE = (512, 288)


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def png(im):
    b=io.BytesIO(); im.save(b,format='PNG'); return b.getvalue()
def dump(p,obj): p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def copy(src,dst): shutil.copyfile(src,dst); return sha(src)
def rgba_light(rgb):
    """Remove black matte by treating generated RGB as premultiplied light.
    Not native pixel extraction. The same conversion is used for every frame.
    """
    a=rgb.max(axis=2).astype(np.uint16)
    out=np.zeros((*a.shape,4),np.uint8)
    out[:,:,:3]=np.minimum(255,np.rint(rgb.astype(float)*255/np.maximum(a[:,:,None],1))).astype(np.uint8)
    out[:,:,3]=a.astype(np.uint8); out[a==0]=0
    return Image.fromarray(out)
def premult(im):
    a=np.array(im,dtype=np.uint16); a[:,:,:3]=a[:,:,:3]*a[:,:,3:4]//255
    return Image.fromarray(a.astype(np.uint8))
def write_dir(path,frames,cols):
    w,h=frames[0].size;rows=math.ceil(len(frames)/cols)
    atlas=Image.new('RGBA',(cols*w,rows*h))
    for i,im in enumerate(frames):atlas.paste(premult(im),(i%cols*w,i//cols*h))
    raw=png(atlas);path.write_bytes(struct.pack('<q',len(raw))+raw+struct.pack('<4i',w,h,0,len(frames)))
    return {'size':atlas.size,'frame_size':[w,h],'frames':len(frames),'columns':cols}

def build():
    for d in ['layers','keyframes','aurora_frames','star_frames','review','pmdo/Content/BG']:(O/d).mkdir(parents=True,exist_ok=True)
    checks=[]
    def check(name,test):
        assert test,name
        checks.append({'check':name,'status':'PASS'})
    old=R/'renders/ice_arena_aurora_coherent_v3/layers/IceAuroraCoherentV3_Terrain.png'
    terrain_path=O/'layers'/f'{P}_Terrain.png'; terrain_hash=copy(old,terrain_path)
    terrain=Image.open(terrain_path).convert('RGBA'); ta=np.asarray(terrain)
    check('V3 terrain preserved byte-for-byte',sha(terrain_path)==terrain_hash)
    sky_source=cv.sky(SIZE,'nuit');sky_a=np.asarray(sky_source)
    # A uniform native night color avoids extending extraction/dither artifacts
    # into visible bands. The aurora and stars supply the sky's spatial detail.
    sky=Image.new('RGBA',SIZE,tuple(int(v) for v in sky_a[0,0]))
    sky.save(O/'layers'/f'{P}_Sky.png')
    check('Sky RGBs come only from approved Guilde/Sharpedo night sheet',set(map(tuple,np.asarray(sky).reshape(-1,4)))<=set(map(tuple,sky_a.reshape(-1,4))))

    raw=Image.open(O/'bruts/aurora_two_keyframes.png').convert('RGB')
    assert raw.size==(1072,992), 'Reinspect panel divider if raw changes'
    rects=[(0,0,1072,493),(0,500,1072,992)]
    resized=[raw.crop(rect).resize(FX,Image.Resampling.NEAREST) for rect in rects]
    palette_sheet=Image.new('RGB',(512,480))
    for i,im in enumerate(resized):palette_sheet.paste(im,(0,i*240))
    shared_palette=palette_sheet.quantize(colors=64,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    keys=[]
    for label,im in zip('AB',resized):
        a=np.array(im.quantize(palette=shared_palette,dither=Image.Dither.NONE).convert('RGB'));a[a.max(axis=2)<=10]=0
        keys.append(a)
        rgba_light(a).save(O/'keyframes'/f'{P}_Aurora_{label}.png')
    check('Both generated poses reach left and right sky edges',all((a[:,:24].max(2)>70).any() and (a[:,-24:].max(2)>70).any() for a in keys))
    check('Generated separator is excluded from both crops',rects[0][3]==493 and rects[1][1]==500)
    def aurora(f):
        q=(1-math.cos(2*math.pi*(f%N)/N))/2
        light=np.rint(keys[0].astype(float)*(1-q)+keys[1].astype(float)*q).astype(np.uint8)
        return rgba_light(light)
    auroras=[aurora(f) for f in range(N)]
    check('Closed aurora loop: sample 64 exactly equals sample 0',aurora(N).tobytes()==aurora(0).tobytes())
    seam=np.abs(np.asarray(premult(auroras[-1])).astype(int)-np.asarray(premult(auroras[0])).astype(int)).max()
    check('Aurora seam has at most two premultiplied levels of change',seam<=2)
    check('Panoramic alpha spans entire 512px width at all phases',all(np.asarray(im)[:,:24,3].max()>70 and np.asarray(im)[:,-24:,3].max()>70 for im in auroras))

    # Small original star motifs, never rescaled/rotated/recolored. New positions
    # and alpha scintillation are authored and explicitly not a native star cycle.
    source=cv.load('astres_nuit_native');sa=np.array(source)[:,:240]
    labels,n=ndimage.label(sa[:,:,3]>0)
    sprites=[];glyphs=[]
    for lab,box in enumerate(ndimage.find_objects(labels),1):
        if box is None:continue
        ys,xs=box;w=xs.stop-xs.start;h=ys.stop-ys.start
        if w<=4 and h<=4:
            a=sa[ys,xs].copy();a[labels[ys,xs]!=lab]=0
            if a[:,:,3].max()<110:continue  # faint extraction specks are not useful bright stars
            sprites.append(Image.fromarray(a));glyphs.append([xs.start,ys.start,w,h])
    check('Small native star motifs available',len(sprites)>=8)
    rng=np.random.default_rng(20260920)
    stars=[];attempts=0
    while len(stars)<190 and attempts<40000:
        attempts+=1;x=int(rng.integers(4,505));y=int(rng.integers(3,270))
        if ta[y:y+5,x:x+5,3].any():continue
        if any((x-s['x'])**2+(y-s['y'])**2<64 for s in stars):continue
        stars.append({'x':x,'y':y,'glyph':int(rng.integers(len(sprites))),'phase':float(rng.uniform(0,2*math.pi)), 'frequency':int(rng.integers(1,4))})
    check('190 spaced visible-sky star placements',len(stars)==190)
    def star_frame(f):
        out=Image.new('RGBA',STAR_SIZE)
        for s in stars:
            a=np.array(sprites[s['glyph']]);factor=0.58+0.42*(0.5+0.5*math.sin(2*math.pi*(f%N)/N*s['frequency']+s['phase']))
            a[:,:,3]=np.rint(a[:,:,3].astype(float)*(255/float(a[:,:,3].max()))*factor).astype(np.uint8);a[a[:,:,3]==0]=0
            out.alpha_composite(Image.fromarray(a),(s['x'],s['y']))
        return out
    star_frames=[star_frame(f) for f in range(N)]
    check('Star loop is closed without position changes',star_frame(N).tobytes()==star_frames[0].tobytes())
    check('Star scintillation varies across the cycle',len({hashlib.sha256(i.tobytes()).hexdigest() for i in star_frames})>32)
    dump(O/'star_placements.json',{'source':str((cv.REF/'source__falaise__astres_nuit_native.png').relative_to(R)), 'glyph_rectangles':glyphs,'placements':stars,'authored_alpha_cycle':True,'peak_alpha_normalization':255})

    strip=Image.new('RGBA',(1440,288));clouds=cv.clouds('nuit')
    ca=np.array(clouds);ca[:,:,3]=np.rint(ca[:,:,3].astype(float)*0.30).astype(np.uint8);ca[ca[:,:,3]==0]=0
    strip.paste(Image.fromarray(ca),(0,80));strip.save(O/'layers'/f'{P}_CloudStrip.png')
    def cloud_at(seconds):return cv.wrap(strip,STAR_SIZE,int(seconds*2))
    check('Cloud strip wraps continuously at 720 seconds',cloud_at(0).tobytes()==cloud_at(720).tobytes())
    check('Clouds are not falsely frozen in continuous playback',cloud_at(0).tobytes()!=cloud_at(10).tobytes())
    cloud_at(0).save(O/'layers'/f'{P}_Clouds_phase0.png')
    auroras[0].save(O/'layers'/f'{P}_Aurora_phase0.png');star_frames[0].save(O/'layers'/f'{P}_Stars_phase0.png')
    for f in range(N):
        auroras[f].save(O/'aurora_frames'/f'{P}_Aurora_{f:02}.png')
        star_frames[f].save(O/'star_frames'/f'{P}_Stars_{f:02}.png')
    def compose(f,seconds=0):
        out=sky.copy();out.alpha_composite(star_frames[f%N]);out.alpha_composite(auroras[f%N]);out.alpha_composite(cloud_at(seconds));out.alpha_composite(terrain);return out
    scenes=[compose(f) for f in range(N)]
    scenes[0].save(O/'composition.png')
    scenes[0].save(O/'composition_loop.webp',save_all=True,append_images=scenes[1:],duration=100,loop=0,lossless=True,method=4)
    excerpt=[compose(f,f*.1) for f in range(80)]
    excerpt[0].save(O/'composition_clouds_excerpt.webp',save_all=True,append_images=excerpt[1:],duration=100,loop=1,lossless=True,method=4)
    opaque=ta[:,:,3]==255
    check('All terrain pixels unchanged in every scene and cloud sample',all(np.array_equal(np.asarray(im)[opaque],ta[opaque]) for im in scenes+excerpt))
    check('Sky occupies whole map width, no old 264px central window',sky.size==SIZE and all(im.size==FX for im in auroras))
    durations={}
    for filename,expected,loop in [('composition_loop.webp',6400,0),('composition_clouds_excerpt.webp',8000,1)]:
        movie=Image.open(O/filename);total=0
        for f in range(movie.n_frames):movie.seek(f);movie.load();total+=movie.info['duration']
        check(filename+' duration/loop flags',total==expected and movie.info['loop']==loop)
        durations[filename]={'ms':total,'loop':loop,'encoded_frames':movie.n_frames}
    board=Image.new('RGB',(2048,528),'#09132b');draw=ImageDraw.Draw(board)
    for i,f in enumerate(range(0,64,8)):
        x=i%4*512;y=i//4*264
        draw.text((x+8,y+5),f'Phase {f:02}/64',fill='white')
        b=sky.crop((0,0,512,240));b.alpha_composite(auroras[f]);board.paste(b,(x,y+24))
    board.save(O/'review/aurora_cycle.png')

    layers=[('Sky',Image.open(O/'layers'/f'{P}_Sky.png')),('Stars',star_frames[0]),('Aurora',auroras[0]),('Clouds',cloud_at(0)),('Terrain_V3_unchanged',terrain)]
    root=ET.Element('image',w='512',h='720',version='0.0.3',name='Northern sky V4');stack=ET.SubElement(root,'stack')
    with zipfile.ZipFile(O/f'{P}_layers.ora','w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
        for i,(name,im) in reversed(list(enumerate(layers))):
            path=f'data/layer{i}.png';z.writestr(path,png(im));ET.SubElement(stack,'layer',name=name,src=path,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
        z.writestr('stack.xml',ET.tostring(root,encoding='utf-8',xml_declaration=True));z.writestr('mergedimage.png',png(scenes[0]))
    composed=Image.new('RGBA',SIZE)
    for _,im in layers:composed.alpha_composite(im)
    check('Five ORA layers recompose phase zero exactly',composed.tobytes()==scenes[0].tobytes())

    dirs={};path=O/'pmdo/Content/BG'
    for name,frames,cols in [('Sky',[sky],1),('Stars',star_frames,8),('Aurora',auroras,8),('CloudStrip',[strip],1),('Terrain',[terrain],1)]:
        dest=path/f'{P}_{name}.dir';dirs[name]=write_dir(dest,frames,cols)
        data=dest.read_bytes();length,=struct.unpack_from('<q',data);w,h,rotation,count=struct.unpack_from('<4i',data,8+length)
        atlas=Image.open(io.BytesIO(data[8:8+length])).convert('RGBA')
        assert (w,h)==frames[0].size and rotation==0 and count==len(frames)
        for i,im in enumerate(frames):
            assert atlas.crop((i%cols*w,i//cols*h,i%cols*w+w,i//cols*h+h)).tobytes()==premult(im).tobytes()
        check('PMDO container and every frame slot: '+name,True)
    recipe=[]
    for name in ['Sky','Stars','Aurora','CloudStrip','Terrain']:
        recipe.append({'$type':'RogueEssence.Dungeon.MapBG, RogueEssence','MapLoc':{'X':0,'Y':0}, 'BGAnim':{'AnimIndex':P+'_'+name,'FrameTime':6 if name in ['Stars','Aurora'] else 1,'StartFrame':0,'EndFrame':63 if name in ['Stars','Aurora'] else 0,'AnimDir':-1,'Alpha':255,'AnimFlip':0},'BGMovement':{'X':-2 if name=='CloudStrip' else 0,'Y':0},'Parallax':'1, 1','RepeatX':name=='CloudStrip','RepeatY':False})
    dump(O/'pmdo/placement_recipe.json',{'schema':'placement_recipe_NOT_a_Ground','render_back_to_front':recipe,'runtime_tested':False,'collisions_provided':False})
    metadata={'canvas':SIZE,'terrain_source':str(old.relative_to(R)),'terrain_sha256':terrain_hash,'terrain_changed':False,
              'aurora_origin':'TWO GENERATED panoramic keyframes referenced to original native poses; not official frames or native pixel-identical artwork',
              'raw_sha256':sha(O/'bruts/aurora_two_keyframes.png'),'raw_size':raw.size,'generated_panel_crops':rects,'generated_only_resize':FX,'filter':'nearest',
              'shared_generated_key_palette_colors':64,'palette_note':'Shared median-cut palette for the two generated poses only, no dithering; not a native-palette certification',
              'black_key':'max channel <=10 removed on keyframes; light unpremultiplied to alpha','animation':'64 computed cosine crossfade frames A -> B -> A, same XY, no scrolling/warping/optical flow',
              'frame_ticks':6,'aurora_star_period_seconds':6.4,'native_timing_claimed':False,'star_count':len(stars),'star_motion':'authored alpha only, native RGB motifs at fixed new positions; peak alpha normalized to 255 then modulated 0.58..1',
              'clouds':{'source':cv.provenance(),'opacity_factor':0.30,'offset_y':80,'movement_px_s':[-2,0],'strip_size':[1440,288],'period_seconds':720},
              'all_effects_common_period_seconds':1440,'preview_files':durations,'loop_preview_clouds':'fixed, to avoid false wrap reset at 6.4s','excerpt':'8s continuous clouds, single play; not seamless loop',
              'sky':'Uniform dark color sampled at (0,0) from approved Guilde/Sharpedo night sky; no new RGBs',
              'dir_atlases':dirs,'GPU_tested':False,'collisions_tested':False,'art_approval':'pending'}
    dump(O/'manifest.json',metadata)
    dump(O/'audit.json',{'status':'PASS','count':len(checks),'checks':checks,'native_engine_or_GPU_test':False})
    data={'aurora':[f'aurora_frames/{P}_Aurora_{f:02}.png' for f in range(N)],
          'stars':[f'star_frames/{P}_Stars_{f:02}.png' for f in range(N)],
          'sky':f'layers/{P}_Sky.png','terrain':f'layers/{P}_Terrain.png','clouds':f'layers/{P}_CloudStrip.png'}
    dump(O/'timeline.json',{'frames':64,'frame_ticks':6,'seconds':6.4,'native_cycle':False,'samples':[{'frame':f,'ticks':6,'weight_A':round((1+math.cos(2*math.pi*f/64))/2,8),'weight_B':round((1-math.cos(2*math.pi*f/64))/2,8),'aurora':data['aurora'][f],'stars':data['stars'][f]} for f in range(N)]})
    (O/'index.html').write_text((S/'viewer.html').read_text().replace('__DATA__',json.dumps(data)))
    print(f'{len(checks)} checks PASS. Generated sky extension; V3 terrain unchanged. No GPU/gameplay certification.')

if __name__=='__main__':build()
