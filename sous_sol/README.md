# Sous-sol du café — salle de concert privée

Le niveau sous le café : une cave voûtée dans la roche, aménagée en petite
salle de spectacle avec estrade, mur de rideaux de velours rouge et sièges
tournés vers la scène.

## Provenance des pixels

**La coque de la salle n'est pas une génération neuve.** C'est le calque
souterrain d'origine, celui à paroi rocheuse fourni au début du projet
(`interieur/variante_caverne/`), simplement remis au format PMDO. Sa géométrie,
son sol à spirales et sa paroi de roche sont donc conservés tels quels.

Seuls les **éléments de scène** sont générés, et uniquement en planche d'objets
détachés sur fond magenta — jamais en scène complète — conformément à la règle
établie dans `tileset_pmd/AUDIT_PIPELINE_SPRITE.md`.

## Fichiers

| Fichier | Contenu |
|---|---|
| `sous_sol_sans_deco_{jour,nuit}.png` | la salle vide, 576 × 400 |
| `sous_sol_deco_seule_{jour,nuit}.png` | les aménagements seuls, fond transparent |
| `sous_sol_avec_deco_{jour,nuit}.png` | la composition |
| `sous_sol_*_grille8.png` | variantes calées sur la grille 8 px |
| `scene_objets_pmdo.png` | la planche des 14 éléments de scène |

Tous partagent le **même cadre 576 × 400** (72 × 50 cellules de 8 px) et le même
offset que la salle du haut : les calques se superposent au pixel près.

## Aménagement

* **fond de scène** — trois pans de rideau de velours rouge formant un mur
  continu, surmontés d'une double frise suspendue ;
* **la scène** — estrade de bois au centre du fond, pupitre à partition et
  tambour posés à son pied ;
* **éclairage** — deux lampadaires de laiton encadrant la scène, deux torches
  murales sur les parois latérales ;
* **le public** — quatre bancs à dossier en deux rangées, retournés pour faire
  face à l'estrade, un fauteuil capitonné en place d'honneur au centre et deux
  tabourets de velours ;
* **l'entrée** — tapis rouge menant à l'escalier, encadré de deux cordons de
  velours ; l'escalier reste entièrement dégagé.

## Conformité PMDO

| Calque | Couleurs | Coul./tuile | Tuiles ≤16 | Semi-transp. | Orphelins |
|---|---|---|---|---|---|
| salle vide (jour) | 117 | 5,9 | 100 % | 0 | 0,0 % |
| salle vide (nuit) | 45 | 3,1 | 100 % | 0 | 0,0 % |
| aménagée (jour) | 231 | 6,9 | 99,8 % | 0 | 0,8 % |
| aménagée (nuit) | 188 | 4,4 | 100 % | 0 | 0,4 % |
| planche d'éléments | 151 | 4,3 | 100 % | 0 | 0,4 % |
| *étalon officiel EOS* | *147* | *4,8* | *99,0 %* | *0* | *8,3 %* |

La mise au format a fait passer la coque d'origine de **80 862 à 117 couleurs**
et de 2,7 % à 100 % de tuiles conformes, sans altérer son dessin.

## Reproduire

```bash
python3 tileset_pmd/poser_scene_sous_sol.py
python3 tileset_pmd/caler_grille8_interieur.py sous_sol/sous_sol_*.png
```

## Note sur la palette

La palette du café ne contient ni rouge velours ni or. Pour ces éléments, la
palette de référence a été étendue de 48 teintes issues de la génération
elle-même, en plus des 256 couleurs des assets réels — c'est le cas d'usage du
paramètre `--palette` de `pipeline_sprite_pmdo.py`.
