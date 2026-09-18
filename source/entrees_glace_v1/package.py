from pathlib import Path
import json,zipfile
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'renders/entrees_glace_v1'
def main():
 data=(OUT/'manifest.json').read_text();template=(HERE/'viewer.html').read_text().replace('__DATA__',data.replace('</','<\\/'))
 page=template.replace('<!--BASE-->','')
 (OUT/'index.html').write_text(page)
 (ROOT/'apercu_entrees_glace_v1.html').write_text(template.replace('<!--BASE-->','<base href="renders/entrees_glace_v1/">'))
 files=[p for p in OUT.rglob('*') if p.is_file() and p.suffix!='.zip']
 repo='https://github.com/meromoonmeri/guilde-treehouse-pmd/blob/arena/01a0b45b-guilde-treehouse-pmd/'
 packpage=page.replace('../../source/cote_dix_zones/reference_autre_agent/source__falaise__nuages_native.png','references/nuages_native.png').replace('../../iceroadpmdsky.png','references/iceroadpmdsky.png').replace('../../apercu_cliffs_metano_v1.html',repo+'apercu_cliffs_metano_v1.html')
 with zipfile.ZipFile(OUT/'ICE_ENTRY_V1_pack.zip','w',zipfile.ZIP_DEFLATED) as archive:
  for p in files:
   name=str(p.relative_to(OUT))
   if name=='index.html':archive.writestr(name,packpage)
   else:archive.write(p,name)
  for name in ['verification.json','viewer_checks.json']:
   p=HERE/name
   if p.exists():archive.write(p,'controles/'+name)
  archive.write(ROOT/'iceroadpmdsky.png','references/iceroadpmdsky.png')
  archive.write(ROOT/'pmdskyicearena.png','references/pmdskyicearena.png')
  archive.write(ROOT/'source/cote_dix_zones/reference_autre_agent/source__falaise__nuages_native.png','references/nuages_native.png')
  archive.writestr('OUVRIR.txt','Ouvrir index.html après décompression. Calques et animations sont locaux, aucun serveur nécessaire. Lire README.md avant import. Les liens vers la méthode du dépôt ou le précédent lot nécessitent GitHub. PNG/ORA : candidats référencés, pas un mod PMDO intégré.\n')
 print('Galeries + ZIP',round((OUT/'ICE_ENTRY_V1_pack.zip').stat().st_size/1024**2,1),'MiB')
if __name__=='__main__':main()
