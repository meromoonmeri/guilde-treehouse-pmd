"""Package the V2 layers, indexed sea phases and offline wrap/palette preview."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,zipfile
R=Path(__file__).resolve().parents[1];O=R/'sprites/cote_v2'
assert json.loads((O/'verification.json').read_text())['status']=='PASS'
old=Image.open(R/'sprites/falaises_cotieres_nues/02_terrasse/COTE02_02_TERRAIN_GENERE.png').convert('RGBA')
new=Image.open(O/'02_terrasse/COTEV2_02_03_TERRAIN.png').convert('RGBA')
board=Image.new('RGB',(928,496),'#20372a');d=ImageDraw.Draw(board);fp='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';font=ImageFont.truetype(fp,18);small=ImageFont.truetype(fp,13)
for x,label,im in [(8,'Avant : blocs arrondis',old),(472,'Après : assises et retours',new)]:
    d.text((x,12),label,font=font,fill='#ebd99b');crop=im.crop((288,416,736,832));board.paste(crop,(x,48),crop)
d.text((8,476),'Extraits sans redimensionnement. Roche générée : pas une copie certifiée des tuiles originales.',font=small,fill='#bed0b3')
board.save(O/'ROCHE_AVANT_APRES_NE_PAS_IMPORTER.png',optimize=True)
# Keep the archive lean: reference the PNGs already inside it rather than embedding duplicates.
m=json.loads((O/'manifest.json').read_text());view=[]
for z in m['zones']:
    base='sprites/cote_v2/'+z['id']+'/'
    view.append({'id':z['id'],'w':z['dimensions_px'][0],'h':z['dimensions_px'][1],
        'sky':base+z['files']['sky'],'terrain':base+z['files']['terrain'],
        'sea':[base+f for f in z['files']['sea']],
        'palettes':z['sea_palette_frames_rgb'],'cycle':z['cycle_indices']})
linked=(R/'source/cote_v2/viewer.html').read_text().replace('__DATA__',json.dumps(view)).replace('__CLOUD__',json.dumps('sprites/cote_v2/'+m['clouds']['tile'])).replace('__PERIOD__',str(m['clouds']['period_px'])).replace('__CLOUDY__',str(m['clouds']['y']))
linked=linked.replace('<button id="save">','<button id="save" hidden>').replace('<footer>','<footer>Aperçu lié aux PNG du pack : conserver cette arborescence. Les PNG sont déjà fournis séparément ; pour exporter une combinaison, utiliser la version autonome du visualiseur.<br>')
path=R/'cote_metano_v2_wrap_palette.zip' 
with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in sorted(O.rglob('*')):
        if p.is_file():z.write(p,p.relative_to(R))
    z.writestr('apercu_cote_v2.html',linked)
with zipfile.ZipFile(path) as z:assert z.testzip() is None
print('Pack MiB:',round(path.stat().st_size/1048576,2))
