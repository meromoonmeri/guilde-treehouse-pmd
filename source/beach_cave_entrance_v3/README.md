# Beach Cave Entrance V3 — la Plage Douillette

Variante **large et cozy** de Beach Cave, construite par rendu de cellules PMDO natives et organisée en plusieurs calques. La V1 et la V2 restent intactes.

## Layout

- **40 × 20 cellules de 24 px**, soit **960 × 480 px**, `TexSize=3`.
- Grande arrivée sableuse sud–nord, seuil de grotte centré et espace de circulation ouvert.
- Lagune animée sur le côté est.
- Terrasse de palmiers sur le côté ouest.
- Falaises latérales et petit épaulement rocheux devant la lagune pour une composition plus enveloppante.

## Méthode et sources

Le script résout chaque `TexLoc` du Ground vers les payloads des feuilles `.tile` auditées. Les cellules sont uniquement déplacées ou répétées à leur échelle native de 24 px : aucune rotation, recoloration, interpolation, déformation ou texture inventée.

Sources EoSO utilisées :

- `D01P11A_layer1.tile` — fond sable/ciel ;
- `beach_animation.tile` — bande supérieure animée ;
- `D01P11A_layer2.tile` — falaises, roches et palmiers ;
- `BeachCavePit.tile` — bouche de grotte et lagune animée.

Le guide `renders/beach_cave_entrance_v3/guide_layout_cozy_magenta.png` a servi uniquement à réfléchir à la composition. Aucun de ses pixels n'est importé.

## Calques et previews

1. `01_fond_magenta.png` — fond canonique ;
2. `02_animation_magenta.png` — animation supérieure canonique ;
3. `03_eau_magenta.png` — eau canonique ;
4. `04_premier_plan_magenta.png` — falaises, terrasse, palmiers et entrée.

Le magenta est seulement un fond de contrôle des transparences. Il n'est présent ni dans le Ground PMDO ni dans les feuilles `.tile` du ZIP.

L'eau conserve ses **23 frames natives** avec `FrameLength=8`. Le bandeau supérieur conserve les **17 frames présentes dans le Ground référent** de `beach_animation` avec `FrameLength=16` ; aucune phase n'est fabriquée.

## Sorties

- `apercu_beach_cave_entrance_v3.html` — aperçu interactif des phases et calques ;
- `beach_cave_entrance_v3_pmdo.zip` — archive PMDO à basenames distincts ;
- `renders/beach_cave_entrance_v3/` — Ground, manifest et previews ;
- `source/beach_cave_entrance_v3/build.py` — reproduction du rendu et du packaging.

## Limites

Le rendu local, les références de cellules, les hashes et l'intégrité ZIP sont contrôlés. PMDO/GPU, déplacements, collisions finales et raccord de destination n'ont pas été exécutés ici.
