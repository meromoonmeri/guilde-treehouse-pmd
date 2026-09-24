# Spinda V4 — workflow prioritaire après les corrections utilisateur

## Direction validée et périmètre

- L’utilisateur exige de passer à la **génération référencée**, pas à un nouvel agrandissement par bandes. Plusieurs pièces et étages, bordures suivant les ouvertures, extérieur magenta, éléments d’aménagement séparés.
- Après cinq études trop massives, il montre le café de **Spinda** et demande de reprendre ce design : pièce ovale, intérieur bois, plancher horizontal doré à lumières, rebord bas et entrée sud.
- Référence disponible : crop natif80,8–616,432 du Spinda EoSO local, `references/spinda_design_reference.png`. Le fichier joint affiché dans la conversation était inaccessible sur disque ; ne pas revendiquer une extraction de cet upload.
- Nouvel accueil généré en proposant deux variantes : **option1 choisie**. Le brut choisi est `accueil_spinda_fidele.webp`. Les quatre autres salles sont des déclinaisons de cette direction, **pas quatre approbations utilisateur**.
- Casino et salon bas retenus après inspection. Premier café d’étage (façade extérieure) et premier salon haut (grands ovales muraux) remplacés par deux nouvelles générations référencées sur l’accueil et le casino ; fichiers `cafe_spinda_corrige.webp` et `salon_haut_spinda_corrige.webp`.

Les douze générations sélectionnées à chaque appel, y compris celles supplantées, sont préservées en WebP lossless. Chaque conversion a comparé RGBA à l’original PNG avant retrait du doublon. Les variantes non choisies du comparateur restent hors de ce lot. Empreintes et statuts : `renders/cafe_spinda_reseau_v4/bruts/provenance_etudes.json` ; les cinq bruts utilisés sont explicitement indiqués dans le manifeste final.

## Build et véritables pixels natifs

`build.py` produit cinq cartes600×448 (générations1200×896 réduites à50% NN). **Cette opération ne s’applique jamais aux assets natifs.** Détourage du magenta et petits points isolés ; remplacement local de l’avis mural de l’accueil par son bois adjacent, raccord6–8px. Pas de collage de bandes pour fabriquer la pièce.

Les vingt-cinq calques sont stockés en WebP lossless dans le dépôt ; `package.py` les convertit en PNG après comparaison RGBA pour l’import. Le viewer fait également ces exports via canvas, avec grille et marqueurs exclus. `compose()` respecte les valeurs par défaut : fenêtres visibles à l’étage, escaliers de proposition masqués, aucun meuble ni feu en scène.

Fenêtre réellement extraite de `Guild_Heros_Room_Objects.tile`, crop64² aux coordonnées176,56. Banque/atlas/provenance conservés ici. Escalier spiralé96×72 de `Guild_Second_Floor_Objects.tile`, crop208,128–304,200. Source déjà conservée dans `source/cafe_multietage_v3/references/`. Les deux banques sont redécodées dans le vérificateur, pas simplement comparées au PNG de sortie.

Deux banques Spinda (`SpindaCafe1/2`) et les quatre poses feu/brasero Ledian existantes sont copiées sans transformation dans le catalogue. Kiosque et corps de fourneau restent **générés, non canoniques**. Le natif du feu ne rend pas le corps du fourneau natif.

Les lumières extraites du plancher sont des éléments **statiques générés**. Sous ces lumières seulement, le plancher est complété par le voisin non éclairé de la même rangée. Recomposition éclairée exacte ; fond masqué reconstruit, pas obtenu d’un atlas officiel. Murs et bordures = partitions de surfaces visibles, pas volumes complets mobiles.

## Réseau et limites

RDC accueil ; −1 casino et salon bas ; +1 café et salon des croisillons. Quatre liaisons réciproques dans le manifeste. Les sorties latérales sont relevées sur le plancher clair à l’extrémité, **pas sur la face verticale dorée au-dessus du passage**. La différence est vérifiée par couleur au point de repère. Les sorties E du casino/café et W du salon haut sont versy232 ; la porte W du salon bas est plus basse.

**Transitions de cartes indépendantes, pas mosaïque seamless.** Escaliers sur couches facultatives à l’échelle1× ; marqueurs et destinations sont des propositions, pas des warps PMDO. Pas de contrôle collision, spawn ou runtime revendiqué. `plan.json` et `guides/` concernent les anciennes études512² : NE PAS les utiliser comme coordonnées de la livraison finale. Le manifeste600×448 fait foi.

## Vérifications et commandes

```sh
.venv/bin/python source/cafe_spinda_reseau_v4/build.py
.venv/bin/python source/cafe_spinda_reseau_v4/verify.py
.venv/bin/python source/cafe_spinda_reseau_v4/package.py
node source/cafe_spinda_reseau_v4/test_viewer.cjs
.venv/bin/python source/cafe_spinda_reseau_v4/package.py
```

- Vérifications pixels, banques natives, recomposition, graphe, dimensions8px, poses/cadence du feu et magenta.
- Tests DOM simulés : navigation, choix de calques, PNG sans guides, escaliers optionnels, quatre poses, liens d’assets et protection contre courses asynchrones ; variantes dépôt et ZIP extrait. Alias racine vérifié comme redirection vers le bon atelier.
- ZIP : CRC, fichiers identiques, dépendances disponibles, pixels des PNG identiques aux WebP. Packaging déterministe, hors modification volontaire des rapports/docs.
- Inspection des compositions et fenêtres : images effectivement ouvertes, pas un test graphique automatisé du navigateur. Pas de test moteur.

Rapports dans `renders/cafe_spinda_reseau_v4/verification*.json`. Les anciennes livraisons sont conservées ; l’archivage lossless des bruts Beach et l’externalisation de ses138images de viewer économisent les doublons, sans remplacer ses rendus ou ZIP. Tests dédiés : `source/beach_layers_v1/test_compact.py`, `source/beach_layers_v1/test_viewer.cjs`, vérification de sources par `source/beach_network_v1/archive_raws.verify_record`.
