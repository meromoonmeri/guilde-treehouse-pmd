# Variantes de l'aile droite

Le kiosque Spinda de gauche est conservé **à l'identique** dans toutes les
variantes. Seule l'aile droite change, et chacune garde l'entrée telle qu'elle
a été validée : **ouverture sans battants**, intérieur noir opaque, et la rangée
de demi-cercles dorés qui éclaire le seuil.

| Fichier | Aile droite |
|---|---|
| `d1_chaumiere.png` | chaumière en pierre, toit de chaume, cheminée fumante |
| `d2_serre.png` | serre vitrée, parois vert d'eau et plantes |
| `d3_pagode.png` | pagode à deux étages, balcon et lanternes |
| `d4_kiosque_spirales.png` | murs de kiosque crème et bois, ornés des spirales de Spinda |
| `d5_kiosque_toit_droit.png` | même idée mais toit droit en tuiles — **écartée**, elle perdait le design de `d4` |
| `d6_porte_bois_kiosque.png` | `d4` avec l'encadrement de porte dans le bois miel du kiosque |
| **`d7_spirales_toit.png`** | **`d6` + les spirales de Spinda peintes sur le toit** |

`d4` reprend `d2` en remplaçant le vitrage et la végétation par de vrais murs
de kiosque, dans les mêmes matériaux que la partie gauche.

`d6` conserve `d4` trait pour trait et ne change que l'encadrement de l'entrée,
jusque-là dans un doré pâle qui jurait avec le reste. Les montants et l'arc
reprennent le bois miel des poteaux et du comptoir du kiosque, veinures et
contours compris.

`d7` est la version retenue : elle reprend `d6` et ajoute les spirales
orange-rouge de Spinda sur la grande toiture courbe, jusque-là nue. Elles
suivent la courbure du toit et reprennent le motif déjà présent sur le toit du
kiosque et sur les panneaux crème.

Ces fichiers sont les **sorties brutes du générateur** : fond magenta uni,
agrandies. Pour en tirer un PNG transparent au format de la source :

```bash
cd ../spinda_cafe
python3 ../tileset_pmd/detourer_magenta.py \
    spindacafevFINAL.png ../variantes/d7_spirales_toit.png sortie.png
```

La version détourée de `d7` est déjà disponible :
`../spinda_cafe/spinda_cafe_variante_kiosque.png` (425 × 251, bords nets).
