"""User-requested faceless jewel variants. Never edit the source Pokemon sprites."""
from PIL import ImageDraw
import numpy as np
# Native 64px crown canvases. None = rear view without a face-bearing gem.
FACE_BOXES={
 'fire':[(28,47,35,56),(23,45,31,55),(22,46,28,56),None,None,(39,46,45,55),(42,46,49,55),(19,46,26,55)],
 'water':[(28,44,38,54),(34,37,42,47),None,None,None,None,None,(24,44,34,54)]
}
def remove_face(im,kind,direction):
 box=FACE_BOXES[kind][direction]
 if box is None:return im.copy()
 out=im.copy();alpha=im.getchannel('A');d=ImageDraw.Draw(out);x0,y0,x1,y1=box;cx=(x0+x1)//2;cy=(y0+y1)//2
 colors=([(125,12,48,255),(210,38,70,255),(255,136,110,255)] if kind=='fire' else [(22,57,143,255),(38,127,218,255),(126,225,248,255)])
 # Replace ALL facial pixels in the inspected jewel region by angular planes.
 # No paired glints that could recreate eyes, and no head-shaped foreground added.
 d.rectangle((x0,y0,x1-1,y1-1),fill=colors[0])
 d.polygon([(x0,y0),(x1-1,y0),(cx,y1-1)],fill=colors[1])
 d.polygon([(x0,y0),(cx,cy),(x0,y1-1)],fill=colors[2])
 out.putalpha(alpha)
 assert np.array_equal(np.array(out)[:,:,3],np.array(im)[:,:,3])
 return out
