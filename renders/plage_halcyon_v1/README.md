# Plage Halcyon V1 — arène de plage (`arenapmdskybeach.png`) aux critères Halcyon

Première zone du lot en attente traitée avec la **méthode canonique éprouvée (V15/V16)** :
terrain généré plein cadre avec bande magenta → alpha par inondation, calques fixes
empilés, animation multi-frames sur son propre calque, grille 8 px, sans wrap.

## Contenu

- **`bruts/terrain_plein_cadre.png`** (1008×1061) — terrain généré d'après la référence,
  bande magenta de 34 px en haut. **Zéro magenta cuit intérieur** (tout est inondable
  depuis les bords, vérifié avant et après passage à 928×1152 en nearest).
- **`bruts/eau_ondulation_15cases.png`** (1376×768) — planche d'eau générée. Le
  générateur a produit une grille **5×3 = 15 cases** : les gouttières magenta sont
  **détectées**, jamais supposées.
- **`couches/fond_fixe.png`** (928×1152) — fond teinte crique (39,39,55).
- **`couches/terrain_fixe.png`** (928×1152) — terrain nettoyé, sable central continu
  (rochers posés conservés, comme la référence), bassins et crique intacts.
- **`couches/eau/EauLumiereV1_00..09.png`** (928×256 ×10) — scintillement des bassins :
  5 poses réparties (k-centre sur les 15 cases) ordonnées en chemin circulaire min-max,
  + 5 fondus 50 % (précédent V11) = **10 frames, boucle fermée par construction**
  (la frame 10 est un demi-pas de la frame 1). 140 ms par frame (1,4 s).
  Les traînées lumineuses sont **restreintes au masque d'eau profonde** du terrain
  (composants ≥ 200 px) : rien sur le sable ni la roche. Tuilage miroir [A|Ā|A|Ā]
  pour couvrir les 928 px sans couture visible.
- **`scene/scene_00/03/06/09.png`** — recompositions d'essai.
- **`eau_scintillement_10frames.webp`**, **`review/scene_scintillement.gif`**,
  **`review/eau_seule.gif`** — revues animées.
- **`manifest.json`** — SHA256 des bruts, position (0, 408), critères Halcyon.
- **`verification.json`** — 9 tests dédiés PASS, JS PASS, navigateur et PMDO non testés.

## Position de la bande d'eau

`y = 408` (multiple de 8), choisie par balayage pour **maximiser la couverture du
masque d'eau** : **75,1 %** de toute l'eau du terrain. Hors bande, restent statiques
en V1 : la crique haute (y≈168-300) et les petites poches basses.

## Limites honnêtes

- Poses et cadence : **nos choix** — cycle officiel inconnu.
- Le scintillement est volontairement discret (densité ~2 % de la bande).
- Aperçu interactif : `apercu_plage_halcyon_v1.html` (racine) — syntaxe JS vérifiée,
  **pas de test navigateur réel** ; **PMDO runtime NON TESTÉ**.
- Généré d'après la référence PMD Sky © Pokémon / Nintendo / Creatures / GAME FREAK /
  Chunsoft.

Rebuild : `.venv/bin/python source/plage_halcyon_v1/build.py` puis `package.py`.
