"""Render any listed SpriteCollab animation sheet on demand, without species profiles.
Source PNG/XML/credits are pinned and cached outside Git. This is NOT a PMDO hook.
Example: python catalogue_surface.py --source 0025/Idle-Anim.png --phase 6 --output exports/tera_v2/custom/preview.png
"""
from pathlib import Path
import sys,csv,subprocess,hashlib,xml.etree.ElementTree as ET,argparse
from PIL import Image
from prismatic import sheet
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'exports/tera_v2';CACHE=ROOT/'.cache/tera_v2/native'
PIN='3609a86be2a4c8ad7cf255bd2255f044daafe24f'

def catalogue():
    with (OUT/'spritecollab_catalogue.csv').open() as f:return {r['sprite_relative_path']:r for r in csv.DictReader(f)}

def native(path):
    if path.startswith('/') or '..' in Path(path).parts:raise ValueError('Invalid repository-relative path')
    target=CACHE/path
    if not target.exists():
        target.parent.mkdir(parents=True,exist_ok=True)
        r=subprocess.run(['gh','api',f'repos/PMDCollab/SpriteCollab/contents/sprite/{path}?ref={PIN}','-H','Accept: application/vnd.github.raw+json'],capture_output=True,timeout=60)
        if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace')[:600])
        target.write_bytes(r.stdout)
    return target

def load(path,index=None):
    index=catalogue() if index is None else index
    if path not in index:raise ValueError('Sheet absent from complete pinned inventory')
    file=native(path);raw=file.read_bytes()
    sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if sha!=index[path]['git_blob_sha']:raise ValueError('Source blob hash mismatch')
    parent=str(Path(path).parent);xml=native(parent+'/AnimData.xml');credits=native(parent+'/credits.txt')
    nodes={n.findtext('Name'):n for n in ET.parse(xml).getroot().findall('./Anims/Anim')}
    action=Path(path).name.removesuffix('-Anim.png');node=nodes[action];seen=set()
    while node.findtext('CopyOf'):
        name=node.findtext('Name')
        if name in seen:raise ValueError('Cyclic CopyOf')
        seen.add(name);node=nodes[node.findtext('CopyOf')]
    size=[int(node.findtext('FrameWidth')),int(node.findtext('FrameHeight'))]
    image=Image.open(file).convert('RGBA')
    if image.width%size[0] or image.height%size[1]:raise ValueError('Native geometry mismatch')
    return image,size,{'source':path,'git_blob_sha':sha,'cell_size':size,'source_sheet_size':image.size,'credits':credits.read_text(),'xml_sha256':hashlib.sha256(xml.read_bytes()).hexdigest()}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--phase',type=int,default=0);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    if not args.output.resolve().is_relative_to(OUT.resolve()):raise ValueError('Output must stay in exports/tera_v2, never in native or approved source folders')
    image,size,info=load(args.source);result=sheet(image,size,args.phase)
    args.output.parent.mkdir(parents=True,exist_ok=True);result.save(args.output)
    print(info)
