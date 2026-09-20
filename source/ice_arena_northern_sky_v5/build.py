"""V5: taller sky, regenerated southern entrance, six-pose flow-assisted aurora.
Generated art, not native tiles/official animation. Native climate motifs reused.
Build streams WebP frames to avoid holding every full-scene image in memory.
"""
from pathlib import Path
import sys, json, math, hashlib, io, struct, shutil, zipfile
import xml.etree.ElementTree as ET
import numpy as np
import cv2
from scipy import ndimage
from PIL import Image, ImageDraw, _webp

R=Path(__file__).resolve().parents[2];S=Path(__file__).resolve().parent
O=R/'renders/ice_arena_northern_sky_v5';OLD=R/'renders/ice_arena_northern_sky_v4'
sys.path.insert(0,str(R/'source'))
import ciels_valides as climate
P='NorthernSkyV5';SIZE=(512,864);FX=(512,320);STARS=(512,448)
COUNT=192;FPS=30;STAR_COUNT=64;FLOW_LIMIT=14.0

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,data):p.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def png(im):
    b=io.BytesIO();im.save(b,format='PNG',compress_level=6);return b.getvalue()
def load(p):return Image.open(p).convert('RGBA')
def premult(im):
    a=np.array(im,dtype=np.uint16);a[:,:,:3]=a[:,:,:3]*a[:,:,3:4]//255
    return Image.fromarray(a.astype(np.uint8))
def light_rgba(rgb):
    alpha=rgb.max(2).astype(np.uint16);a=np.zeros((*alpha.shape,4),np.uint8)
    a[:,:,:3]=np.minimum(255,np.rint(rgb.astype(float)*255/np.maximum(alpha[:,:,None],1))).astype(np.uint8)
    a[:,:,3]=alpha;a[alpha==0]=0;return Image.fromarray(a)
def webp_stream(path,size,frames,count,fps,loop=0):
    # Same encoder calls as pinned Pillow WebPImagePlugin._save_all, without
    # materializing its append_images list of 192 complete 512x864 images.
    enc=_webp.WebPAnimEncoder(size,0,loop,False,9,17,False,False)
    n=0
    for n,frame in enumerate(frames,1):
        enc.add(frame.convert('RGBA').getim(),round((n-1)*1000/fps),True,80,100,4)
    assert n==count
    enc.add(None,round(count*1000/fps),True,80,100,0)
    payload=enc.assemble('','','');assert payload;path.write_bytes(payload)
def write_dir(path,frames,cols):
    w,h=frames[0].size;rows=math.ceil(len(frames)/cols)
    atlas=Image.new('RGBA',(cols*w,rows*h))
    for i,im in enumerate(frames):atlas.paste(premult(im),(i%cols*w,i//cols*h))
    raw=png(atlas);path.write_bytes(struct.pack('<q',len(raw))+raw+struct.pack('<4i',w,h,0,len(frames)))
    return {'atlas_size':atlas.size,'frame_size':[w,h],'frames':len(frames),'columns':cols,'GPU_uncompressed_MiB':round(atlas.width*atlas.height*4/1048576,2)}

def prepare_terrain():
    source=O/'bruts/terrain_entry_refined.png';raw=load(source);a=np.array(raw)
    c=a[:,:,:3].astype(np.int16);key=(c[:,:,0]>c[:,:,1]+20)&(c[:,:,2]>c[:,:,1]+20)
    a[key]=0;cut=Image.fromarray(a);box=cut.getbbox();assert box[1]==248
    cut.save(O/'bruts/terrain_keyed.png')
    fitted=cut.crop((0,box[1],raw.width,raw.height)).resize((512,576),Image.Resampling.NEAREST)
    out=Image.new('RGBA',SIZE);out.alpha_composite(fitted,(0,288))
    out.save(O/'layers'/f'{P}_Terrain.png')
    return out,{'raw_size':raw.size,'crop':[0,box[1],raw.width,raw.height],'generated_only_resize':[512,576],'placement':[0,288],'filter':'nearest','aspect_ratio_preserved':False,'raw_sha256':sha(source)}

def prepare_aurora():
    raw=Image.open(O/'bruts/aurora_six_poses.png').convert('RGB');assert raw.size==(1072,992)
    rects=[(x0,y0,x1,y1) for y0,y1 in [(0,328),(333,659),(665,992)] for x0,x1 in [(0,534),(540,1072)]]
    poses=[raw.crop(box).resize(FX,Image.Resampling.NEAREST) for box in rects]
    sheet=Image.new('RGB',(512,320*6))
    for i,im in enumerate(poses):sheet.paste(im,(0,i*320))
    palette=sheet.quantize(colors=64,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    keys=[]
    for i,im in enumerate(poses):
        a=np.array(im.quantize(palette=palette,dither=Image.Dither.NONE).convert('RGB'))
        a[a.max(2)<=10]=0;keys.append(a)
        light_rgba(a).save(O/'keyframes'/f'{P}_Key_{i}.png')
    yy,xx=np.indices((320,512),dtype=np.float32);grid=np.dstack((xx,yy))
    fields=[];stats=[]
    cv2.setNumThreads(1);cv2.setRNGSeed(20260921)
    def flow(a,b):
        # Value-channel contours avoid mistaking cyan/magenta luminance changes
        # for motion. Both directions are independently estimated.
        g1=cv2.GaussianBlur(a.max(2),(0,0),1.0);g2=cv2.GaussianBlur(b.max(2),(0,0),1.0)
        f=cv2.calcOpticalFlowFarneback(g1,g2,None,.5,4,25,5,7,1.5,0)
        f=cv2.GaussianBlur(f,(0,0),1.2)
        magnitude=np.linalg.norm(f,axis=2)
        record={'raw_p95_px':float(np.percentile(magnitude,95)),'raw_max_px':float(magnitude.max()),'clipped_fraction':float((magnitude>FLOW_LIMIT).mean())}
        f*=np.minimum(1,FLOW_LIMIT/np.maximum(magnitude,1e-6))[:,:,None]
        record['limited_max_px']=float(np.linalg.norm(f,axis=2).max())
        return f,record
    for i in range(6):
        fw,s1=flow(keys[i],keys[(i+1)%6]);bw,s2=flow(keys[(i+1)%6],keys[i]);fields.append((fw,bw));stats.append({'pair':[i,(i+1)%6],'forward':s1,'backward':s2})
    def sample(frame):
        phase=(frame%COUNT)/32;i=int(phase);u=phase-i;q=(1-math.cos(math.pi*u))/2
        a=keys[i];b=keys[(i+1)%6];fw,bw=fields[i]
        if u==0:return light_rgba(a)
        posA=grid-q*fw;posB=grid-(1-q)*bw
        aa=cv2.remap(a,posA[:,:,0],posA[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
        bb=cv2.remap(b,posB[:,:,0],posB[:,:,1],cv2.INTER_LINEAR,borderMode=cv2.BORDER_CONSTANT,borderValue=0)
        rgb=np.rint(aa.astype(np.float32)*(1-q)+bb.astype(np.float32)*q).clip(0,255).astype(np.uint8)
        return light_rgba(rgb)
    frames=[]
    for f in range(COUNT):
        im=sample(f);im.save(O/'aurora_frames'/f'{P}_Aurora_{f:03}.png');frames.append(im)
    return frames,keys,sample,{'raw_size':raw.size,'crops':rects,'generated_only_resize':FX,'shared_key_palette':64,'flow_method':'Bidirectional Farneback, Gaussian regularization, value channel, displacement capped to 14px, inverse warps + eased blend','flow_stats':stats,'subpixel_sampling':'bilinear, generated aurora only','key_interval_frames':32,'max_warp_coordinate_step_bound_px':FLOW_LIMIT*math.pi/(2*32),'raw_sha256':sha(O/'bruts/aurora_six_poses.png')}

def prepare_stars(terrain):
    src=climate.load('astres_nuit_native');sa=np.array(src)[:,:240]
    labels,_=ndimage.label(sa[:,:,3]>0);glyphs=[];boxes=[]
    for idx,sl in enumerate(ndimage.find_objects(labels),1):
        if sl is None:continue
        ys,xs=sl;w=xs.stop-xs.start;h=ys.stop-ys.start
        if w>4 or h>4:continue
        a=sa[sl].copy();a[labels[sl]!=idx]=0
        if a[:,:,3].max()<110:continue
        glyphs.append(a);boxes.append([xs.start,ys.start,w,h])
    rng=np.random.default_rng(20260921);placements=[];mask=np.array(terrain)[:,:,3]
    for _ in range(60000):
        if len(placements)==300:break
        x=int(rng.integers(3,505));y=int(rng.integers(3,426))
        if mask[y:y+5,x:x+5].any() or any((x-p['x'])**2+(y-p['y'])**2<64 for p in placements):continue
        placements.append({'x':x,'y':y,'glyph':int(rng.integers(len(glyphs))),'phase':float(rng.uniform(0,2*math.pi)),'frequency':int(rng.integers(1,4))})
    assert len(placements)==300
    frames=[]
    for f in range(STAR_COUNT):
        im=Image.new('RGBA',STARS)
        for p in placements:
            a=glyphs[p['glyph']].copy();light=.58+.42*(.5+.5*math.sin(2*math.pi*f/64*p['frequency']+p['phase']))
            a[:,:,3]=np.rint(a[:,:,3].astype(float)*(255/float(a[:,:,3].max()))*light).astype(np.uint8);a[a[:,:,3]==0]=0
            im.alpha_composite(Image.fromarray(a),(p['x'],p['y']))
        frames.append(im);im.save(O/'star_frames'/f'{P}_Stars_{f:02}.png')
    dump(O/'star_placements.json',{'glyph_rects':boxes,'placements':placements,'source':str((climate.REF/'source__falaise__astres_nuit_native.png').relative_to(R)),'new_layout_and_alpha':True})
    return frames

def build():
    for d in ['layers','keyframes','aurora_frames','star_frames','review','pmdo/Content/BG']:(O/d).mkdir(parents=True,exist_ok=True)
    checks=[]
    def check(name,result,detail=None):
        assert result,name
        checks.append({'check':name,'status':'PASS','detail':detail})
    terrain,terrain_info=prepare_terrain();t=np.array(terrain);opaque=t[:,:,3]==255
    check('New sky header is 288px, vs 144px in V4',not t[:288,:,3].any() and t[288:,:,3].any())
    tc=t[:,:,:3].astype(np.int16)
    check('Terrain alpha keyed, no magenta visible',not np.any((tc[:,:,0]>tc[:,:,1]+20)&(tc[:,:,2]>tc[:,:,1]+20)&opaque))
    lane=t[584:864,224:288,:3];median=np.median(lane.reshape(-1,3),axis=0)
    check('Central strip is opaque with continuous snow color (sample, not topology proof)',bool(opaque[584:864,224:288].all()) and float(np.abs(lane.astype(float)-median).max())<=16,{'visible_sample_rect':[224,584,288,864],'RGB_max_deviation':float(np.abs(lane.astype(float)-median).max()),'not_collision_validation':True})
    sky=Image.new('RGBA',SIZE,tuple(int(x) for x in np.array(climate.load('ciel_nuit_native'))[0,0]));sky.save(O/'layers'/f'{P}_Sky.png')
    auroras,keys,sample,aurora_info=prepare_aurora()
    check('192 samples at 30Hz, 3x V4 temporal sampling',len(auroras)==192 and COUNT/FPS==6.4)
    check('Every generated key pose is reached exactly',all(auroras[i*32].tobytes()==light_rgba(keys[i]).tobytes() for i in range(6)))
    check('Cyclic sample 192 equals sample zero',sample(192).tobytes()==sample(0).tobytes())
    check('Warp coordinate speed bounded below 0.7 px per frame',aurora_info['max_warp_coordinate_step_bound_px']<.7)
    check('All flow vectors are bounded to 14px',all(s[d]['limited_max_px']<=14.00001 for s in aurora_info['flow_stats'] for d in ['forward','backward']))
    check('Aurora covers both edges in every frame',all(np.array(im)[:,:24,3].max()>64 and np.array(im)[:,-24:,3].max()>64 for im in auroras))
    temporal=[]
    for i in range(COUNT):
        a=np.array(premult(auroras[i]));b=np.array(premult(auroras[(i+1)%COUNT]));active=(a[:,:,3]>10)|(b[:,:,3]>10)
        delta=np.abs(a[:,:,:3].astype(float)-b[:,:,:3].astype(float))
        temporal.append({'from':i,'to':(i+1)%COUNT,'mean_active_RGB_delta':float(delta[active].mean()),'max_RGB_delta':float(delta.max())})
    check('Loop seam is not an outlier in frame-to-frame RGB change',temporal[-1]['mean_active_RGB_delta']<=max(r['mean_active_RGB_delta'] for r in temporal[:-1]))
    dump(O/'temporal_audit.json',{'type':'premultiplied pixel changes, not perceptual/game validation','samples':temporal,'warp_coordinate_step_bound':aurora_info['max_warp_coordinate_step_bound_px']})
    stars=prepare_stars(terrain)
    check('300 fixed star placements, native RGB motifs',len(json.loads((O/'star_placements.json').read_text())['placements'])==300)
    strip=Image.new('RGBA',(1440,448));ca=np.array(climate.clouds('nuit'));ca[:,:,3]=np.rint(ca[:,:,3].astype(float)*.30).astype(np.uint8);ca[ca[:,:,3]==0]=0
    strip.paste(Image.fromarray(ca),(0,224));strip.save(O/'layers'/f'{P}_CloudStrip.png')
    def clouds(time=0):return climate.wrap(strip,STARS,int(time*2))
    check('Cloud wrap remains 720s and independent of aurora loop',clouds(0).tobytes()==clouds(720).tobytes() and clouds(0).tobytes()!=clouds(6.4).tobytes())
    for name,im in [('Aurora_phase0',auroras[0]),('Stars_phase0',stars[0]),('Clouds_phase0',clouds())]:im.save(O/'layers'/f'{P}_{name}.png')
    def scene(f,cloud_time=0):
        im=sky.copy();im.alpha_composite(stars[(f%COUNT)//3]);im.alpha_composite(auroras[f%COUNT]);im.alpha_composite(clouds(cloud_time));im.alpha_composite(terrain);return im
    initial=scene(0);initial.save(O/'composition.png')
    def checked_scenes():
        for f in range(COUNT):
            im=scene(f);assert np.array_equal(np.array(im)[opaque],t[opaque]);yield im
    webp_stream(O/'composition_loop.webp',SIZE,checked_scenes(),COUNT,FPS)
    check('Terrain remains stationary in every output phase',True)
    webp_stream(O/'aurora_loop.webp',FX,iter(auroras),COUNT,FPS)
    webp_stream(O/'stars_loop.webp',STARS,iter(stars),STAR_COUNT,10)
    for name,expected in [('composition_loop.webp',6400),('aurora_loop.webp',6400),('stars_loop.webp',6400)]:
        movie=Image.open(O/name);total=0
        for f in range(movie.n_frames):movie.seek(f);movie.load();total+=movie.info['duration']
        check('Exact animation duration: '+name,total==expected and movie.info['loop']==0,{'encoded_frames':movie.n_frames,'duration_ms':total})
    # All images remain at their actual pixel scale in the inspection boards.
    board=Image.new('RGB',(1024,248),'#0e1b30');dr=ImageDraw.Draw(board)
    dr.text((12,8),'V4 - ancienne entree',fill='white');dr.text((524,8),'V5 - neige et berges raccordees',fill='white')
    board.paste(load(OLD/'composition.png').crop((0,496,512,720)),(0,24));board.paste(initial.crop((0,640,512,864)),(512,24));board.save(O/'review/entry_before_after.png')
    contact=Image.new('RGB',(1536,688),'#090f2f');draw=ImageDraw.Draw(contact)
    for i in range(6):
        x=i%3*512;y=i//3*344;im=Image.new('RGBA',FX,(9,15,47,255));im.alpha_composite(auroras[i*32]);contact.paste(im,(x,y+24));draw.text((x+8,y+5),f'Pose {i+1} / phase {i*32}',fill='white')
    contact.save(O/'review/keyposes.png')
    entries=[('Sky',sky),('Stars',stars[0]),('Aurora',auroras[0]),('Clouds',clouds()),('Terrain_corrected',terrain)]
    root=ET.Element('image',w='512',h='864',name='Northern sky V5 - corrected entry',version='0.0.3');stack=ET.SubElement(root,'stack')
    with zipfile.ZipFile(O/f'{P}_layers.ora','w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
        for i,(name,im) in reversed(list(enumerate(entries))):
            path=f'data/layer{i}.png';z.writestr(path,png(im));ET.SubElement(stack,'layer',name=name,src=path,x='0',y='0',opacity='1.0',visibility='visible',**{'composite-op':'svg:src-over'})
        z.writestr('stack.xml',ET.tostring(root,encoding='utf-8',xml_declaration=True));z.writestr('mergedimage.png',png(initial))
    composed=Image.new('RGBA',SIZE)
    for _,im in entries:composed.alpha_composite(im)
    check('Five ORA layers recompose exactly',composed.tobytes()==initial.tobytes())
    native_dir={};bg=O/'pmdo/Content/BG'
    for name,frames,cols in [('Sky',[sky],1),('Stars',stars,8),('Aurora',auroras,16),('CloudStrip',[strip],1),('Terrain',[terrain],1)]:
        p=bg/f'{P}_{name}.dir';native_dir[name]=write_dir(p,frames,cols)
        data=p.read_bytes();length,=struct.unpack_from('<q',data);w,h,rotate,total=struct.unpack_from('<4i',data,8+length)
        atlas=Image.open(io.BytesIO(data[8:8+length])).convert('RGBA');assert total==len(frames) and rotate==0
        for i,im in enumerate(frames):
            assert atlas.crop((i%cols*w,i//cols*h,(i%cols+1)*w,(i//cols+1)*h)).tobytes()==premult(im).tobytes()
        check('Native-format container and all slots: '+name,True)
    recipe=[]
    for name in ['Sky','Stars','Aurora','CloudStrip','Terrain']:
        recipe.append({'$type':'RogueEssence.Dungeon.MapBG, RogueEssence','MapLoc':{'X':0,'Y':0},'BGAnim':{'AnimIndex':P+'_'+name,'FrameTime':2 if name=='Aurora' else 6 if name=='Stars' else 1,'StartFrame':0,'EndFrame':191 if name=='Aurora' else 63 if name=='Stars' else 0,'AnimDir':-1,'Alpha':255,'AnimFlip':0},'BGMovement':{'X':-2 if name=='CloudStrip' else 0,'Y':0},'Parallax':'1, 1','RepeatX':name=='CloudStrip','RepeatY':False})
    dump(O/'pmdo/placement_recipe.json',{'schema':'recipe_NOT_a_Ground','render_order':recipe,'GPU_warning':'Aurora texture 8192x3840 =120MiB; requires hardware test. Use PNG/ORA for art review first.','runtime_tested':False,'collisions_provided':False})
    timeline=[{'frame':f,'key_pair':[f//32,(f//32+1)%6],'pair_progress':(f%32)/32,'blend':(1-math.cos(math.pi*(f%32)/32))/2,'ticks':2,'ms':round((f+1)*1000/FPS)-round(f*1000/FPS),'stars_frame':f//3,'aurora':f'aurora_frames/{P}_Aurora_{f:03}.png'} for f in range(COUNT)]
    dump(O/'timeline.json',{'frames':COUNT,'fps':FPS,'nominal_seconds':6.4,'samples':timeline})
    manifest={'date':'2026-09-21','canvas':SIZE,'old_canvas':[512,720],'sky_header_height':288,'old_sky_header_height':144,'terrain':terrain_info,'terrain_origin':'GENERATED correction, not native tiles; entire new terrain is an editable single layer',
              'aurora':aurora_info,'aurora_origin':'Six generated key poses, 192 computed bidirectional flow intermediates; not official frames or a physical simulation',
              'aurora_frames':COUNT,'aurora_fps':FPS,'period_s':6.4,'old_aurora_fps':10,'stars':{'count':300,'frames':64,'fps':10,'new_placements_and_alpha':True,'native_RGB_unscaled':True},
              'climate':climate.provenance(),'clouds':{'native_strip':[1440,448],'offset_y':224,'opacity':.30,'speed_px_s':-2,'period_s':720,'combined_period_s':1440},
              'webp_scene_clouds':'fixed for a genuinely looping 6.4s preview; live viewer/recipe have continuous drifting clouds',
              'native_dir':native_dir,'native_GPU_validated':False,'collision_validated':False,'art_approval':'pending','old_versions_untouched':True}
    dump(O/'manifest.json',manifest);dump(O/'audit.json',{'status':'PASS','count':len(checks),'checks':checks,'GPU_tested':False,'collision_tested':False})
    data={'prefix':P,'frames':COUNT,'fps':FPS,'period':6.4,'terrain':f'layers/{P}_Terrain.png','sky':f'layers/{P}_Sky.png','clouds':f'layers/{P}_CloudStrip.png','aurora_movie':'aurora_loop.webp','stars_movie':'stars_loop.webp'}
    (O/'index.html').write_text((S/'viewer.html').read_text().replace('__DATA__',json.dumps(data)))
    print(f'{len(checks)} build checks PASS. Six generated poses, 192 frames at30Hz, corrected entrance. No native GPU/collision test.')
if __name__=='__main__':build()
