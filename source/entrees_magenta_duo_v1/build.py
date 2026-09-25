"""
Entrées donjon — pipeline magenta duo, multicouche, animation selon map.
Méthode : layouts_magenta_v1 conservée (key, detourage, separation, tint, ORA).
Duo = 2 fonds issus de la même map canonique à profondeurs distinctes.
"""
from pathlib import Path
import json, hashlib, io, zipfile, xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as nd

R=Path(__file__).resolve().parents[2]
SRC=Path(__file__).resolve().parent
P=SRC / 'references'
BRUTS=SRC / 'bruts'
OUT=R / 'renders' / 'entrees_magenta_duo_v1'
CONFIG=json.loads((P/'config.json').read_text())
from palette import key, tint
NN=Image.Resampling.NEAREST

PALETTES={
    'foret': [('mousse', 'Forêt · mousse profonde'), ('brume', 'Forêt · brume claire')],
    'volcan': [('braise', 'Volcan · braise'), ('cendre', 'Volcan · cendre')],
    'vapeur': [('azur', 'Vapeur · azur'), ('ardoise', 'Vapeur · ardoise')],
}

def load(p,size=None):
    im=Image.open(p).convert('RGBA')
    return im.resize(size, NN) if size else im

def clipped(a, mask):
    out=a.copy(); out[~mask]=0; return Image.fromarray(out)

def poly(size, points):
    w,h=size; m=Image.new('L', size); ImageDraw.Draw(m).polygon([(round(x*w), round(y*h)) for x,y in points], fill=255); return np.array(m)>0

def ora(path, layers, comp):
    root=ET.Element('image', {'w': str(comp.width), 'h': str(comp.height), 'name': path.stem})
    stack=ET.SubElement(root, 'stack')
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('mimetype', 'image/openraster', compress_type=zipfile.ZIP_STORED)
        for i,(name,im) in reversed(list(enumerate(layers.items()))):
            filename=f'data/layer{i}.png'
            ET.SubElement(stack, 'layer', {'name': name, 'src': filename, 'x':'0','y':'0','opacity':'1.0','visibility':'visible','composite-op':'svg:src-over'})
            b=io.BytesIO(); im.save(b, format='PNG'); z.writestr(filename, b.getvalue())
        z.writestr('stack.xml', ET.tostring(root, encoding='utf-8', xml_declaration=True))
        b=io.BytesIO(); comp.save(b, format='PNG'); z.writestr('mergedimage.png', b.getvalue())

def make_ground_mask(size, terrain_alpha, biome):
    """Heuristique pour séparer duo fonds : lointain (haut) vs proche (bas), puis sol."""
    w,h=size
    yy,xx=np.mgrid[:h,:w]
    valid=terrain_alpha>0
    if biome=='foret':
        # foret : canopée haut + masses laterales
        lointain = valid & (yy < h*0.38)
        proche = valid & (yy >= h*0.38) & (yy < h*0.78)
        sol = valid & (yy >= h*0.55) & (xx>w*0.22) & (xx<w*0.78)
        # sol is part of proche but extracted as dedicated layer
        proche = proche & ~sol
        # entree : trou sombre au nord centre
        entree = valid & (xx>w*0.38) & (xx<w*0.62) & (yy>h*0.18) & (yy<h*0.42)
        # adjust: entree is inside proche, cut out
        proche = proche & ~entree
        lointain = lointain & ~entree
        return {'00_fond_lointain': lointain, '01_fond_proche': proche, '02_sol': sol, '06_entree': entree}
    elif biome=='volcan':
        lointain = valid & (yy < h*0.35)
        proche = valid & (yy >= h*0.28) & (yy < h*0.75)
        sol = valid & (yy >= h*0.62) & (xx>w*0.18) & (xx<w*0.82)
        proche = proche & ~sol
        entree = valid & (xx>w*0.30) & (xx<w*0.70) & (yy>h*0.20) & (yy<h*0.50)
        lointain = lointain & ~entree
        proche = proche & ~entree
        # lave zone at bottom
        lave = valid & (yy > h*0.78) & (xx>w*0.15) & (xx<w*0.85)
        sol = sol & ~lave
        return {'00_fond_lointain': lointain & ~lave, '01_fond_proche': proche, '02_sol': sol, '06_entree': entree, '01b_lave_anim': lave}
    else: # vapeur
        lointain = valid & (yy < h*0.32)
        proche = valid & (yy >= h*0.30) & (yy < h*0.72)
        sol = valid & (yy >= h*0.58)
        proche = proche & ~sol
        entree = valid & (xx>w*0.32) & (xx<w*0.68) & (yy>h*0.22) & (yy<h*0.48)
        lointain = lointain & ~entree
        proche = proche & ~entree
        # vapeur zone near entrance arch
        vapeur = valid & (xx>w*0.35) & (xx<w*0.65) & (yy>h*0.28) & (yy<h*0.55)
        # vapeur overlaps entree/proche — keep as separate anim layer, cut from proche
        proche = proche & ~vapeur
        return {'00_fond_lointain': lointain, '01_fond_proche': proche, '02_sol': sol, '06_entree': entree, '01b_vapeur_anim': vapeur}

def build_one(conf):
    cid=conf['id']; biome=conf['biome']; size=tuple(conf['size']); w,h=size
    print(f"Building {cid} {size} biome={biome}")
    ref_path=R/conf['source']
    # brut terrain sur magenta : if exists use it else fallback to reference with magenta added demo
    brut_path=BRUTS/f"{cid}.png"
    brut_sol_path=BRUTS/f"{cid}_sol.png"
    if brut_path.exists():
        raw=load(brut_path, size)
    else:
        # fallback : reference image on magenta (for demo before generation) — place reference centered on magenta
        raw_bg=Image.new('RGBA', size, (255,0,255,255))
        ref=Image.open(ref_path).convert('RGBA')
        # center crop/resize nearest to size if mismatch
        if ref.size != size:
            # resize to fit inside, keep aspect, centered
            ref=ref.resize(size, NN)
        raw_bg.alpha_composite(ref, (0,0))
        # simulate slight layout mod : shift path 8px
        arr=np.array(raw_bg)
        # add magenta border to force key extraction demo : already magenta bg where ref transparent (but ref opaque)
        # For demo, we just use raw_bg as raw (will not have magenta transparent, but key will keep all)
        # To force magenta extraction we composite magenta outside terrain mask demo: create magenta mask around edges
        raw=raw_bg
        print(f"  [demo] using reference fallback for {cid} (brut manquant)")
    terrain=key(raw)
    ta=np.array(terrain)
    valid=ta[:,:,3]>0
    # floor : either brut sol or tiled 24px patch from terrain
    if brut_sol_path.exists():
        floor=load(brut_sol_path, size)
        floor=key(floor) if np.any(np.array(floor)[:,:,3]==0) else floor
    else:
        # reconstitue sol par echantillon 24px comme sables
        if valid.any():
            # find a ground patch 24x24 inside sol zone
            sample = terrain.crop((w//2-12, h//2+40, w//2+12, h//2+64))
            if np.min(np.array(sample)[:,:,3])<255:
                # fallback to center 24px of terrain
                sample = terrain.crop((w//2-12, h//2-12, w//2+12, h//2+12))
            floor=Image.new('RGBA', size)
            for y in range(0,h,24):
                for x in range(0,w,24):
                    floor.alpha_composite(sample, (x,y))
            floor=np.array(floor)
            # keep only where valid for sol, else transparent
        else:
            floor=Image.new('RGBA', size, (0,0,0,0))
            floor=np.array(floor)
        floor=Image.fromarray(floor)
        print(f"  [demo] sol reconstitue patch 24px for {cid}")

    # distance for seam
    # preserve = animation zone if any (lave/vapeur) will be overlayed as animation, not preserved exactly like layouts
    masks=make_ground_mask(size, valid, biome)
    # fill any gap so valid is fully partitioned (demo fallback: ensure no hole)
    union=np.zeros((h,w), bool)
    for mm in masks.values():
        union|=mm
    remaining=valid & ~union
    if remaining.any():
        # attach remaining to proche for continuity, or lointain if top
        target='01_fond_proche' if '01_fond_proche' in masks else list(masks.keys())[0]
        masks[target]=masks[target]|remaining
        print(f"  gap fill: {remaining.sum()} px -> {target}")
    # separate distinct layers
    # prepare base arrays
    a=np.array(Image.new('RGBA', size, (0,0,0,0)))
    # composite floor + terrain for color reference (like layouts)
    full=Image.new('RGBA', size, (0,0,0,0))
    full.alpha_composite(floor)
    full.alpha_composite(terrain)
    a=np.array(full)

    # shadows: derived from structure silhouette
    structure_mask = np.zeros((h,w), bool)
    for k in ['01_fond_proche','06_entree']:
        if k in masks:
            structure_mask |= masks[k]
    # contact shadow
    sh=Image.fromarray((structure_mask*255).astype('uint8'))
    shifted=Image.new('L', size); shifted.paste(sh, (0,3))
    shadow_alpha=np.array(shifted.filter(ImageFilter.GaussianBlur(1))).astype(float)*0.23
    shadow_alpha[structure_mask]=0
    shadow_alpha[~valid]=0
    sa=np.zeros_like(a); sa[:,:,:3]=[15,24,27]; sa[:,:,3]=np.rint(shadow_alpha).astype('uint8'); sa[sa[:,:,3]==0]=0

    # seam 8px outer band
    dist=nd.distance_transform_edt(~valid) if valid.any() else np.full((h,w),1000.)
    seam = (dist>0)&(dist<=6)&valid
    for k in list(masks.keys()):
        masks[k]=masks[k]&~seam & valid

    # build ungraded dict
    ungraded={}
    # duo fonds : lointain & proche
    if '00_fond_lointain' in masks and masks['00_fond_lointain'].any():
        ungraded['00_fond_lointain_duo']=clipped(a, masks['00_fond_lointain'])
    if '01_fond_proche' in masks and masks['01_fond_proche'].any():
        ungraded['01_fond_proche_duo']=clipped(a, masks['01_fond_proche'])
    if '02_sol' in masks and masks['02_sol'].any():
        ungraded['02_sol_reconstitue']=clipped(np.array(floor), masks['02_sol'])
        # also keep sol visible on top of floor? Use floor clipped
    # shadows
    if np.any(sa[:,:,3]):
        ungraded['03_ombres_contact']=Image.fromarray(sa)
    # structure laterale : split left/right for forets
    if biome=='foret':
        left = masks.get('01_fond_proche', np.zeros((h,w),bool)) & (np.mgrid[:h,:w][1]<w*0.5)
        # we already used proche, so create left/right as part of proche duo already; add decor
        pass
    # entree
    if '06_entree' in masks and masks['06_entree'].any():
        ungraded['06_ouverture']=clipped(a, masks['06_entree'])
    # animation layers (lave/vapeur) — keep as separate if present
    anim_masks={}
    if '01b_lave_anim' in masks and masks['01b_lave_anim'].any():
        anim_masks['lave']=masks['01b_lave_anim']
    if '01b_vapeur_anim' in masks and masks['01b_vapeur_anim'].any():
        anim_masks['vapeur']=masks['01b_vapeur_anim']
    if seam.any():
        ungraded['07_raccord']=clipped(a, seam)

    # save masques for inspection
    md=OUT/'masques'/cid; md.mkdir(parents=True, exist_ok=True)
    for k,msk in masks.items():
        Image.fromarray(msk.astype('uint8')*255).save(md/f"{k}.png")
    Image.fromarray(valid.astype('uint8')*255).save(md/'valid.png')
    terrain.save(md/'terrain_detoure.png')
    floor.save(md/'sol_reconstitue.png')

    # now palette variants
    scene_records=[]
    for pi,(pal_id, pal_title) in enumerate(PALETTES[biome]):
        ident=f"{cid}_{pal_id}"
        out=OUT/'zones'/ident; out.mkdir(parents=True, exist_ok=True)
        layers={k: tint(v, biome, pi) for k,v in ungraded.items()}
        layerfiles=[]
        for key_name, im in layers.items():
            fn=f"{ident}_{key_name}.png"
            im.save(out/fn)
            layerfiles.append({'name': key_name, 'file': fn})
            # TSX
            root=ET.Element('tileset', version='1.10', name=Path(fn).stem, tilewidth='8', tileheight='8', columns=str(w//8), tilecount=str(w//8*h//8))
            ET.SubElement(root, 'image', source=fn, width=str(w), height=str(h))
            ET.ElementTree(root).write(out/Path(fn).with_suffix('.tsx').as_posix(), encoding='utf-8', xml_declaration=True)

        # animation handling
        anim_files=[]
        frames=[]
        durations=conf['durations_ms']
        nframes=conf['frames']
        # generate animation frames: for volcan/vapeur, create cycling tint of anim mask
        if anim_masks:
            # generate nframes animation layers by tint shifting or alpha
            base_anim_a = a.copy()
            for fi in range(nframes):
                anim_layer=np.zeros((h,w,4), dtype=np.uint8)
                for anim_name, msk in anim_masks.items():
                    # create shimmer : for lave, vary brightness; for vapeur, vary alpha
                    if anim_name=='lave':
                        # brightness pulse
                        factor=0.85 + 0.15*np.sin(2*np.pi*fi/nframes)
                        col=np.array([255, 90, 20, 230], dtype=float)*factor
                        col=np.clip(col,0,255).astype(np.uint8)
                        anim_layer[msk]=col
                        # add second color for cracks
                        crack=msk & (np.mgrid[:h,:w][0]%8<2)
                        anim_layer[crack]=np.array([255,180,60,255], dtype=np.uint8)
                    elif anim_name=='vapeur':
                        # alpha drift
                        alpha=int(90 + 60*np.sin(2*np.pi*(fi/nframes + 0.1)))
                        alpha=np.clip(alpha, 40, 180)
                        col=np.array([220,230,240, alpha], dtype=np.uint8)
                        anim_layer[msk]=col
                        # second puff
                        puff=msk & (np.mgrid[:h,:w][1]%16<8) & (np.mgrid[:h,:w][0]%12<6)
                        # shift puff with frame
                        shift=(fi*2)%16
                        # simple: vary alpha slightly
                        anim_layer[msk & puff]=np.array([240,245,255, min(180, alpha+40)], dtype=np.uint8)
                # tint anim layer per palette
                anim_im=Image.fromarray(anim_layer)
                anim_tinted=tint(anim_im, biome, pi)
                fn=f"{ident}_01_animation_{fi:03}.png"
                anim_tinted.save(out/fn)
                anim_files.append(fn)
                # composite scene frame
                comp=Image.new('RGBA', size, (0,0,0,0))
                if anim_files:
                    comp.alpha_composite(anim_tinted)
                for im in layers.values():
                    comp.alpha_composite(im)
                # coverage debug: check opaque where valid, log but not hard fail for demo fallback
                arr=np.array(comp)
                masked=arr[valid]
                covered=(masked[:,:3].any(axis=1) | (masked[:,3]>0))
                if not np.all(covered):
                    print(f"    warning: {np.sum(~covered)} valid pixels not covered (demo fallback ok)")
                frames.append(comp)
        else:
            # static : one composite
            comp=Image.new('RGBA', size, (0,0,0,0))
            for im in layers.values():
                comp.alpha_composite(im)
            frames=[comp]
            # also show with no animation layer
            durations=[1000]

        # save composition
        frames[0].save(out/'COMPOSITION.png')
        if len(frames)>1:
            # save WebP lossless with durations
            try:
                frames[0].save(out/'ANIMATION_COMPLETE.webp', save_all=True, append_images=frames[1:], duration=durations, loop=0, lossless=True)
            except Exception as e:
                print(f"    WebP save failed {e}, fallback GIF")
                frames[0].save(out/'ANIMATION_COMPLETE.gif', save_all=True, append_images=frames[1:], duration=durations, loop=0)

        # ORA
        ora_layers={}
        if anim_files:
            ora_layers['01_animation_phase0']=load(out/anim_files[0])
        ora_layers.update(layers)
        # ensure comp exists
        ora(out/f"{ident}.ora", ora_layers, frames[0])

        # also save TMJ (Tiled map) — simple : one layer image
        # Create .tmj with tileset references
        tmj={
            "compressionlevel": -1,
            "height": h//8,
            "infinite": False,
            "layers": [{"data": [0]*(w//8*h//8), "height": h//8, "id":1, "name": "Sol", "opacity":1, "type":"tilelayer", "visible":True, "width": w//8, "x":0, "y":0}],
            "nextlayerid": 2,
            "nextobjectid": 1,
            "orientation": "orthogonal",
            "renderorder": "right-down",
            "tiledversion": "1.10",
            "tileheight": 8,
            "tilesets": [{"firstgid":1, "source": f"{ident}_02_sol_reconstitue.tsx"}] if any('02_sol' in lf['name'] for lf in layerfiles) else [],
            "tilewidth": 8,
            "type": "map",
            "version": "1.10",
            "width": w//8
        }
        (out/f"{ident}.tmj").write_text(json.dumps(tmj))

        record={
            'id': ident,
            'title': pal_title,
            'base': cid,
            'biome': biome,
            'palette_index': pi,
            'size': list(size),
            'source': conf['source'],
            'source_sha256': conf['source_sha256'],
            'layers': layerfiles,
            'animation': {'files': anim_files, 'durations_ms': durations, 'cycle_ms': sum(durations), 'mode': 'generated according to map composition', 'source_sequence_preserved': False} if anim_files else None,
            'duo': conf['duo'],
            'layout_note': conf['layout_note'],
            'hidden_ground': 'generator plate on magenta, keyed' if brut_path.exists() else 'reference fallback demo (brut missing) -> to be replaced by generated magenta',
            'contact_shadows': 'reconstructed, not native',
            'grid': 8,
            'native_runtime_validated': False
        }
        scene_records.append(record)
        print(f"  -> {ident} {len(layerfiles)} layers, {len(anim_files)} anim frames")
    return scene_records

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'masques').mkdir(parents=True, exist_ok=True)
    (OUT/'zones').mkdir(parents=True, exist_ok=True)
    BRUTS.mkdir(parents=True, exist_ok=True)
    manifest={'method': 'Generator magenta -> key(alpha) -> duo fonds + multicouche -> animation selon composition', 'runtime_validated': False, 'grid': 8, 'scenes': []}
    all_checks=[]
    for conf in CONFIG:
        recs=build_one(conf)
        manifest['scenes'].extend(recs)
        all_checks.extend([{'id': r['id'], 'layers': len(r['layers']), 'anim_frames': len(r['animation']['files']) if r['animation'] else 0} for r in recs])
    (OUT/'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    (OUT/'verification_build.json').write_text(json.dumps(all_checks, indent=2))
    print(f"Built {len(manifest['scenes'])} scenes. See {OUT}")

if __name__=='__main__':
    main()
