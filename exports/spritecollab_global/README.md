# SpriteCollab — périmètre global confirmé

**Toute la collection**, et non plus seulement la liste du projet. Révision vérifiée : `3609a86be2a4c8ad7cf255bd2255f044daafe24f`.

| Inventaire | Nombre |
|---|---:|
| Entrées inventoriées (formes, genres, shinies compris) | 5640 |
| Entrées déclarées requises pour les sprites | 3825 |
| Entrées déclarées requises pour les portraits | 3849 |
| Jeux de sprites requis entièrement absents | 489 |
| Jeux de sprites existants mais incomplets selon le tracker | 2654 |
| Entrées portrait requises avec émotions manquantes | 1509 |
| Portraits manquants parmi les 16 émotions du contrat | 21636 |
| Vues inverses manquantes à examiner séparément | 54905 |
| Entrées avec travail principal identifié | 3333 |
| Entrées avec propositions upstream en attente | 22 |
| Créations terminées par cet inventaire | 0 |

## Lecture et limites

Les totaux incluent les variantes : ce ne sont pas des nombres de Pokémon distincts. Toutes les 5 640 entrées figurent dans le JSON/CSV, y compris celles marquées non requises. Ces dernières nécessitent un examen de pertinence avant de fabriquer des doublons. Les quatre expressions Special et les vues inverses sont suivies séparément.

Les manques du profil **32 actions du projet** ne sont pas les exigences officielles de chaque sprite SpriteCollab ; ils sont donc informatifs, pas comptés comme autant de créations obligatoires absentes. Les niveaux de complétion du tracker sont conservés. Les valeurs des dictionnaires sont des verrous, jamais des indicateurs de présence.

## Production

Progression distincte : à produire → généré → validation technique → validation artistique → test moteur. Aucun passage automatique de généré à terminé. Les propositions upstream en attente bloquent une production concurrente sans coordination. Les originaux, crédits et portraits approuvés sont conservés. Les essais locaux Zarude/Stellaire/Méga-Raichu en cours restent des brouillons, pas des trous déclarés comblés.

Fichiers : `backlog.json` (détail), `backlog.csv` (tableur), `apercu_spritecollab_global.html` à la racine (recherche et filtres). Reconstruction : `python source/sprite_audit_v2/global_backlog.py`. Ce plan ne lance pas de production autonome en arrière-plan.
