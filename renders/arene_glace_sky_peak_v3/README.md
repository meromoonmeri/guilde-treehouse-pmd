# Arène V3 — roche/glace, horizon lointain et mer de sapins

![Arène animée](ARENE_SKYPEAK_V3_composition_animee.webp)

[Composition PNG](ARENE_SKYPEAK_V3_composition_nuit.png) · [Dix calques PNG](calques/README.md) · [Quatre poses PNG](frames_composition/README.md) · [Projet OpenRaster](ARENE_SKYPEAK_V3_editable.ora) · [Atelier interactif](index.html)

## Correction demandée

- **Terrain régénéré** d’après [`pmdskyicearena.png`](../../pmdskyicearena.png) et [`iceroadpmdsky.png`](../../iceroadpmdsky.png) : masses rocheuses enneigées, pics de glace irréguliers, champ de combat et approche sud. L’ancien petit anneau lisse n’est pas réutilisé.
- **Montagnes ramenées à une frise de l’horizon**, beaucoup plus petites que les reliefs de l’arène.
- **Vallée couverte de sapins enneigés**, entre cet horizon et le sommet de falaise. La canopée se poursuit derrière tout le premier plan, sans bande flottante coupée sur du ciel vide.
- Ciel bleu-noir, étoiles, **croissant natif33×36 à(800,64)** et aurore panoramique V2 conservés sans redimensionnement. Le canevas est prolongé vers le bas : **960×896**.

**Les nouvelles roches/glaces, montagnes et forêts sont des dessins générés guidés par les références canoniques, pas des copies de tuiles natives.** La fidélité artistique est à juger sur l’image ; aucun test de palette ne sert de preuve de motif canonique.

## Calques et animation

Dix plans alignés : ciel → étoiles → aurore → lune → montagnes → vallée forestière → sol visible/accès sud → roches arrière → immersion gauche → immersion droite.

Le découpage du nouveau terrain recompose exactement le dessin détouré. Il ne reconstitue **pas les surfaces cachées** : masquer un rocher peut laisser un trou. Le sol V1 reconstitué n’est pas réutilisé sous cette nouvelle géométrie.

L’aurore reprend les **32PNG V2 existants**, couleurs mobiles et légère ondulation±2px, sans translation horizontale. Boucle de4s,32×125ms. [PNG de l’effet seul](../arene_glace_sky_peak_v2/aurore/README.md) · [WebP transparent](../arene_glace_sky_peak_v2/aurore/ARENE_SKYPEAK_V2_onde_transparente.webp).

Le WebP ci-dessus contient les32compositions. Quatre poses PNG sont publiées individuellement pour éviter32copies lourdes du même terrain ; toutes les autres sont reproductibles depuis les dix calques et les PNG d’aurore.

## Sources et contrôles

- [Bruts de génération conservés](bruts/) ; le premier bandeau de forêt est conservé comme essai, le fond final utilise `mer_de_sapins_profonde_magenta.png`.
- [Manifest, normalisations, références et SHA-256](manifest.json).
- [Recette et tests](../../source/arene_glace_sky_peak_v3/README.md).
- **17contrôles d’assets PASS**, **13contrôles de galerie en DOM simulé PASS**. WebP vérifié image par image, ORA vérifié, accès sud contrôlé sur le masque visible.

Ce sont des contrôles de fichiers et de composition, **pas une validation PMDO, de collisions ou de rendu GPU**. Aucune approbation utilisateur de cette V3 n’est présumée. Les V1/V2 sont conservées.

Le patch d’animation de `cliffnordouesttest1.rsground` est une livraison distincte : [nuages natifs / mer encore bloquée](../../exports/cliffnordouesttest1_animation_v1/README.md).
