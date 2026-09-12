"""Verify existing build, make a lossless standalone viewer and the native ZIP."""
from pathlib import Path
import base64
import importlib.util
import io
import json
import shutil
import zipfile

from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent
WEB=ROOT/'sprites/cote_dix_zones'
PACK=Path.home()/'.cache/cote_dix_pack'


def main():
    spec=importlib.util.spec_from_file_location('verify_ten_coasts',HERE/'verify.py')
    checks=importlib.util.module_from_spec(spec);spec.loader.exec_module(checks)
    checks.main()
    manifest=json.loads((WEB/'manifest.json').read_text())
    required=set()
    for zone in manifest['zones']:
        for mode in ['jour','nuit']:
            required.update(zone['id']+'/'+f for f in zone['variants'][mode]['layers'])
    required.update('fonds/'+p.name for p in (WEB/'fonds').glob('*.png'))
    images={}
    for name in sorted(required):
        im=Image.open(WEB/name).convert('RGBA')
        stream=io.BytesIO();im.save(stream,format='WEBP',lossless=True,exact=True,method=6)
        encoded=stream.getvalue()
        decoded=Image.open(io.BytesIO(encoded)).convert('RGBA')
        assert decoded.size==im.size and decoded.tobytes()==im.tobytes(),name
        images[name]='data:image/webp;base64,'+base64.b64encode(encoded).decode()
    data={'manifest':manifest,'images':images}
    html=(HERE/'viewer.html').read_text().replace('__DATA__',json.dumps(data,ensure_ascii=False,separators=(',',':')))
    (ROOT/'apercu_dix_zones_metano.html').write_text(html)
    archive_html=html.replace('<a href="cote_metano_dix_zones_pmdo.zip" download>Pack PMDO ↓</a>',
                              '<span class="small">Pack natif déjà extrait · voir README.md</span>')
    (PACK/'apercu_dix_zones_metano.html').write_text(archive_html)
    # Presentation only, reduced by an integer factor; all real assets stay native.
    board=Image.new('RGB',(1312,5*288),'#101d2b');draw=ImageDraw.Draw(board)
    for i,z in enumerate(manifest['zones'][:10]):
        x=i%2*656;y=i//2*288
        draw.text((x+10,y+8),z['title']+' | NUIT / JOUR',fill='#ebeee9')
        for j,mode in enumerate(['nuit','jour']):
            im=Image.open(WEB/z['id']/f'{mode}_composition.png')
            board.paste(im.resize((328,256),Image.Resampling.NEAREST),(x+j*328,y+28))
    board.save(WEB/'PLANCHE_JOUR_NUIT_NE_PAS_IMPORTER.png',optimize=True)
    shutil.copyfile(HERE/'README.md',PACK/'README.md')
    shutil.copyfile(HERE/'README.md',WEB/'README.md')
    shutil.copyfile(ROOT/'source/pmdo_cote/INSTALLER.py',PACK/'INSTALLER.py')
    report=json.loads((PACK/'verification.json').read_text())
    report['standalone_viewer_lossless_images']=len(images)
    for p in [PACK/'verification.json',WEB/'verification.json',HERE/'verification.json']:
        p.write_text(json.dumps(report,ensure_ascii=False,indent=2))
    output=ROOT/'cote_metano_dix_zones_pmdo.zip'
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path in sorted(PACK.rglob('*')):
            if path.is_file():
                info=zipfile.ZipInfo(path.relative_to(PACK).as_posix(),(2026,9,12,0,0,0))
                info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
                archive.writestr(info,path.read_bytes(),compresslevel=9)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert len([n for n in archive.namelist() if n.endswith('.rsground')])==24
        assert not any(n.endswith('index.idx') for n in archive.namelist())
    print(f'{len(images)} images WebP sans perte; viewer {len(html.encode())/2**20:.2f} MiB')
    print(f'Pack natif verifie : {output} ({output.stat().st_size/2**20:.2f} MiB)')


if __name__=='__main__':main()
