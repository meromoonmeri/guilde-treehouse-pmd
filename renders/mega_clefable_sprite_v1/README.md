# Méga-Mélodelfe (Mega Clefable) — proposition de sprite SpriteCollab 0036/0001 (lot `mega_clefable_sprite_v1`)

## Relecture du dépôt PMDCollab/SpriteCollab (@aae4cee2, 2026-09-22)
`tracker.json` → `0036 Clefable` : base complète (CHUNSOFT), `0036/0000/0001 Shiny` complète, `0036/0002 Altcolor` complète (mod reward),
**`0036/0001 Mega` : `sprite_complete 0`, aucun crédit — emplacement vide**. Il n'existe donc pas encore de sprite Méga-Mélodelfe dans le dépôt ; ce lot est une proposition, il ne remplace rien.

## Méthode (dérivée, générée — non native)
Base : les 13 animations CHUNSOFT de `sprite/0036` (Walk, Attack, Strike=CopyOf Attack, Withdraw, Dance, Sleep, Hurt, Idle, Swing, Double, Hop, Charge, Rotate), copiées dans `source/mega_clefable_sprite_v1/references/spritecollab_0036/` (SHA256 dans le manifest).
Pour chaque frame et chaque direction, sans changer tailles ni durées :
- transfert de palette (13 couleurs natives → pêche du corps, ailes rose vif, table dans `manifest.json`) ;
- ailes élargies d'un pixel + pointes jaunes sur la partie externe (d'après l'art officiel Légendes Z-A : grandes ailes roses à bouts jaunes) ;
- calotte de cheveux blancs sur le haut de la silhouette + petite boucle ;
- menottes noires posées sur les marqueurs de mains rouge/bleu de `Offsets.png`.
`AnimData.xml`, `*-Offsets.png`, `*-Shadow.png` sont **identiques octet pour octet** à la base : centres, mains, tête et ombres restent corrects.

## Critères du format (PMDOWiki « PMD Sprite Format ») — `verify.py` 52/52 PASS
noms uniques ≤ 44, CopyOf sans chaînage, 3 PNG de même taille par anim, dimensions de frame paires, frames = nombre de `<Duration>`, 8 directions, silhouette native conservée (aucun pixel natif rendu transparent), ≤ 15 couleurs par feuille (règle des portraits, appliquée par prudence).

## Fichiers
`sprite/0036/0001/` (AnimData.xml, 36 PNG, credits.txt), `0036_0001_mega_clefable_spritecollab.zip`, `comparatif_{Idle,Walk,Attack,Sleep}_x2.png` (base | Méga), `manifest.json`.
Limites : pixels générés par règles, pas de nouveau dessin manuel ; la soumission réelle passe par le Discord SpriteCollab (template `!sprite`, même nom de zip) et une relecture humaine. Non testé en moteur.
