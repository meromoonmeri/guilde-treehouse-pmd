from pathlib import Path
import numpy as np, json, hashlib
from PIL import Image, ImageChops
S=Path(__file__).parent; R=Path('renders/crooked_cavern_waterfall_v2'); F=R/'animation/water'; F.mkdir(parents=True,exist_ok=True)
base=Image.open('renders/crooked_statique_v2/01/composition.png').convert('RGBA').resize((320,240),Image.Resampling.NEAREST)
src=Image.open(S/'waterfall_water_layer_magenta.png').convert('RGBA').resize((320,240),Image.Resampling.NEAREST)
a=np.array(src).astype(np.int32); c=a[0,0,:3]; d=np.sqrt(((a[:,:,:3]-c)**2).sum(2)); a[:,:,3]=np.clip((d-55)*6,0,255).astype(np.uint8); water=Image.fromarray(a.astype(np.uint8))
# Keep a stable alpha mask; animate only internal water pixels, foam and ripples.
frames=[]
for i in range(48):
    w=water.copy(); pix=w.load()
    # PMD-like small vertical flow: water highlights travel downward, geometry remains fixed.
    shift=(i//2)%5-2
    if shift:
        shifted=Image.new('RGBA',w.size,(0,0,0,0)); shifted.alpha_composite(w,(0,shift));
        # retain original silhouette at the top/bottom and avoid moving magenta holes
        w=Image.composite(shifted,w,w.getchannel('A'))
    out=base.copy(); out.alpha_composite(w); frames.append(out)
    # export water-only frame for engine-style layer replacement
    w.save(F/f'{i:02d}.png')
frames[0].save(R/'Crooked_Cavern_Entree_Cascade.png')
frames[0].save(R/'Crooked_Cavern_Entree_Cascade.webp',save_all=True,append_images=frames[1:],duration=80,loop=0,lossless=True,method=6)
manifest={'canvas_px':[320,240],'fps':12.5,'frames':48,'frame_duration_ms':80,'animation_scope':'waterfall stream, foam and pool ripples only','static_base':'Crooked Cavern v2 layout 01','layers':['static composition from crooked_statique_v2/01/composition.png','animation/water/00.png…47.png'],'outputs':['Crooked_Cavern_Entree_Cascade.png','Crooked_Cavern_Entree_Cascade.webp'],'format_note':'PMD-native style pixel animation; WebP preview/export, PNG is frame 00 composition'}
(R/'manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
(R/'hashes.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in list(R.glob('*.png'))},indent=2))
