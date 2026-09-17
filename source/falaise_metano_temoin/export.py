"""Chroma export only: never recolor retained generated terrain pixels."""
from pathlib import Path
import hashlib,json
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'renders/falaise_metano_temoin'
src=P/'01_crete_sillage_magenta.png'
im=Image.open(src).convert('RGBA');a=np.array(im)
key=(a[:,:,0]>210)&(a[:,:,1]<60)&(a[:,:,2]>210)
flat=a.copy();flat[key]=[255,0,255,255]
Image.fromarray(flat).save(P/'01_crete_sillage_fond_uniforme.png',optimize=True)
cut=a.copy();cut[key]=0
Image.fromarray(cut).save(P/'01_crete_sillage_transparent.png',optimize=True)
assert np.array_equal(cut[~key],a[~key])
assert np.all(cut[key]==0)
files=['source/falaise_metano_temoin/01_layout_metano_magenta.png','source/falaises_generees/reference_canonique.png']
report={'method':'existing layout + authoritative Metano rock and grass reference -> image generator on magenta -> chroma extraction','generated_image':str(src.relative_to(ROOT)),'size':im.size,'reference_files':[{ 'path':f,'sha256':hashlib.sha256((ROOT/f).read_bytes()).hexdigest()} for f in files],'transparent_pixels':int(key.sum()),'retained_terrain_pixel_changes_during_export':0,'image_resampled':False,'native_tile_equality_claimed':False,'all_cliff_joins_certified_seamless':False,'native_mod_modified':False,'ocean_animation_modified':False}
(ROOT/'source/falaise_metano_temoin/verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
