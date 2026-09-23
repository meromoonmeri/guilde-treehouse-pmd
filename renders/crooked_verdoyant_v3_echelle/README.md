# Crooked Cavern verdoyante V3 — échelle 1:1 (928×1152)

## Problème (V2 512×640)

- Carte **plus étroite** que les fenêtres caméra PMDO courantes (640×360, 848×480) → **bandes noires au clamp**.
- Downscale NEAREST des bruts 928×1152 → arbres générés ~100 px, trop petits vs sprite de marche Pokémon (~24–40 px) et vs l’**arbre canonique Vast Steppe 144×120**.

## Approche retenue (pas d’upscale)

Les bruts magenta V2 **sont déjà** 928×1152 (standard guilde / largeur Altere Pond). V3 les détoure **sans** `resize` 512×640.

| Mesure | Valeur |
|---|---|
| Canevas | **928×1152** (116×144 tuiles de 8 px) |
| Arbre Vast Steppe (natif, translation) | **144×120** |
| Arbres générés (brut) | ~175–199 × 143–152 |
| Chemin | largeur **84–117 px** (sud 111 px), continu bord sud → entrée |
| Sprite Pokémon (réf.) | 24–40 px |
| Caméra | 640×360 et 848×480 **<** 928×1152 ; sous-couche **opaque** → pas de bande noire |

Aucun module natif n’est mis à l’échelle / miroir / recoloré. V1 et V2 restent en place.

## Fichiers

- `calques/` `nuit/` `masques/` — 9 calques jour/nuit
- `complement_natif/` — rochers Crooked + arbres Steppe 144×120
- `composition_{jour,nuit}.png`
- `CrookedEchelleV3_editable.ora`
- `review/echelle_arbre_sprite_camera.png`
- Galerie : `apercu_crooked_verdoyant_v3_echelle.html`
- Exports : `exports/crooked_verdoyant_v3_echelle/multicalques/`

Pixels générés ≠ pixels natifs. PMDO / Aseprite / Tiled apps : **non testés**.
