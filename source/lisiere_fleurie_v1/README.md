# Lisière fleurie / grotte Vast Steppe — TRAVAIL EN PAUSE (pas un livrable)

Chantier interrompu par l'utilisateur au profit de Furnace Desert (biome eau). Conservé pour reprise.

- `modules.py` : modules natifs Vast Steppe (Halcyon 1522c7a8) extraits par composante connexe depuis les `.tile`
  (canopée 126x72, tronc+ombre 80x41, rochers, touffes, galets, fleur animée 3 poses, séquence 0-1-0-2, cadences 8/10/14),
  corniche cyclique (raccord natif x=511|0, prolongement jusqu'à 816 px avec le couloir).
- `compose.py`, `layout.py`, `checks.py`, `preview.py` : assemblage par translation (multiples de 8), provenance
  feuille/x/y par pixel, résolveur d'éléments (visibles, sans chevauchement).
- `generateur/` : configuration du générateur (références natives, palette hex échantillonnée, schémas, prompts) et
  deux guides bruts NON canoniques (`bruts/guide_legere_01.png`, `bruts/guide_spacieuse_01.png`, la 2e validée comme
  « bonne voie » par l'utilisateur).
- Demande suivante en attente : zone finale avec **entrée de grotte encastrée dans une falaise en roche Vast Steppe**,
  **chemin style Apple Woods**, arbres canoniques autour, **calques séparés** (arbres, roche, fleurs animées...).
  Constat : Vast Steppe n'a ni grotte ni chemin natifs, et aucune feuille Halcyon/Sky Peak/Métano ne partage sa palette
  d'herbe ; question posée à l'utilisateur (100 % natif 3 sources / générateur pour ces 2 pièces / Vast Steppe strict),
  restée sans réponse.
