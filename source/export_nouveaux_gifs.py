"""Previews GIF des nouvelles références, en jour puis en nuit, depuis les vrais calques."""
from pathlib import Path
from PIL import Image,ImageDraw
import json
from prepare_paysages_nouveaux import CONFIG
from verify_falaise import references,expected

R=Path(__file__).resolve().parents[1]


def export():
    output=R/'previews';output.mkdir(exist_ok=True)
    for name,cfg in CONFIG.items():
        root=R/'paysages'/name;m=json.loads((root/'kit.json').read_text());size=tuple(m['dimensions'])
        width=320 if name=='etang' else 384;height=round(size[1]*width/size[0]);frames=[]
        for mode in ['jour','nuit']:
            refs=references(root,m,mode)
            for frame in range(24):
                q=expected(refs,frame,size).convert('RGB').resize((width,height),Image.Resampling.NEAREST)
                board=Image.new('RGB',(width,height+24),(21,28,29));board.paste(q,(0,0))
                ImageDraw.Draw(board).text((8,height+6),cfg['label']+' — '+('Jour' if mode=='jour' else 'Nuit'),fill=(235,224,197))
                frames.append(board)
        sample=Image.new('RGB',(width*2,height+24));sample.paste(frames[0],(0,0));sample.paste(frames[24],(width,0))
        palette=sample.quantize(colors=256,dither=Image.Dither.NONE)
        indexed=[q.quantize(palette=palette,dither=Image.Dither.NONE) for q in frames]
        dest=output/f'{name}_jour_nuit.gif'
        indexed[0].save(dest,save_all=True,append_images=indexed[1:],duration=250,loop=0,optimize=True,disposal=1)
        with Image.open(dest) as check:
            total=0
            for i in range(check.n_frames):check.seek(i);total+=check.info.get('duration',0)
            assert total==12000 and check.size==(width,height+24)
            print(dest.name,check.n_frames,'images,',total,'ms,',dest.stat().st_size,'octets')


if __name__=='__main__':export()
