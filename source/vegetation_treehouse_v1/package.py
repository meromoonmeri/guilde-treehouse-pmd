from pathlib import Path
import zipfile,base64
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'exports/vegetation_treehouse_v1';ZIP=ROOT/'exports/vegetation_treehouse_v1_pack.zip'
def main():
 gallery=ROOT/'apercu_vegetation_treehouse_v1.html';html=gallery.read_text();start='<p id="download-pack">'
 if start in html:
  a=html.index(start);b=html.index('</p>',a)+4;html=html[:a]+html[b:]
 with zipfile.ZipFile(ZIP,'w') as z:
  for p in sorted(OUT.rglob('*')):
   if p.is_file():
    info=zipfile.ZipInfo(str(p.relative_to(OUT)),(2026,9,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,p.read_bytes())
  info=zipfile.ZipInfo('PREVIEW.html',(2026,9,17,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,html)
 with zipfile.ZipFile(ZIP) as z:assert z.testzip() is None
 link=start+'<a style="color:#f0dfaf" download="vegetation_treehouse_v1_pack.zip" href="data:application/zip;base64,'+base64.b64encode(ZIP.read_bytes()).decode()+'">Télécharger le pack PNG · TSX · GIF · documentation</a></p>'
 gallery.write_text(html.replace('</h1>','</h1>'+link,1));print('Pack verified:',ZIP.name,ZIP.stat().st_size,'bytes')
if __name__=='__main__':main()
