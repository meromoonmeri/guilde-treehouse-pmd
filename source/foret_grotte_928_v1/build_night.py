"""Génère variante nuit Abyss exacte pour forêt 928x1152, depuis les calques jour natifs."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from PIL import Image
import json
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'source/cote_v4_abyss'))
from night import night
R=Path(__file__).resolve().parents[2]
O=R/'exports/foret_grotte_928_v1/forest_cave_928'
manifest=json.loads((R/'exports/foret_grotte_928_v1/manifest.json').read_text())
m=manifest['maps'][0]
night_layers=[]
for l in m['layers']:
    src=O/l['file']
    im=Image.open(src).convert('RGBA')
    n=night(im)
    out_name=l['file'].replace('Foret928_','Foret928_NUIT_')
    n.save(O/out_name)
    # tsx
    import xml.etree.ElementTree as ET
    root=ET.Element('tileset', version='1.10', name=Path(out_name).stem, tilewidth='8', tileheight='8', columns=str(928//8), tilecount=str(928//8*(1152//8)))
    ET.SubElement(root,'image', source=out_name, width=str(928), height=str(1152))
    ET.ElementTree(root).write(O/Path(out_name).with_suffix('.tsx').name, encoding='utf-8', xml_declaration=True)
    night_layers.append(dict(id=l['id']+'_nuit', file=out_name, provenance=l['provenance']+' (jour provenance, filtre nuit appliqué)', source=l['id']))
# composite nuit
comp_night=Image.new('RGBA',(928,1152))
for nl in night_layers:
    comp_night.alpha_composite(Image.open(O/nl['file']).convert('RGBA'))
comp_night.save(O/'composite_nuit.png')
# also save night provenance manifest
manifest['variants']={'jour': m['layers'], 'nuit': night_layers, 'nuit_composite': 'composite_nuit.png', 'nuit_filter': 'Abyss V4 tools/tile_night.py blob 438383f4, une seule application, jour natif inchangé'}
(R/'exports/foret_grotte_928_v1/manifest_nuit.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+'\n')
print(f'Nuit générée: {len(night_layers)} layers + composite_nuit.png (Abyss exact)')
