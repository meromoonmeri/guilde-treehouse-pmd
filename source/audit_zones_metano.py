"""Read-only audit of approved zone scale and native tile assembly. Never rebuilds assets.
Usage: python source/audit_zones_metano.py [path/to/metano_town_palika.rsground]
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import numpy as np
import json,hashlib,sys,struct
from zones_guidees.native_tools import Bank,BASE,CLIFF,ROOT
O=ROOT/'sprites/zones_guidees';D=ROOT/'audits/metano_import';D.mkdir(parents=True,exist_ok=True)
B=Bank();M=json.loads((O/'provenance.json').read_text());A=M['atlas'];entries=A['entries']
def sig(im):return hashlib.sha256(im.tobytes()).digest()
def source_sig(g):
    r=entries[g-1];return sig(B.sources[r['sheet']][tuple(r['texloc'])])
# Adjacency dictionary in the actual native cliff sheet (all these source coordinates
# are placed at the same coordinates in the original Ground map, verified below).
cs=B.sources[CLIFF];hs={p:sig(im) for p,im in cs.items()};adj=[set(),set()]
for (x,y),h in hs.items():
    for k,(dx,dy) in enumerate([(1,0),(0,1)]):
        if (x+dx,y+dy) in hs:adj[k].add((h,hs[x+dx,y+dy]))
report={'scope':'Asset/code audit, not an observation of the user game runtime','source_tile_px':8,'native_cliff_cells':len(cs),'native_cliff_unique_rgba_tiles':len(set(hs.values())),'zones':[]}
p=Path(sys.argv[1]) if len(sys.argv)>1 else Path('/home/user/metano_town_palika.rsground')
if p.exists():
    raw=p.read_bytes();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest();assert blob=='38d178520e95d2b1f17d57c12682579d9e37bbae'
    ground=json.loads(raw.decode('utf-8-sig'))['Object'];layers=[]
    for l in ground['Layers']:
        if l['Name'] not in ['Base','Cliffs']:continue
        used=0;direct=0
        for x,col in enumerate(l['Tiles']):
            for y,c in enumerate(col):
                for sub in c.get('Layers',[]):
                    if not sub['Frames']:continue
                    f=sub['Frames'][0]
                    if f['Sheet'] not in [BASE,CLIFF]:continue
                    used+=1;direct+=f['TexLoc']=={'X':x,'Y':y}
        assert used==direct
        layers.append({'name':l['Name'],'grid':[len(l['Tiles']),len(l['Tiles'][0])],'placed_cells':used,'source_to_ground_coordinates_identical':direct})
    report['original_ground']={'blob':blob,'TexSize':ground['TexSize'],'layers':layers,'interpretation':'Native 8px cells and direct source-to-map coordinates; no source-cell magnification present in these original terrain layers.'}
else:report['original_ground']={'available':False}
for z in M['zones']:
    folder=O/z['id'];tm=json.loads((folder/'eau.tmj').read_text());ids=tm['layers'][1]['data'];hmap={g:source_sig(g) for g in set(ids)-{0}}
    totals=[0,0];missing=[0,0]
    for i,g in enumerate(ids):
        if not g:continue
        for k,j in enumerate([i+1 if i%256<255 else -1,i+256 if i<256*191 else -1]):
            if j<0 or not ids[j]:continue
            totals[k]+=1;missing[k]+=(hmap[g],hmap[ids[j]]) not in adj[k]
    layer=folder/'multicalques/02_parois.png';im=Image.open(layer)
    guide=Image.open(ROOT/z['guide']);sizes={'guide':list(guide.size),'canonical_dry':list(Image.open(folder/'canonique_sec.png').size),'layer':list(im.size),'layer_png_mode':im.mode,'layer_dpi_metadata':im.info.get('dpi')}
    n=struct.unpack_from('<HHHHH',(folder/'multicalques/zone_eau_animee.aseprite').read_bytes(),4)
    report['zones'].append({'id':z['id'],'sizes':sizes,'guide_to_map_scale':[2048/guide.width,1536/guide.height],'tiled_grid':[tm['width'],tm['height']],'tiled_tile_px':[tm['tilewidth'],tm['tileheight']],'aseprite_header_magic_frames_width_height_depth':list(n),'placed_cliff_cells':sum(bool(g) for g in ids),'unique_cliff_tile_images_used':len(set(hmap.values())),'adjacency_pairs':totals,'pairs_absent_from_native_cliff_adjacencies':missing,'absent_percent':[round(100*a/b,2) for a,b in zip(missing,totals)],'adjacency_caveat':'Diagnostic of assembly change, NOT a proof that every absent pair is visually invalid. Repetition and new legal layouts can also create absent pairs.','water_crossing_cliff_heights_px':[b-a for a,b in z['cliff_bands_px']],'visible_reference_hashes_unchanged':all(hashlib.sha256((folder/f).read_bytes()).hexdigest()==s for f,s in json.loads((O/'multicalques.json').read_text())['zones'][len(report['zones'])]['reference_sha256'].items())})
report['code_findings']={'native_grid_is_not_a_complete_cliff_module':True,'body_repeat_px':[64,48],'shadow_repeat_column_px':8,'shadow_source_columns':[85,86,92],'body_source_rows':[59,64],'boundary_reconstruction':'Nearest candidate per 8px cell; local color/rock-mask score, not a semantic cliff-edge module system','layer_border':'One-cell peripheral band of selected cliff cells; not a reconstruction of native complete rims','fit_preview_scale':'Noninteger fit-to-width; nearest sampling can hide or exaggerate detail. Native 100% must be used for review.','import_settings_known':False,'no_proven_export_downscale':True,'approved_geometry_preserved':True}
(D/'mesures.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
# Original terrain reconstructed directly from native Base + Cliffs; no image-generation pixels.
terrain=Image.new('RGBA',(1512,1512))
for name in [BASE,CLIFF]:
    layer=Image.new('RGBA',terrain.size)
    for x,y in B.sources[name]:layer.paste(B.image(B.get(name,x,y)),(x*8,y*8))
    terrain=Image.alpha_composite(terrain,layer)
rect_native=(656,368,976,592);rect_zone=(304,640,624,864)
guide=Image.open(ROOT/M['zones'][1]['guide']).convert('RGBA').resize((2048,1536),Image.Resampling.NEAREST)
final=Image.open(O/'02_terrasses/canonique_sec.png').convert('RGBA')
board=Image.new('RGB',(1976,678),'#192d24');d=ImageDraw.Draw(board);fp='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';title=ImageFont.truetype(fp,25);small=ImageFont.truetype(fp,17)
d.text((20,15),'AUDIT — PIXELS IDENTIQUES ≠ FALAISES ASSEMBLÉES À L’IDENTIQUE',font=title,fill='#efd69d')
items=[('Terrain original Métano',terrain.crop(rect_native),'Source : crop (656,368) → (976,592)'),('Guide généré — échelle non calibrée',guide.crop(rect_zone),'Guide adapté à 2048 × 1536 pour sa silhouette'),('Reconstruction livrée',final.crop(rect_zone),'Zone 02 : crop (304,640) → (624,864)')]
for i,(label,im,caption) in enumerate(items):
    x=16+i*652;d.text((x,62),label,font=small,fill='#efd69d');board.paste(im.convert('RGB').resize((640,448),Image.Resampling.NEAREST),(x,96));d.text((x,554),caption,font=small,fill='#becfb4')
d.text((20,599),'Chaque extrait mesure 320 × 224 px, affiché ici à ×2 entier sans lissage. Ce ne sont pas les mêmes lieux.',font=small,fill='#efd69d')
d.text((20,633),'À gauche et à droite : pixels natifs. La répétition des fragments modifie le volume ; aucun zoom du jeu n’est mesuré ici.',font=small,fill='#becfb4')
board.save(D/'comparaison_echelle.png');print(json.dumps(report,ensure_ascii=False,indent=2))
