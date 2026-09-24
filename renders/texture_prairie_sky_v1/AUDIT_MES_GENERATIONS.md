# Audit de mes propres générations (bruts)

Méthode : comparaison visuelle + mesures contre le GIF Sky Peak natif
(`source/sky_peak_v1/gif_0.png`, herbe médiane **(135,247,119)**, 37 couleurs).

## 1. `bruts/panorama.png` v1 — REJETÉ
Pikachu-like, Treecko-like, hutte, chemin : des **entités** interdites par
l'utilisateur. Jete et régénéré. Leçon : exiger `no characters, no creatures,
no buildings` explicitement dans le prompt.

## 2. `bruts/panorama.png` v2 — RETENU (avec réserves)
Zéro entité, ciel magenta propre, détourage net. Réserves : rendu un peu
lisse vs grain GIF, mais acceptable de nuit et à distance (2e-3e plans).
Statut : **généré DA Sky**, jamais présenté comme natif.

## 3. `bruts/sommet.png` — NON UTILISÉ
Avant-plan généré correct (rim + rochers) mais remplacé par la **bande
prairie native** (miroir GIF) suite à la correction utilisateur.
Archivé, aucun pixel repris.

## 4. `bruts/nuages.png` — RETENU
14 sprites propres (8 fins + 6 gros), magenta franc, détourage sans frange.
Réserve : style légèrement cartoon vs PMD ; atténué par la taille réduite
et la nuit. Wraps à marges ≥32px vérifiés seamless.

## 5. `bruts/guide_prairie.png` — GUIDE UNIQUEMENT, textures REFUSÉES
- Herbe médiane **(128,229,38)** vs (135,247,119) : vert lime
  **sursaturé**, bleu écrasé (38 vs 119). Visible à l'œil nu.
- Rochers gris neutres anguleux vs falaises **bleu-ardoise arrondies**
  à chapeaux d'herbe du GIF. Mauvais vocabulaire de formes.
- **Plaques de terre marron** : intrus, inexistantes au sommet Sky.
- Coin de ciel bleu : cadrage non rempli, zone inutilisable.
- Traits d'herbe 2-3× trop gros vs grain natif 8px.
- 0 fleur, 0 entité : les seuls points conformes.

**Verdict : aucune texture générée n'entre dans les surfaces finales.**
La surface `prairie_sky_512_*` est quiltée à 100% en tuiles GIF natives
(442 motifs, 4096 cellules, 0 différence vérifiée). Le générateur sert
la composition ; le pixel final est natif ou contrôlé.
