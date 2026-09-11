"""GIF démontrant la carte fixe et la palette cyclique de l'overlay cascade."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
import numpy as np

R=Path(__file__).resolve().parents[1]


def export():
    root=R/'paysages/cascades'
    m=json.loads((root/'kit.json').read_text());spec=m['fichiers']['jour']['operations']['cascade_01']
    ids=np.array(Image.open(root/spec['indices'])).astype(int)
    gray=np.rint(ids/max(1,ids.max())*255).astype('uint8')
    guide=Image.fromarray(gray).convert('RGB').resize((280,210),Image.Resampling.NEAREST)
    frames=[]
    for palette in spec['palettes']:
        im=Image.fromarray(np.array(palette,np.uint8)[ids]).resize((280,210),Image.Resampling.NEAREST)
        board=Image.new('RGB',(608,302),(18,33,41));d=ImageDraw.Draw(board)
        board.paste(guide,(12,35));board.paste(im,(316,35),im)
        d.text((12,12),'Indices fixes',fill=(235,227,201));d.text((316,12),'Palette animee',fill=(235,227,201))
        for i,index in enumerate(spec['cycled_indices']):d.rectangle((318+i*34,257,348+i*34,277),fill=tuple(palette[index][:3]))
        d.text((12,283),'Les pixels ne bougent pas : seules les couleurs changent.',fill=(197,214,213))
        frames.append(board.quantize(colors=128,dither=Image.Dither.NONE))
    path=R/'previews/palette_cycling_tt.gif'
    frames[0].save(path,save_all=True,append_images=frames[1:],duration=250,loop=0,optimize=False)
    print(path.name, len(frames),'phases de vraie palette,',path.stat().st_size,'octets')


if __name__=='__main__':export()
