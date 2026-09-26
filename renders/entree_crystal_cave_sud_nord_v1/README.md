# ECC1 — Entrée Grotte de cristal sud → nord, format 4:3 vaste

Demande : « passe à la suite stp » (après EFF2). Biome **choisi par l'agent** : la salle du joyau de Waterfall Cave, dont la capture `Waterfall_Cave_gem_TDS.png` n'avait jamais servi de référence principale. Taille : 768 × 576 px = 96 × 72 cases de 8 px.

- Aperçu : `apercu_entree_crystal_cave_sud_nord_v1.html` (racine).
- Pack PMDO 0.8.12 : `ECC1_projet_pmdo_0812.zip`.
- Calques PNG 8 px : `ECC1_calques_png_8px.zip`, ORA, `review/ECC1_scene_animee.webp`.
- Source : `source/entree_crystal_cave_sud_nord_v1/`, 12 tests.

## Méthode : textures canoniques par rendu généré référencé

La capture est passée au générateur comme image de référence. Les prompts complets sont dans `manifest.json`.

1. `bruts/decor_magenta.png` : décor 4:3 **nouveau**.
   - Chemin de galets au sud entre des rochers, puis une grande salle semée de cristaux.
   - Deux bassins, peints en magenta, à l'ouest et à l'est.
   - Au nord, un joyau rose et un tunnel dans la paroi de stalactites.
2. `bruts/sol_complet.png` : sol de galets complet, obtenu par édition du décor. Il sert de sous-couche.
3. `bruts/eclats_poses.png` : éclats d'étoile sur magenta, rendus en 3 rangées de 4. Les rangées cyan et rose sont utilisées.

Découpage en pleine résolution, puis réduction matière par matière. Les palettes sont séparées : terrain, roche, fond, cristaux, tunnel.

## Animations

- **Bassins** : structure de la rivière Métano (lake_water d'EUL1), avec les **couleurs exactes de la capture** (aplat (0,87,143), bande (0,63,111), accent (23,135,191)) et sans liseré clair. 4 × 10 ticks.
- **Scintillements** : pixels Métano natifs, 4 × 10 ticks.
- **Éclats** : poses générées réduites à 14 px. Ils s'allument à tour de rôle sur les 18 plus gros cristaux, 8 phases allumées sur 48, 48 × 5 ticks.
- Toutes les boucles sont fermées (testé). La scène boucle en 240 ticks, soit 4 s.

## Fidélité au rip, mesurée par test

| Matière | Brut | Calque final |
|---|---|---|
| Sol de galets | 13,6 | 14,9 |
| Roche | 24,3 | 20,4 |
| Fond | 2,0 | 4,2 |

## Accès

- 1113 cases praticables.
- `entrance` est au sud. `donjon_seuil` est en (376, 224), en haut du sol, sous le joyau.
- Le tunnel est sur la paroi du fond, derrière la rangée de rochers, et on ne peut pas y marcher : le raccord reste à scripter.
- Pas de test PMDO en jeu. L'art n'est pas validé.
