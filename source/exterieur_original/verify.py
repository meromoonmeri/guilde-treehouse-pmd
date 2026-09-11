#!/usr/bin/env python3
"""Contrat : cinq layers IA, chroma magenta, nuages wrap et mer palette."""
from __future__ import annotations
import json, struct
from pathlib import Path
import numpy as np
from PIL import Image
from build import CLOUD_PERIOD, FRAMES, LAYERS, MAGENTA, OUT, SEA_PERIOD, SIZE, keyed_rgba
from animation import AnimatedLayer, compose
ROOT=Path(__file__).resolve().parents[2]

def read(p):
    with Image.open(p) as im: return im.copy()
def same(a,b,m): assert np.array_equal(np.asarray(a),np.asarray(b)),m

def verify():
    m=json.loads((OUT/'kit.json').read_text()); f=m['fichiers']['original']; assert m['grille_px']==8 and m['fond_chroma_key']=='#FF00FF'
    assert len(m['calques'])==5 and m['animation']['frames']==FRAMES
    rgba=[]
    for i,d in enumerate(m['calques']):
        mag=read(OUT/f['calques_magentas'][d['id']]); assert mag.mode=='RGB' and mag.size==SIZE
        if i: assert np.any(np.all(np.array(mag)==MAGENTA,axis=2)),d['id']
        alpha=read(OUT/f['calques'][d['id']]).convert('RGBA'); same(keyed_rgba(mag) if i else mag.convert('RGBA'),alpha,'chroma '+d['id']); rgba.append(alpha)
    specs=f['operations']; cloud=AnimatedLayer(rgba[1],specs['01_nuages_wrap'],OUT); sea=AnimatedLayer(rgba[2],specs['02_mer_palette'],OUT)
    same(cloud.at(0),cloud.at(CLOUD_PERIOD),'wrap nuage'); assert not np.array_equal(np.array(cloud.at(0)),np.array(cloud.at(1)))
    alpha = np.asarray(sea.at(0).getchannel('A'))
    for frame in range(SEA_PERIOD):
        same(Image.fromarray(alpha), sea.at(frame).getchannel('A'), f'mer déplacée à la phase {frame}')
    assert not np.array_equal(np.array(sea.at(0)),np.array(sea.at(12)))
    same(compose([AnimatedLayer(im,specs.get(d['id']),OUT) for d,im in zip(m['calques'],rgba)],SIZE,0),read(OUT/f['composition']).convert('RGBA'),'composition')
    raw=(OUT/f['aseprite']).read_bytes(); header=struct.unpack_from('<IHHHHHIH',raw); assert header[:7]==(len(raw),0xA5E0,FRAMES,*SIZE,32,1)
    tiled=json.loads((OUT/f['tiled']).read_text()); assert sorted(t['tilecount'] for t in tiled['tilesets'])==[SEA_PERIOD,CLOUD_PERIOD]
    assert (OUT/'README.md').is_file()
    h=(ROOT/'apercu_exterieur_original.html').read_text(); assert all(x in h for x in ('#FF00FF','x+=8','y+=8','f%344','f%24')) and 'http://' not in h and 'https://' not in h
    (OUT/'controle_qualite.json').write_text(json.dumps({'resultat':'PASS','layers':5,'fond':'#FF00FF','grille_px':8,'nuages_wrap_px':CLOUD_PERIOD,'mer_palette_frames':SEA_PERIOD,'aseprite_frames':FRAMES},indent=2)+'\n')
    print('PASS : 5 layers IA PMD, fond magenta, nuages wrap et mer palette.')
if __name__=='__main__': verify()
