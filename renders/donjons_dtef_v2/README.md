# Donjons V2 — véritables gabarits DTEF PMDO et texture bombing

Cette livraison remplace les planches génériques de `donjons_10_biomes_v1` pour le travail d’autotiles. Elle réutilise **la disposition exacte auditée pour Sakura**, et les géométries/matières de véritables donjons PMD. Aucun nouveau rendu de texture généré n’est utilisé dans ce lot.

## Références Halcyon vérifiées
La lecture des `Data/Zone/*.json` au commit `1522c7a8b7a34d70078e11ed605b21d563b0dc51` montre :
- **Relic Forest** → `treeshroud_forest_1_wall`, `_secondary`, `_floor`.
- **Illuminant Riverbed** → `sky_peak_4th_pass_wall`, `_secondary`, `_floor`.

Les fichiers `Relic_Forest_Base.tile` et `Illuminant_Riverbed_Base.tile` sont des décors Ground. Ils ne sont **pas** les feuilles d’autotiles du donjon. Les JSON de zone, scripts et deux feuilles Ground sont conservés dans `source/donjons_dtef_v2/references/`. Les vrais autotiles sont hérités des ressources PMDO, récupérées dans DumpAsset au commit `3e767571f9dd94270b848b3a73de9bec2553a2eb0`.

| Biome | Donjon source réel |
|---|---|
| Forêt | Treeshroud Forest1 — utilisé par Relic Forest |
| Jungle | Southern Jungle |
| Marais | Murky Forest |
| Roche | Southern Cavern1 |
| Cristal | Crystal Cave1 |
| Glace | Vast Ice Mountain |
| Volcan | Dark Crater |
| Désert | Quicksand Cave |
| Ruines | Sealed Ruin |
| Vapeur | Steam Cave |
| Référence supplémentaire | Sky Peak4th Pass — utilisé par Illuminant Riverbed |

Les références supplémentaires ne sont pas un onzième biome inventé. Les décors/geysers et Waterfall Lake des livraisons précédentes ne sont pas modifiés.

## Format DTEF — pas « EDTF »
`RAW/TileDtef/d2_<biome>_<jour|nuit>/` contient :
- `tileset_0.png`, `tileset_1.png`, `tileset_2.png` : variantes visuelles natives disponibles, et non trois phases d’animation. Les emplacements absents restent transparents.
- `tileset_<variante>_frame<couche>_<index>.<duree>.png` : séquences indépendantes, indices à partir de0, durées en frames logiques du jeu.

Chaque feuille mesure **432×192px** : trois blocs144×192, dans l’ordre **Wall / Secondary / Floor**. Chaque bloc : **6colonnes ×8lignes**,47cases utiles et1vide. Une tuile de ces sources fait **24×24px**. Le mapping vient directement de `FieldDtefMapping` dans le C# RogueEssence inspecté pour Sakura, pas d’un tableau47cases réordonné arbitrairement.

**Correction de la V1 : ne pas traiter ces fichiers DTEF comme des planches PNG à importer en8px.** L’importeur DTEF calcule lui-même24px depuis192/8. Le découpage générique8px et la disposition sur8colonnes des précédentes planches ne conviennent pas à cette route d’import.

## Texture bombing, local et contrôlé
La variante0 reste **strictement native de jour**. Sur neuf familles, les variantes1/2 de la tuile de sol complètement entourée (`TilexFF`) reçoivent cinq petits tampons irréguliers chacun, échantillonnés dans les trois variantes de sol du **même donjon**. Les couleurs des patchs ne sont pas réinventées. Les positions/donneurs et graines déterministes sont documentés dans les manifests et le code.

-90tampons appliqués au total ;1118pixels effectivement différents de leurs variantes sources.
- Bordure de4px strictement conservée ; aucune modification des silhouettes/alphas.
- Aucune modification des murs, du terrain secondaire ou des couches animées.
- **Dark Crater est exclu du bombing** car son sol est animé. Illuminant est gardé comme référence native intacte.
- Les exemples alternent les variantes existantes avec un choix pseudo-aléatoire déterministe, au lieu d’un motif de sélection périodique.

Il s’agit d’une **adaptation discrète de textures natives**, pas de dix nouveaux styles entièrement redessinés ni de nouvelles tuiles canoniques. La limite de trois variantes vient de l’importeur PMDO inspecté. Le bombing n’ajoute pas un shader moteur : ce sont les pixels des variantes DTEF exportées.

`apercus/*/SOL_VARIANTES.png` montre les trois cellules de sol. La galerie permet la comparaison « Carte sans variations — V0 seule ». Celle-ci compare l’usage d’une seule variante à l’alternance des trois ; elle n’isole pas uniquement l’effet des tampons par rapport aux variantes natives originales. Les fichiers de référence complets sont disponibles dans `references_dtef/` pour cette comparaison exacte.

## Animations et nuit
Toutes les couches natives, variantes, images et durées sont conservées. Les couches sont regroupées par type, index local, longueur de séquence et durée, pour éviter les collisions de noms rencontrées dans les anciennes études. Glace et ruines restent statiques lorsqu’aucune animation n’existe dans leur source.

La galerie déroule les couches à leurs cadences propres à60frames logiques/s. Les WebP `EXTRAIT_2S.webp` sont **des extraits répétés de2secondes, pas nécessairement des boucles complètes**. Les périodes complètes sont dans `manifest.json`.

La nuit utilise le filtre exact Abyss, sans recoloration approximative. Les identités de pixels natifs concernent le JOUR ; les pixels nocturnes sont volontairement transformés.

## Import sur une copie de test
Extraire le ZIP dans un dossier de travail puis, avec une **copie de test de PMDO** :
```
./PMDO -raw "/chemin/vers/le/pack/RAW/" -convert autotile
```
Commande confirmée dans le code inspecté, **non exécutée ici**. Ne pas la lancer à l’aveugle sur une installation de production. Les préfixes `d2_` évitent de remplacer les autotiles des donjons originaux. Les noms `tileset_0.png` sont répétés conformément au format, dans des dossiers distincts : ne pas les aplatir ou les renommer.

L’import génère les ressources d’autotiles ; il ne configure pas les collisions, règles d’étage, spawns ou zones jouables. L’importeur examiné n’utilise pas `tileset.dtef.xml` dans cette route. Une compatibilité universelle SkyTemple/éditeurs externes n’est pas revendiquée.

## Vérifications et provenance
`verification.json` : **802PNG DTEF jour/nuit**,12684références natives de tuiles/frames contrôlées,47configurations, bordures/alphas conservés, animations natives exactes de jour, aucune frame source transparente perdue, noms/cadences cohérents, nuit exacte. Les contrôles ne remplacent pas un jugement artistique ni un import moteur.

**Aucun test PMDO exécuté.** La galerie est testée en DOM simulé, pas comme preuve d’intégration GPU/moteur.

Scripts : `source/donjons_dtef_v2/{fetch,sources,build,verify,gallery,package}.py`. Dépendances Pillow/NumPy ; SciPy pour les outils partagés du dépôt. Reconstruction depuis le dépôt avec les fichiers de référence ; SHA256 DumpAsset dans `references/provenance.json`.

Sources : Palikadude/Halcyon, audinowho/DumpAsset, RogueCollab/RogueEssence. Les ressources restent soumises aux droits de leurs auteurs/contributeurs et ayants droit ; leur présence dans un dépôt public n’est pas une licence universelle.
