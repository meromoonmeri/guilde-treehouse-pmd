# Sommet Sky Peak de nuit — vista multicouche 960×600

Vue depuis le sommet : prairie native au premier plan, vaste forêt en contrebas,
chaîne de montagnes au loin, ciel nocturne étoilé. **Zéro entité dans le décor**
(vérifié visuellement, bruts archivés).

Galerie autonome : **`apercu_sommet_sky_nuit_v1.html`** — 11 calques, fleurs
4×200ms, étoiles 64×80ms, wraps en défilement continu, grille 8px, export PNG.

## couches (arrière → avant, toutes en 0,0)

1. `sky_01_ciel.png` — dégradé nuit échantillonné du ciel canonique v1
2. `etoiles/00..63.png` — scintillement réutilisé de ref_v2 à l'octet, 64×80ms
3. `sky_03_nuages_lointains_wrap.png` + 32 phases (pas 30px) — derrière les monts
4. `sky_04_montagnes.png` — chaîne générée, split exact avec la forêt
5. `sky_06_foret.png` — étendue générée (devant les monts)
6. `sky_05_nuages_proches_wrap.png` + 24 phases (pas 40px) — vallée, devant forêt
7. `sky_07_brume_wrap.png` + 16 phases (pas 60px) — procédural, miroir seamless
8. `sky_08_prairie.png` — **pixels natifs du GIF Sky Peak** + nuit Abyss
9. `sky_09_reliefs.png` — rebords/rochers natifs + nuit Abyss
10. `sky_10_fleurs_loin_{native,nuit}_ph0..3.png` — 4 phases canoniques @200ms
11. `sky_11_fleurs_proche_{native,nuit}_ph0..3.png` — idem, premier plan

Plus : `COMPOSITION.png`, `ANIMATION_FLORA_STELLA.webp` (8×100ms : fleurs +
étoiles échantillonnées, nuages fixes), `sommet_nuit.ora` (13 calques dont
2 variantes natives masquées), `sprites/` (10 groupes floraux natifs ×4),
`SOMMET_SKY_NUIT_calques.zip`.

## Textures : ce qui est canonique, ce qui ne l'est pas

- **Canonique** : prairie + reliefs (bande GIF y328..504, miroir 504→960,
  coutures à x=228/732, 1× sans redimensionnement), fleurs (10 sprites natifs,
  pixels/échelle/cadence conservés, 34 sites), nuit via filtre Abyss (pipeline
  canonique v1), étoiles (système ref_v2), couleurs du ciel.
- **Généré** (DA Sky, zéro entité) : panorama forêt/montagnes, sprites de nuages.
- **Procédural** : brume (seamless par construction).

## Wraps seamless — import PMDO

- Nuages : marges transparentes ≥32px aux deux bords (méthode côte V2) ;
  période 960px ; 2 copies à x et x+960, x=−floor(t×v) mod 960.
- Vitesses : lointains −4, proches −8, brume −3 px/s (indépendantes des
  horloges fleurs/étoiles ; ne pas réinitialiser aux boucles courtes).
- Alternative frames : phases PNG + durées dans `manifest.json`.
- Dimensions multiples de 8 ; PNG to Tileset à 8px ; calques à superposer
  à l'origine commune. Pas de `.rsground`, collisions ou test GPU fournis.

Vérifications : `verification.json` (PASS — recompositions, splits,
marges, identités de wrap, octets étoiles/fleurs). Reproduction :
`source/sommet_sky_nuit_v1/{build,verify,gallery,package}.py`.
Sources : GIF Sky Peak du commit 8b7e760, ref_calques_v2. Respecter les
droits PMD avant redistribution publique.
