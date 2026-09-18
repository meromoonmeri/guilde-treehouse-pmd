from pathlib import Path
import json
R=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;O=R/'renders/arene_glace_sky_peak_v3'
def main():
 m=json.loads((O/'manifest.json').read_text());m['aurora']['frames']=m['effect_frames']
 html=(HERE/'viewer.html').read_text().replace('__DATA__',json.dumps(m,ensure_ascii=False).replace('</','<\\/'))
 (O/'index.html').write_text(html.replace('<!--BASE-->',''))
 (R/'apercu_arene_glace_sky_peak_v3.html').write_text(html.replace('<!--BASE-->','<base href="renders/arene_glace_sky_peak_v3/">'))
 layers='# Dix calques PNG indépendants\n\n960×896, alignés en(0,0). Sol et rochers : pixels visibles seulement, pas de surfaces cachées reconstituées.\n\n[Composition / provenance](../README.md) · [Projet OpenRaster](../ARENE_SKYPEAK_V3_editable.ora)\n\n'
 for name,p in m['layers'].items():layers+=f'- [{name.replace("_"," ")}]({Path(p).name})\n'
 (O/'calques/README.md').write_text(layers)
 frames='# Quatre poses PNG de composition\n\nLe WebP contient les32phases. Quatre poses sont exportées individuellement pour éviter de dupliquer32fois le même grand terrain ; les32PNG de l’aurore restent accessibles dans V2.\n\n![Animation](../ARENE_SKYPEAK_V3_composition_animee.webp)\n\n'
 for frame,p in m['scene_frames'].items():frames+=f'- [Phase{int(frame):02d} / {int(frame)*.125:g}s]({Path(p).name})\n'
 (O/'frames_composition/README.md').write_text(frames)
 print('V3 viewer and individual PNG catalogs published.')
if __name__=='__main__':main()
