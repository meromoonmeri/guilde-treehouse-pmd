# Terapagos — référence correcte de la forme Stellaire

**Correction utilisateur du 17 septembre 2026 : la planche générée ne ressemble pas à la forme Stellaire. Elle est rejetée comme base de production.**

## Références GitHub vérifiées

1. Art officiel, corps entier : [PokeAPI/sprites — official-artwork/10277.png](https://github.com/PokeAPI/sprites/blob/9d7c667b9ce7a400186892777c5affcb24fbeb84/sprites/pokemon/other/official-artwork/10277.png). La copie `official.png` est identique octet pour octet à cette révision. `official_on_dark.png` ne fait que la présenter sur un fond sombre, sans génération ni modification du sujet.
2. Portrait PMD : [SpriteCollab — portrait/1024/0002](https://github.com/PMDCollab/SpriteCollab/tree/3609a86be2a4c8ad7cf255bd2255f044daafe24f/portrait/1024/0002), `Normal.png` et `Normal^.png`, crédits originaux conservés. La copie de la vue inverse est nommée `Normal_reverse.png` dans ce dossier de référence uniquement ; ce n'est pas un export de soumission renommé.
3. Correspondance PokeAPI :1024=Terapagos normal,10276=Téracristal,**10277=Stellaire**. Correspondance SpriteCollab :1024/0002=Stellar, distinct de1024/0001=Terastal.
4. Le propre dépôt de l'utilisateur contient déjà cet art officiel depuis `fc8f595`, au chemin de ce dossier. Il n'est donc pas exact de dire qu'aucune référence n'était disponible : le problème était la non-fidélité du résultat généré à la référence fournie.

## Erreurs de la génération rejetée

`../../generation/terapagos_stellar_idle_views.png` est conservé comme **essai rejeté**, pas comme atlas de jeu ou travail validé. Ne pas l'utiliser dans un export Idle, ne pas le quantifier puis l'appeler conforme, ne pas produire Walk/Attack à partir de lui.

Le résultat remplace le globe sombre, facetté et multicolore par une boule cyan opaque générique ; simplifie fortement la couronne et l'ornement cristallin vertical ; invente une silhouette de tortue et une étoile ; ne conserve pas fidèlement les volumes de tête, de nageoires et de queue. Les directions arrière et la disposition des cristaux sont également incohérentes/non vérifiées.

## Porte de validation pour la reprise

Reprendre **une seule vue fidèle** depuis l'art officiel complet et le portrait natif avant de demander plusieurs directions. Étudier silhouette globale, globe facetté, anatomie de tête/nageoires/queue, couronne et ornement vertical, puis disposition des joyaux. Ne pas inverser automatiquement les couleurs/emblèmes asymétriques. La contrainte de15couleurs ne justifie pas une espèce/form e méconnaissable.

Dans la révision SpriteCollab vérifiée, le dossier `sprite/1024` contient la base et la forme0001, pas0002. Ne pas renommer un sprite Téracristal en Stellaire. Les portraits natifs sont des références, pas des créations du projet. Crédit courant `<@!350050109741858829>`, CC_BY-NC_4 selon `credits.txt`.

Provenance machine et résultat de comparaison dans `reference_audit.json`.
