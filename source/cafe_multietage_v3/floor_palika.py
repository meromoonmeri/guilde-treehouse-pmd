from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
R=Path(__file__).resolve().parents[2];O=R/'renders/cafe_multietage_v3';im=Image.open(O/'bruts/A_accueil_sol_palika.png').convert('RGBA')
# Native floor pixels, repeated at integer 3x preview scale (no synthesized wood).
p=Image.open(R/'source/cafe_multietage_v1/references/Metano_Town_Cafe_Base.png').convert('RGBA').crop((128,160,192,224));p=p.resize((192,192),Image.Resampling.NEAREST)
floor=Image.new('RGBA',im.size)
for y in range(0,im.height,192):
 for x in range(0,im.width,192):floor.paste(p,(x,y))
m=Image.new('L',im.size);ImageDraw.Draw(m).polygon([(404,255),(839,255),(1173,444),(1173,630),(1043,746),(951,746),(951,710),(772,710),(772,746),(224,746),(96,631),(96,444)],fill=255)
# Retain wall contact shading and threshold; feather only the edge of the replacement.
m=m.filter(ImageFilter.GaussianBlur(4));im=Image.composite(floor,im,m)
im.save(O/'accueil_ludicolo/01_salle_intacte.png');m.save(O/'accueil_ludicolo/masque_reprise_sol.png')
