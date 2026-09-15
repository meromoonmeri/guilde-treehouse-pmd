from PIL import Image, ImageDraw
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[2]
REF=ROOT/'source/portraits_politoed/reference'
BGDIR=ROOT/'source/portraits_politoed/backgrounds'
OUT=ROOT/'portrait/0186';OUT.mkdir(parents=True, exist_ok=True)

# The palette comes from the four existing Politoed SpriteCollab portraits.
O=(65,70,45)       # dark olive line
G=(152,203,97)     # main green
DG=(112,159,60)    # dark green
MG=(133,183,77)    # mid green
S=(105,122,72)     # green shadow / AA
L=(228,243,185)    # light face/belly
Y=(245,190,71)     # yellow belly / lower mouth
B=(153,110,53)     # brown shadow
MD=(143,67,35)     # mouth interior
P=(222,160,207)    # tongue/cheek
PD=(178,117,162)   # tongue shadow
BODY={O,G,DG,MG,S,L,Y,B,MD,P,PD}

EMOTIONS=['Normal','Happy','Pain','Angry','Worried','Sad','Crying','Shouting','Teary-Eyed','Determined','Joyous','Inspired','Surprised','Dizzy','Special0','Special1','Sigh','Stunned','Special2','Special3']
# Existing upstream art is retained pixel-for-pixel for these four emotions.
UPSTREAM={'Normal','Inspired','Shouting','Surprised'}

def art_from(path):
    src=Image.open(path).convert('RGB')
    out=Image.new('RGBA',(40,40),(0,0,0,0)); p=out.load()
    for y in range(40):
        for x in range(40):
            c=src.getpixel((x,y))
            if c in BODY:p[x,y]=(*c,255)
    return out

def patch(img, x0,y0,x1,y1, color=G):
    d=ImageDraw.Draw(img)
    # repaint only existing art pixels, not the transparent background
    for y in range(max(0,y0),min(40,y1+1)):
        for x in range(max(0,x0),min(40,x1+1)):
            if img.getpixel((x,y))[3]: img.putpixel((x,y),(*color,255))

def clear_face(img):
    # Politoed's reusable head base: preserve the silhouette and pink cheek;
    # clear only the eye/mouth artwork before placing a new expression.
    patch(img,18,9,30,24,G)
    # restore a quiet shadow at the rear of the muzzle
    d=ImageDraw.Draw(img)
    for x,y in [(18,10),(18,11),(18,12),(19,9),(20,9),(18,17),(18,18),(19,18)]:
        if img.getpixel((x,y))[3]: img.putpixel((x,y),(*S,255))

def px(img, points, color):
    for x,y in points:
        if 0<=x<40 and 0<=y<40 and img.getpixel((x,y))[3]:
            img.putpixel((x,y),(*color,255))

def eye(img, kind):
    d=ImageDraw.Draw(img)
    # Eye placement is deliberately compact; it follows the 3/4 Politoed head in the source portraits.
    if kind in ('normal','wide','sparkle'):
        pts=[(19,11),(20,10),(22,10),(24,12),(24,14),(22,16),(20,15),(19,13)]
        px(img,pts,O); px(img,[(20,11),(21,11),(22,11),(23,12),(23,14),(22,14),(20,14)],L)
        px(img,[(21,12),(22,12),(22,13)],O)
        if kind=='sparkle': px(img,[(20,11),(23,13),(21,14)],L)
        if kind=='wide': px(img,[(20,10),(21,10),(23,11),(24,12),(24,14),(23,15),(19,13)],L)
    elif kind=='closed':
        px(img,[(19,13),(20,14),(21,14),(22,13),(23,13)],O)
        px(img,[(19,14),(20,15),(21,15),(22,14)],S)
    elif kind=='angry':
        px(img,[(18,11),(19,11),(20,12),(21,12),(22,13),(23,13)],O)
        px(img,[(20,13),(21,13),(22,14)],L); px(img,[(21,13)],O)
    elif kind=='determined':
        px(img,[(19,12),(20,12),(21,12),(22,13),(23,13)],O)
        px(img,[(20,13),(21,13),(22,13)],L); px(img,[(21,13)],O)
    elif kind=='dizzy':
        px(img,[(21,10),(22,10),(23,11),(23,12),(22,13),(21,13),(20,12),(20,11),(21,11)],O)
        px(img,[(22,11),(22,12),(21,12)],G)
        px(img,[(22,14),(23,14),(23,15),(22,16),(21,16),(21,15)],O)
    elif kind=='sad':
        px(img,[(19,12),(20,11),(21,11),(22,12),(23,12)],O)
        px(img,[(20,12),(21,12),(22,13)],L); px(img,[(21,12)],O)
    elif kind=='blank':
        px(img,[(19,11),(20,10),(22,10),(24,12),(24,14),(22,16),(20,15),(19,13)],O)
        px(img,[(20,11),(21,11),(22,11),(23,12),(23,14),(22,15),(20,14)],L)
    elif kind=='squint':
        px(img,[(18,13),(19,13),(20,14),(21,14),(22,13),(23,13)],O)
        px(img,[(20,13),(21,13)],S)
    else:
        eye(img,'normal')

def mouth(img, kind):
    d=ImageDraw.Draw(img)
    if kind=='closed':
        # The small yellow lower lip keeps the expression readable at 1x.
        d.polygon([(18,19),(20,20),(26,20),(29,19),(28,22),(26,23),(21,23),(19,22)],fill=Y)
        px(img,[(18,19),(20,19),(22,20),(26,20),(28,19)],O)
        px(img,[(21,22),(22,23),(26,23),(27,22)],B)
    elif kind=='smile':
        d.polygon([(17,18),(20,19),(27,19),(30,18),(29,22),(27,24),(20,23),(18,21)],fill=O)
        d.polygon([(19,19),(21,20),(27,20),(28,19),(27,22),(20,22)],fill=MD)
        d.polygon([(20,21),(27,21),(26,23),(21,23)],fill=P)
        px(img,[(21,22),(22,23),(25,23),(26,22)],PD)
    elif kind=='open':
        d.polygon([(17,16),(20,15),(28,15),(31,17),(31,22),(29,25),(20,24),(17,22)],fill=O)
        d.polygon([(18,17),(21,16),(28,16),(30,18),(29,22),(20,22),(18,20)],fill=MD)
        d.polygon([(19,20),(25,20),(29,21),(28,23),(21,23),(19,22)],fill=P)
        px(img,[(21,22),(22,23),(26,23),(27,22)],PD)
    elif kind=='o':
        d.rectangle((20,18,24,23),fill=O)
        d.rectangle((21,19,23,22),fill=MD)
        px(img,[(22,20)],P)
    elif kind=='frown':
        px(img,[(18,21),(19,21),(20,20),(21,20),(22,21),(23,21),(24,22),(26,22),(27,21)],O)
        px(img,[(20,22),(21,22),(22,23),(24,23),(25,22)],B)
    elif kind=='flat':
        px(img,[(18,20),(19,20),(20,20),(21,21),(23,21),(24,20),(25,20),(26,20),(27,20)],O)
    elif kind=='tiny':
        px(img,[(21,20),(22,19),(24,20),(24,22),(22,23),(21,22)],O)
        px(img,[(22,20),(23,20),(23,21)],MD)
    else: mouth(img,'closed')

def tear(img, x=19, y=16, side='down'):
    # Pale tear with a single dark-green edge; stays inside the established palette.
    px(img,[(x,y),(x+1,y+1),(x+1,y+3),(x,y+4)],L)
    px(img,[(x-1,y+1),(x-1,y+2)],S)

def sweat(img):
    px(img,[(27,10),(28,9),(29,10),(29,12),(28,13),(27,12)],L)
    px(img,[(28,10),(28,11)],(159,215,231))

def create(emotion):
    # Pick one of the existing 2D head bases, then redraw only the face.
    if emotion in UPSTREAM:
        return art_from(REF/(emotion+'.png'))
    if emotion in {'Angry','Joyous','Happy'}:
        art=art_from(REF/'Shouting.png')
    elif emotion in {'Crying','Pain','Stunned','Worried','Teary-Eyed','Dizzy'}:
        art=art_from(REF/'Surprised.png')
    else:
        art=art_from(REF/'Inspired.png')
    clear_face(art)
    if emotion=='Happy': eye(art,'closed');mouth(art,'smile')
    elif emotion=='Pain': eye(art,'squint');mouth(art,'open');tear(art,20,15);sweat(art)
    elif emotion=='Angry': eye(art,'angry');mouth(art,'open');px(art,[(17,10),(18,10),(19,11)],O)
    elif emotion=='Worried': eye(art,'sad');mouth(art,'frown');px(art,[(18,9),(19,8),(21,8),(23,9)],O);tear(art,23,15)
    elif emotion=='Sad': eye(art,'sad');mouth(art,'frown');tear(art,21,15)
    elif emotion=='Crying': eye(art,'wide');mouth(art,'open');tear(art,19,15);tear(art,23,15)
    elif emotion=='Teary-Eyed': eye(art,'sparkle');mouth(art,'closed');tear(art,23,15)
    elif emotion=='Determined': eye(art,'determined');mouth(art,'flat');px(art,[(18,9),(19,9),(20,10),(21,10)],O)
    elif emotion=='Joyous': eye(art,'closed');mouth(art,'open');px(art,[(15,16),(16,15),(16,14)],P);px(art,[(31,15),(32,16)],P)
    elif emotion=='Dizzy': eye(art,'dizzy');mouth(art,'o');sweat(art)
    elif emotion=='Special0': eye(art,'sparkle');mouth(art,'smile');px(art,[(16,10),(16,9),(17,9)],L)
    elif emotion=='Special1': eye(art,'wide');mouth(art,'tiny');tear(art,24,15)
    elif emotion=='Sigh': eye(art,'closed');mouth(art,'flat');px(art,[(27,16),(28,15),(29,16),(29,18)],L)
    elif emotion=='Stunned': eye(art,'blank');mouth(art,'o');px(art,[(17,8),(18,8)],L)
    elif emotion=='Special2': eye(art,'dizzy');mouth(art,'open');px(art,[(15,15),(16,14),(16,13)],P)
    elif emotion=='Special3': eye(art,'angry');mouth(art,'smile');px(art,[(27,9),(28,8),(29,9)],L)
    return art

def compose(emotion, art):
    bg=Image.open(BGDIR/(emotion+'.png')).convert('RGB')
    out=bg.convert('RGBA')
    out.alpha_composite(art)
    # Explicit palette restriction is a final guard against ImageDraw internals.
    return out.convert('RGB')

# Build the 20 canonical slots and their mirrored half.  The four existing
# SpriteCollab portraits are copied byte-for-byte; only missing expressions are
# rendered from the reusable head base above.
for e in EMOTIONS:
    if e in UPSTREAM:
        # Preserve upstream PNG bytes; do not rewrite Chunsoft/PMDCollab art.
        shutil.copyfile(REF/(e+'.png'), OUT/(e+'.png'))
        im=Image.open(OUT/(e+'.png')).convert('RGB')
    else:
        im=compose(e,create(e))
        im.save(OUT/(e+'.png'))
    im.transpose(Image.Transpose.FLIP_LEFT_RIGHT).save(OUT/(e+'^.png'))

# SpriteBot/SpriteViewer order: five columns, four rows, then the flipped half.
sheet=Image.new('RGB',(200,320),(0,0,0))
for i,e in enumerate(EMOTIONS):
    im=Image.open(OUT/(e+'.png')).convert('RGB')
    sheet.paste(im,((i%5)*40,(i//5)*40))
    sheet.paste(im.transpose(Image.Transpose.FLIP_LEFT_RIGHT),((i%5)*40,160+(i//5)*40))
sheet.save(OUT/'Sheet.png')
