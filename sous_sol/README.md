# Sous-sol du café — salle de concert privée

Le niveau sous le café : une cave voûtée dans la roche, aménagée en petite
salle de spectacle avec estrade, mur de rideaux de velours rouge et sièges
tournés vers la scène.

## Provenance des pixels

**Le sous-sol reprend littéralement la variante caverne du café.** Rien de cette
variante n'est regénéré :

* **la coque** — géométrie, sol à spirales, paroi de roche — vient du calque
  `interieur/variante_caverne/interieur_sans_deco_*.png` ;
* **le mobilier de café** — les deux comptoirs à auvent rayé rouge et bleu, la
  guirlande de fanions, les tables-souches et leurs tabourets, les plantes en
  pot — est extrait par différence entre les calques `avec_deco` et `sans_deco`
  de cette même variante, puis découpé en objets réutilisables
  (`cafe_caverne_deco_pmdo.png`).

Les deux sont simplement passés au format PMDO par `pipeline_sprite_pmdo.py`.
Ce sont donc les pixels d'origine, replacés — la cave est bien le même café,
au sous-sol.

Seuls les **éléments propres au spectacle** (estrade, rideaux de velours,
bancs, fauteuil, lampadaires, torches, cordons) sont générés, et uniquement en
planche d'objets détachés sur fond magenta — jamais en scène complète —
conformément à `tileset_pmd/AUDIT_PIPELINE_SPRITE.md`.

## Fichiers

| Fichier | Contenu |
|---|---|
| `sous_sol_sans_deco_{jour,nuit}.png` | la salle vide, 576 × 400 |
| `sous_sol_deco_seule_{jour,nuit}.png` | les aménagements seuls, fond transparent |
| `sous_sol_avec_deco_{jour,nuit}.png` | la composition |
| `sous_sol_*_grille8.png` | variantes calées sur la grille 8 px |
| `scene_objets_pmdo.png` | la planche des 14 éléments de scène générés |
| `cafe_caverne_deco_pmdo.png` | les 9 éléments de café repris à la variante caverne |

Tous partagent le **même cadre 576 × 400** (72 × 50 cellules de 8 px) et le même
offset que la salle du haut : les calques se superposent au pixel près.

## Aménagement

* **le café** — les deux comptoirs à auvent rayé de la variante caverne, placés
  de part et d'autre de la salle, la guirlande de fanions sur le mur du fond, et
  des tables-souches avec leurs tabourets dans les coins ;
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
| aménagée (jour) | 372 | 7,8 | 99,1 % | 0 | 1,1 % |
| aménagée (nuit) | 333 | 5,7 | 99,8 % | 0 | 0,8 % |
| déco café caverne | 252 | 5,8 | 99,8 % | 0 | 1,2 % |
| planche de scène | 151 | 4,3 | 100 % | 0 | 0,4 % |
| *étalon officiel EOS* | *147* | *4,8* | *99,0 %* | *0* | *8,3 %* |

La mise au format a fait passer la coque d'origine de **80 862 à 117 couleurs**
et de 2,7 % à 100 % de tuiles conformes, et le mobilier de café de **137 738 à
252 couleurs** (41,7 % → 99,8 % de tuiles conformes), sans altérer leur dessin :
la teinte moyenne du mur reste à 168/118/42 contre 169/118/42 à l'origine.

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
