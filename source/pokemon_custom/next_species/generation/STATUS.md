# Statut des premiers essais

- `terapagos_stellar_idle_views.png` : **REJETÉ PAR L'UTILISATEUR** le17septembre2026. Ne pas exporter ni animer. Référence correcte et erreurs détaillées dans `../references/terapagos_stellar/README.md`.
- `zarude_idle_views.png` : source générée non finie, pas approuvée et pas encore exportée. Les directions doivent être inspectées/corrigées (la case annoncée ouest regarde notamment vers l'est). Aucun sprite jouable de Zarude n'est livré par la seule présence de cette image.

## Reprise après synchronisation GitHub / interruption

La branche distante bc15f714 a été récupérée ; les anciens fichiers locaux sont préservés dans le stash nommé « Safety snapshot of restored old workspace before syncing bc15f714 » (065c86366ae48007b9de461948c9e2e2a46309f6), sans réapplication aveugle sur les versions plus récentes.

Nouvelles générations effectivement présentes, **aucune exportée ou approuvée** :
- `terapagos_stellar_front_v2.png` : une vue, nouvelle reconstruction avec globe sombre, vraie hiérarchie tortue/couronne/symbole et joyaux ; revue initiale plus fidèle que la V1 rejetée, nombre/disposition des icônes et réduction native à vérifier. Ne pas dériver des directions avant revue.
- `zarude_west_v2.png` : le générateur a rendu DEUX profils malgré la demande d’un seul. Le sujet de gauche regarde bien à gauche et peut servir à corriger l’Ouest ; le sujet droit ne doit pas être pris pour l’Ouest. Pas encore découpé/exporté.
- `mega_raichu_x_emotions_v1.png` : oreilles dérivées avec intérieur doré et boucles absentes du portrait natif X ; ne pas exporter comme anatomie conforme.
- `mega_raichu_x_emotions_v2.png` : fichier effectivement présent malgré l’appel interrompu ; revue pas encore faite.
- `mega_raichu_y_emotions_v1.png` : seize cases générées, expressions et silhouette à comparer au Normal natif ; non exporté.
- `terapagos_stellar_emotions_v1.png` : seize cases générées, changement d’angle/exagération des expressions à revoir ; préserver Normal/Normal^ natifs.
- `zarude_walk_back_v1.png` : fichier reçu pour les quatre directions arrière/gauche, pas encore inspecté ni découpé. La moitié avant n’existe pas ; **aucun Walk complet livré**.
- `mega_raichu_y_emotions_v2.png` et `zarude_walk_front_v1.png` : appels interrompus, fichiers absents au contrôle.

Dernière correction utilisateur : production de **toutes les créations manquantes de SpriteCollab**, pas seulement cette liste. L’inventaire global figure dans `exports/spritecollab_global/` ; ces brouillons locaux n’y sont pas décomptés comme ressources terminées.
