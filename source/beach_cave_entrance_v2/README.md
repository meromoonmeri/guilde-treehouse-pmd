# Beach Cave Entrance V2 — la Crique des Palmes

Cette variante répond à la demande d'un **layout différent en plusieurs calques**, tout en gardant la contrainte canonique.

## Règles

- Le magenta (#ff00ff) n'est qu'un fond de contrôle pour inspecter les transparences des PNG de calques. Il n'entre jamais dans le Ground ni dans les `.tile`.
- Toutes les cellules finales viennent des feuilles natives auditées de `Minemaker0430/ExplorersOfSkyOrigins` : `D01P11A_layer1.tile`, `beach_animation.tile`, `D01P11A_layer2.tile` et `BeachCavePit.tile`.
- Aucun pixel du guide généré n'est copié dans la map.
- Aucune rotation, recoloration, interpolation, réduction ou agrandissement.

## Layout

- **33 × 18 cellules de 24 px**, soit 792 × 432 px ; `TexSize=3`.
- Arrivée au sud et seuil de grotte central au nord.
- Promenade sableuse sud–nord plus ouverte que la référence.
- Bouche centrale assemblée avec des cellules natives de la référence `beach_cave_pit`.
- Palmiers canoniques déplacés sur la terrasse ouest.
- Lagune centrale copiée depuis une sélection contiguë de cellules d'eau de `beach_cave_pit`.

## Calques livrés

1. `01_fond_magenta.png` — sable/ciel canonique ;
2. `02_animation_magenta.png` — bande animée canonique de `beach_animation.tile` ;
3. `03_eau_magenta.png` — eau canonique de `BeachCavePit.tile` ;
4. `04_premier_plan_magenta.png` — parois, roches et palmiers canoniques.

L'eau de la lagune utilise les **23 frames natives** de Beach Cave Pit (`FrameLength=8`). Le bandeau supérieur conserve en parallèle les **17 frames natives présentes dans le Ground référent** de `beach_animation` (`FrameLength=16`) ; aucune phase n'est dupliquée.

## Reproduction

```bash
python source/beach_cave_v1/audit.py
python source/beach_cave_entrance_v2/build.py
```

Sorties :

- `apercu_beach_cave_entrance_v2.html` ;
- `beach_cave_entrance_v2_pmdo.zip` ;
- `renders/beach_cave_entrance_v2/` ;
- `renders/beach_cave_entrance_v2/guide_layout_magenta.png` (guide hors import).

Le ZIP est séparé de la livraison canonique V1, avec un index propre contenant les quatre feuilles nécessaires. Les marqueurs sont présents mais la destination du donjon et le retour ne sont pas configurés.

## Limites

Le ZIP et les références sont contrôlés structurellement. Le rendu GPU, le déplacement, les collisions finales et le raccord de destination n'ont pas été validés dans PMDO ici.
