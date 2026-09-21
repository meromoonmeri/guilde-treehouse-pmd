"""Optional atmosphere only. Terrain layers are never edited or graded.
Sky appears in a separate 504×288 panel, not a fabricated native horizon.
"""
from pathlib import Path
import json, math, sys
import numpy as np
from PIL import Image, ImageDraw
from build import ROOT, SRC, OUT, PREFIX, SIZE, SCENES, dump, sha
sys.path.insert(0,str(ROOT/'source'))
import ciels_valides as climate
V5=ROOT/'renders/ice_arena_northern_sky_v5'
COUNT=96
FPS=15

def build_weather():
    dest=OUT/'atmosphere';dest.mkdir(exist_ok=True)
    skies={}
    sky_size=(504,288)
    boreal=Image.open(V5/'layers/NorthernSkyV5_Sky.png').convert('RGBA').crop((0,0,*sky_size))
    stars=Image.open(V5/'layers/NorthernSkyV5_Stars_phase0.png').convert('RGBA').crop((0,0,*sky_size))
    aurora=Image.open(V5/'aurora_frames/NorthernSkyV5_Aurora_000.png').convert('RGBA').crop((0,0,*sky_size))
    strip=climate.clouds('jour')
    cloudy=climate.sky(sky_size,'jour');cloud_layer=Image.new('RGBA',sky_size)
    cloud_layer.alpha_composite(climate.wrap(strip,sky_size,0))
    cloud_layer.alpha_composite(climate.wrap(strip,sky_size,470),(0,72))
    cloud_layer.save(dest/f'{PREFIX}_Cloudy_Clouds.png')
    for label,im in [('Boreal_Sky',boreal),('Boreal_Stars',stars),('Boreal_Aurora',aurora),('Cloudy_Sky',cloudy)]:
        im.save(dest/f'{PREFIX}_{label}.png')
    skies['boreal']=Image.alpha_composite(Image.alpha_composite(boreal,stars),aurora)
    skies['cloudy']=Image.alpha_composite(cloudy,cloud_layer)
    for mode,im in skies.items(): im.save(dest/f'{PREFIX}_{mode}_Preview.png')
    # Newly authored weather particles, NOT claimed as original PMD animations.
    rng=np.random.default_rng(20260921)
    clusters=[(float(rng.uniform(0,504)),float(rng.uniform(12,540)),float(rng.uniform(0,2*math.pi))) for _ in range(16)]
    flakes=[(float(rng.uniform(0,504)),float(rng.uniform(0,552)),int(rng.integers(1,3))) for _ in range(48)]
    frames={'Powder':[],'Flakes':[]}
    for i in range(COUNT):
        phase=i/COUNT
        powder=Image.new('RGBA',SIZE);d=ImageDraw.Draw(powder)
        for x,y,p in clusters:
            cx=round((x-504*phase)%504);cy=round(y+3*math.sin(2*math.pi*phase+p))
            opacity=round(55+35*(1+math.sin(2*math.pi*phase+p))/2)
            for shift in [-504,0,504]:
                for k in range(5):
                    dx=cx+shift+k*5;dy=cy+((k*7)%5)-2
                    d.line((dx,dy,dx+7+k%3,dy),fill=(248,255,255,opacity),width=1)
                d.ellipse((cx+shift+6,cy-2,cx+shift+23,cy+3),fill=(241,253,255,opacity//3))
        snow=Image.new('RGBA',SIZE);d=ImageDraw.Draw(snow)
        for x,y,n in flakes:
            cx=round((x-12*math.sin(2*math.pi*phase))%504);cy=round((y+552*phase)%552)
            d.rectangle((cx,cy,cx+n-1,cy+n-1),fill=(251,255,255,140 if n==1 else 205))
        for label,im in [('Powder',powder),('Flakes',snow)]:
            folder=dest/label.lower();folder.mkdir(exist_ok=True)
            im.save(folder/f'{PREFIX}_{label}_{i:03d}.png');frames[label].append(im)
    for label,images in frames.items():
        images[0].save(dest/f'{PREFIX}_{label}_Animated.webp',save_all=True,append_images=images[1:],duration=[round((i+1)*1000/FPS)-round(i*1000/FPS) for i in range(COUNT)],loop=0,lossless=True)
    # Static labelled diptychs: native top-down ground is not blended into a fake horizon.
    from build import font
    for s in SCENES:
        terrain=Image.open(OUT/s['id']/f'{PREFIX}_{s["id"]}_Terrain.png').convert('RGBA')
        for mode in skies:
            image=Image.new('RGBA',(504,888),'#10202a');image.alpha_composite(skies[mode],(0,24))
            image.alpha_composite(terrain,(0,336))
            d=ImageDraw.Draw(image)
            d.text((9,4),'CIEL SÉPARÉ · '+('BORÉAL' if mode=='boreal' else 'NUAGEUX'),font=font(12),fill='#e4f3eb')
            d.text((9,316),'TERRAIN NATIF · 1:1 · '+s['title'],font=font(12),fill='#e4f3eb')
            image.save(OUT/s['id']/f'{PREFIX}_{s["id"]}_{mode}_Preview.png')
    dump(dest/'provenance.json',dict(native_terrain_unchanged=True,sky_panel_size=sky_size,sky_panel_not_a_native_horizon=True,clouds=climate.provenance(),boreal_source_commit='ed8fe362e4c9ecb66caf9b9acdc8484897ed3bf5',boreal_note='Existing approved V5: authored blue-black sky, native star motifs, generated/flow-assisted aurora. Cropped to 504×288 without resizing. Not a canonical aurora animation.',boreal_sources=[dict(path=str(p.relative_to(ROOT)),sha256=sha(p)) for p in [V5/'layers/NorthernSkyV5_Sky.png',V5/'layers/NorthernSkyV5_Stars_phase0.png',V5/'aurora_frames/NorthernSkyV5_Aurora_000.png']],particles=dict(origin='Newly authored procedural effect layers, not canonical PMD sprites',frames=COUNT,fps=FPS,period_seconds=COUNT/FPS,powder='Horizontal low streaks, independent from falling flakes',aurora_animated_here=False)))

if __name__=='__main__':
    build_weather()
    print('Separate sky panels and 96-frame weather overlays built.')

def build_animated_previews():
    from PIL import _webp
    def encode(path, size, frames):
        enc=_webp.WebPAnimEncoder(size,0,0,False,9,17,False,False)
        for i,frame in enumerate(frames):
            enc.add(frame.getim(),round(i*1000/30),True,80,100,4)
        assert i==191
        enc.add(None,6400,True,80,100,0)
        path.write_bytes(enc.assemble('','',''))
    dest=OUT/'atmosphere'
    sky=Image.open(dest/f'{PREFIX}_Boreal_Sky.png').convert('RGBA')
    def boreal_frames():
        for i in range(192):
            frame=sky.copy()
            stars=Image.open(V5/f'star_frames/NorthernSkyV5_Stars_{i//3:02d}.png').convert('RGBA').crop((0,0,504,288))
            aura=Image.open(V5/f'aurora_frames/NorthernSkyV5_Aurora_{i:03d}.png').convert('RGBA').crop((0,0,504,288))
            frame.alpha_composite(stars);frame.alpha_composite(aura)
            yield frame
    encode(dest/f'{PREFIX}_boreal_Animated.webp',(504,288),boreal_frames())
    for scene in SCENES:
        mode=scene['weather'];base=OUT/scene['id']/f'{PREFIX}_{scene["id"]}'
        preview=Image.open(str(base)+f'_{mode}_Preview.png').convert('RGBA')
        sky_frames=boreal_frames() if mode=='boreal' else iter([Image.open(dest/f'{PREFIX}_cloudy_Preview.png').convert('RGBA')]*192)
        def compositions():
            for i,skyframe in enumerate(sky_frames):
                frame=preview.copy();frame.paste(skyframe,(0,24))
                for label in ['Powder','Flakes']:
                    effect=Image.open(dest/label.lower()/f'{PREFIX}_{label}_{i//2:03d}.png').convert('RGBA')
                    frame.alpha_composite(effect,(0,336))
                yield frame
        encode(Path(str(base)+'_AnimatedPreview.webp'),(504,888),compositions())
    provenance=json.loads((dest/'provenance.json').read_text())
    provenance['particles']['aurora_animated_here']=True
    provenance['boreal_animation']={'frames':192,'fps':30,'period_seconds':6.4,'method':'All existing V5 aurora poses retained, cropped without resampling or scrolling. V5 star phase advances every three frames. Cloudy sky is static; only its terrain weather moves.'}
    dump(dest/'provenance.json',provenance)

if __name__=='__main__':
    build_animated_previews()
    print('Six animated compositions; boreal sky retains all 192 V5 frames.')
