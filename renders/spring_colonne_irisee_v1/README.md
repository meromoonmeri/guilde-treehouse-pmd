# Correction : seule la colonne est irisée

Le layout central, le relief bas et l’escalier validés sont conservés. Le bassin et son halo retrouvent leur coloration turquoise d’origine. **Seul le rectangle du faisceau (275,0)–(325,201) reçoit une variation multicolore**, avec bords adoucis et cœur blanc préservé.

- `composition.png` : aperçu fixe.
- `animation.webp` : 78 frames, boucle 6,5 s.
- `colonne/00.png`…`77.png` : calque de remplacement RGBA 600×600, sans décalage.
- `planche_colonne_78.png` : 10 colonnes × 8 lignes, cellules 100×210 ; deux dernières cases vides. Fenêtre de chaque cellule : (250,0)–(350,210) de la scène.
- `calques/` : décor turquoise et les deux retouches relief/escalier, inchangées.
- Galerie : `apercu_spring_colonne_irisee_v1.html` à la racine. Désactiver « Colonne irisée » restitue la colonne turquoise originale.

Ordre : décor, relief, escalier, cycles natifs 3/13, colonne irisée. Les cycles natifs proviennent de `../soleil_spring_v1/spring/{02_cycle_3,03_cycle_13}/`. À la nouvelle frame f, utiliser la phase native floor(f/2), modulo 3 ou 13. La boucle conserve 6,5 secondes ; seule la variation chromatique possède 78 étapes. WebP : 83/83/84 ms répétés 26 fois.

Vérification : sur les 78 frames, chaque pixel **hors de la colonne** est exactement identique à la version turquoise avec escalier. La lumière multicolore est une adaptation nouvelle ; les sources Halcyon/RawAsset et leur provenance restent celles du pack précédent. Pas de validation en jeu. Les versions précédentes ne sont pas supprimées.

Reproduction : `source/spring_escalier_v1/colonne_seule.py` (Pillow, numpy).
