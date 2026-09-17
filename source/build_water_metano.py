"""Extraction SANS génération, redimensionnement, filtre ni quantification.
python source/build_water_metano.py (Pillow)
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import struct,io,json,hashlib,math,base64
R=Path(__file__).resolve().parents[1];S=R/'source/eau_metano';O=R/'sprites/eau_metano';O.mkdir(exist_ok=True)
NAMES=['Metano_Town_Animation_Tileset']+[f'Metano_Town_River_Animation_{i}' for i in range(1,5)]+['Metano_Town_River_Sparkles']

def decode(path):
    raw=path.read_bytes();size,n=struct.unpack_from('<II',raw);assert size==8
    records=[struct.unpack_from('<IIQ',raw,8+16*i) for i in range(n)];tiles={}
    im=Image.new('RGBA',((max(x for x,y,o in records)+1)*8,(max(y for x,y,o in records)+1)*8))
    for x,y,o in records:
        length=struct.unpack_from('<q',raw,o)[0];t=Image.open(io.BytesIO(raw[o+8:o+8+length])).convert('RGBA');assert t.size==(8,8)
        tiles[x,y]=t;im.paste(t,(x*8,y*8))
    return im,tiles

def straight(im):
    # PNG for image editors: remove premultiplication only on partial-alpha pixels.
    out=im.copy();out.putdata([(round(r*255/a),round(g*255/a),round(b*255/a),a) if 0<a<255 else (r,g,b,a) for r,g,b,a in im.getdata()]);return out

def write_native(im,path):
    records=[];payload=bytearray();seen={};n=(im.width//8)*(im.height//8)
    for y in range(im.height//8):
        for x in range(im.width//8):
            tile=im.crop((x*8,y*8,x*8+8,y*8+8));key=tile.tobytes()
            if key not in seen:
                seen[key]=8+16*n+len(payload);b=io.BytesIO();tile.save(b,format='PNG');v=b.getvalue();payload.extend(struct.pack('<q',len(v))+v)
            records.append(struct.pack('<IIQ',x,y,seen[key]))
    path.write_bytes(struct.pack('<II',8,n)+b''.join(records)+payload)

def tsj(name,im,anims):
    (O/(name+'.tsj')).write_text(json.dumps({'type':'tileset','version':'1.10','name':name,'tilewidth':8,'tileheight':8,'columns':im.width//8,'tilecount':(im.width//8)*(im.height//8),'margin':0,'spacing':0,'image':name+'.png','imagewidth':im.width,'imageheight':im.height,'tiles':anims},indent=2))

source={n:decode(S/'natifs'/(n+'.tile')) for n in NAMES}
manifest={'origin':'EXTRACTION_PIXELS_SOURCE','repository':'https://github.com/Palikadude/Halcyon','commit':'da6c2130d641507447e6386a5e47a296e8cb4c71','grid_px':8,'sources':{},'cascades':{},'river':{}}
for n,(im,tiles) in source.items():
    straight(im).save(O/(n+'.png'))
    manifest['sources'][n]={'file':'../../source/eau_metano/natifs/'+n+'.tile','sha256':hashlib.sha256((S/'natifs'/(n+'.tile')).read_bytes()).hexdigest(),'size_px':list(im.size),'tile_count':len(tiles),'partial_alpha_pixels':sum(0<a<255 for r,g,b,a in im.getdata())}
# Original layout is untouched in the complete atlas. Four aligned crops form the convenient sheet.
base=source[NAMES[0]][0];cascade_frames=[];rects=[]
for i in range(4):
    rect=(8+72*i,496,72+72*i,632);rects.append(list(rect));im=base.crop(rect);cascade_frames.append(im);im.save(O/f'cascade_frame_{i+1}.png')
cascade=Image.new('RGBA',(256,136))
for i,im in enumerate(cascade_frames):cascade.paste(im,(i*64,0))
cascade.save(O/'Cascades_Metano_Exact.png');write_native(cascade,O/'Cascades_Metano_Exact.tile')
anims=[];native_cells=[]
for y in range(17):
    for x in range(8):
        tid=y*32+x;frames=[{'tileid':tid+i*8,'duration':167} for i in range(4)];anims.append({'id':tid,'animation':frames})
        native_cells.append({'x':x,'y':y,'Layers':[{'Frames':[{'Sheet':'Cascades_Metano_Exact','TexLoc':{'X':x+i*8,'Y':y}} for i in range(4)],'FrameLength':10}]})
tsj('Cascades_Metano_Exact',cascade,anims)
manifest['cascades']={'source_sheet':NAMES[0],'source_rects_xyxy_px':rects,'frame_size_px':[64,136],'frame_count':4,'order':'gauche vers droite dans la planche originale','timing':'Aperçu proposé à 10 ticks/phase ; la séquence autonome de ces quatre rectangles n’est pas référencée telle quelle dans la carte examinée. Ne pas confondre avec le timing vérifié de la rivière.','cells':native_cells}
# Deduplicate only identical FOUR-FRAME tuples. Never alter a pixel or rotate a tile.
river_names=NAMES[1:5];coordinates=sorted(source[river_names[0]][1],key=lambda p:(p[1],p[0]));groups={};entries=[]
for xy in coordinates:
    tiles=[source[n][1][xy] for n in river_names];key=b''.join(t.tobytes() for t in tiles)
    if key not in groups:groups[key]=len(entries);entries.append({'source_texlocs':[],'tiles':tiles})
    entries[groups[key]]['source_texlocs'].append(list(xy))
cols=16;rows=math.ceil(len(entries)/cols);river_compact=Image.new('RGBA',(cols*8,rows*8*4));river_anims=[]
for i,e in enumerate(entries):
    x=i%cols;y=i//cols
    for f,t in enumerate(e['tiles']):river_compact.paste(t,(x*8,(y+rows*f)*8))
    river_anims.append({'id':i,'animation':[{'tileid':i+cols*rows*f,'duration':167} for f in range(4)]})
river_compact.save(O/'Riviere_Metano_Compacte.png');write_native(river_compact,O/'Riviere_Metano_Compacte.tile');tsj('Riviere_Metano_Compacte',river_compact,river_anims)
manifest['river']={'source_sheets':river_names,'source_order':[1,2,3,4],'FrameLength':10,'timing_proof':'source/eau_metano/animations_carte.json — relevé de metano_town.rsground','compact_frame_size_px':[cols*8,rows*8],'unique_animated_tiles':len(entries),'original_cells':len(coordinates),'compact_layout':'4 phases de haut en bas ; sélectionner les tuiles de la première phase','entries':[{'compact_index':i,'compact_xy_cells':[i%cols,i//cols],'source_texlocs':e['source_texlocs'],'Frames':[{'Sheet':'Riviere_Metano_Compacte','TexLoc':{'X':i%cols,'Y':i//cols+rows*f}} for f in range(4)],'FrameLength':10} for i,e in enumerate(entries)]}
(O/'eau_metano.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
# Exact map-layout river crops for an animated preview only (all four remain aligned).
river_views=[source[n][0].crop((832,0,1136,560)) for n in river_names]
for i,im in enumerate(river_views):im.save(O/f'apercu_riviere_frame_{i+1}.png')
# Legended proof sheet, kept separate from importable sprites.
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';f=ImageFont.truetype(font,22);small=ImageFont.truetype(font,14)
board=Image.new('RGB',(1000,580),'#1d2f32');d=ImageDraw.Draw(board)
d.text((24,20),'MÉTANO / CASCADES — FRAMES ORIGINALES',font=f,fill='#dce9db')
d.text((24,56),'Extraction native · 64 × 136 px par frame · grille 8 px · aucune génération',font=small,fill='#9ebebc')
for i,im in enumerate(cascade_frames):
    x=40+i*240;view=im.resize((192,408),Image.Resampling.NEAREST);board.paste(view,(x,100),view);d.text((x,522),f'FRAME {i+1} · source x={8+72*i}',font=small,fill='#dfcc8a')
d.text((24,555),'Référence : Palika / Halcyon • Atlas complet et rivière fournis séparément',font=small,fill='#9ebebc');board.save(O/'planche_cascades.png')
def uri(p):return 'data:image/png;base64,'+base64.b64encode(p.read_bytes()).decode()
data={'cascades':[uri(O/f'cascade_frame_{i+1}.png') for i in range(4)],'river':[uri(O/f'apercu_riviere_frame_{i+1}.png') for i in range(4)],'sheet':uri(O/'Cascades_Metano_Exact.png'),'original':uri(O/'Metano_Town_Animation_Tileset.png'),'compact':uri(O/'Riviere_Metano_Compacte.png'),'unique':len(entries)}
(R/'apercu_eau_metano.html').write_text((S/'viewer.html').read_text().replace('__DATA__',json.dumps(data)))
print(f'4 cascades exactes ; rivière : {len(coordinates)} cellules => {len(entries)} séquences uniques ; exports PNG/.tile/TSJ.')
