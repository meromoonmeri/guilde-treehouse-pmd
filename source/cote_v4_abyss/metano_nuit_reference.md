# Metano Town la nuit — vraies cartes, méthode EoSO

Build : `2026-08-01-G`

---

## 1. Comment EoSO fait — vérifié dans son dépôt

Tu m'as demandé de regarder leur méthode. Ils **ne posent pas un filtre
sombre** : ils ont de **vraies cartes séparées**.

| carte | tileset |
|---|---|
| `guild_outside.rsground` | `GuildOutside` |
| `guild_outside_dusk.rsground` | `GuildOutsideDusk` |
| `guild_outside_night.rsground` | `GuildOutsideNight` + `GuildOutsideNightGate` |

**Même géométrie** (480×408 pour les trois), `AssetName` distinct, jeux de
tuiles différents. Et leurs scripts de nuit sont quasi **vides** (74 lignes,
un `FadeIn`) : tout le travail est dans la carte.

Détail parlant : `guild_outside` a 1 PNJ, `guild_outside_dusk` en a 4,
`guild_outside_night` **zéro**. La nuit, il n'y a personne dehors.

---

## 2. Le format `.tile` — décodé et **prouvé**

Aucune documentation ne le décrit. Je l'ai reconstitué en analysant
`Metano_Town_Base.tile` :

```
[0..3]    uint32  tileSize  = 8
[4..7]    uint32  nbEntrées = 35646
[8..]     table   x(u32) y(u32) offset(u64)   × nbEntrées
[offset]  uint32  taillePNG
          uint32  padding
          PNG     8×8 RGBA
```

Plusieurs entrées pointent le **même** offset : les tuiles identiques sont
mutualisées (3929 tuiles distinctes pour 35 646 références).

**Preuve du décodage** — relire puis réécrire sans transformation redonne un
fichier au **MD5 identique** (`2dd72c6a…`) sur 1 231 857 octets. Test passé
sur les **14 tilesets** de Metano : `roundtrip=OK` partout.

Sans cette validation, je n'aurais pas touché aux fichiers.

---

## 3. Ce qui a été produit

### `tools/tile_night.py`

Convertit les 14 tilesets en versions nocturnes : **14 958 tuiles** traitées
en 3 secondes, 3,6 Mo générés.

La transformation, par tuile :
- assombrissement **non linéaire** — les pixels déjà sombres perdent moins,
  sinon la carte devient un aplat noir illisible ;
- bascule franche vers le **bleu nuit** : le rouge s'effondre (×0,52), le
  bleu est amplifié (×1,60) ;
- désaturation **légère** (0,95).

**Réglage trouvé par comparaison visuelle.** Mon premier essai
(désaturation 0,55, bleu ×1,22) donnait un **brouillard gris illisible** — je
l'ai vu en générant une planche jour/nuit et en la regardant. J'ai testé
trois variantes avant de retenir la bonne. La planche est dans
`docs/apercu_tuiles_nuit.png`.

### `Data/Ground/metano_town_nuit.rsground`

Clone de `metano_town` : **géométrie identique au pixel près** (vérifié :
`obstacles == obstacles`), 1512×1512, `AssetName` distinct, les 14 feuilles
repointées vers les `_Night`. Musique `Goodnight.ogg`.

Enregistré dans les `GroundMaps` de `master_zone` (80 entrées) et dans
`index.idx` — **cohérence vérifiée**, car `EnterGroundMap` n'atteint que les
grounds de la zone courante.

### `TownNight.lua` — la vie nocturne

**Trois habitants qui n'existent que la nuit**, pas des PNJ de jour déplacés.
Chacun a **4 paliers** de dialogue : ce qu'il dit change selon le nombre de
fois qu'on lui a parlé. La nuit récompense l'habitué.

| PNJ | ce qu'il sait |
|---|---|
| **Veilleur de Nuit** (Granbull) | Il compte les lanternes allumées depuis onze ans. Avant : dix-neuf. Cette nuit : quatorze. Puis douze. « Ce n'est pas la peur. C'est la fatigue. C'est pire, la fatigue. » |
| **Compteuse d'Étoiles** (Cornèbre) | Vingt ans qu'elle observe. Elle a remarqué qu'**il manque une étoile** — et une étoile ne s'éteint pas en quelques saisons. Elle n'ose le dire à personne de jour. |
| **Plume-Grise** (Noarfang) | Insomniaque, il a connu la ville avant la guilde. Ce qui a changé : « les gens rentrent. Personne n'a décidé ça. C'est venu tout seul. » |

Les 12 marchands sont retirés. Chaque commerce fermé a **sa réplique** — on
ne bloque jamais le joueur avec un mur silencieux.

### Le choix de fin de journée

Trois options : **dîner** (comportement actuel), **dormir** (saut direct au
lendemain), **explorer la ville**.

**Le scénario garde la priorité** : `TownNight.StoryLocked()` teste les
drapeaux existants (`MissionCompleted`, `MorningWakeup`, `MorningAddress`) et
renvoie « dîner » **sans rien demander** si une scène imposée attend.

Aucun système temporel parallèle : on réutilise `DaysPassed`,
`GeneralFunctions.EndOfDay()` et les 4 drapeaux déjà employés à 71 endroits.
Le circuit existant est **encadré**, pas remplacé.

---

## 4. Ce que ça n'est pas

Honnêteté sur la limite : EoSO redessine ses tuiles **à la main** — fenêtres
allumées, ombres portées réorientées. Ma conversion est **colorimétrique** :
on obtient une ville bleutée sous la lune, cohérente et lisible, mais **pas
de sources de lumière**.

Les fichiers générés restent remplaçables : le jour où des tuiles peintes
existent, on écrase les `_Night.tile`, rien d'autre ne bouge.

---

## Validation

Lua **651/651** · `.resx` **576/576** · zones + index **208/208** ·
`master_zone` **80/80 cohérent** · `verify_legend`, `verify_bg_format`,
`verify_scene_positions` au vert.

Positions des 3 PNJ nocturnes **vérifiées libres** sur les obstacles.
Espèces (granbull, murkrow, noctowl) **vérifiées** dans `MonsterFeature.json`.

## Non testé

**Rien n'est testé en jeu.** À vérifier en priorité :
- le rendu réel des tuiles nocturnes à l'écran (la planche est un aperçu de
  24 tuiles sur 14 958) ;
- que le moteur accepte bien les `.tile` réécrits — le roundtrip prouve que
  le format est respecté, pas que le chargeur les avale ;
- l'enchaînement retour de donjon → choix → ville de nuit → coucher.

Le choix n'est branché que sur le **chapitre 6** (`zone/gloomy_forest`) pour
l'instant : c'est le point d'entrée de test. Les 7 autres donjons suivront
une fois le circuit validé à l'écran.
