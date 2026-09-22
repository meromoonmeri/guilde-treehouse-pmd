"""Portable decoder: lossless atlases/layers -> full-size PNGs for import."""
from pathlib import Path
import argparse,json
from PIL import Image

def save(im,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    if im.getcolors(256) is not None:
        p=im.quantize(colors=256,method=Image.Quantize.FASTOCTREE)
        if p.convert('RGBA').tobytes()==im.tobytes():im=p
    im.save(path,optimize=True)

def export(root,output,frames=False,compositions=True):
    data=json.loads((root/'manifest.json').read_text());count=0
    for room in data['rooms']:
        if not room.get('new',True):continue
        for mode,desc in room['modes'].items():
            if compositions:
                im=Image.new('RGBA',tuple(room['size']))
                for layer in desc['layers']:im.alpha_composite(Image.open(root/layer['file']).convert('RGBA'))
                save(im,output/room['id']/mode/f"BeachExt_{room['id']}_{mode}_composition.png");count+=1
            if frames:
                for ident,a in desc['animation'].items():
                    atlas=Image.open(root/a['file']).convert('RGBA');x,y,w,h=a['rect']
                    for k in range(a['frames']):
                        cx=k%a['columns']*w;cy=k//a['columns']*h;im=Image.new('RGBA',tuple(room['size']));im.paste(atlas.crop((cx,cy,cx+w,cy+h)),(x,y))
                        save(im,output/room['id']/mode/'animation'/ident/f"BeachExt_{room['id']}_{mode}_{ident}_{k:02d}.png");count+=1
    return count

if __name__=='__main__':
    here=Path(__file__).resolve().parent;default=here if (here/'manifest.json').exists() else here.parents[1]/'renders/beach_extension_v2'
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,default=default);parser.add_argument('--output',type=Path);parser.add_argument('--frames',action='store_true',help='Also decode all 512 water/foam PNG frames')
    args=parser.parse_args();print('Exported',export(args.root,args.output or args.root/'export_png',args.frames),'PNG files')
