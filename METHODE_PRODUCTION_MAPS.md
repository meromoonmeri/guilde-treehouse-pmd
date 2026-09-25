# Méthode de production des maps PMD (générateur + pipeline natif)

Synthèse de `MANUEL_METHODE_PMDO.md` et `AGENTS.md`. Cible : PMDO 0.8.12. Ce dépôt alimente les imports du moteur, il ne le remplace pas.

## Rôle du générateur
Le générateur sert **uniquement de guide de composition** : rythme des masses (falaises, terrasses, entrées), silhouettes, profondeur, cadrage, ambiance. Il ne produit **jamais** de tuiles d'import.

> « Une référence générée ne constitue jamais une preuve de fidélité des pixels natifs. »
> « Ne jamais tenter de réparer une roche non conforme par une succession de retouches générées présentées comme pixel perfect. »

## Pipeline
1. **Références canoniques** — Crooked Cavern (Palika, grille 8 px, Base/Objects/Shadows), Brine Cave (EoSO, grille 24 px, feuille animée), Drenched Bluff (EoSO, 8 px, Background/Details). Pour chacune : commit précis, `.rsground` téléchargé, toutes les références Sheet lues, hash Git + SHA-256 local conservés.
2. **Spécification avant génération** — fonction (espace libre, passage, belvédère, entrée de donjon), nombre et ordre des terrasses, bords rejoignant la limite de carte, point d'arrivée ; pour un donjon : seuil, largeur libre, direction d'entrée.
3. **Génération guidée** — références caméra/échelle/composition, exclusion explicite des éléments non voulus, plusieurs propositions, sélection manuelle. Jamais de découpage automatique en tuiles.
4. **Reconstruction native** — tuiles 8 px de Métano, modules complets (sommet, face, pied, retours), sans recoloration/rotation/agrandissement ; calques séparés : sol, parois, bordures, berges, surface d'eau, cascades.
5. **Nuit Abyss** — `source/cote_v4_abyss/tile_night_reference.py` (blob `438383f`), transformation vérifiée sur `Metano_Town_Base_Night.tile`, `Metano_Town_Cliffs_Night.tile`, `Metano_Town_Fringe_Night.tile` (New Era). Les pixels de jour restent natifs.
6. **Audit** —
   ```bash
   python source/cote_v5_expeditions/audit_references.py   # provenance des tuiles
   python source/audit_zones_metano.py                     # contrôle des exports
   ```
   Dimensions multiples de 8, aucun resampling, alpha propre, aucun objet parasite, continuité des terrasses.
7. **Import** — PMDO Dev › *PNG to Tileset*, taille 8 px. Noms uniques (`METANO_V3_*`, `v50812_*`) : l'importeur nomme par basename, deux homonymes s'écrasent.

## Livraisons
- `cotes_metano_abyss_0812_pmdo.zip` — 10 terrains × jour/nuit = 20 Ground
- `mod_metano_expeditions_pmdo_0812.zip` — 40 Ground (20 nouveaux + 20 précédents)

Identifiant unique par zone ; anciennes livraisons conservées, jamais écrasées. Les `apercu_*.html` montrent le rendu sans moteur mais ne valident ni raccords ni collisions.

## Métano vs nouvelles entrées
- **Falaises de Métano** : tuiles natives Métano uniquement, référence = tilesets nuit New Era.
- **Entrées de donjon indépendantes** (autorisé depuis le 13/09/2026) : textures inventées dans la DA PMD via le générateur ; construction inspirée des Ground PMD Sky (layout, pas copie de textures).

## Limites
- Lancement PMDO en échec (code 139) dans cet environnement : aucun test d'affichage. Les 40 Ground Expéditions passent la désérialisation par le vrai chargeur.
- Approbation visuelle ≠ validation moteur.
- Un guide non conforme (ex. 12 panneaux au lieu de 10) ne se découpe pas automatiquement.

## À retenir
Générateur = composition seulement · spécifier avant de générer · reconstruire en tuiles natives 8 px · calques séparés · noms uniques · valider un échantillon au zoom natif puis en jeu · ne jamais écraser une livraison.
