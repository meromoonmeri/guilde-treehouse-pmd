# Méthode de production des maps PMD (générateur + pipeline natif)

**Dépôt de référence :** `meromoonmeri/guilde-treehouse-pmd`  
**Branche source :** `arena/01a095e8-guilde-treehouse-pmd`  
**Cible moteur :** PMDO 0.8.12

---

## Contexte

Ce dépôt documente la méthode développée pour créer des ground maps compatibles PMDO 0.8.12, en combinant un générateur d'images (IA générative) et un pipeline de tuiles natives. Il ne remplace pas le moteur PMDO — il alimente ses imports.

---

## Ce que fait le générateur (et ce qu'il ne fait PAS)

### Rôle exact : guide de composition, pas source de tuiles

Le générateur d'images est utilisé uniquement pour proposer la composition :
- Rythme des masses (falaises, terrasses, entrées de donjon)
- Silhouettes organiques, profondeur, cadrages
- Ambiances (jour, nuit Abyss, biomes différents)

**Il ne produit jamais de tuiles certifiées pixel-perfect pour l'import.**  
Les pixels générés ≠ tuiles canoniques. Cette distinction est absolue.

> *Règle issue de l'expérience ([AGENTS.md](AGENTS.md)) :*  
> « Une référence générée ne constitue jamais une preuve de fidélité des pixels natifs. »  
> « Ne jamais tenter de réparer une roche non conforme par une succession de retouches générées présentées comme pixel perfect. »

---

## Le pipeline complet (étapes dans l'ordre)

### Étape 1 — Références canoniques
Étudier les vraies cartes PMDO de référence :
- **Crooked Cavern (Palika)** : grille 8 px, calques Base / Objects / Shadows
- **Brine Cave (EoSO)** : grille 24 px, feuille animée
- **Drenched Bluff (EoSO)** : grille 8 px, calques Background / Details

Pour chaque référence :
- Résoudre un commit précis
- Télécharger le `.rsground`
- Lire toutes les références `Sheet`
- Conserver le hash Git et le SHA-256 local

### Étape 2 — Spécification de composition
Pour chaque carte à créer, écrire **avant** de générer quoi que ce soit :
1. Sa fonction (espace libre, passage, belvédère, entrée de donjon)
2. Nombre de terrasses et ordre de profondeur
3. Côtés où le terrain rejoint la limite de carte
4. Position du point d'arrivée
5. Pour un donjon : seuil, largeur libre, direction d'entrée

### Étape 3 — Génération guidée
- Fournir au générateur : références de caméra, d'échelle, de composition.
- Demander explicitement l'absence de structures et de détails non voulus.
- Produire plusieurs propositions, sélectionner la composition utile.
- **Ne jamais découper automatiquement une image générée en tuiles.**

### Étape 4 — Reconstruction avec tuiles natives
La composition générée sert de guide. La carte réelle est construite avec :
- Tuiles natives de 8 px extraites de Métano (terrain de référence du projet)
- Modules complets : sommet, face, pied, retours
- Aucune recoloration, rotation, agrandissement des tuiles sources
- Calques séparés : sol, parois, bordures, berges, surface de rivière, cascades

### Étape 5 — Filtre nuit Abyss (si variante nocturne)
`tools/tile_night.py` applique une transformation colorimétrique vérifiée sur les trois feuilles nocturnes officielles de New Era :
- `Metano_Town_Base_Night.tile`
- `Metano_Town_Cliffs_Night.tile`
- `Metano_Town_Fringe_Night.tile`

Les pixels de jour restent natifs. Le filtre ne s'applique qu'aux variantes nuit.

### Étape 6 — Audit avant livraison
Scripts d'audit dans `source/` et `exports/` :
```bash
python source/cote_v5_expeditions/audit_references.py   # provenance des tuiles
python exports/audit_zones_metano.py                   # contrôle des exports
```
**Contrôles :** dimensions divisibles par 8, pas de resampling, alpha propre, absence d'objets parasites, continuité des terrasses.

### Étape 7 — Import dans le moteur
L'utilisateur importe les PNG dans l'éditeur PMDO Dev via **PNG to Tileset**.
- Taille d'import : **8 px**
- Noms de fichiers uniques (`METANO_V3_*`, `v50812_*`) car l'importeur nomme les tilesets par basename — deux fichiers homonymes venant de dossiers différents peuvent s'écraser.

---

## Structure des livraisons

Les livrables sont des zips PMDO contenant des Ground complets jour + nuit :
- `cotes_metano_abyss_0812_pmdo.zip` → 10 terrains × 2 variantes = 20 Ground
- `mod_metano_expeditions_pmdo_0812.zip` → 40 Ground (20 nouveaux + 20 précédents)

Chaque zone a un identifiant unique.  
**Les anciennes livraisons sont toujours conservées — jamais écrasées.**

Les aperçus HTML (`apercu_*.html`) montrent le rendu visuel sans nécessiter le moteur. Ils ne valident pas les raccords artistiques ni les collisions.

---

## Distinction terrain Métano vs nouvelles entrées

### Terrain Métano (falaises de la ville)
- **Contrainte stricte :** utiliser uniquement les tuiles natives de Métano.
- Aucune texture inventée par le générateur.
- Référence : les tilesets nuit de New Era déjà existants.

### Nouvelles entrées de donjon indépendantes
- **Autorisé depuis le 13 septembre 2026 ([AGENTS.md](AGENTS.md)) :** textures inventées dans la DA PMD, via le générateur, avec de nombreux layouts et biomes.
- La contrainte Métano exacte ne s'applique pas.
- Référence pour la construction : les Ground PMD Sky (*Crooked Cavern*, *Brine Cave*, *Drenched Bluff*) — layout et construction, pas copie de textures.

---

## Limites documentées

- **Pas de test moteur validé ici :** le lancement PMDO a échoué (code 139) dans cet environnement. Les 40 Ground du mod Expéditions ont passé la désérialisation par le vrai chargeur PMDO, sans affichage.
- **Approbation visuelle ≠ validation moteur :** l'import peut donner un résultat décevant en jeu même si l'aperçu HTML est correct.
- Un guide généré non conforme (ex. 12 panneaux numérotés au lieu de 10) ne doit pas être découpé automatiquement. Toujours sélectionner manuellement.

---

## Sources de référence du dépôt

- `MANUEL_METHODE_PMDO.md` → méthode complète documentée
- `AGENTS.md` → règles approuvées par l'utilisateur
- `source/build_zones_guidees.py` → pipeline zones guidées
- `source/build_zones_multicalques.py` → pipeline calques séparés
- `sprites/zones_guidees/README.md` → documentation du format
- `exports/audit_zones_metano.py` → script de contrôle qualité
- `renders/` → aperçus générés (non certifiés)
- `exports/` → packs PMDO prêts à importer

---

## À retenir pour toute nouvelle map

1. **Générateur = guide de composition uniquement**, jamais source de tuiles.
2. **Toujours spécifier la carte AVANT de générer** (fonction, terrasses, entrée).
3. **Reconstruire avec des tuiles natives 8 px**, jamais des pixels générés.
4. **Calques séparés :** sol / parois / détails / eau / ombres.
5. **Noms de fichiers uniques** pour éviter l'écrasement à l'import.
6. **Valider un échantillon au zoom natif** puis en jeu avant de généraliser.
7. **Conserver toutes les anciennes livraisons**, ne jamais écraser.
