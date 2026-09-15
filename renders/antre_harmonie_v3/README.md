# Antre harmonisé V3 — Crooked Cavern / Altere Pond / Métano

## Références effectivement inspectées
La référence appelée « Altair’s Pond » dans la demande a été identifiée comme **Altere Pond**, nom du lieu et des fichiers dans Halcyon. La carte présente un disque de pierre claire sur l’eau, avec trois pas japonais. Le plancher en bois des versions précédentes est donc remplacé, sans modifier les anciennes livraisons.

- Crooked Cavern : `source/cote_v5_expeditions/audit/Halcyon__crooked_cavern_entrance_layer_0.png` et sa composition ; roche ocre-gris, stratifiée, sombre dans les creux. Il s’agit de la palette de cette référence, pas de l’ancienne variante artificiellement grisée.
- Altere Pond : carte et neuf atlas téléchargés à partir de Halcyon `working-copy`, commit **1522c7a8b7a34d70078e11ed605b21d563b0dc51**, reconstitués en couches. Hachages et blobs dans `source/antre_harmonie_v3/references/provenance.json`.
- L’écume d’Altere Pond utilise effectivement **Metano_Town_Animation_Tileset**, dont les ressources natives sont déjà archivées dans `source/eau_metano/natifs/`.
- Foggy Forest n’est pas utilisé : l’option Métano de la demande est satisfaite via les poses d’écume natives, avec les chutes assemblées dans Altere Pond.

## Composition
480 × 312, **23 calques alignés** :
- 10 statiques : ombre, paroi du fond, bordures gauche/droite, rebord rocheux du bas, tranche et dessus de la plateforme, trois pas japonais indépendants.
- 13 animés : eau de fond, six cascades, six écumes.

La roche et le grand disque ont été régénérés sur magenta avec les références exactes. La palette du rocher est ensuite ramenée aux couleurs présentes dans la partie rocheuse de Crooked. Celle du disque est ramenée aux couleurs du petit disque natif d’Altere. Cela garantit les couleurs, **pas l’identité des motifs ni un statut de sprite natif**.

Le grand disque est une adaptation plus large, 160 × 106. Les trois pas japonais sont copiés à leur échelle native, sans recoloration ni redimensionnement. Le fond d’eau utilise un échantillon natif d’Altere de 32 × 32, répété ; ce n’est pas une simulation du bassin entier. Le rebord du bas est indépendant et un chenal étroit reste ouvert sous l’accès en pierres.

## Animation native retrouvée — différence importante avec la V2
La carte fournit des cycles distincts :
- couche River, chutes : **4 phases**, 10 frames de jeu par pose ;
- couche Objects Over, écume Métano : **3 phases**, 10 frames de jeu par pose.

Le relevé direct `references/timing_proof.json` enregistre les cellules et toutes leurs références de frames. La boucle commune est **12 poses × 10 frames = 120 frames de jeu**, soit **2 secondes à 60 Hz**. Les fichiers WebP arrondissent les horodatages cumulés à la milliseconde : 167/166/167 ms, sans dérive du cycle. Ne pas imposer quatre poses à l’écume.

Les cascades utilisent la bande centrale des phases natives à l’échelle d’origine, avec des décalages entiers pour suivre les canaux et un masquage contre les roches. **Pas de défilement vertical d’une texture générée.** Les écumes conservent leurs trois poses, mais sont réduites à 50 % au plus proche voisin pour s’adapter aux chutes étroites (48 × 28). Leur placement est masqué contre les roches et la plateforme ; elles ne sont donc pas des copies plein format de l’effet natif. Les six effets sont synchrones comme la référence, sans déphasage inventé.

Les deux chutes extérieures s’arrêtent plus haut que dans V2, au bassin visible avant les saillies du premier plan ; cela évite de cacher leur pied et leur écume derrière un rocher. L’ensemble est une composition adaptée, pas une carte Halcyon récupérée telle quelle.

## Ouvrir
- `../../apercu_antre_harmonie_v3.html` : aperçu animé autonome et sélection de chaque calque.
- `antre/COMPOSITION.png`, `antre/ANIMATION.webp` : rendu initial et boucle commune.
- `antre/antre_harmonie.ora` : les 23 calques à l’état initial.
- `antre/harmonie_*.png` : calques et 12 compositions alignées ; les cycles courts sont répétés pour garder une chronologie commune.
- `sprites/` : disque natif de référence, grand disque adapté et trois pas japonais natifs.
- `antre_harmonie_v3.zip` : paquet autonome, scripts et références nécessaires.

## Contrôles et limites
`verify.py` vérifie les 12 recompositions opaques, la périodicité 4/3 des exports, la cadence réellement déclarée par la carte, les pixels natifs des pas japonais, l’appartenance des couleurs rocheuses à la palette Crooked, l’absence d’effets sur le sec et la recomposition exacte de l’ORA. Aucun test d’import, de collisions, de mouvement ou de combat dans PMDO.

La forme des parois et du grand disque reste générée ; leurs faces cachées ne sont pas reconstituées. Les droits des ressources PMD réutilisées restent ceux de leurs ayants droit. Les V1/V2 sont conservées sans modification.

Depuis la racine, avec Pillow, NumPy et SciPy :
```sh
.venv/bin/python source/antre_harmonie_v3/references_extract.py
.venv/bin/python source/antre_harmonie_v3/native.py
.venv/bin/python source/antre_harmonie_v3/build.py
.venv/bin/python source/antre_harmonie_v3/verify.py
.venv/bin/python source/antre_harmonie_v3/package.py
```
Les sources binaires et PNG déjà présents évitent un nouveau téléchargement ; `gh` ne sert que si les références binaires sont manquantes. Les utilitaires de décodage et de détourage nécessaires sont inclus dans le ZIP.
