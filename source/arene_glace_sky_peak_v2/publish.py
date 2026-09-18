from pathlib import Path
import json
R=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;O=R/'renders/arene_glace_sky_peak_v2'
def main():
 m=json.loads((O/'manifest.json').read_text());template=(HERE/'viewer.html').read_text().replace('__DATA__',json.dumps(m,ensure_ascii=False).replace('</','<\\/'))
 (O/'index.html').write_text(template.replace('<!--BASE-->',''))
 (R/'apercu_arene_glace_sky_peak_v2.html').write_text(template.replace('<!--BASE-->','<base href="renders/arene_glace_sky_peak_v2/">'))
 for folder,field,title in [('aurore','frames','Onde panoramique seule — 32 PNG'),('frames_composition','scene_frames','Arène complète — 32 PNG')]:
  frames=m['aurora'][field] if folder=='aurore' else m[field]
  text=f'# {title}\n\n32 ×125ms =4s. Tous les PNG sont960×720, alignés en(0,0). Aucun wrap de l’aurore.\n\n'
  text+='![Animation]('+('ARENE_SKYPEAK_V2_onde_transparente.webp' if folder=='aurore' else '../ARENE_SKYPEAK_V2_composition_animee.webp')+')\n\n'
  text+='[Notice complète](../README.md) · [Atelier](../index.html)\n\n| Phase | PNG | Phase | PNG |\n|---|---|---|---|\n'
  for i in range(16):text+=f'| {i:02d} | [PNG]({Path(frames[i]).name}) | {i+16:02d} | [PNG]({Path(frames[i+16]).name}) |\n'
  if folder=='aurore':text+='\n[Indices](ARENE_SKYPEAK_V2_indices.png) · [Alpha avant ondulation](ARENE_SKYPEAK_V2_alpha.png) · [32palettes et déplacements](ARENE_SKYPEAK_V2_palettes.json).\n\nDessin généré guidé par PMD, pas un cycle officiel extrait. Les32frames viennent d’un seul dessin maître.\n'
  (O/folder/'README.md').write_text(text)
 print('Galerie et catalogues PNG/WebP publiés localement.')
if __name__=='__main__':main()
