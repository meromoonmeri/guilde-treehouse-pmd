"""Package the verified standalone editing project and lossless offline viewer."""
from pathlib import Path
import base64
import io
import json
import shutil
import zipfile
from PIL import Image

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
WEB=ROOT/'sprites/cote_v3_0812'
PACK=Path.home()/'.cache/cote_v3_0812_pack'
VIEWER='apercu_cotes_v2_0812.html'
ZIP='cotes_v2_0812_pmdo.zip'


def main():
    from verify import main as verify
    verify()
    manifest=json.loads((WEB/'manifest.json').read_text());required=set()
    for zone in manifest['zones']:
        for mode in ['jour','nuit']:
            required.update(zone['id']+'/'+f for f in zone['variants'][mode]['layers'])
    required.update('fonds/'+p.name for p in (WEB/'fonds').glob('*.png'))
    images={}
    for name in sorted(required):
        im=Image.open(WEB/name).convert('RGBA');stream=io.BytesIO()
        im.save(stream,format='WEBP',lossless=True,exact=True,method=6)
        raw=stream.getvalue();decoded=Image.open(io.BytesIO(raw)).convert('RGBA')
        assert decoded.tobytes()==im.tobytes() and decoded.size==im.size
        images[name]='data:image/webp;base64,'+base64.b64encode(raw).decode()
    html=(HERE/'viewer.html').read_text().replace('__DATA__',json.dumps({'manifest':manifest,'images':images},ensure_ascii=False,separators=(',',':')))
    (ROOT/VIEWER).write_text(html)
    (PACK/VIEWER).write_text(html.replace(f'<a href="{ZIP}" download>Pack PMDO ↓</a>','<span class="small">Pack extrait · voir README.md</span>'))
    for destination in [PACK/'README.md',WEB/'README.md']:shutil.copyfile(HERE/'README.md',destination)
    report=json.loads((PACK/'verification.json').read_text());report['lossless_viewer_images']=len(images)
    for path in [PACK/'verification.json',HERE/'verification.json',WEB/'verification.json']:
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    with zipfile.ZipFile(ROOT/ZIP,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path in sorted(PACK.rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                info=zipfile.ZipInfo('cotes_v2_0812/'+path.relative_to(PACK).as_posix(),(2026,9,12,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
                archive.writestr(info,path.read_bytes(),compresslevel=9)
    with zipfile.ZipFile(ROOT/ZIP) as archive:
        assert archive.testzip() is None
        assert len([n for n in archive.namelist() if n.endswith('.rsground')])==20
        assert 'cotes_v2_0812/Content/Tile/index.idx' in archive.namelist()
        assert 'cotes_v2_0812/Mod.xml' in archive.namelist()
    print(f'{len(images)} lossless images; HTML {(ROOT/VIEWER).stat().st_size/2**20:.2f} MiB; ZIP {(ROOT/ZIP).stat().st_size/2**20:.2f} MiB')


if __name__=='__main__':main()
