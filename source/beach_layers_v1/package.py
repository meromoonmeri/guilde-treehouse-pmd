"""Package only this beach delivery; never modify earlier assets."""
from pathlib import Path
import hashlib
import base64
import json
import zipfile
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/beach_layers_v1'
TARGET=OUT/'BeachV1_pack.zip'

def portable_viewer(page):
    # Keep archive viewers self-contained for file-origin canvas exports.
    start=page.index('const DATA=')+len('const DATA=');data,length=json.JSONDecoder().raw_decode(page[start:])
    def embed(value):
        return value if value.startswith('data:') else 'data:image/png;base64,'+base64.b64encode((ROOT/value).read_bytes()).decode()
    for layer in data['layers']:layer['uri']=embed(layer['uri'])
    data['surface']=[embed(v) for v in data['surface']];data['foam']=[embed(v) for v in data['foam']];data['reference']=embed(data['reference'])
    page=page[:start]+json.dumps(data,ensure_ascii=False)+page[start+length:]

    return page

def main():
    report=json.loads((OUT/'verification.json').read_text())
    viewer=json.loads((OUT/'verification_viewer.json').read_text())
    assert report['pass'] and viewer['pass'], 'Run the verification scripts first.'
    manifest=json.loads((OUT/'manifest.json').read_text())
    files=[p for p in OUT.rglob('*') if p.is_file() and p != TARGET and p.name != 'package_verification.json' and p.name != 'index.html']
    files += [p for p in Path(__file__).parent.iterdir() if p.is_file()]
    files += [ROOT/manifest['source']['file'],ROOT/manifest['wave_reference']['file']]
    page=(ROOT/'apercu_beach_calques_v1.html').read_text()
    page=portable_viewer(page)

    page=page.replace('<a class="btn" href="renders/beach_layers_v1/BeachV1_pack.zip" download>Pack complet · ZIP</a>','<span class="small">Pack complet déjà décompressé.</span>')
    with zipfile.ZipFile(TARGET,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(set(files)):z.write(p,p.relative_to(ROOT))
        z.writestr('apercu_beach_calques_v1.html',page)
    with zipfile.ZipFile(TARGET) as z:
        assert z.testzip() is None
        for p in sorted(set(files)):
            assert z.read(str(p.relative_to(ROOT)))==p.read_bytes(),p
        entries=len(z.namelist())
    (OUT/'package_verification.json').write_text(json.dumps({'crc':'PASS','file_identity':'PASS','entries':entries,'bytes':TARGET.stat().st_size,'sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest()},indent=2)+'\n')
    print(f'ZIP verified: {entries} entries, {TARGET.stat().st_size:,} bytes.')
if __name__=='__main__':main()
