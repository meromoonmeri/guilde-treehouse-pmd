from pathlib import Path
from PIL import Image
R = Path(__file__).resolve().parents[2]
OUT = R / 'source/zones_south_north_v4/analysis'
ref0 = Image.open(R/'entrancearidedungeonpmdsky.png').convert('RGBA')
ref1 = Image.open(R/'roadundergound.png').convert('RGBA')
ca = Image.open(R/'exports/zones_south_north_v4/arid_dungeon_entrance/composite_jour.png')
cv = Image.open(R/'exports/zones_south_north_v4/violet_underground_road/composite_jour.png')
# sources des tampons arides
ref0.crop((8,144,56,208)).resize((48*3,64*3),0).save(OUT/'stamp_T1_src.png')
ref0.crop((336,152,384,208)).resize((48*3,56*3),0).save(OUT/'stamp_T2_src.png')
ref0.crop((64,160,112,208)).resize((48*3,48*3),0).save(OUT/'stamp_R1_src.png')
ref0.crop((296,160,344,208)).resize((48*3,48*3),0).save(OUT/'stamp_R2_src.png')
# rendus des tampons x2
ca.crop((0,312,80,400)).resize((80*2,88*2),0).save(OUT/'stamp_T1_out.png')
ca.crop((304,384,392,472)).resize((88*2,88*2),0).save(OUT/'stamp_T2_out.png')
ca.crop((48,472,136,544)).resize((88*2,72*2),0).save(OUT/'stamp_R1_out.png')
# violet : coupe gauche x=136, couture y=408, bas de map
cv.crop((96,200,176,280)).resize((80*2,80*2),0).save(OUT/'violet_cutL.png')
cv.crop((328,200,408,280)).resize((80*2,80*2),0).save(OUT/'violet_cutR.png')
cv.crop((0,368,504,448)).save(OUT/'violet_seam408.png')
cv.crop((150,60,350,160)).resize((200*2,100*2),0).save(OUT/'violet_mouths.png')
print('OK')
