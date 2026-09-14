from pathlib import Path
import zipfile
R=Path(__file__).resolve().parents[2];p=R/'renders/layouts_magenta_v1'
with zipfile.ZipFile(p/'VARIANTES_PMD_calques.zip','w',zipfile.ZIP_DEFLATED) as z:
 for folder in ['variantes','rameaux_detoures']:
  for f in sorted((p/folder).rglob('*')):
   if f.is_file():z.write(f,f.relative_to(p))
 for name in ['README.md','enhancements_manifest.json','verification.json','PLANCHE_VARIANTES.png']:z.write(p/name,name)
print('Archive créée : cinq variantes récentes, PNG/frames/ORA/boucles complètes')
