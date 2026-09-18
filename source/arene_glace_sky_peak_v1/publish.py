from pathlib import Path
import json,zipfile
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'renders/arene_glace_sky_peak_v1'
def main():
 m=json.loads((OUT/'manifest.json').read_text())
 template=(HERE/'viewer.html').read_text().replace('__DATA__',json.dumps(m,ensure_ascii=False).replace('</','<\\/'))
 (OUT/'index.html').write_text(template.replace('<!--BASE-->',''))
 (ROOT/'apercu_arene_glace_sky_peak_v1.html').write_text(template.replace('<!--BASE-->','<base href="renders/arene_glace_sky_peak_v1/">'))
 with zipfile.ZipFile(OUT/'ARENE_SKYPEAK_V1_pack.zip','w',zipfile.ZIP_DEFLATED) as z:
  for p in sorted(OUT.rglob('*')):
   if p.is_file() and p.suffix!='.zip' and 'bruts' not in p.parts:
    if p.name=='index.html':z.writestr('index.html',p.read_text().replace('href="ARENE_SKYPEAK_V1_pack.zip" download>Télécharger PNG + ORA ↓','href="OUVRIR.txt">Notice du kit'))
    else:z.write(p,str(p.relative_to(OUT)))
  z.write(HERE/'verification.json','controles/verification.json')
  z.writestr('OUVRIR.txt','Ouvrir index.html ou ARENE_SKYPEAK_V1_editable.ora. PNG960x720 alignés en0,0. NoticeREADME.md. Les bruts et scripts restent dans le dépôt GitHub ; les liens source/ ne sont pas inclus dans ce kit compact. Pas de carte moteur intégrée.\n')
 print('Galerie + kit',round((OUT/'ARENE_SKYPEAK_V1_pack.zip').stat().st_size/1024**2,2),'MiB')
if __name__=='__main__':main()
