from pathlib import Path
import json,hashlib,shutil
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'renders/world_map_texture_strict_v9'; LAY=OUT/'layers'; RAW=ROOT/'source/world_map_texture_strict_v9/raws/layout_no_cloud_continent.png'
if OUT.exists(): shutil.rmtree(OUT)
(LAY/'cloud_animation').mkdir(parents=True)
mapim=Image.open(RAW).convert('RGBA'); mapim.save(LAY/'00_map_texture_stricte.png'); mapim.save(OUT/'WorldMap_Texture_Strict_Layout_v9.png')
# Pixel-cloud cover: each zone starts hidden and is revealed by shrinking a coherent cloud bank.
centers=[(125,135),(330,145),(590,185),(155,500),(465,725),(650,560),(170,770),(660,770)]
def cloud_layer(cx,cy,r):
    lay=Image.new('RGBA',mapim.size,(0,0,0,0)); d=ImageDraw.Draw(lay)
    if r < 30: return lay
    # stepped cloud silhouette with warm parchment outline and cool grey underside
    x0,y0=cx-r,cy-r//2; w=2*r; h=r
    d.rectangle((x0+14,y0+22,x0+w-14,y0+h-8),fill=(232,225,190,245),outline=(113,101,70,220),width=3)
    for ox,oy,rr in [(25,22,28),(65,8,35),(110,19,31),(155,10,37),(w-30,25,25)]:
        rr=max(8,int(rr*r/100)); xx=x0+int(ox*r/100); yy=y0+int(oy*r/100)
        d.ellipse((xx-rr,yy-rr,xx+rr,yy+rr),fill=(241,235,207,248),outline=(113,101,70,220),width=3)
    # pixelated shadow bands
    if w > 90:
        d.rectangle((x0+28,y0+h-15,x0+w-34,y0+h-7),fill=(176,166,139,190))
    if w > 150:
        d.rectangle((x0+48,y0+h-22,x0+w-64,y0+h-15),fill=(205,196,167,210))
    return lay
frames=[]
for zone,(cx,cy) in enumerate(centers):
    for step in range(7):
        # first frame blankets the zone; later frames retract smoothly.
        r=int(105-(step*17))
        frame=mapim.copy(); frame.alpha_composite(cloud_layer(cx,cy,r)); p=LAY/'cloud_animation'/f'zone_{zone+1:02d}_reveal_{step:02d}.png'; frame.save(p); frames.append(frame)
# A sequential preview: zone clouds clear one after another.
seq=[]
for step in range(7):
    frame=mapim.copy()
    for i,(cx,cy) in enumerate(centers):
        r=max(0,int(105-step*17)) if i==step else (105 if i>step else 0)
        if r: frame.alpha_composite(cloud_layer(cx,cy,r))
    p=OUT/'cloud_animation'/f'world_reveal_{step:02d}.png'; p.parent.mkdir(exist_ok=True); frame.save(p); seq.append(frame.convert('RGB'))
seq[0].save(OUT/'WorldMap_CloudReveal_Progression_v9.webp',save_all=True,append_images=seq[1:],duration=180,loop=0,lossless=True)
state={'format':'StrictTextureMapWithCloudUnlockAnimation','canvas_px':list(mapim.size),'reference_texture':'source/latest_references/IMG_4989.jpeg','generated_layout':'source/world_map_texture_strict_v9/raws/layout_no_cloud_continent.png','continents':8,'reverie_town':'central tree island','cloud_unlock_zones':8,'animation':'one zone clears at a time with seven-step smooth shrink','static_layers':['layers/00_map_texture_stricte.png']}
(OUT/'world_map_state.json').write_text(json.dumps(state,ensure_ascii=False,indent=2))
files={}
for p in OUT.rglob('*'):
 if p.is_file(): files[str(p.relative_to(OUT))]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
(OUT/'manifest.json').write_text(json.dumps({'canvas_px':list(mapim.size),'continents':8,'texture_strict':True,'animation_frames':len(frames)+len(seq),'files':files},ensure_ascii=False,indent=2))
print('built strict-texture map and progressive cloud reveal animation')
