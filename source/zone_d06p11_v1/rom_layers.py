"""Rendu fidèle de d06p11a par couche et par horloge (palette 7x5 f, BPA 10x10 f)."""
import glob, numpy as np
from PIL import Image
from skytemple_files.common.types.file_types import FileType as F
B = '/tmp/pret/files/MAP_BG/'; C = 'd06p11a'
bma = F.BMA.deserialize(open(B+C+'.bma','rb').read()); bpc = F.BPC.deserialize(open(B+C+'.bpc','rb').read())
bpl = F.BPL.deserialize(open(B+C+'.bpl','rb').read())
bpas = [None]*8
for p in sorted(glob.glob(B+C+'[0-9].bpa')): bpas[int(p[-5])-1] = F.BPA.deserialize(open(p,'rb').read())
CW, NX, NY = 24, bma.map_width_chunks, bma.map_height_chunks
NPAL = len(bpl.animation_palette)
def layer(L, fb=0, fp=0):
    strips = bpc.chunks_animated_to_pil(1 - L, bpl.palettes, bpas, 1)
    s = strips[fb % len(strips)]
    idx = np.array(s)  # (n*24, 24) indices
    pal = np.array(list(bpl.apply_palette_animations(fp)) if NPAL else bpl.palettes).reshape(-1, 3)
    rgba = np.zeros(idx.shape + (4,), np.uint8); rgba[..., :3] = pal[idx]; rgba[..., 3] = np.where(idx % 16 == 0, 0, 255)
    mp = bma.layer0 if L == 0 else bma.layer1
    out = np.zeros((NY*CW, NX*CW, 4), np.uint8)
    for i, m in enumerate(mp):
        x, y = i % NX, i // NX; out[y*CW:(y+1)*CW, x*CW:(x+1)*CW] = rgba[m*CW:(m+1)*CW]
    return out, len(strips)
col = np.array(bma.collision).reshape(bma.map_height_camera, bma.map_width_camera)
