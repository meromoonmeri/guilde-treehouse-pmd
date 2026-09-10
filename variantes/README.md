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
| **`d4_kiosque_spirales.png`** | **murs de kiosque crème et bois, ornés des spirales de Spinda** |

`d4` reprend `d2` en remplaçant le vitrage et la végétation par de vrais murs
de kiosque, dans les mêmes matériaux que la partie gauche.

Ces fichiers sont les **sorties brutes du générateur** : fond magenta uni,
agrandies. Pour en tirer un PNG transparent au format de la source :

```bash
cd ../spinda_cafe
python3 ../tileset_pmd/detourer_magenta.py \
    spindacafevFINAL.png ../variantes/d4_kiosque_spirales.png sortie.png
```

La version détourée de `d4` est déjà disponible :
`../spinda_cafe/spinda_cafe_variante_kiosque.png` (425 × 251, bords nets).
