# Cadrage révisé après la précision utilisateur — 21 septembre 2026

## Exigence principale

**Une autre zone du même lieu de référence, pas une nouvelle interprétation générique du biome.** L’utilisateur est satisfait du travail dans l’ensemble, mais exige une continuité plus forte et environ **4 à 6 vrais calques par carte**. Sa satisfaction générale ne vaut pas approbation des dix études produites juste avant son interruption.

La marge de création porte d’abord sur le cheminement, la position des accès, la taille d’une clairière ou d’une terrasse. Conserver les matières, la gamme de couleurs, l’échelle des détails, les formes caractéristiques, le type d’architecture et la perspective du lieu. Ne pas déduire son apparence de son seul nom anglais/français.

## Composition multicalque à viser

Adapter la décomposition à ce qui existe réellement dans la référence ; ne pas inventer une couche pour atteindre un chiffre.

1. Sol praticable continu, sans rochers/arbres/effets cuits dedans.
2. Rochers, parois et reliefs.
3. Bordures et végétation (séparer avant/arrière lorsque l’occlusion le nécessite).
4. Entrée ou éléments architecturaux caractéristiques, s’ils existent.
5. Ciel ou arrière-plan lointain **si la référence en montre**. Un arrière-plan forestier n’est pas automatiquement un ciel ouvert.
6. Eau/lave/effets lumineux ou atmosphériques, selon le lieu.

Il s’agit de 4–6 groupes sémantiques selon la carte, pas d’un quota de fichiers : les frames et les pistes d’animation conservent leur indépendance. Ne pas fusionner une cascade avec le sol, ni les particules avec une lumière, pour afficher artificiellement six fichiers. Ne pas ajouter un ciel à un intérieur/une forêt fermée qui n’en possède pas.

**Changement de méthode nécessaire :** les partitions de surfaces visibles du lot1 ne constituent pas à elles seules un sol continu sous les objets. Pour les nouvelles versions, construire le fond/sol séparément et traiter les occlusions ; ne pas simplement réutiliser les polygones approximatifs du premier script. Délimiter les calques suivant les silhouettes réelles et les matériaux. Si une zone cachée n’est pas reconstruite, le signaler ; ne pas qualifier son calque d’objet mobile complet. Les nouvelles parties générées restent non natives.

## Contrôle visuel des six références restantes

| Référence native | Identité à préserver | Écart constaté dans les études interrompues |
|---|---|---|
| Jungle H14P01 | Grand tronc à racines, eau turquoise au pied, végétation verte dense, fleurs rouges et plantes claires, clairière principalement verte. | Entrée proche de plusieurs motifs ; sol ocre beaucoup trop dominant dans la finale, présence de l’eau à réexaminer. |
| Forêt envahie H07P03 | Profondeur forestière vert pâle, troncs élancés/tortueux, lianes, sol herbeux vert franc, végétation de premier plan. | Études plus sombres et plus massives, rochers et bois noueux surdominants ; profondeur et lumière à reprendre. |
| Mont Discipline H16P01 | Cour d’entraînement en dalles gris clair, marches/structure claire, végétation verte autour, poteaux d’exercice et bord sableux. | Les deux montagnes/grottes brunes sont écartées : elles ne représentent pas une autre zone de cette cour. |
| Plaines sauvages H06P01 | Prairie ouverte vert-jaune, collines lointaines, ciel bleu et nuages, douceur des reliefs. | Trop de murs/terrasses fermés ; finale sans horizon. Préserver l’ouverture et isoler ciel/arrière-plan. |
| Forêt secrète H07P08 | Bleus et cyan, grands troncs courbes, toiles visibles, souches et végétation froide. | Entrée a une palette apparentée mais perd les toiles et la silhouette du lieu ; à reprendre. Finale non générée. |
| Plaines brûlées H06P05 | Sol orange/rouge lumineux, roches chaudes, troncs brûlés, horizon montagneux et ciel, feux séparés. | L’entrée noire quadrillée s’éloigne fortement de la prairie native ; écartée. Finale non générée. |

Ces constats sont une revue interne, pas une nouvelle validation artistique de l’utilisateur. Les références décodées exactes et leur provenance restent dans le pack1 et son audit. Avant de produire les calques finaux, comparer la référence et la nouvelle zone à la même échelle de lecture.

## Application aux lieux du premier lot

Le principe vaut aussi pour les cinq premiers lieux, sans effacer leurs livraisons : forêt lumineuse H07P04 (sol vert vif, grands fûts/pousses, lumière caractéristique), île H29P04 (roche grise, herbe et fond céleste), volcan H26P01 (sol/reliefs rouges et colonnes de lave), désert H20P01 (sable jaune, roches stratifiées et ciel bleu visible dans la référence), courant marin H02P02 (champ bleu/cyan et lumières aquatiques). Ne pas introduire une architecture étrangère qui prendrait le dessus sur cette identité. Les corrections éventuelles seront de nouvelles versions, pas un remplacement silencieux du lot1.

## Animations demandées : rappel prioritaire

- Volcan H26P01 : ne pas se limiter à la texture de lave au sol. Les **cascades/colonnes de lave canoniques** ont été localisées dans les pixels de palette4, cycle BPL8frames ×3ticks. Isoler des modules complets avec leur pied/impact, en vérifiant les contours : sélection de palette ≠ détourage automatiquement complet.
- Forêt lumineuse H07P04W : conserver les vraies lumières/rayons et les particules. La banque utilise BPA14poses ×7ticks et BPL32phases ×8ticks ; distinguer les rôles des indices de couleur et vérifier la recomposition avant de les annoncer comme pistes indépendantes.
- Plaines brûlées H06P05 : BPA10poses ×3ticks ; palettes5/6 de9phases ×4ticks ; particules météo W04. Le masque brut des tuiles animées comporte aussi des morceaux de sol/rocher : il n’est **pas** un sprite de flamme autonome prêt à placer.
- Aucun déplacement artificiel d’une image fixe ne doit être vendu comme une ondulation canonique. Garder les cadences et modes de fusion documentés, les natifs à1× sans recoloration/rotation ajoutée, les adaptations explicitement séparées.
- Ne pas attribuer une animation native de forêt lumineuse à une autre forêt comme si elle était présente dans sa banque d’origine. Une éventuelle réutilisation doit être marquée comme choix de composition, pas comme caractéristique canonique du lieu.

## État honnête après interruption

Dix compositions ont été générées avant la précision utilisateur ; les tentatives `secrete_fin` et `brulees_fin` ont échoué à la limite de dix générations. **Aucun pack2, aucun export multicalque2 et aucune animation complémentaire finalisée ne sont livrés à ce stade.** Les dix bruts sont conservés comme études à requalifier/écarter, pas comme une sélection approuvée. Leur archivage est décrit dans `drafts/archive.json`.

La prochaine production doit appliquer ce cadrage avant de compléter les deux images manquantes. Ne pas terminer machinalement les anciennes compositions. Les22cartes restent la portée globale, par lots. Le premier lot publié est préservé ; toute correction sera additive/versionnée. Les PNG et WebP directs, le push sur la branche de session, les références/historiques et Beach inchangés restent obligatoires. Les tests techniques ne valent pas validation PMDO ni approbation artistique.

## Première application livrée : entrée en lisière

La dernière demande a ciblé cette entrée seule. `source/lisiere_pmd_v1/` et `renders/lisiere_pmd_v1/` livrent cinq générations de plans distincts, dont un vrai sol continu, plus le groupe de lumière à deux pistes natives. Layout boisé inspiré de Mystifying Forest, identité H07P03 préservée ; lumière H07P04W réemployée explicitement. Les huit nouveaux bruts (deux guides, tentative d’arbres incorrecte, cinq plans retenus) sont conservés dans Git. Le guide de finale n’est pas une finale livrée. Ne pas reprendre les dix anciennes études comme si elles étaient approuvées. Le reste du programme22cartes et les reprises restent en attente.

### Suite LF1
Entrée LE1 approuvée ; finale LF1 désormais proposée avec sol/fond/végétation identiques, rochers déplacés, nouvelle bordure générée et lumière native inchangée. Six groupes sémantiques. Voir `../suite_foret_cafe_v1/README.md`. Les cinq autres duos restent à produire/reprendre.
