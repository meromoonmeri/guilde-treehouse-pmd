# Spécification — Lot V17 · 3 nouvelles maps PMDO (méthode canonique générateur + pipeline natif)

Respect strict de la méthode `MANUEL_METHODE_PMDO.md` §5-9 et `AGENTS.md` :

- Générateur = guide de composition uniquement, jamais source de tuiles certifiées pixel-perfect pour l'import sans reconstruction native / ou textures inventées DA PMD pour nouvelles entrées (autorisation 13 sept 2026)
- Calques séparés, noms uniques METANO_V3 / v50812 style, grille 8 px, dimensions divisibles par 8
- Filtre Abyss uniquement pour variantes nuit, provenance conservée

## Références canoniques étudiées (Étape 1)

- Crooked Cavern (Palika) — 320×240, grille 8 px, Base/Objects/Shadows, bouche sombre lisible
- Brine Cave (EoSO) — 648×504, grille 24 px → 9 cellules 8×8, parvis asymétrique, mer au pied
- Drenched Bluff (EoSO) — 528×408, grille 8 px, Background/Details, corridor ouvert sans bouche noire
- Arène Halcyon V16 (928×1152) — méthode canonique magenta → alpha par inondation, 10 frames aurore posées (80,24) grille 8 px

Dépôt Halcyon Vast Steppe inspecté pour végétation animée ; DumpAsset/Palika vérifiés pour construction des calques.

## Spécification avant génération (Étape 2)

### Map A — Jungle aux cascades  (junglewaterfallzonepmdsky.png — 744×1032 référence)
- **Fonction** : passage sud → nord vers paroi à cascades, zone de rassemblement devant le bassin, belvédère latéral
- **Terrasses / profondeur** : 1 paroi verticale principale au nord (haute, 40% de la hauteur), bassin central (20%), chemin/berges au sud (40%) ; 2 niveaux de profondeur (paroi arrière + sol praticable)
- **Limites** : terrain rejoint les limites latérales et sud ; nord fermé par la paroi (pas de sortie)
- **Arrivée** : sud-centre, 16×16 dégagé sur chemin
- **Entrée** : pas de grotte noire ; l'axe mène au pied des cascades (effet d'eau vertical), largeur libre 64 px
- **Calques prévus** : 00_ciel, 01_sol_chemin, 02_paroi_cascades, 03_berges_bassin, 04_vegetation_devant, 05_cascades_surface (animée à phases séparées ensuite), 06_ombres
- **Animation** : eau verticale et bassin en plusieurs phases (à générer après terrain, RGB fixes/alpha variable)

### Map B — Arène côtière  (arenapmdskybeach.png — 456×480 référence)
- **Fonction** : arène / espace libre face à la mer, combat et rassemblement
- **Terrasses** : sol sableux central (60%), falaises rouges latérales basses (20%), mer + écume au nord-est (20%)
- **Limites** : sud et ouest ouverts (plage), nord-est fermé par mer, falaises touchent les bords latéraux par retours arrondis
- **Arrivée** : sud-ouest, sur sable
- **Entrée** : aucune ; zone libre
- **Calques** : 00_ciel_mer, 01_sable, 02_falaises, 03_rochers_isoles, 04_ecume (animée)
- **Animation** : mer 6-8 phases, écume indépendante

### Map C — Grotte violette à deux issues  (large.P27P01A 360×312 / grotte violette)
- **Fonction** : chambre / passage souterrain avec deux bouches, chemin est-ouest
- **Terrasses** : chambre unique au centre, deux parois violettes arrière/avant, sol sombre
- **Limites** : parois rejoignent les 4 limites, deux ouvertures nord et sud (ou est/ouest selon cadrage)
- **Arrivée** : sud-centre, dégagement 16×16
- **Entrée** : deux seuils 48 px de large, direction nord/sud, seuil dégagé
- **Calques** : 00_fond_sombre, 01_sol, 02_paroi_arriere, 03_paroi_avant, 04_piliers_blocs
- **Animation** : aucune (statique ; lueur éventuelle ajoutée en variante)

## Génération guidée (Étape 3) — consignes communes
- Fournir références caméra/échelle : vue légèrement plongeante PMD, sol lisible, parois verticales, pas de perspective extrême
- Demander explicitement : **fond magenta uni #FF00FF** (255,0,255) partout hors terrain, sans dégradé ni ciel, pour détourage par inondation ; absence de personnages, bâtiments, UI, texte, chiffres
- Produire plusieurs propositions, sélectionner la composition utile, **ne jamais découper automatiquement une image générée en tuiles 8 px** sans reconstruction native
- Conserver les bruts, hashes SHA-256, dimensions ; documenter rejet si 12 panneaux au lieu de 10 etc.

## Reconstruction (Étape 4) — selon type
- **Métano strict** (si extension ville) : tuiles natives 8 px extraites de Métano, modules complets sommet/face/pied/retours, sans recoloration/rotation/agrandissement
- **Nouvelles entrées/biomes** (ce lot) : textures inventées dans la DA PMD autorisées, via générateur, mais en plusieurs calques PNG natifs nets, transparence propre, grille 8 px, noms uniques `V17_*` — ce sont des illustrations aplaties non certifiées pixel-perfect natives, comme `renders/entrees_pmd_collection/` ; ne pas les annoncer comme tuiles canoniques extraites
- Calques ORA + PNG individuels + WebP/GIF pour animations, recomposition exacte vérifiée (alpha droit, prémultiplié documenté si .tile futur)

## Étapes 5-7 (filtre nuit, audit, import)
- Variante nuit : `tools/tile_night.py` blob 438383f uniquement si demandé, appliqué aux 3 feuilles nuit d'Abyss, pixels jour restant natifs
- Audit : dimensions divisibles par 8, alpha propre, absence de magenta résiduel, recomposition = brut détouré, pas de resampling
- Import : PNG to Tileset en 8 px dans PMDO Dev, basename unique, test désérialisation 0.8.12 si pack Ground

---
*Spécification écrite AVANT génération, 20 sept 2026.*
