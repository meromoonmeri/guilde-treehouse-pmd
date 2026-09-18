"""Galerie locale et catalogues Markdown lisibles directement sur GitHub."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent;OUT=ROOT/'renders/onde_boreale_glace_v2'

def main():
 data=(OUT/'manifest.json').read_text();m=json.loads(data)
 template=(HERE/'viewer.html').read_text().replace('__DATA__',data.replace('</','<\\/'))
 (OUT/'index.html').write_text(template.replace('<!--BASE-->',''))
 (ROOT/'apercu_onde_boreale_glace_v2.html').write_text(template.replace('<!--BASE-->','<base href="renders/onde_boreale_glace_v2/">'))
 rows=['# Onde seule — 32 calques PNG transparents\n',
 '![Onde seule animée](GLACE_BOREALE_V2_onde_transparente.webp)\n',
 '**32 × 125 ms = 4 s.** Nouveau dessin généré, variations de couleur et ondulation ±2 px, aucun ciel ni terrain. Les PNG sont tous alignés en768×640, à placer en(0,0).\n',
 '[Sur le ciel nocturne validé](../GLACE_BOREALE_V2_sur_ciel_nuit.webp) · [Notice complète](../README.md)\n',
 '| Phase | PNG | Phase | PNG |\n|---|---|---|---|']
 for i in range(16):rows.append(f'| {i:02d} | [PNG](GLACE_BOREALE_V2_onde_{i:02d}.png) | {i+16:02d} | [PNG](GLACE_BOREALE_V2_onde_{i+16:02d}.png) |')
 rows+=['\n## Assets d’animation\n','- [Dessin détouré](GLACE_BOREALE_V2_dessin_detoure.png)\n- [Plan d’indices fixe](GLACE_BOREALE_V2_indices.png)\n- [Alpha fixe avant ondulation](GLACE_BOREALE_V2_alpha.png)\n- [32 palettes et32 vecteurs de déplacement](GLACE_BOREALE_V2_palettes.json)\n',
 'Les indices et l’alpha sont fixes **avant** déplacement vertical. Après l’ondulation, l’alpha suit la forme. Les32images ne sont pas32dessins indépendants du générateur.']
 (OUT/'aurore/README.md').write_text('\n'.join(rows)+'\n')
 for z in m['zones']:
  folder=OUT/z['id'];relative=lambda p:Path(p).relative_to(z['id']).as_posix()
  text=f'''# {z['title']} — nouvelle onde boréale

![Composition animée]({relative(z['webp_loop'])})

**WebP en boucle,4s :** couleurs et légère ondulation. Nuages fixes dans cette boucle courte.

**[Extrait8s avec les nuages réellement en mouvement]({relative(z['webp_cloud_excerpt'])})** — une seule lecture, pas de raccord artificiel. Recharger l’image pour le rejouer.

[Scène jour PNG]({relative(z['scene_jour'])}) · [Scène nuit PNG]({relative(z['scene_nuit'])}) · [Projet ORA9calques]({relative(z['ora_nuit'])}) · [Atelier](../index.html)

Terrain et ciel de V1 conservés. Le chemin rejoint la grotte depuis le sud. Candidat référencé PMD, pas un Ground intégré ; collisions et échelle non validées en jeu.

## Calques PNG

| Plan | Jour | Nuit |
|---|---|---|
'''
  for key in z['layers']['jour']:
   text+=f'| {key} | [PNG]({relative(z["layers"]["jour"][key])}) | [PNG]({relative(z["layers"]["nuit"][key])}) |\n'
  text+='\nCiel, étoiles, nuages : [`../climat/`](../climat/). Onde indépendante : [`../aurore/`](../aurore/).\n\n##32frames de composition en PNG\n\n'
  text+=' · '.join(f'[{i:02d}]({relative(p)})' for i,p in enumerate(z['frames_nuit']))+'\n'
  (folder/'README.md').write_text(text)
 print('Galerie et quatre catalogues GitHub générés (aucun ZIP redondant).')
if __name__=='__main__':main()
