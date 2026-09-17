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

## Correction utilisateur — visage Normal impératif

`terapagos_stellar_emotions_v1.png` est maintenant **REJETÉ PAR L’UTILISATEUR** : la forme du visage n’est pas fidèle à la référence. Ne pas exporter, ne pas compléter, ne pas relancer cette planche. Préserver les portraits Normal/Normal^ natifs. Cette suspension concerne les expressions, pas l’identité du sprite entier traité séparément.

Pour Méga-Raichu X et Y, les traits/anatomie du Normal sont une règle fixe, applicable à toutes les futures expressions : pas de modification de silhouette faciale, proportions, museau/nez, joues, implantation/design des yeux, oreilles ou marquages. Mouvements naturels uniquement. Les anciennes grandes planches ne constituent pas des modèles validés.

Deux nouvelles études individuelles `mega_raichu_{x,y}_happy_locked_v1.png` ont été générées directement depuis chaque Normal. Le script `../portrait_identity.py` ne prélève que les régions yeux/bouche et garde tous les autres pixels natifs inchangés ; il utilise exclusivement la palette native. Résultats 40×40 dans `exports/pokemon_custom/portrait_identity_v1/`, comparaison Normal/Happy et masques explicites. Ce sont des études sobres pour revue anatomique, **pas** des portraits Happy définitivement approuvés ; le fond Normal est conservé pour comparaison, l’association au fond Happy canonique reste à faire. Les tests de masque ne prouvent pas que l’expression est artistiquement réussie.

## Correction suivante — expressions animales et fonds canoniques

Raichu ne doit pas avoir de lèvres humaines, se mordre la lèvre ni montrer des dents. Les anciens `mega_raichu_{x,y}_Pain_locked_v2.png`, dont le prompt autorisait une ligne de dents, sont **écartés** ; ne pas les exporter. Remplacement généré : `*_Pain_animal_v3.png`. Les Angry/Sad/Surprised du lot interrompu existent bien et ont été repris avec zones d’expression bornées et bouche sans couleurs de dents/lèvres.

Carapagos suit désormais la même méthode depuis son Normal approuvé : nouvelles sources `tirtouga_Pain_locked_v1.png` et `tirtouga_Worried_locked_v1.png`, œil seul modifiable ; bec, narine et reste du visage natifs conservés.

`build_canonical_expressions.py` produit `exports/pokemon_custom/canonical_expressions_v1/` et `apercu_expressions_canoniques_v1.html` : 12 propositions placées sur leurs fonds canoniques (10 techniquement exportables ; Angry et Surprised de Méga Y à16couleurs sont explicitement bloqués et rangés en review, pas portraits_individual). Pas de réduction silencieuse de palette qui recolorerait les traits fixes. Normal X/Y conservés ; six portraits approuvés de Carapagos copiés avec hashes identiques. Les nouveaux candidats restent non approuvés artistiquement. Les planches sont partielles, pas des packs complets. Les vues inversées ne sont pas produites.

## Carapagos — huit expressions supplémentaires, méthode anatomique verrouillée

Nouvelles sources individuelles : `tirtouga_{Crying,Teary-Eyed,Determined,Joyous,Inspired,Dizzy,Sigh,Stunned}_locked_v1.png`. Elles ont été assemblées dans `canonical_expressions_v2` depuis le Normal approuvé, œil seul modifiable, puis fond canonique de chaque émotion. Revue de la planche4×4 effectuée ; bec/narine et silhouette conservés hors masque. Six portraits approuvés restent inchangés. Les dix nouveaux sujets ne sont pas des copies exactes entre eux ; l’écart des seuls fonds n’est pas utilisé comme preuve de nouvelles expressions.

Seize émotions de face Carapagos présentes, profil technique completPASS ; **pas** d’approbation artistique automatique, de vues inverses produites, de validation PMDO ou de soumission SpriteCollab acceptée. Raichu X/Y sont repris sans nouvelles créations dans ce lot ; les deux blocages16couleurs de Y restent ouverts. Terapagos Stellaire portraits toujours bloqué.
