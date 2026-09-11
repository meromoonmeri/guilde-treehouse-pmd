"""Aseprite INDEXÉ : image d'indices fixe, palettes réellement modifiées par frame."""
from pathlib import Path
from PIL import Image
import struct
import zlib
import numpy as np


def chunk(kind,payload):return struct.pack('<IH',len(payload)+6,kind)+payload

def string(text):
    raw=text.encode('utf-8');return struct.pack('<H',len(raw))+raw


def write_indexed(path,indices,palettes,duration=250,name='Palette cycling'):
    indices=np.asarray(indices,dtype=np.uint8);h,w=indices.shape;frames=len(palettes);colors=len(palettes[0])
    assert all(len(p)==colors for p in palettes)
    assert indices.max()<colors and colors<=256
    content=bytearray()
    for f,palette in enumerate(palettes):
        blocks=[]
        if f==0:
            blocks.append(chunk(0x2004,struct.pack('<HHHHHHB',3,0,0,0,0,0,255)+b'\0'*3+string(name)))
        payload=struct.pack('<III',colors,0,colors-1)+b'\0'*8
        for rgba in palette:payload+=struct.pack('<HBBBB',0,*rgba)
        blocks.append(chunk(0x2019,payload))
        if f==0:
            data=struct.pack('<HhhBHh',0,0,0,255,2,0)+b'\0'*5+struct.pack('<HH',w,h)+zlib.compress(indices.tobytes(),9)
        else:data=struct.pack('<HhhBHh',0,0,0,255,1,0)+b'\0'*5+struct.pack('<H',0)
        blocks.append(chunk(0x2005,data))
        payload=b''.join(blocks);content+=struct.pack('<IHHH2sI',len(payload)+16,0xF1FA,len(blocks),duration,b'\0\0',len(blocks))+payload
    header=bytearray(128)
    struct.pack_into('<IHHHHHIH',header,0,len(content)+128,0xA5E0,frames,w,h,8,1,duration)
    struct.pack_into('<HBBhhHH',header,32,colors,1,1,0,0,8,8)
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(header+content)
