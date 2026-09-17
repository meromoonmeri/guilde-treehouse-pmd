# Côte Métano — 10 falaises et animations multicouches V2

## Ouvrir / regarder
- Galerie autonome à la racine : **`apercu_references_calques_v2.html`**, télécharger puis ouvrir dans un navigateur. 10 falaises × 3 ambiances ; 8 calques masquables ; pause et export PNG.
- [Planche des 10 falaises](PLANCHE_10_FALAISES.png)
- [Aperçu animé lune](apercus/nuit_animation.webp) / [soleil](apercus/coucher_animation.webp)
- [Étoiles : layout 64 phases](planches/etoiles_64.png)
- [Halo : layout 64 phases](planches/halo_64.png)
- [Reflet lunaire : 8 clés](planches/reflet_lune_8_cles.png) / [64 phases](planches/reflet_lune_64.png)
- [Reflet solaire : 8 clés](planches/reflet_soleil_8_cles.png) / [64 phases](planches/reflet_soleil_64.png)

## Référence retenue
Le **promontoire côtier généré avant la guilde** (`renders/references_calques_v1/bruts/promontoire.png`), PAS le plateau de guilde. Les 10 dessins ont été générés avec ce promontoire et la référence canonique Métano. Huit appels terrain : deux planches de deux propositions et six propositions individuelles. Deux appels supplémentaires pour les planches de reflets, guidées par `IMG_4889.png` et `IMG_4899.jpeg`.

Ce sont des dessins générés guidés par Métano, **pas des tuiles natives ni une palette certifiée identique**. Les originaux sont conservés dans `bruts/` ; aucun ancien rendu n’est supprimé.

## Organisation des calques
Canvas de scène **960 × 600**. Voir `manifest.json` pour dimensions/positions terrain et source du ciel.

| Élément | Fichiers | Lecture |
|---|---|---|
| Ciel seul | `fonds/{jour,coucher,nuit}/01_ciel.png` | Fixe |
| Étoiles | `etoiles/00.png`…`63.png` | 64 × 80 ms, transparence, indépendant |
| Nuages | `fonds/*/03_nuages_wrap.png` | overlay transparent, wrap X 960 px, vitesse −4 px/s |
| Lune fixe | `astres/lune.png` | Dessin sans halo |
| Halo / shine | `astres/halo/00.png`…`63.png` | 64 × 80 ms, indépendant de la lune |
| Soleil fixe | `fonds/{jour,coucher}/04_soleil.png` | Indépendant de son reflet |
| Mer seule | `fonds/*/05_mer.png` | Sans reflet incrusté |
| Reflets | `reflets/{lune,soleil}/frames/00.png`…`63.png` | 152 × 218, position (674,281) sur scène gauche |
| Falaises | `falaises/01`…`10` | Originaux détourés + nuits + calques de scène |

Ordre arrière → avant : ciel / étoiles / nuages / halo / astre / mer / reflet / falaise. Pour les falaises à droite, **le fond complet est retourné horizontalement** pour placer l’astre et son reflet dans la partie dégagée ; le terrain lui-même n’est pas retourné.

### Animations et loop
- Reflets : **8 images clés réellement générées**, détourées et recalées sur une taille/ancre commune ; **64 phases exportées par interpolation en alpha prémultiplié**, avec raccord 7→0. Ce n’est ni l’animation originale du jeu ni 64 générations indépendantes. La variation inclut les formes des rides, pas seulement l’opacité de lignes fixes.
- Étoiles : scintillement paramétrique déphasé, disposition fixe, calque sans ciel.
- Lune : disque fixe, halo isolé ; modulation sinusoïdale du halo. Les étoiles et le halo ont chacun leurs fichiers, même s’ils partagent une période de 5,12 s dans l’aperçu.
- Nuages : dessiner deux copies du PNG, à `x = -floor(temps_secondes × 4) mod 960` et `x+960`. La période spatiale est **240 secondes**, indépendante des 64 phases lumineuses. Ne pas réinitialiser leur position à chaque boucle lumière.
- Les deux WebP courts montrent les cycles lumineux avec nuages fixes, afin de ne pas introduire de saut de nuages à 5,12 s. **Le wrap continu est démontré par la galerie HTML.**

### Planches propres
Toutes les planches exportées sont transparentes, sans texte ni fond magenta. Les reflets ont 4 colonnes × 2 lignes pour les clés, 8 × 8 pour les 64 phases. Chaque cellule mesure 152 × 218 px. La planche étoiles est une vue réduite 8 × 8 de cellules 240 × 150 ; utiliser les frames individuelles 960 × 600 pour l’import. Halo : cellules 220 × 220, position de la fenêtre (640,55) dans les frames complètes.

## Ciel du pack côtier
Source explicitement retenue : `cote_metano_v2_wrap_palette.zip`, membre `sprites/cote_v2/01_promontoire/COTEV2_01_00_CIEL_SANS_NUAGES.png`.
- Jour : **RGB du ciel source conservé**, recadrage des marges transparentes et ajustement nearest à 960 × 280.
- Coucher : même disposition des paliers, teintes lavande → pêche dérivées (pas une source sunset native du ZIP).
- Nuit : **filtre Abyss exact** sur ce ciel et sur les terrains (`source/cote_v4_abyss/night.py`).

## Audit visuel — ne pas confondre livraison et validation
Les 10 variantes sont livrées, mais ne sont pas toutes certifiées conformes au dessin demandé.
- 01 : proche du langage de la référence, plateau gauche.
- 02–04 : réserves sur contours plus rectilignes et silhouettes parfois isolées. Les calques de scène sont recadrés au premier plan ; une bande terminale de paroi est répétée vers le bas si nécessaire. **Les terrains détourés originaux restent intacts.** Cette extension mérite une retouche artistique avant intégration native.
- 05 : tracé de terre généré remplacé en partie par l’herbe canonique ; jonction encore perceptible.
- 06 : crochet latéral, matériau fin proche du promontoire ; validation utilisateur requise.
- 07 : terrasses décalées, quelques petites marques/rochers générés persistent malgré la correction partielle de l’herbe.
- 08 : paroi haute, creux frontal ; validation utilisateur requise.
- 09 : **réserve marquée**, blocs et contours trop gros par rapport à la référence.
- 10 : trois balcons latéraux ; strates assez régulières, à valider.

Limite de 10 appels de génération atteinte sur cette passe ; les dessins réservés sont signalés plutôt que présentés comme corrigés par le générateur.

## Vérifications et reproduction
`source/references_calques_v2/build.py` : génération des exports depuis les bruts conservés (Pillow + numpy). `gallery.py` : galerie autonome. `verify.py` : contrôles indépendants. `test_viewer.cjs` : contrôles JavaScript avec DOM simulé.

Résultats : **373 PNG décodés**, **30 recompositions exactes**, 10 conversions nocturnes terrain exactement égales au filtre Abyss, ciel jour vérifié contre le membre ZIP, 4 séries de 64 phases avec contrôle numérique du raccord, identité du wrap à 960 px. Galerie : 30 choix, 8 contrôles, pause/reset/masquage testés en DOM simulé.

**Pas de validation GPU/PMDO. Aucun mod natif ou fichier `.rsground` n’a été modifié.** Les vérifications numériques ne remplacent pas une validation artistique.
